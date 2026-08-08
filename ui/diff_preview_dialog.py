"""
Предпросмотр диффа перед перезаписью существующего .rpy файла - чтобы не
потерять ручные правки, внесённые прямо в файл мимо редактора.

Помимо "всё или ничего" (перезаписать / сохранить копию), есть построчный
merge-помощник (HunkMergeDialog): каждый непересекающийся кусок различий
(хунк) можно принять (взять сгенерированную версию) или отклонить (оставить
как в файле на диске) по отдельности.
"""
import difflib
import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFileDialog, QScrollArea, QWidget, QFrame, QButtonGroup, QRadioButton
)
from PyQt6.QtGui import QTextCharFormat, QColor, QFont

from core.i18n import tr


class HunkMergeDialog(QDialog):
    """Построчный merge: каждый хунк (блок различий) можно принять
    (сгенерированная версия) или отклонить (оставить как в файле на диске).
    После exec(): self.accepted_merge и self.merged_text (итоговый текст)."""

    def __init__(self, old_text: str, new_text: str, target_path: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("diff.merge_title", name=os.path.basename(target_path)))
        self.setMinimumSize(920, 650)
        from ui.theme import fit_window_to_screen
        fit_window_to_screen(self, 920, 650, min_w=760, min_h=520)
        self.accepted_merge = False
        self.merged_text = new_text

        self.old_lines = old_text.splitlines()
        self.new_lines = new_text.splitlines()
        self.opcodes = difflib.SequenceMatcher(a=self.old_lines, b=self.new_lines).get_opcodes()
                                                                      
        self._hunk_choices = {}                                     

        layout = QVBoxLayout(self)
        info = QLabel(tr("diff.merge_info"))
        info.setWordWrap(True)
        info.setObjectName("info_banner")
        info.setStyleSheet("padding:6px;")
        layout.addWidget(info)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setSpacing(10)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)

        mono = QFont("Consolas", 10)
        n_hunks = 0
        for idx, (tag, i1, i2, j1, j2) in enumerate(self.opcodes):
            if tag == "equal":
                if i2 - i1 > 0:
                    ctx = QLabel("\n".join(self.old_lines[i1:i2][:4]) +
                                 ("\n…" if i2 - i1 > 4 else ""))
                    ctx.setFont(mono)
                    ctx.setObjectName("hint_text")
                    ctx.setStyleSheet("padding:2px 6px;")
                    self._content_layout.addWidget(ctx)
                continue

            n_hunks += 1
            box = QFrame()
            box.setObjectName("surface_frame")
            box_l = QVBoxLayout(box)

            group = QButtonGroup(box)
            row = QHBoxLayout()
            rb_new = QRadioButton(tr("diff.accept_new"))
            rb_old = QRadioButton(tr("diff.keep_old"))
            rb_new.setChecked(True)                                             
            group.addButton(rb_new, 1)
            group.addButton(rb_old, 0)
            row.addWidget(rb_new)
            row.addWidget(rb_old)
            row.addStretch()
            box_l.addLayout(row)

            old_block = "\n".join(self.old_lines[i1:i2]) if i2 > i1 else tr("diff.no_lines")
            new_block = "\n".join(self.new_lines[j1:j2]) if j2 > j1 else tr("diff.lines_removed")

            old_view = QTextEdit(old_block)
            old_view.setReadOnly(True)
            old_view.setFont(mono)
            old_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
            self._size_hunk_view(old_view, max(1, i2 - i1))
            old_view.setObjectName("danger_banner")
            box_l.addWidget(QLabel(tr("diff.from_disk")))
            box_l.addWidget(old_view)

            new_view = QTextEdit(new_block)
            new_view.setReadOnly(True)
            new_view.setFont(mono)
            new_view.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
            self._size_hunk_view(new_view, max(1, j2 - j1))
            new_view.setObjectName("success_banner")
            box_l.addWidget(QLabel(tr("diff.generated_by_editor")))
            box_l.addWidget(new_view)

            self._hunk_choices[idx] = group
            self._content_layout.addWidget(box)

        if n_hunks == 0:
            self._content_layout.addWidget(QLabel(tr("diff.identical_no_merge")))

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton(tr("diff.cancel"))
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)
        btn_apply = QPushButton(tr("diff.apply_merge", count=n_hunks))
        btn_apply.setObjectName("btn_primary")
        btn_apply.setEnabled(n_hunks > 0)
        btn_apply.clicked.connect(self._apply_merge)
        btn_row.addWidget(btn_apply)
        layout.addLayout(btn_row)

    def _size_hunk_view(self, view: QTextEdit, n_lines: int):
        """Раньше высота считалась как 24px/строку с потолком в 140px - на
        практике из-за отступов QTextEdit и переноса строк одна-две строки
        схлопывались в нечитаемую полоску. Теперь считаем по реальной
        высоте строки шрифта + отступы, с щедрым минимумом на 2 строки."""
        fm = view.fontMetrics()
        line_h = fm.lineSpacing()
        margins = view.contentsMargins()
        padding = margins.top() + margins.bottom() + 16                             
        visible_lines = max(2, min(n_lines, 12))
        height = visible_lines * line_h + padding
        height = max(64, min(280, height))
        view.setMinimumHeight(height)
        view.setMaximumHeight(height)

    def _apply_merge(self):
        result_lines = []
        for idx, (tag, i1, i2, j1, j2) in enumerate(self.opcodes):
            if tag == "equal":
                result_lines.extend(self.old_lines[i1:i2])
                continue
            group = self._hunk_choices.get(idx)
            use_new = group.checkedId() == 1 if group else True
            if use_new:
                result_lines.extend(self.new_lines[j1:j2])
            else:
                result_lines.extend(self.old_lines[i1:i2])
        self.merged_text = "\n".join(result_lines) + ("\n" if result_lines else "")
        self.accepted_merge = True
        self.accept()


class DiffPreviewDialog(QDialog):
    """После exec(): self.action - 'overwrite' / 'copy' / None (отменено).
    Если 'copy' - self.copy_path указывает, куда сохранить копию."""

    def __init__(self, old_text: str, new_text: str, target_path: str, parent=None):
        super().__init__(parent)
        self.target_path = target_path
        self.action = None
        self.copy_path = None
        self.merged_text = None
        self.setWindowTitle(tr("diff.preview_title", name=os.path.basename(target_path)))
        self.setMinimumSize(880, 620)
        self._old_text = old_text
        self._new_text = new_text
        self._setup_ui(old_text, new_text)

    def _setup_ui(self, old_text: str, new_text: str):
        layout = QVBoxLayout(self)

        info = QLabel(tr("diff.overwrite_warning", path=self.target_path))
        info.setWordWrap(True)
        info.setObjectName("warning_banner")
        info.setStyleSheet("padding:6px;")
        layout.addWidget(info)

        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setFont(QFont("Consolas", 10))
        self.diff_view.setObjectName("code_box")
        layout.addWidget(self.diff_view, 1)

        self._render_diff(old_text, new_text)

        stats = self._diff_stats(old_text, new_text)
        stats_lbl = QLabel(stats)
        stats_lbl.setObjectName("hint_text")
        layout.addWidget(stats_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton(tr("diff.cancel"))
        btn_cancel.clicked.connect(self._on_cancel)
        btn_row.addWidget(btn_cancel)
        btn_copy = QPushButton(tr("diff.save_copy"))
        btn_copy.clicked.connect(self._on_save_copy)
        btn_row.addWidget(btn_copy)
        btn_merge = QPushButton(tr("diff.merge_button"))
        btn_merge.clicked.connect(self._on_merge)
        btn_row.addWidget(btn_merge)
        btn_overwrite = QPushButton(tr("diff.overwrite_button"))
        btn_overwrite.setObjectName("btn_primary")
        btn_overwrite.clicked.connect(self._on_overwrite)
        btn_row.addWidget(btn_overwrite)
        layout.addLayout(btn_row)

    def _diff_stats(self, old_text: str, new_text: str) -> str:
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        sm = difflib.SequenceMatcher(a=old_lines, b=new_lines)
        added = removed = 0
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "replace":
                removed += i2 - i1
                added += j2 - j1
            elif tag == "delete":
                removed += i2 - i1
            elif tag == "insert":
                added += j2 - j1
        return tr("diff.stats", added=added, removed=removed)

    def _render_diff(self, old_text: str, new_text: str):
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        diff = difflib.unified_diff(old_lines, new_lines, lineterm="",
                                     fromfile=tr("diff.fromfile_label"), tofile=tr("diff.tofile_label"))

        cursor = self.diff_view.textCursor()
        fmt_add = QTextCharFormat()
        fmt_add.setForeground(QColor("#7ee787"))
        fmt_del = QTextCharFormat()
        fmt_del.setForeground(QColor("#ff8a8a"))
        fmt_hunk = QTextCharFormat()
        fmt_hunk.setForeground(QColor("#7aa2ff"))
        fmt_default = QTextCharFormat()
        fmt_default.setForeground(QColor("#aaa"))

        any_lines = False
        for line in diff:
            any_lines = True
            if line.startswith("+++") or line.startswith("---") or line.startswith("@@"):
                cursor.insertText(line + "\n", fmt_hunk)
            elif line.startswith("+"):
                cursor.insertText(line + "\n", fmt_add)
            elif line.startswith("-"):
                cursor.insertText(line + "\n", fmt_del)
            else:
                cursor.insertText(line + "\n", fmt_default)

        if not any_lines:
            cursor.insertText(tr("diff.identical_lines"), fmt_default)

    def _on_cancel(self):
        self.action = None
        self.reject()

    def _on_overwrite(self):
        self.action = "overwrite"
        self.accept()

    def _on_save_copy(self):
        base, ext = os.path.splitext(self.target_path)
        suggested = f"{base}_new{ext}"
        path, _ = QFileDialog.getSaveFileName(
            self, tr("diff.save_copy_title"), suggested,
            f"Ren'Py Script (*.rpy);;{tr('diff.all_files')} (*)"
        )
        if not path:
            return
        self.action = "copy"
        self.copy_path = path
        self.accept()

    def _on_merge(self):
        merge_dlg = HunkMergeDialog(self._old_text, self._new_text, self.target_path, self)
        if merge_dlg.exec() == QDialog.DialogCode.Accepted and merge_dlg.accepted_merge:
            self.action = "merge"
            self.merged_text = merge_dlg.merged_text
            self.accept()
