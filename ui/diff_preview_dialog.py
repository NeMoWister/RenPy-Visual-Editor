"""
Предпросмотр диффа перед перезаписью существующего .rpy файла — чтобы не
потерять ручные правки, внесённые прямо в файл мимо редактора.
"""
import difflib
import os

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFileDialog
)
from PyQt6.QtGui import QTextCharFormat, QColor, QFont


class DiffPreviewDialog(QDialog):
    """После exec(): self.action — 'overwrite' / 'copy' / None (отменено).
    Если 'copy' — self.copy_path указывает, куда сохранить копию."""

    def __init__(self, old_text: str, new_text: str, target_path: str, parent=None):
        super().__init__(parent)
        self.target_path = target_path
        self.action = None
        self.copy_path = None
        self.setWindowTitle(f"Проверка изменений — {os.path.basename(target_path)}")
        self.setMinimumSize(880, 620)
        self._setup_ui(old_text, new_text)

    def _setup_ui(self, old_text: str, new_text: str):
        layout = QVBoxLayout(self)

        info = QLabel(
            f"Файл «{self.target_path}» уже существует и отличается от того, что "
            f"сгенерирует редактор. Если в нём есть ручные правки, сделанные мимо "
            f"редактора (например, напрямую в Ren'Py) — они будут потеряны при "
            f"перезаписи. Красным — что удалится, зелёным — что добавится."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#ffb84d; background:#332a1a; padding:6px; border-radius:4px;")
        layout.addWidget(info)

        self.diff_view = QTextEdit()
        self.diff_view.setReadOnly(True)
        self.diff_view.setFont(QFont("Consolas", 10))
        self.diff_view.setStyleSheet("background:#1a1a21; color:#ccc;")
        layout.addWidget(self.diff_view, 1)

        self._render_diff(old_text, new_text)

        stats = self._diff_stats(old_text, new_text)
        stats_lbl = QLabel(stats)
        stats_lbl.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(stats_lbl)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self._on_cancel)
        btn_row.addWidget(btn_cancel)
        btn_copy = QPushButton("💾 Сохранить копию рядом")
        btn_copy.clicked.connect(self._on_save_copy)
        btn_row.addWidget(btn_copy)
        btn_overwrite = QPushButton("⚠ Перезаписать существующий файл")
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
        return f"Добавлено строк: {added}   •   Удалено строк: {removed}"

    def _render_diff(self, old_text: str, new_text: str):
        old_lines = old_text.splitlines()
        new_lines = new_text.splitlines()
        diff = difflib.unified_diff(old_lines, new_lines, lineterm="",
                                     fromfile="текущий файл на диске", tofile="то, что сгенерирует редактор")

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
            cursor.insertText("(файлы идентичны построчно)", fmt_default)

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
            self, "Сохранить копию рядом", suggested,
            "Ren'Py Script (*.rpy);;Все файлы (*)"
        )
        if not path:
            return
        self.action = "copy"
        self.copy_path = path
        self.accept()
