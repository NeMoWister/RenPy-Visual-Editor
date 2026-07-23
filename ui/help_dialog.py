                       
"""
Диалог руководства пользователя.

HTML-текст руководства лежит в help_content.py как USER_GUIDE_HTML
(готовый HTML, не Markdown). Скриншоты - в HELP_IMAGES (base64 PNG).
Рендерится через MarkdownView (по сути QTextBrowser + setHtml) с
тёмной темой.

Чтобы добавить скриншот в руководство:
1. Конвертируйте PNG в base64:
       import base64
       data = base64.b64encode(open("shot.png", "rb").read()).decode()
       print(f'HELP_IMAGES["my_key"] = "data:image/png;base64,{data}"')
2. Вставьте строку выше в help_content.py в словарь HELP_IMAGES.
3. В тексте USER_GUIDE_HTML напишите:
       <p align="center">
         <img src="{{my_key}}" alt="Подпись" width="100%">
       </p>
       <p align="center" style="color:#9a9a9a;font-style:italic;
          font-size:9pt;">Подпись под картинкой</p>
   Плейсхолдер {{my_key}} будет заменён на data URI при рендере.
   width="100%" растягивает на ширину окна; width="480" - фикс. ширина;
   без width - натуральный размер.
"""
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QDialogButtonBox

from ui.help_content import USER_GUIDE_HTML, HELP_IMAGES
from ui.markdown_document import MarkdownView, PALETTE


class HelpDialog(QDialog):
    """Окно с подробным руководством пользователя."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Руководство пользователя")
        self.resize(1280, 720)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        self.viewer = MarkdownView(USER_GUIDE_HTML, HELP_IMAGES)
        self.viewer.setStyleSheet(f"""
            QTextBrowser {{
                background: {PALETTE['background']};
                color: {PALETTE['text']};
                border: 1px solid {PALETTE['border']};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(self.viewer)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).clicked.connect(self.accept)
        layout.addWidget(buttons)
