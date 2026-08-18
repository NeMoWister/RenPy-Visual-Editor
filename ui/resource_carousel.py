
import os 
from typing import List ,Optional ,Dict 
from PyQt6 .QtWidgets import (
QWidget ,QHBoxLayout ,QVBoxLayout ,QLabel ,QPushButton ,
QScrollArea ,QFrame ,QComboBox ,QLineEdit ,QMessageBox ,QSizePolicy 
)
from PyQt6 .QtCore import Qt ,pyqtSignal ,QTimer ,QEvent 
from PyQt6 .QtGui import QPixmap ,QPainter 
from core .resource_manager import ResourceEntry 
from core .i18n import tr 
from core .composite_sprite_parser import CompositeSprite 
from ui .pixmap_cache import get_scaled ,get_composite ,get_pixmap 
from ui .theme import theme_manager 


SCROLL_EXTRA =14 
SMALL_CONTENT_ITEM_THRESHOLD =1 


def _apply_scroll_fill_alignment (layout ,scroll_widget ,item_count :int ,small_content_width :int ):

    if item_count <=SMALL_CONTENT_ITEM_THRESHOLD :
        scroll_widget .setMaximumWidth (small_content_width )
        layout .setAlignment (scroll_widget ,Qt .AlignmentFlag .AlignLeft |Qt .AlignmentFlag .AlignTop )
    else :
        scroll_widget .setMaximumWidth (16777215 )
        layout .setAlignment (scroll_widget ,Qt .AlignmentFlag (0 ))


FAVORITES_LABEL ="\u2605 \u0418\u0437\u0431\u0440\u0430\u043d\u043d\u043e\u0435"
RECENT_LABEL ="\U0001F551 \u041d\u0435\u0434\u0430\u0432\u043d\u0438\u0435"


class DragOverlay (QLabel ):


    def __init__ (self ,parent ):
        super ().__init__ (parent )
        self .setAlignment (Qt .AlignmentFlag .AlignCenter )
        _t =theme_manager .tokens ()
        self .setStyleSheet (
        f"background: {_t .accent_soft }; border: 2px dashed {_t .accent_1 }; "
        "border-radius: 8px; color: #fff; font-size: 13px; font-weight: bold;"
        )
        self .hide ()

    def show_over (self ,text :str ):
        self .setText (text )
        self .setGeometry (0 ,0 ,self .parent ().width (),self .parent ().height ())
        self .raise_ ()
        self .show ()


class HOnlyWheelScrollArea (QScrollArea ):


    def wheelEvent (self ,event ):
        delta =event .angleDelta ().y ()or event .angleDelta ().x ()
        if delta ==0 :
            super ().wheelEvent (event )
            return 
        hbar =self .horizontalScrollBar ()
        hbar .setValue (hbar .value ()-delta )
        event .accept ()


class HWheelScrollArea (QScrollArea ):


    def wheelEvent (self ,event ):
        delta =event .angleDelta ().y ()or event .angleDelta ().x ()
        if delta ==0 :
            super ().wheelEvent (event )
            return 
        vbar =self .verticalScrollBar ()
        hbar =self .horizontalScrollBar ()
        if vbar .maximum ()>vbar .minimum ():
            vbar .setValue (vbar .value ()-delta )
        else :
            hbar .setValue (hbar .value ()-delta )
        event .accept ()


def _build_title_row (title_text :str )->Optional [QLabel ]:

    if not title_text :
        return None 
    lbl =QLabel (title_text )
    lbl .setObjectName ("section_title")
    return lbl 


class ResourceCard (QFrame ):
    clicked =pyqtSignal (object )
    favorite_toggled =pyqtSignal (object )

    LABEL_HEIGHT =28 

    def __init__ (self ,entry :ResourceEntry ,thumb_size :int =160 ,is_favorite :bool =False ,
    show_favorite_star :bool =True ):
        super ().__init__ ()
        self .entry =entry 
        self .selected =False 
        self .thumb_size =thumb_size 
        self .is_favorite =is_favorite 
        self .show_favorite_star =show_favorite_star 
        self ._suppress_tooltip =False 
        self .setFixedSize (thumb_size +16 ,thumb_size +self .LABEL_HEIGHT +14 )
        self .setCursor (Qt .CursorShape .PointingHandCursor )
        self .setObjectName ("resource_card")
        self ._setup_ui (thumb_size )

    def _setup_ui (self ,thumb_size :int ):
        layout =QVBoxLayout (self )
        layout .setContentsMargins (4 ,4 ,4 ,4 )
        layout .setSpacing (3 )

        self .preview =QLabel ()
        self .preview .setFixedSize (thumb_size ,thumb_size )
        self .preview .setAlignment (Qt .AlignmentFlag .AlignCenter )
        self .preview .setObjectName ("code_box")

        if self .show_favorite_star :
            self .star_btn =QPushButton (self .preview )
            self .star_btn .setFixedSize (22 ,22 )
            self .star_btn .move (thumb_size -24 ,2 )
            self .star_btn .setCursor (Qt .CursorShape .PointingHandCursor )
            self .star_btn .setFlat (True )
            self .star_btn .clicked .connect (self ._on_star_clicked )
            self .star_btn .installEventFilter (self )
            self ._update_star_style ()

        ext =os .path .splitext (self .entry .filename )[1 ].lower ()
        if ext in {'.png','.jpg','.jpeg','.webp','.bmp'}:




            self .preview .setText ("…")
            self .preview .setStyleSheet (self .preview .styleSheet ()+"color:#555; font-size:11px;")
            self ._needs_thumb =True 
        else :
            icon ="🎵"if self .entry .category =='music'else "🔊"
            self .preview .setText (icon )
            self .preview .setStyleSheet (self .preview .styleSheet ()+"font-size:32px;")
            self ._needs_thumb =False 

        layout .addWidget (self .preview )
        name_label =QLabel (self .entry .display_name )
        name_label .setAlignment (Qt .AlignmentFlag .AlignCenter )
        name_label .setWordWrap (True )
        name_label .setObjectName ("hint_text")
        name_label .setMaximumWidth (thumb_size +8 )
        layout .addWidget (name_label )
        self ._update_style ()

    def load_thumbnail (self ):

        if not self ._needs_thumb :
            return 
        self ._needs_thumb =False 
        pm =get_scaled (self .entry .abs_path ,self .thumb_size ,self .thumb_size )
        if pm is not None :
            self .preview .setPixmap (pm )
            self .preview .setObjectName ("code_box")
        else :
            self .preview .setText ("🖼")
            self .preview .setObjectName ("code_box")
            self .preview .setStyleSheet ("font-size:24px;")

    def _update_style (self ):




        self .setProperty ("selected",self .selected )
        self .style ().unpolish (self )
        self .style ().polish (self )

    def set_selected (self ,val :bool ):
        self .selected =val 
        self ._update_style ()

    def _update_star_style (self ):
        if not self .show_favorite_star :
            return 
        self .star_btn .setText ("★"if self .is_favorite else "☆")
        color ="#ffcf40"if self .is_favorite else "#bbb"
        self .star_btn .setStyleSheet (
        f"QPushButton {{ background: rgba(20,20,24,150); color:{color }; "
        f"border-radius:11px; font-size:14px; border:none; }}"
        f"QPushButton:hover {{ background: rgba(40,30,10,200); color:#ffcf40; }}"
        )
        self .star_btn .setToolTip (tr ("carousel.remove_favorite")if self .is_favorite else tr ("carousel.add_favorite"))

    def set_suppress_tooltip (self ,suppress :bool ):

        self ._suppress_tooltip =suppress 

    def eventFilter (self ,obj ,event ):
        if event .type ()==QEvent .Type .ToolTip and self ._suppress_tooltip :
            return True 
        return super ().eventFilter (obj ,event )

    def _on_star_clicked (self ):
        self .is_favorite =not self .is_favorite 
        self ._update_star_style ()
        self .favorite_toggled .emit (self .entry )

    def mousePressEvent (self ,event ):
        self .clicked .emit (self .entry )
        super ().mousePressEvent (event )


class FolderCard (QFrame ):

    clicked =pyqtSignal (str )

    def __init__ (self ,folder_name :str ,thumb_size :int =160 ):
        super ().__init__ ()
        self .folder_name =folder_name 
        self .thumb_size =thumb_size 
        self .selected =False 
        self .setFixedSize (thumb_size +16 ,thumb_size +ResourceCard .LABEL_HEIGHT +14 )
        self .setCursor (Qt .CursorShape .PointingHandCursor )
        self .setObjectName ("folder_card")
        layout =QVBoxLayout (self )
        layout .setContentsMargins (4 ,4 ,4 ,4 )
        layout .setSpacing (3 )

        self .icon =QLabel ("📁")
        self .icon .setFixedSize (thumb_size ,thumb_size )
        self .icon .setAlignment (Qt .AlignmentFlag .AlignCenter )
        self .icon .setObjectName ("code_box")
        self .icon .setStyleSheet ("font-size:36px;")
        layout .addWidget (self .icon )

        name_label =QLabel (folder_name )
        name_label .setAlignment (Qt .AlignmentFlag .AlignCenter )
        name_label .setWordWrap (True )
        name_label .setObjectName ("hint_text_bright")
        name_label .setStyleSheet ("font-weight:bold;")
        name_label .setMaximumWidth (thumb_size +8 )
        layout .addWidget (name_label )
        self ._update_style ()

    def _update_style (self ):
        self .setProperty ("selected",self .selected )
        self .style ().unpolish (self )
        self .style ().polish (self )

    def set_selected (self ,val :bool ):
        self .selected =val 
        self ._update_style ()

    def mousePressEvent (self ,event ):
        self .clicked .emit (self .folder_name )
        super ().mousePressEvent (event )


class CharacterGroupPicker (QWidget ):

    selection_changed =pyqtSignal (str )

    def __init__ (self ,resource_manager =None ,category :str ="sprites",thumb_size :int =160 ):
        super ().__init__ ()
        self .rm =resource_manager 
        self .category =category 
        self .thumb_size =thumb_size 
        self .cards :List [FolderCard ]=[]
        self .selected_folder :str =""
        self ._setup_ui ()

    def _setup_ui (self ):
        outer =QVBoxLayout (self )
        outer .setContentsMargins (0 ,0 ,0 ,0 )
        outer .setSpacing (4 )

        row =QHBoxLayout ()
        self .row_layout =row 
        row .setContentsMargins (0 ,0 ,0 ,0 )

        self .scroll =HWheelScrollArea ()
        self .scroll .setHorizontalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAsNeeded )
        self .scroll .setVerticalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAlwaysOff )
        self .scroll .setFixedHeight (self .thumb_size +52 +SCROLL_EXTRA )
        self .scroll .setWidgetResizable (False )

        self .container =QWidget ()
        self .container_layout =QHBoxLayout (self .container )
        self .container_layout .setContentsMargins (4 ,0 ,4 ,0 )
        self .container_layout .setSpacing (6 )
        self .container_layout .addStretch ()
        self .scroll .setAlignment (Qt .AlignmentFlag .AlignLeft |Qt .AlignmentFlag .AlignTop )
        self .scroll .setWidget (self .container )
        row .addWidget (self .scroll ,1 )
        outer .addLayout (row )

        none_row =QHBoxLayout ()
        self .btn_none =QPushButton (tr ("carousel.clear_selection"))
        self .btn_none .setObjectName ("btn_secondary")
        self .btn_none .setFixedHeight (36 )
        self .btn_none .clicked .connect (self ._clear_selection )
        none_row .addWidget (self .btn_none )
        none_row .addStretch ()
        outer .addLayout (none_row )

    def set_resource_manager (self ,rm ,category :Optional [str ]=None ):
        self .rm =rm 
        if category :
            self .category =category 
        self ._refresh ()

    def select_folder (self ,folder_name :str ):
        self .selected_folder =folder_name or ""
        self ._refresh ()

    def get_selected (self )->str :
        return self .selected_folder 

    def _refresh (self ):
        for card in self .cards :
            card .hide ()
        self .cards .clear ()
        while self .container_layout .count ():
            item =self .container_layout .takeAt (0 )
            w =item .widget ()
            if w :
                w .hide ()
                w .deleteLater ()

        folders =list (self .rm .get_folders (self .category ,""))if self .rm else []
        if self .rm and self .category =="sprites":



            for character in self .rm .get_composite_characters ():
                if character not in folders :
                    folders .append (character )
            folders .sort ()

        for folder_name in folders :
            card =FolderCard (folder_name ,self .thumb_size )
            card .set_selected (folder_name ==self .selected_folder )
            card .clicked .connect (self ._on_folder_clicked )
            self .cards .append (card )
            self .container_layout .addWidget (card )

        self .container_layout .addStretch ()
        w =len (folders )*(self .thumb_size +22 )+10 
        self .container .setFixedWidth (max (w ,200 ))
        self .container .setFixedHeight (self .thumb_size +ResourceCard .LABEL_HEIGHT +14 )
        _apply_scroll_fill_alignment (self .row_layout ,self .scroll ,len (folders ),max (w ,200 )+12 )

    def _on_folder_clicked (self ,folder_name :str ):
        self .selected_folder =folder_name 
        for card in self .cards :
            card .set_selected (card .folder_name ==folder_name )
        self .selection_changed .emit (folder_name )

    def _clear_selection (self ):
        self .selected_folder =""
        for card in self .cards :
            card .set_selected (False )
        self .selection_changed .emit ("")


class FolderResourceCarousel (QWidget ):

    selection_changed =pyqtSignal (object )

    def __init__ (self ,resource_manager =None ,category :str ="sprites",
    category_label :str ="",thumb_size :int =160 ):
        super ().__init__ ()
        self .rm =resource_manager 
        self .category =category 
        self .thumb_size =thumb_size 
        self .current_path :List [str ]=[]
        self .cards :List [QWidget ]=[]
        self .selected_entry :Optional [ResourceEntry ]=None 
        self ._all_entries :List [ResourceEntry ]=[]
        self ._setup_ui (category_label )
        self .setAcceptDrops (True )
        self ._drag_overlay =DragOverlay (self )

    def dragEnterEvent (self ,event ):
        if self .rm and self .category and event .mimeData ().hasUrls ():
            event .acceptProposedAction ()
            self ._set_cards_tooltip_suppressed (True )
            self ._drag_overlay .show_over (f"📥 Отпустите файлы, чтобы добавить в «{self .category }»")
        else :
            event .ignore ()

    def dragMoveEvent (self ,event ):
        if self .rm and self .category and event .mimeData ().hasUrls ():
            event .acceptProposedAction ()
        else :
            event .ignore ()

    def dragLeaveEvent (self ,event ):
        self ._set_cards_tooltip_suppressed (False )
        self ._drag_overlay .hide ()

    def _set_cards_tooltip_suppressed (self ,suppressed :bool ):
        for card in self .cards :
            if isinstance (card ,ResourceCard ):
                card .set_suppress_tooltip (suppressed )

    def dropEvent (self ,event ):
        self ._set_cards_tooltip_suppressed (False )
        self ._drag_overlay .hide ()
        if not (self .rm and self .category ):
            event .ignore ()
            return 
        paths =[url .toLocalFile ()for url in event .mimeData ().urls ()if url .isLocalFile ()]
        imported =[]
        skipped =[]
        for path in paths :
            if not os .path .isfile (path ):
                continue 
            entry =self .rm .import_local_file (self .category ,path )
            (imported if entry else skipped ).append (os .path .basename (path ))
        if imported :
            self .current_path =[]
            self ._refresh_view ()
        if skipped :
            QMessageBox .warning (
            self ,tr ("carousel.import_failed_title"),
            tr ("carousel.import_failed_text",files ="\n".join (skipped ))
            )
        event .acceptProposedAction ()

    def _setup_ui (self ,label_text :str ):
        outer =QVBoxLayout (self )
        outer .setContentsMargins (0 ,0 ,0 ,0 )
        outer .setSpacing (4 )

        title =_build_title_row (label_text )
        if title :
            outer .addWidget (title )

        self .breadcrumb_row =QHBoxLayout ()
        self .breadcrumb_row .setContentsMargins (0 ,0 ,0 ,0 )
        self .breadcrumb_row .setSpacing (4 )
        outer .addLayout (self .breadcrumb_row )

        row =QHBoxLayout ()
        self .row_layout =row 
        row .setContentsMargins (0 ,0 ,0 ,0 )

        self .scroll =HWheelScrollArea ()
        self .scroll .setHorizontalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAsNeeded )
        self .scroll .setVerticalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAlwaysOff )
        self .scroll .setFixedHeight (self .thumb_size +52 +SCROLL_EXTRA )
        self .scroll .setWidgetResizable (False )

        self .container =QWidget ()
        self .container_layout =QHBoxLayout (self .container )
        self .container_layout .setContentsMargins (4 ,0 ,4 ,0 )
        self .container_layout .setSpacing (6 )
        self .container_layout .addStretch ()
        self .scroll .setAlignment (Qt .AlignmentFlag .AlignLeft |Qt .AlignmentFlag .AlignTop )
        self .scroll .setWidget (self .container )
        row .addWidget (self .scroll ,1 )

        outer .addLayout (row )

        none_row =QHBoxLayout ()
        self .btn_none =QPushButton (tr ("carousel.clear_selection"))
        self .btn_none .setObjectName ("btn_secondary")
        self .btn_none .setFixedHeight (36 )
        self .btn_none .clicked .connect (self ._clear_selection )
        none_row .addWidget (self .btn_none )
        none_row .addStretch ()
        outer .addLayout (none_row )



    def set_resource_manager (self ,rm ,category :Optional [str ]=None ):
        self .rm =rm 
        if category :
            self .category =category 
        self .current_path =[]
        self .selected_entry =None 
        self ._refresh_view ()

    def select_by_var (self ,var :str ):

        if not self .rm :
            return 
        entry =self .rm .find_by_var (var )
        if entry and entry .category ==self .category :
            self .current_path =entry .group_parts ()
            self .selected_entry =entry 
            self ._refresh_view ()
        else :
            self ._refresh_view ()

    def get_selected (self )->Optional [ResourceEntry ]:
        return self .selected_entry 



    def _current_path_str (self )->str :
        return "/".join (self .current_path )

    def _go_to (self ,path_parts :List [str ]):
        self .current_path =list (path_parts )
        self ._refresh_view ()

    def _enter_folder (self ,folder_name :str ):
        self .current_path .append (folder_name )
        self ._refresh_view ()

    def _rebuild_breadcrumbs (self ):
        while self .breadcrumb_row .count ():
            item =self .breadcrumb_row .takeAt (0 )
            if item .widget ():
                item .widget ().deleteLater ()

        root_label =self .rm .CATEGORIES .get (self .category ,(self .category ,))[0 ]if self .rm else self .category 
        crumbs =[("🏠 "+root_label ,[])]
        for i ,part in enumerate (self .current_path ):
            crumbs .append ((part ,self .current_path [:i +1 ]))

        for i ,(text ,path )in enumerate (crumbs ):
            btn =QPushButton (text )
            btn .setFlat (True )
            is_last =(i ==len (crumbs )-1 )
            btn .setEnabled (not is_last )
            _t =theme_manager .tokens ()
            btn .setStyleSheet (f"""
                QPushButton {{
                    color: {_t .accent_2 if is_last else _t .text_dim };
                    font-weight: {'bold'if is_last else 'normal'};
                    border: none; padding: 2px 4px; text-align: left;
                    background: transparent;
                }}
                QPushButton:hover {{ color: {_t .accent_1 }; }}
                QPushButton:disabled {{ color: {_t .accent_2 }; }}
            """)
            btn .clicked .connect (lambda _ =None ,p =path :self ._go_to (p ))
            self .breadcrumb_row .addWidget (btn )
            if not is_last :
                sep =QLabel ("›")
                sep .setObjectName ("hint_text")
                self .breadcrumb_row .addWidget (sep )
        self .breadcrumb_row .addStretch ()

    def _refresh_view (self ):
        self ._rebuild_breadcrumbs ()

        for card in self .cards :
            card .hide ()
        self .cards .clear ()
        while self .container_layout .count ():
            item =self .container_layout .takeAt (0 )
            w =item .widget ()
            if w :
                w .hide ()
                w .deleteLater ()

        if not self .rm :
            self .container .setFixedWidth (200 )
            self .container .setFixedHeight (self .thumb_size +ResourceCard .LABEL_HEIGHT +14 )
            return 

        folders =self .rm .get_folders (self .category ,self ._current_path_str ())
        entries =self .rm .get_entries_in_folder (self .category ,self ._current_path_str ())

        count =0 
        for folder_name in folders :
            card =FolderCard (folder_name ,self .thumb_size )
            card .clicked .connect (self ._enter_folder )
            self .cards .append (card )
            self .container_layout .addWidget (card )
            count +=1 

        for entry in entries :
            card =ResourceCard (entry ,self .thumb_size )
            card .clicked .connect (self ._on_card_clicked )
            if self .selected_entry and entry .var_name ==self .selected_entry .var_name :
                card .set_selected (True )
            self .cards .append (card )
            self .container_layout .addWidget (card )
            count +=1 

        self .container_layout .addStretch ()
        w =count *(self .thumb_size +22 )+10 
        self .container .setFixedWidth (max (w ,200 ))
        self .container .setFixedHeight (self .thumb_size +ResourceCard .LABEL_HEIGHT +14 )
        _apply_scroll_fill_alignment (self .row_layout ,self .scroll ,count ,max (w ,200 )+12 )
        self ._schedule_thumbnails ()

    def _schedule_thumbnails (self ):
        pending =[c for c in self .cards if isinstance (c ,ResourceCard )]
        batch_size =4 

        def step ():
            for _ in range (batch_size ):
                if not pending :
                    return 
                card =pending .pop (0 )
                try :
                    card .load_thumbnail ()
                except RuntimeError :
                    pass 
            if pending :
                QTimer .singleShot (0 ,step )

        QTimer .singleShot (0 ,step )

    def _on_card_clicked (self ,entry :ResourceEntry ):
        for card in self .cards :
            if isinstance (card ,ResourceCard ):
                card .set_selected (card .entry is entry )
        self .selected_entry =entry 
        self .selection_changed .emit (entry )

    def _clear_selection (self ):
        for card in self .cards :
            if isinstance (card ,ResourceCard ):
                card .set_selected (False )
        self .selected_entry =None 
        self .selection_changed .emit (None )


class ResourceCarousel (QWidget ):
    selection_changed =pyqtSignal (object )
    group_changed =pyqtSignal (object )

    def __init__ (self ,category_label :str ="",thumb_size :int =160 ,tags_store =None ,
    initial_group_id :Optional [str ]=None ,category :str ="",usage_store =None ,rm =None ):
        super ().__init__ ()
        self .thumb_size =thumb_size 
        self .entries :List [ResourceEntry ]=[]
        self .cards :List [QWidget ]=[]
        self .selected_entry :Optional [ResourceEntry ]=None 
        self .tags_store =tags_store 
        self .group_category_id :Optional [str ]=None 
        self .current_tag :Optional [str ]=None 
        self .category =category 
        self .usage_store =usage_store 
        self .rm =rm 
        self .search_text :str =""
        self ._pending_initial_group_id =initial_group_id 
        self ._setup_ui (category_label )
        self .setAcceptDrops (bool (self .rm and self .category ))
        self ._drag_overlay =DragOverlay (self )

    def _setup_ui (self ,label_text :str ):
        outer =QVBoxLayout (self )
        outer .setContentsMargins (0 ,0 ,0 ,0 )
        outer .setSpacing (4 )

        header =QHBoxLayout ()
        title =_build_title_row (label_text )
        if title :
            header .addWidget (title )
        header .addStretch ()

        self .group_label =QLabel (tr ("carousel.group_label"))
        self .group_label .setObjectName ("hint_text")
        header .addWidget (self .group_label )
        self .group_combo =QComboBox ()
        self .group_combo .setFixedWidth (150 )
        self .group_combo .currentIndexChanged .connect (self ._on_group_changed )
        header .addWidget (self .group_combo )
        outer .addLayout (header )
        self ._reload_group_options ()

        search_row =QHBoxLayout ()
        self .search_edit =QLineEdit ()
        self .search_edit .setPlaceholderText ("🔎 Поиск по названию...")
        self .search_edit .setClearButtonEnabled (True )
        self .search_edit .setObjectName ("dark_field")
        _t =theme_manager .tokens ()
        self .search_edit .setStyleSheet (
        f"QLineEdit#dark_field {{ font-size:11px; }}"
        f"QLineEdit#dark_field:focus {{ border-color:{_t .accent_1 }; }}"
        )
        self .search_edit .textChanged .connect (self ._on_search_changed )
        search_row .addWidget (self .search_edit )
        outer .addLayout (search_row )

        self .nav_row =QHBoxLayout ()
        outer .addLayout (self .nav_row )

        row =QHBoxLayout ()
        self .row_layout =row 
        row .setContentsMargins (0 ,0 ,0 ,0 )

        self .scroll =HWheelScrollArea ()
        self .scroll .setHorizontalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAsNeeded )
        self .scroll .setVerticalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAlwaysOff )
        self .scroll .setFixedHeight (self .thumb_size +52 +SCROLL_EXTRA )
        self .scroll .setWidgetResizable (False )

        self .container =QWidget ()
        self .container_layout =QHBoxLayout (self .container )
        self .container_layout .setContentsMargins (4 ,0 ,4 ,0 )
        self .container_layout .setSpacing (6 )
        self .container_layout .addStretch ()
        self .scroll .setAlignment (Qt .AlignmentFlag .AlignLeft |Qt .AlignmentFlag .AlignTop )
        self .scroll .setWidget (self .container )
        row .addWidget (self .scroll ,1 )

        outer .addLayout (row )

        none_row =QHBoxLayout ()
        self .btn_none =QPushButton (tr ("carousel.clear_selection"))
        self .btn_none .setObjectName ("btn_secondary")
        self .btn_none .setFixedHeight (36 )
        self .btn_none .clicked .connect (self ._clear_selection )
        none_row .addWidget (self .btn_none )
        none_row .addStretch ()
        outer .addLayout (none_row )



    def _reload_group_options (self ):

        if not self .tags_store or not self .tags_store .categories :
            self .group_label .setVisible (False )
            self .group_combo .setVisible (False )
            return 


        entry_vars ={e .var_name for e in self .entries }if self .entries else set ()



        visible_cats =[]
        for cat in self .tags_store .categories :
            if any (
            self .tags_store .has_tag_in_category (var ,cat .id )
            for var in entry_vars 
            ):
                visible_cats .append (cat )

        has_visible =bool (visible_cats )
        self .group_label .setVisible (has_visible )
        self .group_combo .setVisible (has_visible )
        if not has_visible :
            return 

        self .group_combo .blockSignals (True )
        self .group_combo .clear ()
        self .group_combo .addItem (tr ("carousel.no_grouping"),None )
        for cat in visible_cats :
            self .group_combo .addItem (cat .name ,cat .id )
        self .group_combo .blockSignals (False )

    def refresh_tag_categories (self ):

        prev =self .group_category_id 
        self ._reload_group_options ()
        if prev and self .tags_store and self .tags_store .get_category (prev ):
            idx =self .group_combo .findData (prev )
            if idx >=0 :
                self .group_combo .setCurrentIndex (idx )
        else :
            self .group_category_id =None 
            self .current_tag =None 
        self ._render ()

    def _on_search_changed (self ,text :str ):
        self .search_text =text .strip ().lower ()
        self ._render ()

    def _on_group_changed (self ,_index :int ):
        self .group_category_id =self .group_combo .currentData ()
        self .current_tag =None 
        self ._render ()
        self .group_changed .emit (self .group_category_id )

    def _enter_tag_folder (self ,tag_text :str ):
        self .current_tag =tag_text 
        self ._render ()

    def _back_to_tags (self ):
        self .current_tag =None 
        self ._render ()

    def _rebuild_nav_row (self ):
        while self .nav_row .count ():
            item =self .nav_row .takeAt (0 )
            if item .widget ():
                item .widget ().deleteLater ()
        if self .group_category_id and self .current_tag is not None :
            cat =self .tags_store .get_category (self .group_category_id )if self .tags_store else None 
            cat_name =cat .name if cat else ""
            btn =QPushButton (f"‹ Все теги «{cat_name }»")
            btn .setFlat (True )
            btn .setObjectName ("link_btn")
            btn .clicked .connect (self ._back_to_tags )
            self .nav_row .addWidget (btn )
            sep =QLabel (f"›  {self .current_tag }")
            sep .setObjectName ("hint_text")
            self .nav_row .addWidget (sep )
        self .nav_row .addStretch ()



    def set_entries (self ,entries :List [ResourceEntry ]):
        self .entries =entries 
        self .selected_entry =None 
        self .current_tag =None 




        prev_group =self .group_category_id or self ._pending_initial_group_id 
        self ._pending_initial_group_id =None 
        self ._reload_group_options ()
        if prev_group and self .tags_store and self .tags_store .get_category (prev_group ):
            idx =self .group_combo .findData (prev_group )
            if idx >=0 :
                self .group_combo .blockSignals (True )
                self .group_combo .setCurrentIndex (idx )
                self .group_combo .blockSignals (False )
                self .group_category_id =prev_group 
            else :




                self .group_category_id =None 
        else :
            self .group_category_id =None 
        self ._render ()

    def _visible_entries_and_tag_folders (self ):

        if self .search_text :
            matches =[
            e for e in self .entries 
            if self .search_text in e .display_name .lower ()or self .search_text in e .var_name .lower ()
            ]
            return [],matches 

        if not self .group_category_id or not self .tags_store :
            return [],self .entries 

        cat =self .tags_store .get_category (self .group_category_id )
        if not cat :
            return [],self .entries 

        if self .current_tag is None :

            untagged =[
            e for e in self .entries 
            if not self .tags_store .has_tag_in_category (e .var_name ,self .group_category_id )
            ]
            return cat .tags ,untagged 


        tagged =[
        e for e in self .entries 
        if self .tags_store .has_tag (e .var_name ,self .group_category_id ,self .current_tag )
        ]
        return [],tagged 

    def _favorites_and_recent_entries (self ):

        if not self .usage_store or not self .usage_store .enabled or not self .category :
            return [],[]
        if self .search_text or self .group_category_id :
            return [],[]
        by_var ={e .var_name :e for e in self .entries }
        fav_vars =self .usage_store .get_favorites (self .category )
        recent_vars =self .usage_store .get_recent (self .category )
        favs =[by_var [v ]for v in fav_vars if v in by_var ]
        recents =[by_var [v ]for v in recent_vars if v in by_var and v not in fav_vars ]
        return favs ,recents 

    def _make_resource_card (self ,entry :ResourceEntry )->"ResourceCard":
        is_fav =bool (self .usage_store and self .category and self .usage_store .is_favorite (self .category ,entry .var_name ))
        card =ResourceCard (entry ,self .thumb_size ,is_favorite =is_fav ,
        show_favorite_star =bool (self .usage_store and self .category ))
        card .clicked .connect (self ._on_card_clicked )
        card .favorite_toggled .connect (self ._on_favorite_toggled )
        if self .selected_entry and entry .var_name ==self .selected_entry .var_name :
            card .set_selected (True )
        return card 

    def _render (self ):
        self ._rebuild_nav_row ()

        for card in self .cards :
            card .hide ()
        self .cards .clear ()
        while self .container_layout .count ():
            item =self .container_layout .takeAt (0 )
            w =item .widget ()
            if w :
                w .hide ()
                w .deleteLater ()

        tag_folders ,visible_entries =self ._visible_entries_and_tag_folders ()
        fav_entries ,recent_entries =self ._favorites_and_recent_entries ()

        count =0 

        if fav_entries or recent_entries :
            for label_text ,group in ((FAVORITES_LABEL ,fav_entries ),(RECENT_LABEL ,recent_entries )):
                if not group :
                    continue 
                sep =QLabel (label_text )
                sep .setObjectName ("accent_caption")
                sep .setStyleSheet ("font-size:11px; padding:0 6px;")
                sep .setFixedHeight (self .thumb_size +ResourceCard .LABEL_HEIGHT +14 )
                sep .setAlignment (Qt .AlignmentFlag .AlignVCenter )
                self .cards .append (sep )
                self .container_layout .addWidget (sep )
                count +=1 
                for entry in group :
                    card =self ._make_resource_card (entry )
                    self .cards .append (card )
                    self .container_layout .addWidget (card )
                    count +=1 
            divider =QFrame ()
            divider .setFrameShape (QFrame .Shape .VLine )
            divider .setObjectName ("hint_text")
            divider .setFixedHeight (self .thumb_size +ResourceCard .LABEL_HEIGHT +14 )
            self .cards .append (divider )
            self .container_layout .addWidget (divider )
            count +=1 

        for tag_text in tag_folders :
            card =FolderCard (tag_text ,self .thumb_size )
            card .clicked .connect (self ._enter_tag_folder )
            self .cards .append (card )
            self .container_layout .addWidget (card )
            count +=1 

        for entry in visible_entries :
            card =self ._make_resource_card (entry )
            self .cards .append (card )
            self .container_layout .addWidget (card )
            count +=1 

        if self .search_text and not visible_entries and not tag_folders :
            empty =QLabel (tr ("carousel.nothing_found"))
            empty .setObjectName ("hint_text")
            empty .setStyleSheet ("padding:0 6px;")
            self .cards .append (empty )
            self .container_layout .addWidget (empty )
            count +=1 

        self .container_layout .addStretch ()
        w =count *(self .thumb_size +22 )+10 
        self .container .setFixedWidth (max (w ,200 ))
        self .container .setFixedHeight (self .thumb_size +ResourceCard .LABEL_HEIGHT +14 )
        _apply_scroll_fill_alignment (self .row_layout ,self .scroll ,count ,max (w ,200 )+12 )
        self ._schedule_thumbnails ()

    def _schedule_thumbnails (self ):

        pending =[c for c in self .cards if isinstance (c ,ResourceCard )]
        batch_size =4 

        def step ():
            for _ in range (batch_size ):
                if not pending :
                    return 
                card =pending .pop (0 )
                try :
                    card .load_thumbnail ()
                except RuntimeError :


                    pass 
            if pending :
                QTimer .singleShot (0 ,step )

        QTimer .singleShot (0 ,step )

    def _on_card_clicked (self ,entry :ResourceEntry ):
        for card in self .cards :
            if isinstance (card ,ResourceCard ):
                card .set_selected (card .entry is entry )
        self .selected_entry =entry 
        if self .usage_store and self .category :
            self .usage_store .touch_recent (self .category ,entry .var_name )
            self .usage_store .save (self ._usage_base_dir ())
            self ._render ()
        self .selection_changed .emit (entry )

    def _usage_base_dir (self )->str :
        from core .paths import get_base_dir 
        return get_base_dir ()

    def _on_favorite_toggled (self ,entry :ResourceEntry ):
        if not self .usage_store or not self .category :
            return 
        self .usage_store .toggle_favorite (self .category ,entry .var_name )
        self .usage_store .save (self ._usage_base_dir ())
        self ._render ()

    def _clear_selection (self ):
        for card in self .cards :
            if isinstance (card ,ResourceCard ):
                card .set_selected (False )
        self .selected_entry =None 
        self .selection_changed .emit (None )

    def get_selected (self )->Optional [ResourceEntry ]:
        return self .selected_entry 

    def select_by_var (self ,var :str ):
        entry =next ((e for e in self .entries if e .var_name ==var ),None )
        self .selected_entry =entry 
        if entry and self .group_category_id and self .tags_store :
            self .current_tag =None 
            for key in self .tags_store .get_tags_for (entry .var_name ):
                cat_id ,tag_text =key .split (":",1 )if ":"in key else (None ,None )
                if cat_id ==self .group_category_id :
                    self .current_tag =tag_text 
                    break 
        self ._render ()



    def dragEnterEvent (self ,event ):
        if self .rm and self .category and event .mimeData ().hasUrls ():
            event .acceptProposedAction ()
            self ._set_cards_tooltip_suppressed (True )
            self ._drag_overlay .show_over (f"📥 Отпустите файлы, чтобы добавить в «{self .category }»")
        else :
            event .ignore ()

    def dragMoveEvent (self ,event ):
        if self .rm and self .category and event .mimeData ().hasUrls ():
            event .acceptProposedAction ()
        else :
            event .ignore ()

    def dragLeaveEvent (self ,event ):
        self ._set_cards_tooltip_suppressed (False )
        self ._drag_overlay .hide ()

    def _set_cards_tooltip_suppressed (self ,suppressed :bool ):
        for card in self .cards :
            if isinstance (card ,ResourceCard ):
                card .set_suppress_tooltip (suppressed )

    def dropEvent (self ,event ):
        self ._set_cards_tooltip_suppressed (False )
        self ._drag_overlay .hide ()
        if not (self .rm and self .category ):
            event .ignore ()
            return 
        paths =[url .toLocalFile ()for url in event .mimeData ().urls ()if url .isLocalFile ()]
        imported =[]
        skipped =[]
        for path in paths :
            if not os .path .isfile (path ):
                continue 
            entry =self .rm .import_local_file (self .category ,path )
            (imported if entry else skipped ).append (os .path .basename (path ))
        if imported :
            self .set_entries (self .rm .get (self .category ))
            self .select_by_var (self .entries [-1 ].var_name if not skipped else 
            next ((e .var_name for e in self .entries if e .filename in imported ),""))
            self .selection_changed .emit (self .selected_entry )
        if skipped :
            QMessageBox .warning (
            self ,tr ("carousel.import_failed_title"),
            tr ("carousel.import_failed_text",files ="\n".join (skipped ))
            )
        event .acceptProposedAction ()


class CompositeAttrCard (QFrame ):

    clicked =pyqtSignal (int ,str )

    LABEL_HEIGHT =ResourceCard .LABEL_HEIGHT 

    def __init__ (self ,group_index :int ,word :str ,representative :Optional [CompositeSprite ],rm ,thumb_size :int =96 ):
        super ().__init__ ()
        self .group_index =group_index 
        self .word =word 
        self .representative =representative 
        self .rm =rm 
        self .selected =False 
        self .compatible =True 
        self .thumb_size =thumb_size 
        self .setFixedSize (thumb_size +16 ,thumb_size +self .LABEL_HEIGHT +14 )
        self .setCursor (Qt .CursorShape .PointingHandCursor )
        self .setObjectName ("resource_card")
        self ._needs_thumb =True 
        self ._base_pixmap :Optional [QPixmap ]=None 
        self ._dimmed_pixmap :Optional [QPixmap ]=None 
        self ._setup_ui (thumb_size )

    def _setup_ui (self ,thumb_size :int ):
        layout =QVBoxLayout (self )
        layout .setContentsMargins (4 ,4 ,4 ,4 )
        layout .setSpacing (3 )

        self .preview =QLabel ()
        self .preview .setFixedSize (thumb_size ,thumb_size )
        self .preview .setAlignment (Qt .AlignmentFlag .AlignCenter )
        self .preview .setObjectName ("code_box")
        self .preview .setText ("…")
        self .preview .setStyleSheet (self .preview .styleSheet ()+"color:#555; font-size:11px;")
        layout .addWidget (self .preview )

        name_label =QLabel (self .word )
        name_label .setAlignment (Qt .AlignmentFlag .AlignCenter )
        name_label .setWordWrap (True )
        name_label .setObjectName ("hint_text")
        name_label .setMaximumWidth (thumb_size +8 )
        self .name_label =name_label 
        layout .addWidget (name_label )
        self ._update_style ()

    def load_thumbnail (self ):
        if not self ._needs_thumb :
            return 
        self ._needs_thumb =False 
        if self .representative is None :
            self .preview .setText ("❓")
            self .preview .setStyleSheet ("font-size:24px;")
            return 
        sprite =self .representative 
        layers =[
        (self .rm .resolve_layer_path (layer .rel_path ,sprite .source ),layer .offset_x ,layer .offset_y )
        for layer in sprite .layers 
        ]
        pm =get_composite (layers ,sprite .width ,sprite .height ,
        target_w =self .thumb_size ,target_h =self .thumb_size )
        if pm is not None :
            self ._base_pixmap =pm 
            self ._dimmed_pixmap =None 
            self ._apply_current_pixmap ()
        else :
            self .preview .setText ("🖼")
            self .preview .setStyleSheet ("font-size:24px;")

    def _apply_current_pixmap (self ):

        if self ._base_pixmap is None :
            return 
        if self .compatible :
            self .preview .setPixmap (self ._base_pixmap )
            return 
        if self ._dimmed_pixmap is None :
            self ._dimmed_pixmap =self ._make_dimmed (self ._base_pixmap )
        self .preview .setPixmap (self ._dimmed_pixmap )

    @staticmethod 
    def _make_dimmed (pixmap :QPixmap )->QPixmap :
        dimmed =QPixmap (pixmap .size ())
        dimmed .fill (Qt .GlobalColor .transparent )
        painter =QPainter (dimmed )
        painter .setOpacity (0.32 )
        painter .drawPixmap (0 ,0 ,pixmap )
        painter .end ()
        return dimmed 

    def _update_style (self ):
        self .setProperty ("selected",self .selected )
        self .style ().unpolish (self )
        self .style ().polish (self )

    def set_selected (self ,val :bool ):
        self .selected =val 
        self ._update_style ()

    def set_compatible (self ,compatible :bool ):

        if self .compatible ==compatible :
            return 
        self .compatible =compatible 
        self ._apply_current_pixmap ()
        self .name_label .setStyleSheet (""if compatible else "color:#666;")

    def mousePressEvent (self ,event ):
        self .clicked .emit (self .group_index ,self .word )
        super ().mousePressEvent (event )


def _position_labels ():
    return {"far":tr ("carousel.pos_far"),"close":tr ("carousel.pos_close"),"normal":tr ("carousel.pos_normal")}

POSITION_LABELS =_position_labels 


class CompositeSpriteCarousel (QWidget ):

    selection_changed =pyqtSignal (object )
    browsing_changed =pyqtSignal (bool )

    PREVIEW_SIZE =220 
    SWATCH_SIZE =96 
    DEFAULT_POSITION ="normal"

    def __init__ (self ,resource_manager =None ,thumb_size :int =160 ):
        super ().__init__ ()
        self .rm =resource_manager 
        self .thumb_size =thumb_size 
        self .current_path :List [str ]=[]
        self .cards :List [QWidget ]=[]
        self .selected_sprite :Optional [CompositeSprite ]=None 
        self .selected_attrs :List [Optional [str ]]=[]
        self .groups :List =[]
        self .selected_position :str =self .DEFAULT_POSITION 
        self .position_buttons :Dict [str ,QPushButton ]={}
        self .preview_label :Optional [QLabel ]=None 
        self ._setup_ui ()

    def _setup_ui (self ):
        outer =QVBoxLayout (self )
        outer .setContentsMargins (0 ,0 ,0 ,0 )
        outer .setSpacing (4 )

        self .breadcrumb_row =QHBoxLayout ()
        self .breadcrumb_row .setContentsMargins (0 ,0 ,0 ,4 )
        outer .addLayout (self .breadcrumb_row )

        self .scroll =HWheelScrollArea ()
        self .scroll .setHorizontalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAsNeeded )
        self .scroll .setVerticalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAsNeeded )
        self .scroll .setFixedHeight (self .thumb_size +52 +SCROLL_EXTRA )
        self .scroll .setWidgetResizable (True )
        self .scroll .setSizePolicy (QSizePolicy .Policy .Expanding ,QSizePolicy .Policy .Preferred )

        self .container =QWidget ()
        self .container .setSizePolicy (QSizePolicy .Policy .Expanding ,QSizePolicy .Policy .Preferred )
        self .container_layout =QHBoxLayout (self .container )
        self .container_layout .setContentsMargins (4 ,0 ,4 ,0 )
        self .container_layout .setSpacing (6 )
        self .container_layout .addStretch ()
        self .scroll .setAlignment (Qt .AlignmentFlag .AlignLeft |Qt .AlignmentFlag .AlignTop )
        self .scroll .setWidget (self .container )
        outer .addWidget (self .scroll )
        self .outer_layout =outer 

        none_row =QHBoxLayout ()
        self .btn_none =QPushButton (tr ("carousel.clear_selection"))
        self .btn_none .setObjectName ("btn_secondary")
        self .btn_none .setFixedHeight (36 )
        self .btn_none .clicked .connect (self ._clear_selection )
        none_row .addWidget (self .btn_none )
        none_row .addStretch ()
        outer .addLayout (none_row )

    def set_resource_manager (self ,rm ):
        self .rm =rm 
        self .current_path =[]
        self .selected_sprite =None 
        self .selected_attrs =[]
        self .selected_position =self .DEFAULT_POSITION 
        self ._refresh_view ()

    def select_by_name (self ,full_name :str ):

        if not self .rm :
            return 
        sprite =self .rm .find_composite_by_name (full_name )
        if sprite :
            self .current_path =[sprite .character ]
            self .selected_sprite =sprite 
            self .selected_attrs =list (sprite .variant_parts )
            self .selected_position =sprite .position 
        self ._refresh_view ()

    def get_selected (self )->Optional [CompositeSprite ]:
        return self .selected_sprite 

    def _go_to (self ,path_parts :List [str ]):
        self .current_path =list (path_parts )
        self ._refresh_view ()

    def _rebuild_breadcrumbs (self ):
        while self .breadcrumb_row .count ():
            item =self .breadcrumb_row .takeAt (0 )
            if item .widget ():
                item .widget ().deleteLater ()

        crumbs =[("🏠 Спрайты",[])]
        if len (self .current_path )>=1 :
            crumbs .append ((self .current_path [0 ],self .current_path [:1 ]))

        for i ,(text ,path )in enumerate (crumbs ):
            btn =QPushButton (text )
            btn .setFlat (True )
            is_last =(i ==len (crumbs )-1 )
            btn .setEnabled (not is_last )
            _t =theme_manager .tokens ()
            btn .setStyleSheet (f"""
                QPushButton {{
                    color: {_t .accent_2 if is_last else _t .text_dim };
                    font-weight: {'bold'if is_last else 'normal'};
                    border: none; padding: 2px 4px; text-align: left;
                    background: transparent;
                }}
                QPushButton:hover {{ color: {_t .accent_1 }; }}
                QPushButton:disabled {{ color: {_t .accent_2 }; }}
            """)
            btn .clicked .connect (lambda _ =None ,p =path :self ._go_to (p ))
            self .breadcrumb_row .addWidget (btn )
            if not is_last :
                sep =QLabel ("›")
                sep .setObjectName ("hint_text")
                self .breadcrumb_row .addWidget (sep )
        self .breadcrumb_row .addStretch ()

    def _clear_container (self ):
        for card in self .cards :
            card .hide ()
        self .cards .clear ()
        self .preview_label =None 
        while self .container_layout .count ():
            item =self .container_layout .takeAt (0 )
            w =item .widget ()
            if w :
                w .hide ()
                w .deleteLater ()

    def _refresh_view (self ):
        self ._rebuild_breadcrumbs ()
        self ._clear_container ()

        if not self .rm :
            self .scroll .setFixedHeight (self .thumb_size +52 +SCROLL_EXTRA )
            self .browsing_changed .emit (False )
            return 

        if len (self .current_path )==0 :
            self .scroll .setWidgetResizable (False )
            self .scroll .setHorizontalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAsNeeded )
            self .scroll .setVerticalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAlwaysOff )
            self .scroll .setFixedHeight (self .thumb_size +52 +SCROLL_EXTRA )
            characters =self .rm .get_composite_characters ()
            for character in characters :
                card =FolderCard (character ,self .thumb_size )
                card .clicked .connect (self ._on_character_clicked )
                self .cards .append (card )
                self .container_layout .addWidget (card )
            self .container_layout .addStretch ()
            w =len (characters )*(self .thumb_size +22 )+10 
            self .container .setMinimumWidth (max (w ,200 ))
            self .container .setFixedHeight (self .thumb_size +ResourceCard .LABEL_HEIGHT +14 )
            _apply_scroll_fill_alignment (self .outer_layout ,self .scroll ,len (characters ),max (w ,200 )+12 )
            self .browsing_changed .emit (False )
            return 

        character =self .current_path [0 ]
        positions =self .rm .get_composite_positions (character )
        if self .selected_position not in positions and positions :
            self .selected_position =positions [0 ]

        groups =self .rm .get_composite_attr_groups (character ,self .selected_position )






        if self .selected_sprite is not None and self .selected_sprite .position ==self .selected_position and self .selected_sprite .character ==character :
            remaining =list (self .selected_sprite .variant_parts )
            new_attrs :List [Optional [str ]]=[None ]*len (groups )
            for gi ,group in enumerate (groups ):
                for w in remaining :
                    if w in group .words :
                        new_attrs [gi ]=w 
                        remaining .remove (w )
                        break 
            self .selected_attrs =new_attrs 
        elif len (self .selected_attrs )<len (groups ):
            self .selected_attrs =self .selected_attrs +[None ]*(len (groups )-len (self .selected_attrs ))
        elif len (self .selected_attrs )>len (groups ):
            self .selected_attrs =self .selected_attrs [:len (groups )]

        self .scroll .setWidgetResizable (True )
        self .scroll .setHorizontalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAlwaysOff )
        self .scroll .setVerticalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAsNeeded )
        self .scroll .setMaximumWidth (16777215 )
        self .outer_layout .setAlignment (self .scroll ,Qt .AlignmentFlag (0 ))

        panel =QWidget ()
        panel .setSizePolicy (QSizePolicy .Policy .Expanding ,QSizePolicy .Policy .Preferred )
        vlayout =QVBoxLayout (panel )
        vlayout .setContentsMargins (4 ,4 ,4 ,4 )
        vlayout .setSpacing (8 )

        top_row =QHBoxLayout ()
        top_row .setSpacing (10 )

        self .preview_label =QLabel ()
        self .preview_label .setFixedSize (self .PREVIEW_SIZE ,self .PREVIEW_SIZE )
        self .preview_label .setAlignment (Qt .AlignmentFlag .AlignCenter )
        self .preview_label .setObjectName ("code_box")
        top_row .addWidget (self .preview_label )

        right_col =QVBoxLayout ()
        right_col .setSpacing (6 )

        if len (positions )>1 :
            pos_label =QLabel (tr ("carousel.position_zoom_label"))
            pos_label .setObjectName ("hint_text")
            right_col .addWidget (pos_label )

            pos_row =QHBoxLayout ()
            pos_row .setSpacing (6 )
            self .position_buttons ={}
            labels =_position_labels ()
            for key in positions :
                btn =QPushButton (labels .get (key ,key ))
                btn .setCheckable (True )
                btn .setChecked (key ==self .selected_position )
                btn .setObjectName ("btn_secondary")
                btn .setFixedHeight (36 )
                btn .clicked .connect (lambda _ =None ,k =key :self ._on_position_clicked (k ))
                self .position_buttons [key ]=btn 
                pos_row .addWidget (btn )
            pos_row .addStretch ()
            right_col .addLayout (pos_row )

        right_col .addStretch ()
        top_row .addLayout (right_col ,1 )
        vlayout .addLayout (top_row )







        self .groups =groups 
        for gi ,group in enumerate (groups ):
            if not group .words :
                continue 
            label_key ="carousel.attribute_n_optional_label"if group .optional else "carousel.attribute_n_label"
            row_label =QLabel (tr (label_key ,n =gi +1 ))
            row_label .setObjectName ("hint_text")
            vlayout .addWidget (row_label )

            row_scroll =HOnlyWheelScrollArea ()
            row_scroll .setWidgetResizable (False )
            row_scroll .setHorizontalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAsNeeded )
            row_scroll .setVerticalScrollBarPolicy (Qt .ScrollBarPolicy .ScrollBarAlwaysOff )
            card_height =self .SWATCH_SIZE +ResourceCard .LABEL_HEIGHT +14 
            row_scroll .setFixedHeight (card_height +18 )

            row_widget =QWidget ()
            row_layout =QHBoxLayout (row_widget )
            row_layout .setContentsMargins (0 ,0 ,0 ,0 )
            row_layout .setSpacing (6 )

            selected_word =self .selected_attrs [gi ]if gi <len (self .selected_attrs )else None 
            for word in group .words :
                representative =self .rm .find_composite_with_word (character ,self .selected_position ,word )
                card =CompositeAttrCard (gi ,word ,representative ,self .rm ,self .SWATCH_SIZE )
                card .set_selected (word ==selected_word )
                card .clicked .connect (self ._on_attr_clicked )
                self .cards .append (card )
                row_layout .addWidget (card )
            row_scroll .setWidget (row_widget )
            vlayout .addWidget (row_scroll )

        vlayout .addStretch ()
        self .container_layout .addWidget (panel ,1 )
        self .container .setMinimumWidth (self .PREVIEW_SIZE +40 )

        natural_height =panel .layout ().sizeHint ().height ()
        self .container .setMinimumHeight (natural_height +10 )
        self .scroll .setFixedHeight (min (natural_height +20 ,560 ))

        self ._update_match ()
        self ._schedule_thumbnails ()
        self .browsing_changed .emit (True )

    def _update_match (self ):

        if not self .rm or not self .current_path :
            return 
        character =self .current_path [0 ]
        matched =self .rm .find_composite_by_attr_selection (character ,self .selected_position ,self .selected_attrs ,self .groups )
        self .selected_sprite =matched 
        self ._update_compatibility_highlight ()
        if self .preview_label is None :
            return 
        if matched is None :
            self .preview_label .setText (tr ("carousel.no_matching_sprite"))
            self .preview_label .setStyleSheet ("color:#888; font-size:11px;")
            return 
        layers =[
        (self .rm .resolve_layer_path (layer .rel_path ,matched .source ),layer .offset_x ,layer .offset_y )
        for layer in matched .layers 
        ]
        pm =get_composite (layers ,matched .width ,matched .height ,
        target_w =self .PREVIEW_SIZE ,target_h =self .PREVIEW_SIZE )
        if pm is not None :
            self .preview_label .setPixmap (pm )
            self .preview_label .setStyleSheet ("")
        else :
            self .preview_label .setText ("🖼")
            self .preview_label .setStyleSheet ("font-size:32px;")

    def _update_compatibility_highlight (self ):

        if not self .rm or not self .current_path or not self .groups :
            return 
        character =self .current_path [0 ]
        any_selected =any (a is not None for a in self .selected_attrs )
        compat_cache :Dict [int ,set ]={}
        for card in self .cards :
            if not isinstance (card ,CompositeAttrCard ):
                continue 
            gi =card .group_index 
            if not any_selected :
                card .set_compatible (True )
                continue 
            if gi not in compat_cache :
                compat_cache [gi ]=self .rm .get_compatible_words (
                character ,self .selected_position ,self .groups ,self .selected_attrs ,gi )
            card .set_compatible (card .word in compat_cache [gi ])

    def _schedule_thumbnails (self ):
        pending =[c for c in self .cards if isinstance (c ,CompositeAttrCard )]
        batch_size =4 

        def step ():
            for _ in range (batch_size ):
                if not pending :
                    return 
                card =pending .pop (0 )
                try :
                    card .load_thumbnail ()
                except RuntimeError :
                    pass 
            if pending :
                QTimer .singleShot (0 ,step )

        QTimer .singleShot (0 ,step )

    def _on_character_clicked (self ,character :str ):
        self .selected_sprite =None 
        self .selected_attrs =[]
        self .selected_position =self .DEFAULT_POSITION 
        self .current_path =[character ]
        self ._refresh_view ()
        self .selection_changed .emit (self .selected_sprite )

    def _on_position_clicked (self ,key :str ):
        self .selected_position =key 
        for k ,btn in self .position_buttons .items ():
            btn .setChecked (k ==key )
        self ._refresh_view ()
        self .selection_changed .emit (self .selected_sprite )

    def _on_attr_clicked (self ,group_index :int ,word :str ):
        if group_index >=len (self .selected_attrs ):
            self .selected_attrs .extend ([None ]*(group_index +1 -len (self .selected_attrs )))


        if self .selected_attrs [group_index ]==word :
            self .selected_attrs [group_index ]=None 
        else :
            self .selected_attrs [group_index ]=word 
        for card in self .cards :
            if isinstance (card ,CompositeAttrCard )and card .group_index ==group_index :
                card .set_selected (card .word ==self .selected_attrs [group_index ])
        self ._update_match ()
        self .selection_changed .emit (self .selected_sprite )

    def _clear_selection (self ):
        self .selected_sprite =None 
        self .selected_attrs =[]
        self .selected_position =self .DEFAULT_POSITION 
        self .current_path =[]
        self ._refresh_view ()
        self .selection_changed .emit (None )

    def reset_silent (self ):

        self .selected_sprite =None 
        self .selected_attrs =[]
        self .selected_position =self .DEFAULT_POSITION 
        self .current_path =[]
        self ._refresh_view ()
