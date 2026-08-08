from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QLineEdit, QMessageBox, QAbstractItemView, QProgressDialog
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.git_scene_commit import (
    read_json_file, read_head_json, diff_scenes, commit_selected_scenes,
    STATUS_ADDED, STATUS_MODIFIED, STATUS_REMOVED,
)
from core.i18n import tr

def _status_label():
    return {
        STATUS_ADDED: tr("git_scene_commit.status_added"),
        STATUS_MODIFIED: tr("git_scene_commit.status_modified"),
        STATUS_REMOVED: tr("git_scene_commit.status_removed"),
    }

_STATUS_COLOR = {STATUS_ADDED: "#6fd68f", STATUS_MODIFIED: "#ffb84d", STATUS_REMOVED: "#ff6b6b"}


class _PartialCommitWorker(QThread):
    done = pyqtSignal(bool, str)
    progress = pyqtSignal(int, int)

    def __init__(self, repo_dir, project_abs_path, relpath, selected, message, parent=None):
        super().__init__(parent)
        self.repo_dir = repo_dir
        self.project_abs_path = project_abs_path
        self.relpath = relpath
        self.selected = selected
        self.message = message

    def run(self):
        try:
            ok, out = commit_selected_scenes(
                self.repo_dir, self.project_abs_path, self.relpath,
                self.selected, self.message,
                on_progress=lambda done, total: self.progress.emit(done, total),
            )
        except Exception as e:
            ok, out = False, tr("git_scene_commit.unexpected_error", error=e)
        self.done.emit(ok, out)


class GitScenePartialCommitDialog(QDialog):
    """Коммит только по выбранным сценам - остальные изменения остаются
    несохранёнными в истории (но никуда не пропадают из самого файла на
    диске/в редакторе, см. core.git_scene_commit)."""            

    def __init__(self, repo_dir: str, project_abs_path: str, relpath: str, parent=None):
        super().__init__(parent)
        self.repo_dir = repo_dir
        self.project_abs_path = project_abs_path
        self.relpath = relpath
        self.setWindowTitle(tr("git_scene_commit.title"))
        self.setMinimumSize(560, 520)

        self.current_data = read_json_file(project_abs_path)
        self.old_data = read_head_json(repo_dir, relpath)
        self.diffs = diff_scenes(self.old_data, self.current_data or {}) if self.current_data else []

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        if self.current_data is None:
            layout.addWidget(QLabel(tr("git_scene_commit.read_failed")))
            return

        if not self.diffs:
            layout.addWidget(QLabel(tr("git_scene_commit.no_changes")))
            buttons = QHBoxLayout()
            buttons.addStretch()
            close_btn = QPushButton(tr("git_scene_commit.close"))
            close_btn.clicked.connect(self.reject)
            buttons.addWidget(close_btn)
            layout.addLayout(buttons)
            return

        layout.addWidget(QLabel(tr("git_scene_commit.info")))

        self.lst = QListWidget()
        self.lst.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        for entry in self.diffs:
            item = QListWidgetItem(f"{_status_label().get(entry.status, entry.status)}  -  {entry.name}")
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked)
            item.setForeground(QColor(_STATUS_COLOR.get(entry.status, "#ccc")))
            item.setData(Qt.ItemDataRole.UserRole, entry.scene_id)
            self.lst.addItem(item)
        layout.addWidget(self.lst, 1)

        sel_row = QHBoxLayout()
        btn_all = QPushButton(tr("git_scene_commit.check_all"))
        btn_all.clicked.connect(lambda: self._set_all(Qt.CheckState.Checked))
        sel_row.addWidget(btn_all)
        btn_none = QPushButton(tr("git_scene_commit.check_none"))
        btn_none.clicked.connect(lambda: self._set_all(Qt.CheckState.Unchecked))
        sel_row.addWidget(btn_none)
        sel_row.addStretch()
        layout.addLayout(sel_row)

        layout.addWidget(QLabel(tr("git_scene_commit.message_label")))
        self.msg_edit = QLineEdit()
        self.msg_edit.setPlaceholderText(tr("git_scene_commit.message_placeholder"))
        layout.addWidget(self.msg_edit)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton(tr("git_scene_commit.cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_commit = QPushButton(tr("git_scene_commit.commit_selected"))
        btn_commit.setObjectName("btn_primary")
        btn_commit.clicked.connect(self._do_commit)
        btn_row.addWidget(btn_commit)
        layout.addLayout(btn_row)

    def _set_all(self, state):
        for i in range(self.lst.count()):
            self.lst.item(i).setCheckState(state)

    def _do_commit(self):
        selected = set()
        for i in range(self.lst.count()):
            item = self.lst.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.add(item.data(Qt.ItemDataRole.UserRole))
        if not selected:
            QMessageBox.information(self, tr("git_scene_commit.nothing_selected_title"), tr("git_scene_commit.nothing_selected_text"))
            return
        message = self.msg_edit.text().strip() or tr("git_scene_commit.default_message")

        progress = QProgressDialog(tr("git_scene_commit.progress_prepare"), None, 0, 0, self)
        progress.setWindowTitle(tr("git_scene_commit.progress_title"))
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.setMinimumDuration(300)
        progress.setCancelButton(None)

        result = {}
        worker = _PartialCommitWorker(self.repo_dir, self.project_abs_path,
                                       self.relpath, selected, message, self)

        def on_progress(done, total):
            if total:
                progress.setMaximum(total)
                progress.setValue(done)
                progress.setLabelText(tr("git_scene_commit.progress_adding", done=done, total=total))
            else:
                progress.setLabelText(tr("git_scene_commit.progress_committing"))

        def on_done(ok, out):
            result["ok"] = ok
            result["out"] = out
            progress.close()

        worker.progress.connect(on_progress)
        worker.done.connect(on_done)
        worker.start()
        progress.exec()
        worker.wait()

        ok, out = result.get("ok", False), result.get("out", "")
        if not ok:
            QMessageBox.critical(self, tr("git_scene_commit.error_title"), out)
            return
        QMessageBox.information(
            self, tr("git_scene_commit.done_title"),
            tr("git_scene_commit.done_text", committed=len(selected), total=len(self.diffs))
        )
        self.accept()
