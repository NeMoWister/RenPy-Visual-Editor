                       
"""
Диалог импорта .rpy-сценария: парсит файл в SceneNode-узлы, показывает
предпросмотр распознанных сцен и процент нераспознанных строк, после чего
добавляет выбранные сцены в текущий проект.
"""
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog,
    QTreeWidget, QTreeWidgetItem, QMessageBox, QSplitter, QTextEdit,
    QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor

from core.rpy_script_import import parse_script, ScriptImportReport
from core.models import Scene
from core.i18n import tr


class ImportScriptDialog(QDialog):
    scenes_imported = pyqtSignal(list)                

    def __init__(self, resource_manager=None, parent=None):
        super().__init__(parent)
        self.rm = resource_manager
        self.report: ScriptImportReport = ScriptImportReport()
        self.setWindowTitle(tr("import_script.title"))
        self.setMinimumSize(880, 600)
        from ui.theme import fit_window_to_screen
        fit_window_to_screen(self, 880, 600, min_w=700, min_h=480)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        hint = QLabel(tr("import_script.hint"))
        hint.setWordWrap(True)
        hint.setObjectName("hint_text")
        layout.addWidget(hint)

        top_row = QHBoxLayout()
        btn_file = QPushButton(tr("import_script.open_file"))
        btn_file.clicked.connect(self._pick_file)
        top_row.addWidget(btn_file)
        self.file_lbl = QLabel(tr("import_script.no_file"))
        self.file_lbl.setObjectName("hint_text")
        top_row.addWidget(self.file_lbl, 1)
        layout.addLayout(top_row)

        self.stat_lbl = QLabel("")
        self.stat_lbl.setObjectName("hint_text")
        layout.addWidget(self.stat_lbl)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter, 1)

                                              
        left_w = QLabel.__new__(QLabel)
        from PyQt6.QtWidgets import QWidget
        left_w = QWidget()
        left_l = QVBoxLayout(left_w)
        left_l.setContentsMargins(0, 0, 0, 0)
        left_l.addWidget(QLabel(tr("import_script.found_scenes")))

        check_row = QHBoxLayout()
        btn_all = QPushButton(tr("import_script.all"))
        btn_all.setObjectName("btn_secondary")
        btn_all.setFixedWidth(70)
        btn_all.clicked.connect(self._check_all)
        check_row.addWidget(btn_all)
        btn_none = QPushButton(tr("import_script.none"))
        btn_none.setObjectName("btn_secondary")
        btn_none.setFixedWidth(120)
        btn_none.clicked.connect(self._check_none)
        check_row.addWidget(btn_none)
        check_row.addStretch()
        left_l.addLayout(check_row)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([tr("import_script.col_scene_node")])
        self.tree.setColumnCount(1)
        self.tree.itemChanged.connect(self._on_item_changed)
        left_l.addWidget(self.tree, 1)
        splitter.addWidget(left_w)

                                               
        right_w = QWidget()
        right_l = QVBoxLayout(right_w)
        right_l.setContentsMargins(0, 0, 0, 0)
        right_l.addWidget(QLabel(tr("import_script.unrecognized_label")))
        self.unrecog_edit = QTextEdit()
        self.unrecog_edit.setReadOnly(True)
        self.unrecog_edit.setPlaceholderText(tr("import_script.unrecognized_placeholder"))
        self.unrecog_edit.setObjectName("code_box")
        right_l.addWidget(self.unrecog_edit, 1)

        right_l.addWidget(QLabel(tr("import_script.needs_resource_label")))
        self.needs_res_edit = QTextEdit()
        self.needs_res_edit.setReadOnly(True)
        self.needs_res_edit.setPlaceholderText(tr("import_script.needs_resource_placeholder"))
        self.needs_res_edit.setObjectName("warning_banner")
        right_l.addWidget(self.needs_res_edit, 1)
        splitter.addWidget(right_w)
        splitter.setSizes([560, 300])

        btn_bottom = QHBoxLayout()
        btn_cancel = QPushButton(tr("import_script.cancel"))
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_bottom.addWidget(btn_cancel)
        btn_bottom.addStretch()
        self.btn_import = QPushButton(tr("import_script.import_selected"))
        self.btn_import.setEnabled(False)
        self.btn_import.clicked.connect(self._import)
        btn_bottom.addWidget(self.btn_import)
        layout.addLayout(btn_bottom)

                                                                          

    def _pick_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("import_script.open_file_title"), "", "Ren'Py script (*.rpy)")
        if not path:
            return
        self.file_lbl.setText(os.path.basename(path))
        try:
            with open(path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            QMessageBox.critical(self, tr("import_script.read_error_title"), str(e))
            return
        self.report = parse_script(text, os.path.basename(path), rm=self.rm)
        self._fill_tree()
        self._fill_unrecognized()

                                                                           

    def _fill_tree(self):
        self.tree.blockSignals(True)
        self.tree.clear()
        for scene in self.report.scenes:
            scene_item = QTreeWidgetItem([scene.name])
            scene_item.setFlags(scene_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            scene_item.setCheckState(0, Qt.CheckState.Checked)
            scene_item.setData(0, Qt.ItemDataRole.UserRole, scene)
            for node in scene.nodes:
                node_item = QTreeWidgetItem([node.preview_text()])
                node_item.setFlags(node_item.flags() & ~Qt.ItemFlag.ItemIsUserCheckable)
                if node.node_type.value == 'raw':
                    node_item.setForeground(0, QColor("#ff9955"))
                self.tree.addTopLevelItem(scene_item)
                scene_item.addChild(node_item)
            scene_item.setExpanded(True)

        self.tree.blockSignals(False)

        ok = self.report.total_nodes > 0
        raw = sum(
            1 for sc in self.report.scenes
            for n in sc.nodes if n.node_type.value == 'raw'
        )
        pct = self.report.recognized_pct
        self.stat_lbl.setText(
            tr("import_script.stats", scenes=len(self.report.scenes),
               nodes=self.report.total_nodes, pct=pct, raw=raw)
        )
        self.btn_import.setEnabled(ok)

    def _fill_unrecognized(self):
        if not self.report.unrecognized:
            self.unrecog_edit.setPlainText("")
        else:
            lines = [tr("import_script.line_prefix", line=ln, text=txt) for ln, txt in self.report.unrecognized]
            self.unrecog_edit.setPlainText('\n'.join(lines))

        needs_res = getattr(self.report, "needs_resource", [])
        if not needs_res:
            self.needs_res_edit.setPlainText("")
        else:
            lines = [tr("import_script.needs_res_line", line=ln, text=txt, var=var) for ln, txt, var in needs_res]
            self.needs_res_edit.setPlainText('\n'.join(lines))

                                                                          

    def _on_item_changed(self, item, col):
        pass                                    

    def _check_all(self):
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setCheckState(0, Qt.CheckState.Checked)
        self.tree.blockSignals(False)

    def _check_none(self):
        self.tree.blockSignals(True)
        for i in range(self.tree.topLevelItemCount()):
            self.tree.topLevelItem(i).setCheckState(0, Qt.CheckState.Unchecked)
        self.tree.blockSignals(False)

                                                                          

    def _import(self):
        selected = []
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            if item.checkState(0) == Qt.CheckState.Checked:
                scene = item.data(0, Qt.ItemDataRole.UserRole)
                if scene:
                    selected.append(scene)
        if not selected:
            QMessageBox.information(self, tr("import_script.dialog_title"), tr("import_script.no_scenes_selected"))
            return
        self.scenes_imported.emit(selected)
        self.accept()
