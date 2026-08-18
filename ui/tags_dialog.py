

from PyQt6 .QtWidgets import (
QDialog ,QVBoxLayout ,QHBoxLayout ,QLabel ,QLineEdit ,
QPushButton ,QListWidget ,QListWidgetItem ,QMessageBox ,QInputDialog ,
QCheckBox ,QScrollArea ,QWidget ,QGroupBox 
)
from PyQt6 .QtCore import pyqtSignal 

from core .tags_store import TagsStore 
from core .i18n import tr 


class TagPickerDialog (QDialog ):


    def __init__ (self ,tags_store :TagsStore ,base_dir :str ,var_name :str ,display_name :str ,parent =None ):
        super ().__init__ (parent )
        self .store =tags_store 
        self .base_dir =base_dir 
        self .var_name =var_name 
        self .setWindowTitle (tr ("tags.picker_title",name =display_name ))
        self .setMinimumSize (360 ,420 )
        self ._checkboxes =[]
        self ._setup_ui ()

    def _setup_ui (self ):
        layout =QVBoxLayout (self )

        if not self .store .categories :
            lbl =QLabel (tr ("tags.no_categories"))
            lbl .setWordWrap (True )
            lbl .setObjectName ("hint_text")
            layout .addWidget (lbl )
        else :
            scroll =QScrollArea ()
            scroll .setWidgetResizable (True )
            inner =QWidget ()
            inner_layout =QVBoxLayout (inner )
            current =set (self .store .get_tags_for (self .var_name ))

            for cat in self .store .categories :
                grp =QGroupBox (cat .name )
                gl =QVBoxLayout (grp )
                if not cat .tags :
                    empty =QLabel (tr ("tags.no_tags_in_category"))
                    empty .setObjectName ("hint_text")
                    gl .addWidget (empty )
                for tag in cat .tags :
                    key =f"{cat .id }:{tag }"
                    cb =QCheckBox (tag )
                    cb .setChecked (key in current )
                    gl .addWidget (cb )
                    self ._checkboxes .append ((key ,cb ))
                inner_layout .addWidget (grp )
            inner_layout .addStretch ()
            scroll .setWidget (inner )
            layout .addWidget (scroll ,1 )

        btn_row =QHBoxLayout ()
        btn_cancel =QPushButton (tr ("tags.cancel"))
        btn_cancel .setObjectName ("btn_secondary")
        btn_cancel .clicked .connect (self .reject )
        btn_row .addWidget (btn_cancel )
        btn_row .addStretch ()
        btn_ok =QPushButton (tr ("tags.save"))
        btn_ok .clicked .connect (self ._on_ok )
        btn_row .addWidget (btn_ok )
        layout .addLayout (btn_row )

    def _on_ok (self ):
        keys =[key for key ,cb in self ._checkboxes if cb .isChecked ()]
        self .store .set_tags_for (self .var_name ,keys )
        self .store .save (self .base_dir )
        self .accept ()


class TagsManagerDialog (QDialog ):
    changed =pyqtSignal ()

    def __init__ (self ,tags_store :TagsStore ,base_dir :str ,parent =None ):
        super ().__init__ (parent )
        self .store =tags_store 
        self .base_dir =base_dir 
        self .setWindowTitle (tr ("tags.manager_title"))
        self .setMinimumSize (560 ,420 )
        self ._setup_ui ()
        self ._reload_categories ()

    def _setup_ui (self ):
        layout =QVBoxLayout (self )

        hint =QLabel (tr ("tags.manager_hint"))
        hint .setWordWrap (True )
        hint .setObjectName ("hint_text")
        layout .addWidget (hint )

        columns =QHBoxLayout ()


        left =QVBoxLayout ()
        left .addWidget (QLabel (tr ("tags.categories_label")))
        self .cat_list =QListWidget ()
        self .cat_list .currentItemChanged .connect (self ._on_category_selected )
        left .addWidget (self .cat_list )

        cat_btn_row =QHBoxLayout ()
        self .new_cat_edit =QLineEdit ()
        self .new_cat_edit .setPlaceholderText (tr ("tags.new_category_placeholder"))
        self .new_cat_edit .returnPressed .connect (self ._add_category )
        cat_btn_row .addWidget (self .new_cat_edit )
        btn_add_cat =QPushButton ("+")
        btn_add_cat .setFixedWidth (50 )
        btn_add_cat .clicked .connect (self ._add_category )
        cat_btn_row .addWidget (btn_add_cat )
        left .addLayout (cat_btn_row )

        cat_actions_row =QHBoxLayout ()
        btn_rename_cat =QPushButton (tr ("tags.rename"))
        btn_rename_cat .setObjectName ("btn_secondary")
        btn_rename_cat .clicked .connect (self ._rename_category )
        cat_actions_row .addWidget (btn_rename_cat )
        btn_del_cat =QPushButton (tr ("tags.delete"))
        btn_del_cat .clicked .connect (self ._delete_category )
        cat_actions_row .addWidget (btn_del_cat )
        left .addLayout (cat_actions_row )

        columns .addLayout (left ,1 )


        right =QVBoxLayout ()
        right .addWidget (QLabel (tr ("tags.tags_in_category_label")))
        self .tag_list =QListWidget ()
        right .addWidget (self .tag_list )

        tag_btn_row =QHBoxLayout ()
        self .new_tag_edit =QLineEdit ()
        self .new_tag_edit .setPlaceholderText (tr ("tags.new_tag_placeholder"))
        self .new_tag_edit .returnPressed .connect (self ._add_tag )
        tag_btn_row .addWidget (self .new_tag_edit )
        btn_add_tag =QPushButton ("+")
        btn_add_tag .setFixedWidth (50 )
        btn_add_tag .clicked .connect (self ._add_tag )
        tag_btn_row .addWidget (btn_add_tag )
        right .addLayout (tag_btn_row )

        btn_del_tag =QPushButton (tr ("tags.delete_tag"))
        btn_del_tag .clicked .connect (self ._delete_tag )
        right .addWidget (btn_del_tag )

        columns .addLayout (right ,1 )
        layout .addLayout (columns )

        btn_close =QPushButton (tr ("tags.close"))
        btn_close .clicked .connect (self .accept )
        layout .addWidget (btn_close )



    def _reload_categories (self ):
        self .cat_list .clear ()
        for cat in self .store .categories :
            item =QListWidgetItem (cat .name )
            item .setData (1000 ,cat .id )
            self .cat_list .addItem (item )
        self .tag_list .clear ()

    def _current_category_id (self ):
        item =self .cat_list .currentItem ()
        return item .data (1000 )if item else None 

    def _add_category (self ):
        name =self .new_cat_edit .text ().strip ()
        if not name :
            return 
        self .store .add_category (name )
        self .new_cat_edit .clear ()
        self ._save_and_refresh ()

    def _rename_category (self ):
        cat_id =self ._current_category_id ()
        if not cat_id :
            return 
        cat =self .store .get_category (cat_id )
        new_name ,ok =QInputDialog .getText (self ,tr ("tags.rename_category_title"),tr ("tags.new_name_label"),text =cat .name )
        if ok and new_name .strip ():
            self .store .rename_category (cat_id ,new_name .strip ())
            self ._save_and_refresh ()

    def _delete_category (self ):
        cat_id =self ._current_category_id ()
        if not cat_id :
            return 
        cat =self .store .get_category (cat_id )
        reply =QMessageBox .question (
        self ,tr ("tags.delete_category_title"),
        tr ("tags.delete_category_confirm",name =cat .name )
        )
        if reply ==QMessageBox .StandardButton .Yes :
            self .store .remove_category (cat_id )
            self ._save_and_refresh ()

    def _on_category_selected (self ,*_ ):
        cat_id =self ._current_category_id ()
        self .tag_list .clear ()
        if not cat_id :
            return 
        cat =self .store .get_category (cat_id )
        if cat :
            for tag in cat .tags :
                self .tag_list .addItem (QListWidgetItem (tag ))



    def _add_tag (self ):
        cat_id =self ._current_category_id ()
        text =self .new_tag_edit .text ().strip ()
        if not cat_id or not text :
            return 
        if self .store .add_tag (cat_id ,text ):
            self .new_tag_edit .clear ()
            self ._save_and_refresh (keep_category =cat_id )

    def _delete_tag (self ):
        cat_id =self ._current_category_id ()
        item =self .tag_list .currentItem ()
        if not cat_id or not item :
            return 
        self .store .remove_tag (cat_id ,item .text ())
        self ._save_and_refresh (keep_category =cat_id )



    def _save_and_refresh (self ,keep_category :str =None ):
        self .store .save (self .base_dir )
        self ._reload_categories ()
        if keep_category :
            for i in range (self .cat_list .count ()):
                if self .cat_list .item (i ).data (1000 )==keep_category :
                    self .cat_list .setCurrentRow (i )
                    break 
        self .changed .emit ()
