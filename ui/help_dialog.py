

from PyQt6 .QtWidgets import QDialog ,QVBoxLayout ,QDialogButtonBox 

from ui .help_content import USER_GUIDE_HTML ,HELP_IMAGES 
from ui .markdown_document import MarkdownView ,PALETTE 
from core .i18n import tr 


class HelpDialog (QDialog ):


    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .setWindowTitle (tr ("menu.help.guide_title"))
        self .resize (1280 ,720 )
        from ui .theme import fit_window_to_screen 
        fit_window_to_screen (self ,1280 ,720 ,min_w =760 ,min_h =520 )
        self ._setup_ui ()

    def _setup_ui (self ):
        layout =QVBoxLayout (self )
        layout .setContentsMargins (10 ,10 ,10 ,10 )
        layout .setSpacing (10 )

        self .viewer =MarkdownView (USER_GUIDE_HTML ,HELP_IMAGES )
        self .viewer .setStyleSheet (f"""
            QTextBrowser {{
                background: {PALETTE ['background']};
                color: {PALETTE ['text']};
                border: 1px solid {PALETTE ['border']};
                border-radius: 6px;
            }}
        """)
        layout .addWidget (self .viewer )

        buttons =QDialogButtonBox (QDialogButtonBox .StandardButton .Close )
        buttons .button (QDialogButtonBox .StandardButton .Close ).clicked .connect (self .accept )
        layout .addWidget (buttons )
