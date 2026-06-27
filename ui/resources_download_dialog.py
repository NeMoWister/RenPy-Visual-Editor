from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

RESOURCES_URL = "https://disk.yandex.ru/d/SqnaZquLyvZ6-Q"


class ResourcesDownloadDialog(QDialog):
    """Окно со ссылкой на архив ресурсов, необходимых для создания модификаций,
    и краткой инструкцией по установке."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ресурсы для модификаций")
        self.resize(480, 220)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        title = QLabel("Ресурсы, необходимые для создания модификаций")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ff8c00;")
        title.setWordWrap(True)
        layout.addWidget(title)

        info = QLabel(
            "Архив скачать и распаковать в папку, где лежит .exe."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #ccc; font-size: 12px;")
        layout.addWidget(info)

        link_row = QHBoxLayout()
        link_label = QLabel(f'<a href="{RESOURCES_URL}" style="color:#5fb3ff;">{RESOURCES_URL}</a>')
        link_label.setOpenExternalLinks(True)
        link_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        link_label.setWordWrap(True)
        link_row.addWidget(link_label, 1)
        layout.addLayout(link_row)

        btn_row = QHBoxLayout()
        open_btn = QPushButton("🔗 Открыть ссылку в браузере")
        open_btn.clicked.connect(self._open_link)
        btn_row.addWidget(open_btn)
        layout.addLayout(btn_row)

        layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.accept)
        layout.addWidget(buttons)

    def _open_link(self):
        QDesktopServices.openUrl(QUrl(RESOURCES_URL))
