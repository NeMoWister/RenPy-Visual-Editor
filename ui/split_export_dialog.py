import os 

from PyQt6 .QtWidgets import (
QDialog ,QVBoxLayout ,QHBoxLayout ,QLabel ,QPushButton ,QFileDialog ,
QRadioButton ,QButtonGroup ,QSpinBox ,QListWidget ,QListWidgetItem ,
QMessageBox ,QGroupBox 
)
from PyQt6 .QtCore import Qt 

from core .split_export import split_project ,SPLIT_RULES 
from core .i18n import tr 


class SplitExportDialog (QDialog ):


    def __init__ (self ,project ,rm =None ,custom_templates =None ,parent =None ,nvl_style ="character"):
        super ().__init__ (parent )
        self .project =project 
        self .rm =rm 
        self .custom_templates =custom_templates 
        self .nvl_style =nvl_style 
        self .target_dir =""
        self ._chunks =[]
        self .setWindowTitle (tr ("split_export.title"))
        self .setMinimumSize (560 ,520 )
        self ._setup_ui ()
        self ._update_preview ()

    def _setup_ui (self ):
        layout =QVBoxLayout (self )

        rule_box =QGroupBox (tr ("split_export.rule_box"))
        rl =QVBoxLayout (rule_box )
        self .rule_group =QButtonGroup (self )
        self .rb_label =QRadioButton (tr ("split_export.rb_label"))
        self .rb_scene =QRadioButton (tr ("split_export.rb_scene"))
        self .rb_count =QRadioButton (tr ("split_export.rb_count"))
        self .rb_label .setChecked (True )
        self .rule_group .addButton (self .rb_label ,0 )
        self .rule_group .addButton (self .rb_scene ,1 )
        self .rule_group .addButton (self .rb_count ,2 )
        for rb in (self .rb_label ,self .rb_scene ,self .rb_count ):
            rb .toggled .connect (self ._update_preview )
        rl .addWidget (self .rb_label )
        rl .addWidget (self .rb_scene )
        count_row =QHBoxLayout ()
        count_row .addWidget (self .rb_count )
        self .count_spin =QSpinBox ()
        self .count_spin .setRange (1 ,200 )
        self .count_spin .setValue (5 )
        self .count_spin .valueChanged .connect (self ._update_preview )
        count_row .addWidget (self .count_spin )
        count_row .addWidget (QLabel (tr ("split_export.scenes_per_file")))
        count_row .addStretch ()
        rl .addLayout (count_row )
        layout .addWidget (rule_box )

        dir_row =QHBoxLayout ()
        self .dir_lbl =QLabel (tr ("split_export.dir_not_selected"))
        self .dir_lbl .setObjectName ("hint_text")
        dir_row .addWidget (self .dir_lbl ,1 )
        btn_dir =QPushButton (tr ("split_export.pick_dir"))
        btn_dir .clicked .connect (self ._pick_dir )
        dir_row .addWidget (btn_dir )
        layout .addLayout (dir_row )

        layout .addWidget (QLabel (tr ("split_export.will_be_created")))
        self .preview_list =QListWidget ()
        layout .addWidget (self .preview_list ,1 )

        note =QLabel (tr ("split_export.note"))
        note .setWordWrap (True )
        note .setObjectName ("hint_text")
        layout .addWidget (note )

        btn_row =QHBoxLayout ()
        btn_row .addStretch ()
        btn_cancel =QPushButton (tr ("split_export.cancel"))
        btn_cancel .clicked .connect (self .reject )
        btn_row .addWidget (btn_cancel )
        self .btn_export =QPushButton (tr ("split_export.export"))
        self .btn_export .setObjectName ("btn_primary")
        self .btn_export .setEnabled (False )
        self .btn_export .clicked .connect (self ._do_export )
        btn_row .addWidget (self .btn_export )
        layout .addLayout (btn_row )

    def _current_rule (self )->str :
        if self .rb_scene .isChecked ():
            return "scene"
        if self .rb_count .isChecked ():
            return "count"
        return "label"

    def _update_preview (self ):
        self .preview_list .clear ()
        try :
            chunks =split_project (
            self .project ,self ._current_rule (),rm =self .rm ,
            custom_templates =self .custom_templates ,
            count_per_file =self .count_spin .value (),
            nvl_style =self .nvl_style ,
            )
        except Exception as e :
            self ._chunks =[]
            self .btn_export .setEnabled (False )
            self .preview_list .addItem (tr ("split_export.error_prefix",error =e ))
            return 
        self ._chunks =chunks 
        for c in chunks :
            scenes_preview =", ".join (c .scene_names [:3 ])
            more =f" +{len (c .scene_names )-3 }"if len (c .scene_names )>3 else ""
            self .preview_list .addItem (QListWidgetItem (f"📄 {c .filename }  -  {scenes_preview }{more }"))
        self .btn_export .setEnabled (bool (chunks )and bool (self .target_dir ))

    def _pick_dir (self ):
        d =QFileDialog .getExistingDirectory (self ,tr ("split_export.pick_dir_title"))
        if d :
            self .target_dir =d 
            self .dir_lbl .setText (d )
            self .dir_lbl .setObjectName ("hint_text_bright")
            self .btn_export .setEnabled (bool (self ._chunks ))

    def _do_export (self ):
        written ,skipped =[],[]
        for chunk in self ._chunks :
            path =os .path .join (self .target_dir ,chunk .filename )
            old_code =None 
            if os .path .isfile (path ):
                try :
                    with open (path ,"r",encoding ="utf-8")as f :
                        old_code =f .read ()
                except Exception :
                    old_code =None 
            code =chunk .code 
            if old_code is not None and old_code !=code :
                from ui .diff_preview_dialog import DiffPreviewDialog 
                dlg =DiffPreviewDialog (old_code ,code ,path ,self )
                if dlg .exec ()!=QDialog .DialogCode .Accepted or dlg .action is None :
                    skipped .append (chunk .filename )
                    continue 
                if dlg .action =="copy":
                    path =dlg .copy_path 
                elif dlg .action =="merge":
                    code =dlg .merged_text 
            try :
                with open (path ,"w",encoding ="utf-8")as f :
                    f .write (code )
                written .append (path )
            except Exception as e :
                QMessageBox .critical (self ,tr ("split_export.write_error_title"),f"{chunk .filename }: {e }")
                skipped .append (chunk .filename )

        msg =tr ("split_export.written_count",count =len (written ))
        if skipped :
            msg +=tr ("split_export.skipped",count =len (skipped ),names =", ".join (skipped ))
        QMessageBox .information (self ,tr ("split_export.done_title"),msg )
        self .accept ()
