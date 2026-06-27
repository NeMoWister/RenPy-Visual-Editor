from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QDialogButtonBox
from PyQt6.QtCore import Qt
from ui.help_content import USER_GUIDE_MARKDOWN


class HelpDialog(QDialog):
    """Окно с подробным руководством пользователя. Текст встроен в
    приложение (ui/help_content.py), поэтому работает без интернета и не
    зависит от внешних файлов при распространении .exe."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Руководство пользователя")
        self.resize(820, 700)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setMarkdown(USER_GUIDE_MARKDOWN)
        browser.setStyleSheet("""
            QTextBrowser {
                background: #1e1e24;
                color: #ddd;
                border: 1px solid #3a3a4a;
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
            }
        """)
        layout.addWidget(browser)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
        buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.accept)
        layout.addWidget(buttons)
