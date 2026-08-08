"""
Диалог «Экспорт/импорт для вычитки» - экспорт сценария в простой текстовый
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
from core.i18n import tr


class ScreenplayExportImportDialog(QDialog):
    imported = pyqtSignal()

    def __init__(self, project: Project, parent=None):
        super().__init__(parent)
        self.project = project
        self.setWindowTitle(tr("screenplay.title"))
        self.setMinimumSize(720, 560)
        self._setup_ui()
        self._refresh_export()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        info = QLabel(tr("screenplay.info"))
        info.setWordWrap(True)
        info.setObjectName("hint_text")
        layout.addWidget(info)

        btn_row = QHBoxLayout()
        btn_save = QPushButton(tr("screenplay.save_to_file"))
        btn_save.clicked.connect(self._save_to_file)
        btn_row.addWidget(btn_save)
        btn_load = QPushButton(tr("screenplay.load_from_file"))
        btn_load.clicked.connect(self._load_from_file)
        btn_row.addWidget(btn_load)
        btn_row.addStretch()
        btn_reexport = QPushButton(tr("screenplay.rebuild"))
        btn_reexport.clicked.connect(self._refresh_export)
        btn_row.addWidget(btn_reexport)
        layout.addLayout(btn_row)

        self.text_edit = QTextEdit()
        self.text_edit.setStyleSheet("font-family: monospace; font-size:12px;")
        layout.addWidget(self.text_edit, 1)

        bottom = QHBoxLayout()
        bottom.addStretch()
        btn_import = QPushButton(tr("screenplay.import_edits"))
        btn_import.setObjectName("btn_primary")
        btn_import.clicked.connect(self._import_edits)
        bottom.addWidget(btn_import)
        btn_close = QPushButton(tr("screenplay.close"))
        btn_close.clicked.connect(self.accept)
        bottom.addWidget(btn_close)
        layout.addLayout(bottom)

    def _refresh_export(self):
        self.text_edit.setPlainText(export_screenplay(self.project))

    def _save_to_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, tr("screenplay.save_dialog_title"), "script_for_proofreading.txt",
            f"{tr('screenplay.text_files')} (*.txt);;{tr('screenplay.all_files')} (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            QMessageBox.information(self, tr("screenplay.done_title"), tr("screenplay.saved_text", path=path))
        except Exception as e:
            QMessageBox.critical(self, tr("screenplay.error_title"), str(e))

    def _load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("screenplay.load_dialog_title"), "",
            f"{tr('screenplay.text_files')} (*.txt);;{tr('screenplay.all_files')} (*)"
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.text_edit.setPlainText(f.read())
        except Exception as e:
            QMessageBox.critical(self, tr("screenplay.error_title"), str(e))

    def _import_edits(self):
        text = self.text_edit.toPlainText()
        result = apply_screenplay_import(self.project, text)
        msg = tr("screenplay.updated_lines", count=result.updated)
        if result.unmatched:
            shown = ", ".join(result.unmatched[:10])
            more = tr("screenplay.unmatched_more", count=len(result.unmatched) - 10) if len(result.unmatched) > 10 else ""
            msg += tr("screenplay.unmatched_text", count=len(result.unmatched), shown=shown, more=more)
        QMessageBox.information(self, tr("screenplay.import_done_title"), msg)
        self.imported.emit()
        self.accept()
