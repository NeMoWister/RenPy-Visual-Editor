"""
Диалог «Экспорт/импорт для вычитки» — экспорт сценария в простой текстовый
формат и импорт правок текста обратно (раунд-трип для редактора/сценариста
без программы).
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QFileDialog, QMessageBox
)
from PyQt6.QtCore import pyqtSignal

from core.screenplay_text import export_screenplay, apply_screenplay_import
from core.models import Project


class ScreenplayExportImportDialog(QDialog):
    imported = pyqtSignal()

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle("Экспорт/импорт текста для вычитки")
        self.setMinimumSize(720, 560)
        self._setup_ui()
        self._refresh_export()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(
            "Экспортируйте текст, отдайте редактору/сценаристу на вычитку (можно править "
            "в любом текстовом редакторе), затем вставьте отредактированный текст сюда "
            "и нажмите «Импортировать правки». Строки в [квадратных скобках] и хвостовые "
            "метки {#...} — служебные, их менять не нужно."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color:#888; font-size:11px;")
        layout.addWidget(info)

        btn_row = QHBoxLayout()
        btn_save = QPushButton("💾 Сохранить в файл...")
        btn_save.clicked.connect(self._save_to_file)
        btn_row.addWidget(btn_save)
        btn_load = QPushButton("📂 Загрузить из файла...")
        btn_load.clicked.connect(self._load_from_file)
        btn_row.addWidget(btn_load)
        btn_row.addStretch()
        btn_reexport = QPushButton("🔄 Пересобрать из текущего проекта")
        btn_reexport.clicked.connect(self._refresh_export)
        btn_row.addWidget(btn_reexport)
        layout.addLayout(btn_row)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("font-family: monospace; font-size:12px;")
        layout.addWidget(self.text_edit, 1)

        bottom = QHBoxLayout()
        bottom.addStretch()
        btn_import = QPushButton("⬅ Импортировать правки в проект")
        btn_import.setObjectName("btn_primary")
        btn_import.clicked.connect(self._import_edits)
        bottom.addWidget(btn_import)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        bottom.addWidget(btn_close)
        layout.addLayout(bottom)

    def _refresh_export(self):
        self.text_edit.setPlainText(export_screenplay(self.project))

    def _save_to_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить текст для вычитки", "script_for_proofreading.txt",
            "Текстовый файл (*.txt);;Все файлы (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            QMessageBox.information(self, "Готово", f"Сохранено:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Загрузить текст с правками", "",
            "Текстовый файл (*.txt);;Все файлы (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.text_edit.setPlainText(f.read())
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def _import_edits(self):
        text = self.text_edit.toPlainText()
        result = apply_screenplay_import(self.project, text)
        msg = f"Обновлено реплик/строк: {result.updated}."
        if result.unmatched:
            shown = ", ".join(result.unmatched[:10])
            more = f" и ещё {len(result.unmatched) - 10}" if len(result.unmatched) > 10 else ""
            msg += (f"\n\nНе найдено в текущем проекте (устарели/удалены): "
                    f"{len(result.unmatched)}\n{shown}{more}")
        QMessageBox.information(self, "Импорт завершён", msg)
        self.imported.emit()
        self.accept()
