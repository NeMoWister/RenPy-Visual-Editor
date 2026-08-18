

from typing import Optional ,Dict 
from PyQt6 .QtCore import QThread ,pyqtSignal ,QUrl 
from PyQt6 .QtGui import QDesktopServices 
from PyQt6 .QtWidgets import (
QDialog ,QVBoxLayout ,QHBoxLayout ,QLabel ,QPushButton ,
QCheckBox ,QTextEdit 
)

from core .updater import check_for_update ,APP_VERSION 
from core .i18n import tr 


class UpdateCheckThread (QThread ):

    finished_check =pyqtSignal (object )

    def run (self ):
        try :
            result =check_for_update ()
        except Exception :
            result =None 
        self .finished_check .emit (result )


class UpdateAvailableDialog (QDialog ):

    def __init__ (self ,release :Dict ,parent =None ):
        super ().__init__ (parent )
        self .release =release 
        self .disable_autocheck =False 
        self .setWindowTitle (tr ("update.title"))
        self .setMinimumSize (460 ,320 )
        self ._setup_ui ()

    def _setup_ui (self ):
        layout =QVBoxLayout (self )
        layout .setSpacing (12 )

        title =QLabel (tr ("update.new_version",version =self .release .get ('version','?')))
        title .setObjectName ("accent_caption")
        title .setStyleSheet ("font-size:15px;")
        layout .addWidget (title )

        current =QLabel (tr ("update.current_version",version =APP_VERSION ))
        current .setObjectName ("hint_text")
        layout .addWidget (current )

        notes =self .release .get ("notes")or tr ("update.no_notes")
        notes_edit =QTextEdit ()
        notes_edit .setReadOnly (True )
        notes_edit .setPlainText (notes )
        notes_edit .setObjectName ("code_box")
        layout .addWidget (notes_edit ,1 )

        self .disable_check =QCheckBox (tr ("update.disable_autocheck"))
        self .disable_check .setObjectName ("hint_text_bright")
        layout .addWidget (self .disable_check )

        btn_row =QHBoxLayout ()
        btn_later =QPushButton (tr ("update.later"))
        btn_later .setObjectName ("btn_secondary")
        btn_later .clicked .connect (self ._on_later )
        btn_row .addWidget (btn_later )
        btn_row .addStretch ()
        btn_download =QPushButton (tr ("update.download"))
        btn_download .clicked .connect (self ._on_download )
        btn_row .addWidget (btn_download )
        layout .addLayout (btn_row )

    def _on_download (self ):
        url =self .release .get ("download_url")or self .release .get ("page_url")
        if url :
            QDesktopServices .openUrl (QUrl (url ))
        self .disable_autocheck =self .disable_check .isChecked ()
        self .accept ()

    def _on_later (self ):
        self .disable_autocheck =self .disable_check .isChecked ()
        self .reject ()
