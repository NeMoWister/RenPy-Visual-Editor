                       
"""
Окно "Доступно обновление" и фоновый поток для проверки обновлений.

Проверка всегда выполняется в отдельном QThread, чтобы поход в сеть
(или таймаут при его отсутствии) не подвешивал интерфейс при запуске.
"""
from typing import Optional, Dict
from PyQt6.QtCore import QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QTextEdit
)

from core.updater import check_for_update, APP_VERSION


class UpdateCheckThread(QThread):
    """Запускает check_for_update() в фоне. Сигнал отдаёт dict с данными
    релиза, если найдено обновление новее текущей версии, иначе None."""
    finished_check = pyqtSignal(object)

    def run(self):
        try:
            result = check_for_update()
        except Exception:
            result = None
        self.finished_check.emit(result)


class UpdateAvailableDialog(QDialog):
    """Показывается, когда найдена версия новее текущей.

    skip_requested — пользователь нажал «Напомнить позже» (просто закрыть,
        больше не показывать ради этой конкретной версии, но проверять
        дальше при следующих запусках).
    disable_requested — пользователь снял галку «Проверять автоматически»;
        сохранение этого в настройки делает вызывающий код.
    """
    def __init__(self, release: Dict, parent=None):
        super().__init__(parent)
        self.release = release
        self.disable_autocheck = False
        self.setWindowTitle("Доступно обновление")
        self.setMinimumSize(460, 320)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel(f"Вышла новая версия: {self.release.get('version', '?')}")
        title.setStyleSheet("font-size:15px; font-weight:bold; color:#ff8c3d;")
        layout.addWidget(title)

        current = QLabel(f"Текущая версия: {APP_VERSION}")
        current.setStyleSheet("color:#aaa; font-size:11px;")
        layout.addWidget(current)

        notes = self.release.get("notes") or "(описание изменений не указано)"
        notes_edit = QTextEdit()
        notes_edit.setReadOnly(True)
        notes_edit.setPlainText(notes)
        notes_edit.setStyleSheet("background:#1c1c22; color:#ddd; border:1px solid #3a3a46;")
        layout.addWidget(notes_edit, 1)

        self.disable_check = QCheckBox("Не проверять обновления автоматически при запуске")
        self.disable_check.setStyleSheet("color:#ccc;")
        layout.addWidget(self.disable_check)

        btn_row = QHBoxLayout()
        btn_later = QPushButton("Напомнить позже")
        btn_later.setObjectName("btn_secondary")
        btn_later.clicked.connect(self._on_later)
        btn_row.addWidget(btn_later)
        btn_row.addStretch()
        btn_download = QPushButton("⬇ Скачать обновление")
        btn_download.clicked.connect(self._on_download)
        btn_row.addWidget(btn_download)
        layout.addLayout(btn_row)

    def _on_download(self):
        url = self.release.get("download_url") or self.release.get("page_url")
        if url:
            QDesktopServices.openUrl(QUrl(url))
        self.disable_autocheck = self.disable_check.isChecked()
        self.accept()

    def _on_later(self):
        self.disable_autocheck = self.disable_check.isChecked()
        self.reject()
