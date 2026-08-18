from PyQt6 .QtWidgets import (
QDialog ,QVBoxLayout ,QHBoxLayout ,QLabel ,QListWidget ,QListWidgetItem ,
QPushButton ,QDialogButtonBox ,QFrame ,QWidget 
)
from PyQt6 .QtCore import Qt ,pyqtSignal 

from core .spellcheck_scanner import LineIssues 
from core .i18n import tr 

_KIND_ICON ={"spelling":"✍","repeat":"🔁","punctuation":"␣","tag":"🏷"}


class SpellcheckReportDialog (QDialog ):

    navigate_requested =pyqtSignal (str ,list ,str )
    rescan_requested =pyqtSignal ()

    def __init__ (self ,results :list ,diagnostics :dict ,whitelist_store ,base_dir :str ,parent =None ):
        super ().__init__ (parent )
        self .results =results 
        self .diagnostics =diagnostics 
        self .whitelist_store =whitelist_store 
        self .base_dir =base_dir 
        self .setWindowTitle (tr ("spellcheck.title"))
        self .setMinimumSize (700 ,560 )
        layout =QVBoxLayout (self )

        self ._add_diagnostics_banner (layout )

        total_issues =sum (len (r .issues )for r in results )
        layout .addWidget (QLabel (tr ("spellcheck.summary",lines =len (results ),issues =total_issues )))

        self .lst =QListWidget ()
        for r in results :
            kinds =" ".join (sorted ({_KIND_ICON .get (i .kind ,"?")for i in r .issues }))
            first_msgs ="; ".join (i .message for i in r .issues [:3 ])
            more =f" (+{len (r .issues )-3 })"if len (r .issues )>3 else ""
            item =QListWidgetItem (f"{kinds }  {r .breadcrumb } - {r .char_label }: «{r .text_preview }»\n{first_msgs }{more }")
            item .setData (Qt .ItemDataRole .UserRole ,r )
            item .setToolTip (tr ("spellcheck.dblclick_tooltip"))
            self .lst .addItem (item )
        self .lst .itemDoubleClicked .connect (self ._on_activate )
        self .lst .currentItemChanged .connect (self ._on_selection_changed )
        layout .addWidget (self .lst ,1 )

        if not results :
            layout .addWidget (QLabel (tr ("spellcheck.none_found")))

        layout .addWidget (QLabel (tr ("spellcheck.words_hint")))
        self .words_frame =QFrame ()
        self .words_layout =QHBoxLayout (self .words_frame )
        self .words_layout .setContentsMargins (0 ,0 ,0 ,0 )
        self .words_layout .addWidget (QLabel (tr ("spellcheck.select_line_above")))
        self .words_layout .addStretch ()
        layout .addWidget (self .words_frame )

        btn_row =QHBoxLayout ()
        go_btn =QPushButton (tr ("spellcheck.go_to_node"))
        go_btn .clicked .connect (lambda :self ._on_activate (self .lst .currentItem ()))
        btn_row .addWidget (go_btn )
        btn_rescan =QPushButton (tr ("spellcheck.rescan"))
        btn_rescan .setToolTip (tr ("spellcheck.rescan_tooltip"))
        btn_rescan .clicked .connect (self ._on_rescan )
        btn_row .addWidget (btn_rescan )
        btn_row .addStretch ()
        layout .addLayout (btn_row )

        buttons =QDialogButtonBox (QDialogButtonBox .StandardButton .Close )
        buttons .rejected .connect (self .reject )
        close_btn =buttons .button (QDialogButtonBox .StandardButton .Close )
        if close_btn is not None :
            close_btn .clicked .connect (self .reject )
        layout .addWidget (buttons )

    def _add_diagnostics_banner (self ,layout ):
        d =self .diagnostics 
        ru_ok =d .get ("pymorphy_ru_ok")or d ["dictionaries"]["ru"]["ok"]
        en_ok =d ["dictionaries"]["en"]["ok"]
        if ru_ok and en_ok :
            return 
        if ru_ok and not en_ok and not d ["import_ok"]:


            text =tr ("spellcheck.banner_ru_only")
            color ,fg ="#152233","#9fd6ff"
        elif not d .get ("pymorphy_import_ok")and not d ["import_ok"]:
            text =tr ("spellcheck.banner_none")
            color ,fg ="#2a1f14","#ffb84d"
        else :
            problems =[]
            if not ru_ok :
                morph_err =d .get ("pymorphy_import_error")or self .diagnostics ["dictionaries"]["ru"]["error"]
                problems .append (tr ("spellcheck.ru_unavailable",reason =morph_err or tr ("spellcheck.reason_unknown")))
            if not en_ok :
                en_err =d ["dictionaries"]["en"]["error"]
                problems .append (tr ("spellcheck.en_unavailable",reason =en_err or tr ("spellcheck.pyspellchecker_missing")))
            text =tr ("spellcheck.banner_partial",problems ="; ".join (problems ))
            color ,fg ="#2a1f14","#ffb84d"
        text +=tr ("spellcheck.banner_tech_checks")
        note =QLabel (text )
        note .setWordWrap (True )
        note .setStyleSheet (f"color:{fg }; background:{color }; padding:6px; border-radius:4px;")
        layout .addWidget (note )

    def _on_selection_changed (self ,current ,previous ):
        while self .words_layout .count ():
            item =self .words_layout .takeAt (0 )
            if item .widget ():
                item .widget ().deleteLater ()

        if current is None :
            self .words_layout .addWidget (QLabel (tr ("spellcheck.select_line_above")))
            self .words_layout .addStretch ()
            return 

        r :LineIssues =current .data (Qt .ItemDataRole .UserRole )
        spelling_words =sorted ({i .word for i in r .issues if i .kind =="spelling"and i .word })
        if not spelling_words :
            self .words_layout .addWidget (QLabel (tr ("spellcheck.no_spelling_issues")))
        for word in spelling_words :
            btn =QPushButton (f"✚ «{word }»")
            btn .setToolTip (tr ("spellcheck.add_word_tooltip"))
            btn .clicked .connect (lambda _ =False ,w =word ,b =btn :self ._add_word (w ,b ))
            self .words_layout .addWidget (btn )
        self .words_layout .addStretch ()

    def _add_word (self ,word :str ,btn :QPushButton ):
        self .whitelist_store .add (word ,self .base_dir )
        btn .setText (tr ("spellcheck.word_added",word =word ))
        btn .setEnabled (False )

    def _on_rescan (self ):
        self .rescan_requested .emit ()
        self .accept ()

    def _on_activate (self ,item ):
        if item is None :
            return 
        r :LineIssues =item .data (Qt .ItemDataRole .UserRole )
        self .navigate_requested .emit (r .scene_id ,r .branch_path ,r .node_id )
        self .accept ()
