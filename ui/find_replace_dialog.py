"""
Диалог «Найти и заменить» - массовая замена текста по всем репликам
сценария (не только при импорте). Показывает предпросмотр совпадений
перед заменой.
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QCheckBox, QListWidget, QListWidgetItem, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

from core.find_replace import find_matches, apply_replace_all
from core.models import Project


class FindReplaceDialog(QDialog):
    replaced = pyqtSignal()

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Найти и заменить по всему сценарию")
        self.setMinimumSize(560, 460)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        find_row = QHBoxLayout()
        find_row.addWidget(QLabel("Найти:"))
        self.find_edit = QLineEdit()
        self.find_edit.textChanged.connect(self._update_preview)
        find_row.addWidget(self.find_edit, 1)
        layout.addLayout(find_row)

        replace_row = QHBoxLayout()
        replace_row.addWidget(QLabel("Заменить на:"))
        self.replace_edit = QLineEdit()
        replace_row.addWidget(self.replace_edit, 1)
        layout.addLayout(replace_row)

        opts_row = QHBoxLayout()
        self.case_check = QCheckBox("Учитывать регистр")
        self.case_check.toggled.connect(self._update_preview)
        opts_row.addWidget(self.case_check)
        self.whole_word_check = QCheckBox("Только целые слова")
        self.whole_word_check.toggled.connect(self._update_preview)
        opts_row.addWidget(self.whole_word_check)
        self.comments_check = QCheckBox("Включая комментарии")
        self.comments_check.toggled.connect(self._update_preview)
        opts_row.addWidget(self.comments_check)
        opts_row.addStretch()
        layout.addLayout(opts_row)

        self.result_lbl = QLabel("Введите текст для поиска.")
        self.result_lbl.setStyleSheet("color:#aaa; font-size:11px;")
        layout.addWidget(self.result_lbl)

        self.preview_list = QListWidget()
        self.preview_list.setStyleSheet("font-size:11px;")
        layout.addWidget(self.preview_list, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_replace = QPushButton("Заменить всё")
        self.btn_replace.setObjectName("btn_primary")
        self.btn_replace.clicked.connect(self._do_replace)
        btn_row.addWidget(self.btn_replace)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.reject)
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _current_matches(self):
        query = self.find_edit.text()
        if not query:
            return []
        return find_matches(
            self.project, query,
            case_sensitive=self.case_check.isChecked(),
            whole_word=self.whole_word_check.isChecked(),
            include_comments=self.comments_check.isChecked(),
        )

    def _update_preview(self):
        self.preview_list.clear()
        matches = self._current_matches()
        if not self.find_edit.text():
            self.result_lbl.setText("Введите текст для поиска.")
            self.btn_replace.setEnabled(False)
            return

        for m in matches:
            item = QListWidgetItem(f"[{m.scene_name}] {m.field_label}: {m.snippet}")
            self.preview_list.addItem(item)

        if matches:
            self.result_lbl.setText(f"Найдено совпадений: {len(matches)}")
            self.btn_replace.setEnabled(True)
        else:
            self.result_lbl.setText("Совпадений не найдено.")
            self.btn_replace.setEnabled(False)

    def _do_replace(self):
        query = self.find_edit.text()
        if not query:
            return
        matches = self._current_matches()
        if not matches:
            return

        confirm = QMessageBox.question(
            self, "Подтверждение",
            f"Заменить все совпадения «{query}» → «{self.replace_edit.text()}» "
            f"({len(matches)} мест)? Это действие можно отменить через Ctrl+Z.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        count = apply_replace_all(
            self.project, query, self.replace_edit.text(),
            case_sensitive=self.case_check.isChecked(),
            whole_word=self.whole_word_check.isChecked(),
            include_comments=self.comments_check.isChecked(),
        )
        self.replaced.emit()
        QMessageBox.information(self, "Готово", f"Произведено замен: {count}.")
        self._update_preview()
