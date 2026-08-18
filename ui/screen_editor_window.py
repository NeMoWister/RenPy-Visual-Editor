
from __future__ import annotations 

import os 
import shutil 
from typing import Dict ,Optional 

from PyQt6 .QtCore import Qt ,QEvent ,QPoint ,QRect ,QRectF ,QSize 
from PyQt6 .QtGui import (
QFont ,QKeySequence ,QShortcut ,QColor ,QPixmap ,QImage ,QPainter ,
QTransform ,QBrush ,
)
from PyQt6 .QtWidgets import (
QWidget ,QMainWindow ,QVBoxLayout ,QHBoxLayout ,QSplitter ,QLabel ,
QPushButton ,QToolButton ,QScrollArea ,QFrame ,QLineEdit ,QCheckBox ,
QComboBox ,QTreeWidget ,QTreeWidgetItem ,QFormLayout ,QPlainTextEdit ,
QGridLayout ,QProgressBar ,QGroupBox ,QMessageBox ,QFileDialog ,
QSizePolicy ,QListWidget ,QListWidgetItem ,QInputDialog ,QMenu 
)

from core .i18n import tr 
from core .screen_model import (
Screen ,ScreenDocument ,ScreenElement ,TAG_CATALOG ,default_element ,
property_fields_for ,
)
from core .screen_code_generator import generate_screen ,generate_document 
from core import screen_templates as tpl_mod 

STAGE_W ,STAGE_H =960 ,540 
GAME_RESOLUTION =(1920 ,1080 )
CANVAS_SCALE =STAGE_W /GAME_RESOLUTION [0 ]
SNAP_THRESHOLD =8 
GRID_STEP =10 

CATEGORY_LABELS ={
"container":"Контейнеры",
"widget":"Виджеты",
"control":"Интерактив",
"logic":"Логика",
}


class _ClickableMixin :



class _BackgroundFrame (QFrame ):


    def __init__ (self ,*a ,**kw ):
        super ().__init__ (*a ,**kw )
        self .bg_pixmap :Optional [QPixmap ]=None 
        self .bg_tile :bool =False 

    def paintEvent (self ,event ):
        if self .bg_pixmap is not None and not self .bg_pixmap .isNull ():
            painter =QPainter (self )
            rect =self .contentsRect ()
            if self .bg_tile :
                painter .drawTiledPixmap (rect ,self .bg_pixmap )
            else :
                painter .drawPixmap (rect ,self .bg_pixmap ,self .bg_pixmap .rect ())
            painter .end ()
        super ().paintEvent (event )


def _install_click (widget :QWidget ,callback )->None :
    def handler (event ,cb =callback ):
        cb ()
        event .accept ()
    widget .mousePressEvent =handler 


class ScreenEditorWindow (QWidget ):


    def __init__ (self ,project =None ,parent =None ,on_export =None ,rm =None ,base_dir =None ):
        super ().__init__ (parent ,Qt .WindowType .Window )
        self .setWindowTitle (tr ("screens.title")if _has_tr ("screens.title")else "Редактор экранов Ren'Py")
        self .project =project 
        self ._on_export =on_export 
        self .rm =rm 



        self .base_dir =base_dir or getattr (rm ,"base_dir",None )or os .getcwd ()



        self ._custom_root =None 
        if rm is not None and hasattr (rm ,"get_source_root"):
            try :
                self ._custom_root =rm .get_source_root ("custom")
            except Exception :
                self ._custom_root =None 
        if not self ._custom_root :
            resources_root =os .path .join (self .base_dir ,"resources")
            self ._custom_root =os .path .join (resources_root ,"custom")
        self .images_dir =os .path .join (self ._custom_root ,"menu")

        self .document =ScreenDocument ()
        self .document .add (tpl_mod .tpl_main_menu ())
        self .current :Screen =self .document .screens [0 ]
        self .selected_id :Optional [str ]=None 
        self ._element_widgets :Dict [str ,QWidget ]={}

        self ._build_ui ()
        self ._refresh_screens_list ()
        self ._select_screen (self .current .name )

        sc =QShortcut (QKeySequence ("Escape"),self )
        sc .activated .connect (self ._maybe_close )
        del_sc =QShortcut (QKeySequence ("Delete"),self )
        del_sc .activated .connect (self ._delete_selected )

        self .showMaximized ()




    def _build_ui (self ):
        root =QVBoxLayout (self )
        root .setContentsMargins (8 ,8 ,8 ,8 )
        root .setSpacing (6 )

        root .addWidget (self ._build_topbar ())

        splitter =QSplitter (Qt .Orientation .Horizontal )
        splitter .addWidget (self ._build_left_panel ())
        splitter .addWidget (self ._build_center_panel ())
        splitter .addWidget (self ._build_right_panel ())
        splitter .setStretchFactor (0 ,0 )
        splitter .setStretchFactor (1 ,1 )
        splitter .setStretchFactor (2 ,0 )
        splitter .setSizes ([260 ,700 ,320 ])
        root .addWidget (splitter ,1 )

        self .code_view =QPlainTextEdit ()
        self .code_view .setReadOnly (True )
        self .code_view .setMaximumHeight (160 )
        self .code_view .setFont (QFont ("Consolas",10 ))
        code_box =QGroupBox ("Код (.rpy) - предпросмотр")
        cl =QVBoxLayout (code_box )
        cl .addWidget (self .code_view )
        root .addWidget (code_box )

    def _build_topbar (self )->QWidget :
        bar =QFrame ()
        lay =QHBoxLayout (bar )
        lay .setContentsMargins (0 ,0 ,0 ,0 )

        title =QLabel ("🖥 Редактор экранов Ren'Py - полноэкранный WYSIWYG")
        title .setStyleSheet ("font-weight: 600; font-size: 13px;")
        lay .addWidget (title )
        lay .addStretch (1 )

        self .tpl_combo =QComboBox ()
        self .tpl_combo .addItem ("- выбрать шаблон -",None )
        for key ,(label ,_fn )in tpl_mod .TEMPLATES .items ():
            self .tpl_combo .addItem (label ,key )
        lay .addWidget (QLabel ("Шаблон:"))
        lay .addWidget (self .tpl_combo )
        btn_add_tpl =QPushButton ("Добавить экран из шаблона")
        btn_add_tpl .clicked .connect (self ._add_screen_from_template )
        lay .addWidget (btn_add_tpl )

        btn_export =QPushButton ("Экспорт .rpy…")
        btn_export .clicked .connect (self ._export_rpy )
        lay .addWidget (btn_export )

        btn_close =QPushButton ("Закрыть")
        btn_close .clicked .connect (self ._maybe_close )
        lay .addWidget (btn_close )
        return bar 

    def _build_left_panel (self )->QWidget :
        panel =QWidget ()
        lay =QVBoxLayout (panel )
        lay .setContentsMargins (0 ,0 ,0 ,0 )

        screens_box =QGroupBox ("Экраны проекта")
        sb =QVBoxLayout (screens_box )
        self .screens_list =QListWidget ()
        self .screens_list .currentTextChanged .connect (self ._on_screen_list_changed )
        sb .addWidget (self .screens_list )
        srow =QHBoxLayout ()
        b_new =QPushButton ("+ Новый")
        b_new .clicked .connect (self ._new_blank_screen )
        b_dup =QPushButton ("Дублировать")
        b_dup .clicked .connect (self ._duplicate_screen )
        b_del =QPushButton ("Удалить")
        b_del .clicked .connect (self ._delete_screen )
        srow .addWidget (b_new )
        srow .addWidget (b_dup )
        srow .addWidget (b_del )
        sb .addLayout (srow )
        lay .addWidget (screens_box )

        pal_box =QGroupBox ("Палитра тегов")
        pal_lay =QVBoxLayout (pal_box )
        by_cat :Dict [str ,list ]={}
        for tag ,spec in TAG_CATALOG .items ():
            by_cat .setdefault (spec .category ,[]).append ((tag ,spec ))
        for cat in ("container","widget","control","logic"):
            items =by_cat .get (cat ,[])
            if not items :
                continue 
            grp =QLabel (CATEGORY_LABELS .get (cat ,cat ))
            grp .setStyleSheet ("font-weight: 600; margin-top: 6px;")
            pal_lay .addWidget (grp )
            col =QVBoxLayout ()
            col .setSpacing (4 )
            for tag ,spec in items :
                b =QToolButton ()
                b .setText (spec .label or tag )
                b .setToolTip (f"Добавить <{tag }>")
                b .setSizePolicy (QSizePolicy .Policy .Expanding ,QSizePolicy .Policy .Fixed )
                b .setToolButtonStyle (Qt .ToolButtonStyle .ToolButtonTextOnly )
                b .clicked .connect (lambda _ =False ,t =tag :self ._add_element (t ))
                col .addWidget (b )
            pal_lay .addLayout (col )
        pal_scroll =QScrollArea ()
        pal_scroll .setWidgetResizable (True )
        pal_inner =QWidget ()
        pal_inner .setLayout (pal_lay )
        pal_scroll .setWidget (pal_inner )
        lay .addWidget (pal_box ,0 )
        lay .addWidget (pal_scroll ,1 )
        panel .setMaximumWidth (320 )
        return panel 

    def _build_center_panel (self )->QWidget :
        panel =QWidget ()
        lay =QVBoxLayout (panel )
        lay .setContentsMargins (0 ,0 ,0 ,0 )

        meta =QGroupBox ("Параметры экрана")
        form =QFormLayout (meta )
        self .name_edit =QLineEdit ()
        self .name_edit .editingFinished .connect (self ._apply_meta )
        self .params_edit =QLineEdit ()
        self .params_edit .setPlaceholderText ("(items=[])")
        self .params_edit .editingFinished .connect (self ._apply_meta )
        self .tag_edit =QLineEdit ()
        self .tag_edit .setPlaceholderText ("напр. menu / choice / nvl")
        self .tag_edit .editingFinished .connect (self ._apply_meta )
        self .zorder_edit =QLineEdit ()
        self .zorder_edit .setPlaceholderText ("напр. 10")
        self .zorder_edit .editingFinished .connect (self ._apply_meta )
        self .modal_check =QCheckBox ("modal")
        self .modal_check .stateChanged .connect (self ._apply_meta )
        form .addRow ("screen",self .name_edit )
        form .addRow ("параметры",self .params_edit )
        form .addRow ("tag",self .tag_edit )
        form .addRow ("zorder",self .zorder_edit )
        form .addRow ("",self .modal_check )
        lay .addWidget (meta )

        stage_scroll =QScrollArea ()
        stage_scroll .setWidgetResizable (False )
        stage_scroll .setAlignment (Qt .AlignmentFlag .AlignCenter )
        stage_scroll .setStyleSheet ("QScrollArea { background: #0c0c10; border: none; }")
        self .stage =QFrame ()
        self .stage .setFixedSize (STAGE_W ,STAGE_H )
        self .stage .setStyleSheet (
        "QFrame { background: qlineargradient(x1:0,y1:0,x2:1,y2:1,"
        "stop:0 #1c1c24, stop:1 #14141a); border: 2px solid #3a3a46; }"
        )
        _install_click (self .stage ,lambda :self ._select_element (None ))
        stage_scroll .setWidget (self .stage )
        lay .addWidget (stage_scroll ,1 )
        return panel 

    def _build_right_panel (self )->QWidget :
        panel =QWidget ()
        panel .setMaximumWidth (360 )
        lay =QVBoxLayout (panel )
        lay .setContentsMargins (0 ,0 ,0 ,0 )

        tree_box =QGroupBox ("Дерево элементов")
        tb =QVBoxLayout (tree_box )
        self .layers_tree =QTreeWidget ()
        self .layers_tree .setHeaderHidden (True )
        self .layers_tree .itemClicked .connect (self ._on_tree_click )
        tb .addWidget (self .layers_tree )
        row =QHBoxLayout ()
        b_dup =QPushButton ("Дублировать")
        b_dup .clicked .connect (self ._duplicate_selected )
        b_del =QPushButton ("Удалить")
        b_del .clicked .connect (self ._delete_selected )
        row .addWidget (b_dup )
        row .addWidget (b_del )
        tb .addLayout (row )
        lay .addWidget (tree_box ,1 )

        self .props_box =QGroupBox ("Свойства элемента")
        self .props_layout =QFormLayout (self .props_box )
        props_scroll =QScrollArea ()
        props_scroll .setWidgetResizable (True )
        props_scroll .setWidget (self .props_box )
        lay .addWidget (props_scroll ,1 )
        return panel 







    def _import_image_file (self ,parent_widget =None )->Optional [str ]:

        path ,_ =QFileDialog .getOpenFileName (
        parent_widget or self ,"Выбрать изображение","",
        "Изображения (*.png *.jpg *.jpeg *.webp *.gif *.bmp);;Все файлы (*)")
        if not path :
            return None 
        try :
            os .makedirs (self .images_dir ,exist_ok =True )
        except OSError as exc :
            QMessageBox .critical (self ,"Ошибка",f"Не удалось создать папку resources/custom/menu:\n{exc }")
            return None 

        base_name =os .path .basename (path )
        stem ,ext =os .path .splitext (base_name )
        dest_name =base_name 
        counter =2 
        while os .path .exists (os .path .join (self .images_dir ,dest_name )):
            dest_name =f"{stem }_{counter }{ext }"
            counter +=1 
        dest_path =os .path .join (self .images_dir ,dest_name )
        try :
            shutil .copy2 (path ,dest_path )
        except OSError as exc :
            QMessageBox .critical (self ,"Ошибка",f"Не удалось скопировать файл:\n{exc }")
            return None 

        rel =os .path .relpath (dest_path ,self ._custom_root ).replace ("\\","/")
        return f'"{rel }"'

    def _resolve_image_abs_path (self ,raw :str )->Optional [str ]:

        if not raw :
            return None 
        candidate =raw .strip ().strip ('"').strip ("'")
        if not candidate or "("in candidate or " "in candidate .strip ():


            pass 
        search_roots =[
        candidate if os .path .isabs (candidate )else None ,
        os .path .join (self ._custom_root ,candidate ),
        os .path .join (self .base_dir ,candidate ),
        os .path .join (self .images_dir ,os .path .basename (candidate )),
        ]
        for p in search_roots :
            if p and os .path .isfile (p ):
                return p 
        return None 

    def _image_pick_row (self ,get_value ,set_value ,placeholder :str )->QWidget :

        wrap =QWidget ()
        row =QHBoxLayout (wrap )
        row .setContentsMargins (0 ,0 ,0 ,0 )
        e =QLineEdit (get_value ())
        e .setPlaceholderText (placeholder )
        e .textChanged .connect (lambda v :(set_value (v ),self ._rebuild_canvas_and_code ()))
        btn =QPushButton ("Обзор…")
        btn .setFixedWidth (70 )

        def browse ():
            renpy_path =self ._import_image_file (wrap )
            if renpy_path :
                e .setText (renpy_path )

        btn .clicked .connect (browse )
        row .addWidget (e ,1 )
        row .addWidget (btn )
        return wrap 


    def _refresh_screens_list (self ):
        self .screens_list .blockSignals (True )
        self .screens_list .clear ()
        for s in self .document .screens :
            self .screens_list .addItem (QListWidgetItem (s .name ))
        self .screens_list .blockSignals (False )

    def _select_screen (self ,name :str ):
        screen =self .document .get (name )
        if screen is None :
            return 
        self .current =screen 
        self .selected_id =None 
        items =self .screens_list .findItems (name ,Qt .MatchFlag .MatchExactly )
        if items :
            self .screens_list .blockSignals (True )
            self .screens_list .setCurrentItem (items [0 ])
            self .screens_list .blockSignals (False )
        self ._load_meta_fields ()
        self ._rebuild_all ()

    def _on_screen_list_changed (self ,name :str ):
        if name :
            self ._select_screen (name )

    def _add_screen_from_template (self ):
        key =self .tpl_combo .currentData ()
        if not key :
            QMessageBox .information (self ,"Шаблон","Сначала выберите шаблон из списка.")
            return 
        screen =tpl_mod .create_from_template (key )
        screen .name =self .document .unique_name (screen .name )
        self .document .add (screen )
        self ._refresh_screens_list ()
        self ._select_screen (screen .name )

    def _new_blank_screen (self ):
        name ,ok =QInputDialog .getText (self ,"Новый экран","Имя экрана:",text ="new_screen")
        if not ok or not name .strip ():
            return 
        screen =tpl_mod .blank_screen (self .document .unique_name (name .strip ()))
        self .document .add (screen )
        self ._refresh_screens_list ()
        self ._select_screen (screen .name )

    def _duplicate_screen (self ):
        clone =self .current .clone ()
        clone .name =self .document .unique_name (self .current .name +"_copy")
        self .document .add (clone )
        self ._refresh_screens_list ()
        self ._select_screen (clone .name )

    def _delete_screen (self ):
        if len (self .document .screens )<=1 :
            QMessageBox .warning (self ,"Удаление","Нельзя удалить последний экран.")
            return 
        name =self .current .name 
        self .document .remove (name )
        self ._refresh_screens_list ()
        self ._select_screen (self .document .screens [0 ].name )

    def _load_meta_fields (self ):
        for w in (self .name_edit ,self .params_edit ,self .tag_edit ,self .zorder_edit ):
            w .blockSignals (True )
        self .modal_check .blockSignals (True )
        self .name_edit .setText (self .current .name )
        self .params_edit .setText (self .current .parameters )
        self .tag_edit .setText (self .current .tag )
        self .zorder_edit .setText (self .current .zorder )
        self .modal_check .setChecked (self .current .modal )
        for w in (self .name_edit ,self .params_edit ,self .tag_edit ,self .zorder_edit ):
            w .blockSignals (False )
        self .modal_check .blockSignals (False )

    def _apply_meta (self ,*_ ):
        old_name =self .current .name 
        new_name =self .name_edit .text ().strip ()or old_name 
        if new_name !=old_name and self .document .get (new_name )is None :
            self .current .name =new_name 
        self .current .parameters =self .params_edit .text ().strip ()
        self .current .tag =self .tag_edit .text ().strip ()
        self .current .zorder =self .zorder_edit .text ().strip ()
        self .current .modal =self .modal_check .isChecked ()
        self ._refresh_screens_list ()
        self ._select_after_rename (self .current .name )
        self ._update_code_preview ()

    def _select_after_rename (self ,name ):
        items =self .screens_list .findItems (name ,Qt .MatchFlag .MatchExactly )
        if items :
            self .screens_list .blockSignals (True )
            self .screens_list .setCurrentItem (items [0 ])
            self .screens_list .blockSignals (False )




    def _add_element (self ,tag :str ):
        new_el =default_element (tag )
        parent =self .current .root 
        if self .selected_id :
            sel =self .current .root .find (self .selected_id )
            if sel is not None and sel .is_container :
                parent =sel 
        parent .children .append (new_el )
        self .selected_id =new_el .id 
        self ._rebuild_all ()

    def _delete_selected (self ):
        if not self .selected_id :
            return 
        parent =self .current .root .find_parent (self .selected_id )
        if parent is None :
            return 
        parent .children =[c for c in parent .children if c .id !=self .selected_id ]
        self .selected_id =None 
        self ._rebuild_all ()

    def _duplicate_selected (self ):
        if not self .selected_id :
            return 
        parent =self .current .root .find_parent (self .selected_id )
        el =self .current .root .find (self .selected_id )
        if parent is None or el is None :
            return 
        clone =el .clone ()
        idx =parent .children .index (el )
        parent .children .insert (idx +1 ,clone )
        self .selected_id =clone .id 
        self ._rebuild_all ()

    def _select_element (self ,el_id :Optional [str ]):
        self .selected_id =el_id 
        self ._highlight_selection ()
        self ._build_properties_panel ()
        self ._sync_tree_selection ()

    def _on_tree_click (self ,item :QTreeWidgetItem ,_col :int ):
        el_id =item .data (0 ,Qt .ItemDataRole .UserRole )
        self ._select_element (el_id )




    def _rebuild_all (self ):
        self ._render_canvas ()
        self ._render_tree ()
        self ._build_properties_panel ()
        self ._update_code_preview ()

    def _render_canvas (self ):

        old_layout =self .stage .layout ()
        if old_layout is not None :
            while old_layout .count ():
                item =old_layout .takeAt (0 )
                w =item .widget ()
                if w :
                    w .setParent (None )
                    w .deleteLater ()
            QWidget ().setLayout (old_layout )

        self ._element_widgets ={}
        outer =QVBoxLayout (self .stage )
        outer .setContentsMargins (4 ,4 ,4 ,4 )
        for child in self .current .root .children :
            outer .addWidget (self ._build_widget (child ))
        outer .addStretch (1 )
        self ._highlight_selection ()

    def _selected_style (self ,el_id :str ,base :str )->str :
        if el_id ==self .selected_id :
            return base +"border: 2px solid #ff8c3d;"
        return base 








    @staticmethod 
    def _parse_tuple (raw :str ,expected :Optional [int ]=None )->Optional [list ]:
        if not raw :
            return None 
        try :
            txt =raw .strip ().strip ('"').strip ("'").strip ()
            txt =txt .strip ("()[]")
            parts =[p .strip ()for p in txt .split (",")if p .strip ()!=""]
            vals =[float (p )for p in parts ]
            if expected and len (vals )!=expected :
                return None 
            return vals 
        except Exception :
            return None 

    def _apply_crop (self ,pm :QPixmap ,el :ScreenElement )->QPixmap :

        box =None 
        crop_vals =self ._parse_tuple (el .properties .get ("crop",""),4 )
        if crop_vals :
            box =crop_vals 
        else :
            c1 =self ._parse_tuple (el .properties .get ("corner1",""),2 )
            c2 =self ._parse_tuple (el .properties .get ("corner2",""),2 )
            if c1 and c2 :
                x =min (c1 [0 ],c2 [0 ])
                y =min (c1 [1 ],c2 [1 ])
                w =abs (c2 [0 ]-c1 [0 ])
                h =abs (c2 [1 ]-c1 [1 ])
                box =[x ,y ,w ,h ]
        if not box :
            return pm 
        x ,y ,w ,h =box 
        w =max (1 ,int (round (w )))
        h =max (1 ,int (round (h )))
        result =QPixmap (w ,h )
        result .fill (Qt .GlobalColor .transparent )
        painter =QPainter (result )
        painter .drawPixmap (int (round (-x )),int (round (-y )),pm )
        painter .end ()
        return result 

    def _apply_rotate (self ,pm :QPixmap ,el :ScreenElement )->QPixmap :

        raw =el .properties .get ("rotate")
        if not raw :
            return pm 
        try :
            deg =float (str (raw ).strip ().strip ('"'))
        except (TypeError ,ValueError ):
            return pm 
        if deg %360 ==0 :
            return pm 
        transform =QTransform ().rotate (deg )
        return pm .transformed (transform ,Qt .TransformationMode .SmoothTransformation )

    def _apply_matrixcolor (self ,pm :QPixmap ,el :ScreenElement )->QPixmap :

        raw =el .properties .get ("matrixcolor")
        if not raw :
            return pm 
        matrix =self ._resolve_color_matrix (raw )
        if matrix is None :
            return pm 
        if pm .width ()*pm .height ()>480 *480 :



            return pm 
        img =pm .toImage ().convertToFormat (QImage .Format .Format_RGBA8888 )
        w ,h =img .width (),img .height ()
        a ,b ,c ,d ,e =matrix [0 ]
        f ,g ,h2 ,i ,j =matrix [1 ]
        k ,l ,m ,n ,o =matrix [2 ]
        p ,q ,r ,s ,t =matrix [3 ]
        for yy in range (h ):
            for xx in range (w ):
                col =img .pixelColor (xx ,yy )
                rn ,gn ,bn ,an =col .redF (),col .greenF (),col .blueF (),col .alphaF ()
                nr =a *rn +b *gn +c *bn +d *an +e 
                ng =f *rn +g *gn +h2 *bn +i *an +j 
                nb =k *rn +l *gn +m *bn +n *an +o 
                na =p *rn +q *gn +r *bn +s *an +t 
                out =QColor .fromRgbF (
                max (0.0 ,min (1.0 ,nr )),max (0.0 ,min (1.0 ,ng )),
                max (0.0 ,min (1.0 ,nb )),max (0.0 ,min (1.0 ,na )))
                img .setPixelColor (xx ,yy ,out )
        return QPixmap .fromImage (img )

    @staticmethod 
    def _resolve_color_matrix (raw :str )->Optional [list ]:

        txt =raw .strip ().strip ('"').strip ("'").strip ()
        low =txt .lower ()

        def identity ():
            return [[1 ,0 ,0 ,0 ,0 ],[0 ,1 ,0 ,0 ,0 ],[0 ,0 ,1 ,0 ,0 ],[0 ,0 ,0 ,1 ,0 ]]


        try :
            body =txt .strip ("()[]")
            nums =[float (p .strip ())for p in body .split (",")if p .strip ()!=""]
        except Exception :
            nums =[]
        if len (nums )==16 :
            rows =[nums [0 :4 ]+[0 ],nums [4 :8 ]+[0 ],nums [8 :12 ]+[0 ],nums [12 :16 ]+[0 ]]
            return rows 
        if len (nums )==20 :
            return [nums [0 :5 ],nums [5 :10 ],nums [10 :15 ],nums [15 :20 ]]

        import re 
        m =re .match (r"([a-z_]+)\s*(?:\(([^)]*)\))?",low )
        if not m :
            return None 
        name ,args_raw =m .group (1 ),m .group (2 )or ""
        args =[]
        for a in args_raw .split (","):
            a =a .strip ().strip ('"').strip ("'")
            if not a :
                continue 
            try :
                args .append (float (a ))
            except ValueError :
                pass 

        if name in ("identitymatrix","identity"):
            return identity ()
        if name in ("invertmatrix","invert"):
            return [[-1 ,0 ,0 ,0 ,1 ],[0 ,-1 ,0 ,0 ,1 ],[0 ,0 ,-1 ,0 ,1 ],[0 ,0 ,0 ,1 ,0 ]]
        if name in ("saturationmatrix","desaturate","grayscale","greyscale"):
            level =args [0 ]if args else 0.0 
            lr ,lg ,lb =0.2126 ,0.7152 ,0.0722 
            return [
            [lr *(1 -level )+level ,lg *(1 -level ),lb *(1 -level ),0 ,0 ],
            [lr *(1 -level ),lg *(1 -level )+level ,lb *(1 -level ),0 ,0 ],
            [lr *(1 -level ),lg *(1 -level ),lb *(1 -level )+level ,0 ,0 ],
            [0 ,0 ,0 ,1 ,0 ],
            ]
        if name in ("sepiamatrix","sepia"):
            return [[0.393 ,0.769 ,0.189 ,0 ,0 ],[0.349 ,0.686 ,0.168 ,0 ,0 ],
            [0.272 ,0.534 ,0.131 ,0 ,0 ],[0 ,0 ,0 ,1 ,0 ]]
        if name in ("tintmatrix","tint"):
            r =args [0 ]if len (args )>0 else 1.0 
            g =args [1 ]if len (args )>1 else 1.0 
            b =args [2 ]if len (args )>2 else 1.0 
            return [[r ,0 ,0 ,0 ,0 ],[0 ,g ,0 ,0 ,0 ],[0 ,0 ,b ,0 ,0 ],[0 ,0 ,0 ,1 ,0 ]]
        if name in ("brightnessmatrix","brightness"):
            v =args [0 ]if args else 0.0 
            return [[1 ,0 ,0 ,0 ,v ],[0 ,1 ,0 ,0 ,v ],[0 ,0 ,1 ,0 ,v ],[0 ,0 ,0 ,1 ,0 ]]
        if name in ("contrastmatrix","contrast"):
            v =args [0 ]if args else 1.0 
            off =0.5 *(1 -v )
            return [[v ,0 ,0 ,0 ,off ],[0 ,v ,0 ,0 ,off ],[0 ,0 ,v ,0 ,off ],[0 ,0 ,0 ,1 ,0 ]]
        if name in ("opacitymatrix","opacity"):
            v =args [0 ]if args else 1.0 
            return [[1 ,0 ,0 ,0 ,0 ],[0 ,1 ,0 ,0 ,0 ],[0 ,0 ,1 ,0 ,0 ],[0 ,0 ,0 ,v ,0 ]]
        if name in ("huematrix","hue"):
            import math 
            deg =args [0 ]if args else 0.0 
            rad =math .radians (deg )
            cosv ,sinv =math .cos (rad ),math .sin (rad )
            lr ,lg ,lb =0.2126 ,0.7152 ,0.0722 
            row0 =[lr +cosv *(1 -lr )-sinv *lr ,lg -cosv *lg -sinv *lg ,lb -cosv *lb +sinv *(1 -lb ),0 ,0 ]
            row1 =[lr -cosv *lr +sinv *0.143 ,lg +cosv *(1 -lg )+sinv *0.14 ,lb -cosv *lb -sinv *0.283 ,0 ,0 ]
            row2 =[lr -cosv *lr -sinv *(1 -lr ),lg -cosv *lg +sinv *lg ,lb +cosv *(1 -lb )+sinv *lb ,0 ,0 ]
            return [row0 ,row1 ,row2 ,[0 ,0 ,0 ,1 ,0 ]]
        return None 

    _BLEND_COMPOSITION ={
    "normal":QPainter .CompositionMode .CompositionMode_SourceOver ,
    "add":QPainter .CompositionMode .CompositionMode_Plus ,
    "multiply":QPainter .CompositionMode .CompositionMode_Multiply ,
    "min":QPainter .CompositionMode .CompositionMode_Darken ,
    "max":QPainter .CompositionMode .CompositionMode_Lighten ,
    "difference":QPainter .CompositionMode .CompositionMode_Difference ,
    }

    def _apply_blend (self ,pm :QPixmap ,el :ScreenElement )->QPixmap :

        raw =(el .properties .get ("blend")or "").strip ().strip ('"').strip ("'").lower ()
        mode =self ._BLEND_COMPOSITION .get (raw )
        if mode is None or mode ==QPainter .CompositionMode .CompositionMode_SourceOver :
            return pm 
        backdrop =QPixmap (pm .size ())
        backdrop .fill (QColor ("#1c1c24"))
        painter =QPainter (backdrop )
        painter .setCompositionMode (mode )
        painter .drawPixmap (0 ,0 ,pm )
        painter .end ()
        return backdrop 

    def _image_display_size (self ,el :ScreenElement ,native_w :int ,native_h :int )->tuple :

        w ,h =float (native_w ),float (native_h )
        xysize =el .properties .get ("xysize")
        if xysize :
            try :
                txt =xysize .strip ().strip ("()")
                xs ,ys =[p .strip ()for p in txt .split (",")]
                w ,h =float (xs ),float (ys )
            except Exception :
                pass 
        else :
            xsize ,ysize =el .properties .get ("xsize"),el .properties .get ("ysize")
            if xsize :
                try :
                    w =float (str (xsize ).strip ().strip ('"'))
                except (TypeError ,ValueError ):
                    pass 
            if ysize :
                try :
                    h =float (str (ysize ).strip ().strip ('"'))
                except (TypeError ,ValueError ):
                    pass 
        zoom =self ._prop_num (el ,"zoom",1.0 )
        xzoom =self ._prop_num (el ,"xzoom",zoom )
        yzoom =self ._prop_num (el ,"yzoom",zoom )
        w *=xzoom 
        h *=yzoom 
        disp_w =max (2 ,int (round (w *CANVAS_SCALE )))
        disp_h =max (2 ,int (round (h *CANVAS_SCALE )))


        disp_w =min (disp_w ,STAGE_W )
        disp_h =min (disp_h ,STAGE_H )
        return disp_w ,disp_h 

    def _processed_pixmap_for (self ,el :ScreenElement ,source_raw :str )->Optional [QPixmap ]:

        abs_path =self ._resolve_image_abs_path (source_raw )
        if not abs_path :
            return None 
        pm =QPixmap (abs_path )
        if pm .isNull ():
            return None 
        pm =self ._apply_crop (pm ,el )
        pm =self ._apply_rotate (pm ,el )
        target_w ,target_h =self ._image_display_size (el ,pm .width (),pm .height ())
        pm =pm .scaled (target_w ,target_h ,Qt .AspectRatioMode .IgnoreAspectRatio ,
        Qt .TransformationMode .SmoothTransformation )
        pm =self ._apply_matrixcolor (pm ,el )
        pm =self ._apply_blend (pm ,el )
        return pm 

    def _register (self ,widget :QWidget ,el :ScreenElement ):

        widget .setProperty ("screen_el_id",el .id )
        self ._element_widgets [el .id ]=widget 
        _install_click (widget ,lambda eid =el .id :self ._select_element (eid ))






    @staticmethod 
    def _split_pair_raw (raw :str )->Optional [list ]:
        txt =raw .strip ().strip ('"').strip ("'").strip ().strip ("()")
        parts =[p .strip ()for p in txt .split (",")]
        return parts if len (parts )==2 else None 

    @staticmethod 
    def _resolve_component (raw_token :str ,parent_dim_canvas :float )->Optional [float ]:

        token =raw_token .strip ().strip ('"').strip ("'")
        try :
            if "."in token :
                return float (token )*parent_dim_canvas 
            return float (int (token ))*CANVAS_SCALE 
        except (TypeError ,ValueError ):
            return None 

    def _resolve_pos (self ,el :ScreenElement ,container :QWidget ,widget :QWidget )->tuple :

        parent_w =max (1 ,container .width ())
        parent_h =max (1 ,container .height ())
        hint =widget .sizeHint ()




        ww =hint .width ()if hint .width ()>0 else max (widget .width (),1 )
        wh =hint .height ()if hint .height ()>0 else max (widget .height (),1 )

        x =y =None 
        xanchor_frac =yanchor_frac =0.0 

        pos =el .properties .get ("pos")
        if pos :
            pair =self ._split_pair_raw (pos )
            if pair :
                x =self ._resolve_component (pair [0 ],parent_w )
                y =self ._resolve_component (pair [1 ],parent_h )
        if x is None :
            xpos =el .properties .get ("xpos")
            if xpos :
                x =self ._resolve_component (xpos ,parent_w )
        if y is None :
            ypos =el .properties .get ("ypos")
            if ypos :
                y =self ._resolve_component (ypos ,parent_h )

        xcenter =el .properties .get ("xcenter")
        if xcenter and x is None :
            x =self ._resolve_component (xcenter ,parent_w )
            xanchor_frac =0.5 
        ycenter =el .properties .get ("ycenter")
        if ycenter and y is None :
            y =self ._resolve_component (ycenter ,parent_h )
            yanchor_frac =0.5 

        xalign =el .properties .get ("xalign")
        if xalign and x is None :
            try :
                f =float (xalign .strip ().strip ('"'))
                x =f *parent_w 
                xanchor_frac =f 
            except (TypeError ,ValueError ):
                pass 
        yalign =el .properties .get ("yalign")
        if yalign and y is None :
            try :
                f =float (yalign .strip ().strip ('"'))
                y =f *parent_h 
                yanchor_frac =f 
            except (TypeError ,ValueError ):
                pass 

        if x is None and y is None :
            return el .canvas_x ,el .canvas_y 
        if x is None :
            x =el .canvas_x 
        if y is None :
            y =el .canvas_y 

        anchor =el .properties .get ("anchor")
        if anchor :
            pair =self ._split_pair_raw (anchor )
            if pair :
                try :
                    xanchor_frac =float (pair [0 ])
                    yanchor_frac =float (pair [1 ])
                except (TypeError ,ValueError ):
                    pass 
        xanchor =el .properties .get ("xanchor")
        if xanchor :
            try :
                xanchor_frac =float (xanchor .strip ().strip ('"'))
            except (TypeError ,ValueError ):
                pass 
        yanchor =el .properties .get ("yanchor")
        if yanchor :
            try :
                yanchor_frac =float (yanchor .strip ().strip ('"'))
            except (TypeError ,ValueError ):
                pass 

        x -=xanchor_frac *ww 
        y -=yanchor_frac *wh 

        xoffset =el .properties .get ("xoffset")
        if xoffset :
            try :
                x +=float (xoffset .strip ().strip ('"'))*CANVAS_SCALE 
            except (TypeError ,ValueError ):
                pass 
        yoffset =el .properties .get ("yoffset")
        if yoffset :
            try :
                y +=float (yoffset .strip ().strip ('"'))*CANVAS_SCALE 
            except (TypeError ,ValueError ):
                pass 

        return int (round (x )),int (round (y ))

    def _make_guides (self ,container :QFrame ):
        v =QFrame (container )
        v .setStyleSheet ("background: #ff8c3d;")
        v .setFixedWidth (1 )
        v .hide ()
        h =QFrame (container )
        h .setStyleSheet ("background: #ff8c3d;")
        h .setFixedHeight (1 )
        h .hide ()
        container ._guide_v =v 
        container ._guide_h =h 

    def _update_guides (self ,container :QFrame ,gx ,gy ):
        v =getattr (container ,"_guide_v",None )
        h =getattr (container ,"_guide_h",None )
        if v is not None :
            if gx is not None :
                v .setGeometry (gx ,0 ,1 ,container .height ())
                v .show ()
                v .raise_ ()
            else :
                v .hide ()
        if h is not None :
            if gy is not None :
                h .setGeometry (0 ,gy ,container .width (),1 )
                h .show ()
                h .raise_ ()
            else :
                h .hide ()

    def _clear_guides (self ,container :QFrame ):
        self ._update_guides (container ,None ,None )

    def _compute_snap (self ,cw :QWidget ,pos :QPoint ,el :ScreenElement ,
    parent_el :ScreenElement ,container :QFrame ):
        best_x ,best_y =pos .x (),pos .y ()
        guide_x ,guide_y =None ,None 
        for sib in parent_el .children :
            if sib is el :
                continue 
            sw =self ._element_widgets .get (sib .id )
            if sw is None or sw is cw or sw .parent ()is not container :
                continue 

            for cand_x ,line_x in (
            (sw .x (),sw .x ()),
            (sw .x ()+sw .width ()//2 -cw .width ()//2 ,sw .x ()+sw .width ()//2 ),
            (sw .x ()+sw .width ()-cw .width (),sw .x ()+sw .width ()),
            ):
                if abs (cand_x -pos .x ())<=SNAP_THRESHOLD :
                    best_x ,guide_x =cand_x ,line_x 

            for cand_y ,line_y in (
            (sw .y (),sw .y ()),
            (sw .y ()+sw .height ()//2 -cw .height ()//2 ,sw .y ()+sw .height ()//2 ),
            (sw .y ()+sw .height ()-cw .height (),sw .y ()+sw .height ()),
            ):
                if abs (cand_y -pos .y ())<=SNAP_THRESHOLD :
                    best_y ,guide_y =cand_y ,line_y 

        if guide_x is None :
            grid_x =round (pos .x ()/GRID_STEP )*GRID_STEP 
            if abs (grid_x -pos .x ())<=SNAP_THRESHOLD :
                best_x =grid_x 
        if guide_y is None :
            grid_y =round (pos .y ()/GRID_STEP )*GRID_STEP 
            if abs (grid_y -pos .y ())<=SNAP_THRESHOLD :
                best_y =grid_y 
        return QPoint (best_x ,best_y ),guide_x ,guide_y 

    def _make_draggable (self ,cw :QWidget ,el :ScreenElement ,parent_el :ScreenElement ,container :QFrame ):

        cw .setCursor (Qt .CursorShape .OpenHandCursor )
        state ={"dragging":False ,"start_mouse":QPoint (),"start_pos":QPoint ()}

        def on_press (event ,cw =cw ,el =el ):
            if event .button ()!=Qt .MouseButton .LeftButton :
                return 
            self ._select_element (el .id )
            state ["dragging"]=False 
            state ["start_mouse"]=event .position ().toPoint ()
            state ["start_pos"]=cw .pos ()
            event .accept ()

        def on_move (event ,cw =cw ,el =el ,parent_el =parent_el ,container =container ):
            if not (event .buttons ()&Qt .MouseButton .LeftButton ):
                return 
            delta =event .position ().toPoint ()-state ["start_mouse"]
            if not state ["dragging"]and delta .manhattanLength ()<4 :
                return 
            state ["dragging"]=True 
            cw .setCursor (Qt .CursorShape .ClosedHandCursor )
            raw =state ["start_pos"]+delta 
            raw .setX (max (0 ,min (raw .x (),max (0 ,container .width ()-cw .width ()))))
            raw .setY (max (0 ,min (raw .y (),max (0 ,container .height ()-cw .height ()))))
            snapped ,gx ,gy =self ._compute_snap (cw ,raw ,el ,parent_el ,container )
            cw .move (snapped )
            self ._update_guides (container ,gx ,gy )
            event .accept ()

        def on_release (event ,cw =cw ,el =el ,container =container ):
            was_dragging =state ["dragging"]
            state ["dragging"]=False 
            cw .setCursor (Qt .CursorShape .OpenHandCursor )
            self ._clear_guides (container )
            if was_dragging :
                el .canvas_x ,el .canvas_y =cw .x (),cw .y ()
                el .properties ["pos"]=f"({cw .x ()}, {cw .y ()})"



                for k in ("xpos","ypos","xcenter","ycenter","xalign","yalign",
                "anchor","xanchor","yanchor","xoffset","yoffset"):
                    el .properties .pop (k ,None )
                if self .selected_id ==el .id :
                    self ._build_properties_panel ()
                self ._update_code_preview ()
            event .accept ()

        cw .mousePressEvent =on_press 
        cw .mouseMoveEvent =on_move 
        cw .mouseReleaseEvent =on_release 

    def _build_widget (self ,el :ScreenElement )->QWidget :
        spec =TAG_CATALOG [el .tag ]
        tag =el .tag 

        if tag in ("text","label"):
            w =QLabel (el .text or " ")
            w .setFont (self ._text_font (el ))
            base =f"color:{self ._prop_color (el ,'color','#e8e8ee')}; padding:2px;"
            w .setStyleSheet (self ._selected_style (el .id ,base ))
            w .setWordWrap (True )
            align_raw =(el .properties .get ("text_align")or "").strip ().strip ('"')
            try :
                af =float (align_raw )
                w .setAlignment (Qt .AlignmentFlag .AlignRight if af >=0.85 else 
                Qt .AlignmentFlag .AlignHCenter if af >=0.15 else 
                Qt .AlignmentFlag .AlignLeft )
            except (TypeError ,ValueError ):
                pass 
            self ._apply_size_constraints (w ,el )
            self ._register (w ,el )
            return w 

        if tag =="textbutton":
            w =QPushButton (el .text or "Button")
            w .setFont (self ._text_font (el ))
            color =self ._prop_color (el ,"text_color",self ._prop_color (el ,"color","#f1f1f4"))
            hover_color =el .properties .get ("hover_color")
            hover_css =f"QPushButton:hover {{ color:{hover_color .strip ().strip (chr (34 ))}; }}"if hover_color else ""
            base =(f"QPushButton {{ background:#2a2a34; color:{color }; "
            f"border:1px solid #45454f; padding:5px 10px; border-radius:4px; }} {hover_css }")
            w .setStyleSheet (self ._selected_style (el .id ,base ))
            self ._apply_size_constraints (w ,el )
            self ._register (w ,el )
            return w 

        if tag =="imagebutton":
            w =QLabel ()
            pm =self ._processed_pixmap_for (el ,el .properties .get ("idle",""))
            if pm is not None :
                w .setPixmap (pm )
                w .setFixedSize (pm .size ())
                w .setStyleSheet (self ._selected_style (el .id ,"border:1px solid #556;"))
            else :
                w .setText ("🖼 imagebutton\n(idle не найден)")
                w .setStyleSheet (self ._selected_style (
                el .id ,"background:#232330; color:#9fd6ff; border:1px dashed #556; padding:8px;"))
            self ._register (w ,el )
            return w 

        if tag in ("image","add"):
            w =QLabel ()
            pm =self ._processed_pixmap_for (el ,el .source )
            if pm is not None :
                w .setPixmap (pm )
                w .setFixedSize (pm .size ())
                w .setStyleSheet (self ._selected_style (el .id ,"border:1px solid #444;"))
            else :
                w .setText (f"🖼 {el .source or tag }")
                w .setStyleSheet (self ._selected_style (
                el .id ,"background:#1a1a21; color:#a8a8b3; border:1px dashed #444; padding:10px;"))
            self ._register (w ,el )
            return w 

        if tag in ("bar","vbar"):
            w =QProgressBar ()
            w .setTextVisible (False )
            rng =max (1 ,int (self ._prop_num (el ,"range",100 )))
            val =self ._prop_num (el ,"value",rng /2 )
            w .setMaximum (rng )
            w .setValue (max (0 ,min (rng ,int (val ))))
            w .setFixedHeight (14 if tag =="bar"else 80 )
            if tag =="vbar":
                w .setOrientation (Qt .Orientation .Vertical )
            left_bar =el .properties .get ("left_bar")or el .properties .get ("top_bar")
            right_bar =el .properties .get ("right_bar")or el .properties .get ("bottom_bar")
            chunk_color ="#7fb8ff"
            if left_bar :
                cand =left_bar .strip ().strip ('"')
                if QColor .isValidColorName (cand )or (cand .startswith ("#")and len (cand )in (4 ,7 ,9 )):
                    chunk_color =cand 
            groove_color ="#2a2a34"
            if right_bar :
                cand =right_bar .strip ().strip ('"')
                if QColor .isValidColorName (cand )or (cand .startswith ("#")and len (cand )in (4 ,7 ,9 )):
                    groove_color =cand 
            w .setStyleSheet (self ._selected_style (
            el .id ,f"QProgressBar {{ background:{groove_color }; border:1px solid #444; }} "
            f"QProgressBar::chunk {{ background:{chunk_color }; }}"))
            self ._apply_size_constraints (w ,el )
            self ._register (w ,el )
            return w 

        if tag =="input":
            w =QLineEdit (el .properties .get ("default","").strip ('"'))
            length =el .properties .get ("length")
            if length :
                try :
                    w .setMaxLength (int (_num (length )))
                except (TypeError ,ValueError ):
                    pass 
            w .setFont (self ._text_font (el ))
            w .setStyleSheet (self ._selected_style (
            el .id ,f"color:{self ._prop_color (el ,'color','#f1f1f4')};"))
            self ._apply_size_constraints (w ,el )
            self ._register (w ,el )
            return w 

        if tag =="null":
            w =QFrame ()
            w .setFixedSize (int (_num (el .properties .get ("width","10"))),int (_num (el .properties .get ("height","10"))))
            w .setStyleSheet (self ._selected_style (el .id ,"background:transparent; border:1px dotted #444;"))
            self ._register (w ,el )
            return w 

        if tag in ("key","on"):

            label =f"⌨ key {el .key_name }"if tag =="key"else f"⚡ on {el .on_event }"
            w =QLabel (label )
            w .setStyleSheet (self ._selected_style (el .id ,"color:#75757f; font-style: italic; padding:2px;"))
            self ._register (w ,el )
            return w 

        if tag =="timer":
            w =QLabel (f"⏱ timer {el .timer_seconds }s")
            w .setStyleSheet (self ._selected_style (el .id ,"color:#75757f; font-style: italic; padding:2px;"))
            self ._register (w ,el )
            return w 

        if tag =="has":
            w =QLabel ("has …")
            w .setStyleSheet (self ._selected_style (el .id ,"color:#75757f; font-style: italic;"))
            self ._register (w ,el )
            return w 

        if tag =="use":
            w =QLabel (f"↪ use {el .use_target }")
            w .setStyleSheet (self ._selected_style (
            el .id ,"background:#20202a; color:#c9a8ff; border:1px dashed #665; padding:6px;"))
            self ._register (w ,el )
            return w 

        if tag in ("if","elif","else","for"):
            box =QFrame ()
            box .setStyleSheet (self ._selected_style (
            el .id ,"QFrame { border:1px dashed #6fd68f; border-radius:4px; margin-top:4px; }"))
            lay =QVBoxLayout (box )
            lay .setContentsMargins (6 ,14 ,6 ,6 )
            if tag =="for":
                cap =f"for {el .loop_expr }:"
            elif tag =="else":
                cap ="else:"
            else :
                cap =f"{tag } {el .condition }:"
            cap_lbl =QLabel (cap ,box )
            cap_lbl .setStyleSheet ("color:#6fd68f; background:transparent; font-family: Consolas; padding:0 4px;")
            cap_lbl .move (4 ,-2 )
            for c in el .children :
                lay .addWidget (self ._build_widget (c ))
            self ._register (box ,el )
            return box 

        if tag =="mousearea":
            box =self ._container_frame (el ,QVBoxLayout ,"#ff8080")
            return box 

        if tag =="grid":
            box =_BackgroundFrame ()
            box .setStyleSheet (self ._selected_style (el .id ,"QFrame { border:1px solid #3a3a46; }"))
            self ._apply_container_background (box ,el )
            self ._apply_size_constraints (box ,el )
            grid =QGridLayout (box )
            grid .setContentsMargins (*self ._prop_margins (el ))
            grid .setSpacing (self ._prop_int (el ,"spacing",6 ))
            cols =max (1 ,int (_num (el .properties .get ("cols","2"))))
            for i ,c in enumerate (el .children ):
                grid .addWidget (self ._build_widget (c ),i //cols ,i %cols )
            self ._register (box ,el )
            return box 

        if tag =="hbox"or tag =="side":
            return self ._container_frame (el ,QHBoxLayout ,"#3a3a46")

        if tag =="vbox":
            return self ._container_frame (el ,QVBoxLayout ,"#3a3a46")

        if tag =="viewport":
            inner =self ._container_frame (el ,QVBoxLayout ,"#3a3a46")
            scroll =QScrollArea ()
            scroll .setWidgetResizable (True )
            scroll .setMaximumHeight (160 )
            scroll .setWidget (inner )
            scroll .setProperty ("screen_el_id",el .id )
            self ._element_widgets [el .id ]=scroll 
            return scroll 

        if tag =="button":
            box =self ._container_frame (el ,QVBoxLayout ,"#4a6a8a")
            return box 

        if tag in ("fixed","imagemap","draggroup","drag"):
            box =_BackgroundFrame ()





            box .resize (STAGE_W ,STAGE_H )
            box .setMinimumSize (200 ,120 )
            box .setStyleSheet (self ._selected_style (el .id ,"QFrame { border:1px solid #55555f; background:#17171e; }"))
            self ._apply_container_background (box ,el )
            self ._apply_size_constraints (box ,el )
            for c in el .children :
                cw =self ._build_widget (c )
                cw .setParent (box )
                x ,y =self ._resolve_pos (c ,box ,cw )
                c .canvas_x ,c .canvas_y =x ,y 
                cw .move (x ,y )
                cw .show ()
                self ._make_draggable (cw ,c ,el ,box )
            self ._make_guides (box )
            self ._register (box ,el )
            return box 


        return self ._container_frame (el ,QVBoxLayout ,"#3a3a46")

    def _container_frame (self ,el :ScreenElement ,layout_cls ,border_color :str )->QFrame :
        box =_BackgroundFrame ()
        box .setStyleSheet (self ._selected_style (
        el .id ,f"QFrame {{ border:1px solid {border_color }; border-radius:3px; }}"))
        self ._apply_container_background (box ,el )
        self ._apply_size_constraints (box ,el )
        lay =layout_cls (box )
        lay .setContentsMargins (*self ._prop_margins (el ))
        lay .setSpacing (self ._prop_int (el ,"spacing",6 ))
        orientation ="v"if layout_cls is QVBoxLayout else "h"
        for c in el .children :
            cw =self ._build_widget (c )
            flag =self ._align_flag_for (c ,orientation )
            if flag is not None :
                lay .addWidget (cw ,0 ,flag )
            else :
                lay .addWidget (cw )
        self ._register (box ,el )
        return box 

    def _apply_size_constraints (self ,widget :QWidget ,el :ScreenElement )->None :

        def px (key :str )->Optional [int ]:
            raw =el .properties .get (key )
            if not raw :
                return None 
            try :
                return max (0 ,int (round (float (raw .strip ().strip ('"'))*CANVAS_SCALE )))
            except (TypeError ,ValueError ):
                return None 

        xysize =self ._parse_tuple (el .properties .get ("xysize",""),2 )
        if xysize :
            w =max (1 ,int (round (xysize [0 ]*CANVAS_SCALE )))
            h =max (1 ,int (round (xysize [1 ]*CANVAS_SCALE )))
            widget .setFixedSize (w ,h )
            return 
        xsize ,ysize =px ("xsize"),px ("ysize")
        if xsize is not None or ysize is not None :
            if xsize is not None :
                widget .setFixedWidth (xsize )
            if ysize is not None :
                widget .setFixedHeight (ysize )
        xmin ,ymin =px ("xminimum"),px ("yminimum")
        if xmin is not None or ymin is not None :
            widget .setMinimumSize (xmin or widget .minimumWidth (),ymin or widget .minimumHeight ())
        xmax ,ymax =px ("xmaximum"),px ("ymaximum")
        if xmax is not None or ymax is not None :
            widget .setMaximumSize (xmax or widget .maximumWidth (),ymax or widget .maximumHeight ())

    def _apply_container_background (self ,box :"_BackgroundFrame",el :ScreenElement )->None :

        raw =el .properties .get ("background")
        if not raw :
            return 
        candidate =raw .strip ().strip ('"').strip ("'")
        abs_path =self ._resolve_image_abs_path (raw )
        if abs_path :
            pm =QPixmap (abs_path )
            if not pm .isNull ():
                box .bg_pixmap =pm 
                box .bg_tile =str (el .properties .get ("tile","")).strip ().strip ('"')=="True"
            return 
        if QColor .isValidColorName (candidate )or (candidate .startswith ("#")and len (candidate )in (4 ,7 ,9 )):
            style =box .styleSheet ()
            box .setStyleSheet (style +f" QFrame {{ background-color: {candidate }; }}")

    @staticmethod 
    def _prop_num (el :ScreenElement ,key :str ,default :float )->float :
        v =el .properties .get (key )
        if v is None :
            return default 
        try :
            return float (str (v ).strip ().strip ('"'))
        except (TypeError ,ValueError ):
            return default 

    @classmethod 
    def _prop_int (cls ,el :ScreenElement ,key :str ,default :int )->int :
        return int (cls ._prop_num (el ,key ,default ))

    @staticmethod 
    def _prop_color (el :ScreenElement ,key :str ,default :str )->str :

        v =el .properties .get (key )
        if not v :
            return default 
        c =v .strip ().strip ('"').strip ("'")
        if QColor .isValidColorName (c )or (c .startswith ("#")and len (c )in (4 ,7 ,9 )):
            return c 
        return default 

    def _text_font (self ,el :ScreenElement )->QFont :
        f =QFont ()
        size =el .properties .get ("size")or el .properties .get ("text_size")
        if size :
            try :
                f .setPointSize (max (6 ,int (_num (size ))//2 ))
            except (TypeError ,ValueError ):
                f .setPointSize (11 )
        else :
            f .setPointSize (11 )
        if str (el .properties .get ("bold","")or el .properties .get ("text_bold","")).strip ().strip ('"')=="True":
            f .setBold (True )
        if str (el .properties .get ("italic","")or el .properties .get ("text_italic","")).strip ().strip ('"')=="True":
            f .setItalic (True )
        if str (el .properties .get ("underline","")).strip ().strip ('"')=="True":
            f .setUnderline (True )
        if str (el .properties .get ("strikethrough","")).strip ().strip ('"')=="True":
            f .setStrikeOut (True )
        font_prop =el .properties .get ("font")or el .properties .get ("text_font")
        if font_prop :
            fam =font_prop .strip ().strip ('"').strip ("'")
            fam =os .path .splitext (os .path .basename (fam ))[0 ]or fam 
            f .setFamily (fam )
        return f 

    @staticmethod 
    def _prop_margins (el :ScreenElement )->tuple :

        padding =el .properties .get ("padding")
        if padding :
            try :
                txt =padding .strip ().strip ("()")
                parts =[p .strip ()for p in txt .split (",")]
                if len (parts )==1 :
                    p =int (float (parts [0 ]))
                    return (p ,p ,p ,p )
                if len (parts )>=2 :
                    px ,py =int (float (parts [0 ])),int (float (parts [1 ]))
                    return (px ,py ,px ,py )
            except Exception :
                pass 
        return (6 ,6 ,6 ,6 )

    @staticmethod 
    def _align_flag_for (el :ScreenElement ,orientation :str ):

        key ="xalign"if orientation =="v"else "yalign"
        val =el .properties .get (key )
        if val is None :
            return None 
        try :
            f =float (str (val ).strip ().strip ('"'))
        except (TypeError ,ValueError ):
            return None 
        if orientation =="v":
            if f <=0.15 :
                return Qt .AlignmentFlag .AlignLeft 
            if f >=0.85 :
                return Qt .AlignmentFlag .AlignRight 
            return Qt .AlignmentFlag .AlignHCenter 
        else :
            if f <=0.15 :
                return Qt .AlignmentFlag .AlignTop 
            if f >=0.85 :
                return Qt .AlignmentFlag .AlignBottom 
            return Qt .AlignmentFlag .AlignVCenter 

    def _highlight_selection (self ):



        for el_id ,w in self ._element_widgets .items ():
            style =w .styleSheet ()
            base =style .replace ("border: 2px solid #ff8c3d;","")
            if el_id ==self .selected_id :
                w .setStyleSheet (base +"border: 2px solid #ff8c3d;")
            else :
                w .setStyleSheet (base )

    def _render_tree (self ):
        self .layers_tree .clear ()

        def add_node (parent_item ,el :ScreenElement ):
            label =f"<{el .tag }>"
            if el .text :
                label +=f' "{el .text [:20 ]}"'
            item =QTreeWidgetItem ([label ])
            item .setData (0 ,Qt .ItemDataRole .UserRole ,el .id )
            if parent_item is None :
                self .layers_tree .addTopLevelItem (item )
            else :
                parent_item .addChild (item )
            for c in el .children :
                add_node (item ,c )
            return item 

        root_item =QTreeWidgetItem ([f"screen {self .current .name }"])
        root_item .setData (0 ,Qt .ItemDataRole .UserRole ,None )
        self .layers_tree .addTopLevelItem (root_item )
        for c in self .current .root .children :
            add_node (root_item ,c )
        self .layers_tree .expandAll ()

    def _sync_tree_selection (self ):
        def walk (item :QTreeWidgetItem ):
            if item .data (0 ,Qt .ItemDataRole .UserRole )==self .selected_id :
                self .layers_tree .setCurrentItem (item )
                return True 
            for i in range (item .childCount ()):
                if walk (item .child (i )):
                    return True 
            return False 
        for i in range (self .layers_tree .topLevelItemCount ()):
            walk (self .layers_tree .topLevelItem (i ))




    def _clear_form (self ):
        while self .props_layout .rowCount ():
            self .props_layout .removeRow (0 )

    def _build_properties_panel (self ):
        self ._clear_form ()
        if not self .selected_id :
            self .props_box .setTitle ("Свойства элемента - ничего не выбрано")
            lbl =QLabel ("Кликните на элемент на холсте или в дереве слева,\n"
            "либо добавьте новый элемент из палитры.")
            lbl .setWordWrap (True )
            self .props_layout .addRow (lbl )
            return 

        el =self .current .root .find (self .selected_id )
        if el is None :
            return 
        spec =TAG_CATALOG [el .tag ]
        self .props_box .setTitle (f"Свойства: <{el .tag }> - {spec .label }")

        if spec .has_text :
            e =QLineEdit (el .text )
            e .textChanged .connect (lambda v ,el =el :self ._set_and_refresh (el ,"text",v ))
            self .props_layout .addRow ("Текст",e )

        if spec .has_action or el .tag in ("key","on"):
            e =QLineEdit (el .action )
            e .setPlaceholderText ("напр. Start() / Return() / ShowMenu(\"save\")")
            e .textChanged .connect (lambda v ,el =el :self ._set_and_refresh (el ,"action",v ))
            self .props_layout .addRow ("action",e )

        if el .tag in ("image","add"):
            row =self ._image_pick_row (
            lambda el =el :el .source ,
            lambda v ,el =el :setattr (el ,"source",v ),
            '"menu/картинка.png"')
            self .props_layout .addRow ("источник",row )

        if el .tag =="imagebutton":
            idle_row =self ._image_pick_row (
            lambda el =el :el .properties .get ("idle",""),
            lambda v ,el =el :el .properties .__setitem__ ("idle",v ),
            '"menu/idle.png"')
            self .props_layout .addRow ("idle",idle_row )
            hover_row =self ._image_pick_row (
            lambda el =el :el .properties .get ("hover",""),
            lambda v ,el =el :el .properties .__setitem__ ("hover",v ),
            '"menu/hover.png"')
            self .props_layout .addRow ("hover",hover_row )

        if el .tag in ("if","elif"):
            e =QLineEdit (el .condition )
            e .textChanged .connect (lambda v ,el =el :self ._set_and_refresh (el ,"condition",v ))
            self .props_layout .addRow ("условие",e )

        if el .tag =="for":
            e =QLineEdit (el .loop_expr )
            e .textChanged .connect (lambda v ,el =el :self ._set_and_refresh (el ,"loop_expr",v ))
            self .props_layout .addRow ("цикл",e )

        if el .tag =="use":
            e =QLineEdit (el .use_target )
            e .textChanged .connect (lambda v ,el =el :self ._set_and_refresh (el ,"use_target",v ))
            self .props_layout .addRow ("целевой экран",e )

        if el .tag =="key":
            e =QLineEdit (el .key_name )
            e .setPlaceholderText ('"K_ESCAPE"')
            e .textChanged .connect (lambda v ,el =el :self ._set_and_refresh (el ,"key_name",v ))
            self .props_layout .addRow ("клавиша",e )

        if el .tag =="timer":
            e =QLineEdit (el .timer_seconds )
            e .textChanged .connect (lambda v ,el =el :self ._set_and_refresh (el ,"timer_seconds",v ))
            self .props_layout .addRow ("секунды",e )

        if el .tag =="on":
            e =QLineEdit (el .on_event )
            e .setPlaceholderText ('"show"')
            e .textChanged .connect (lambda v ,el =el :self ._set_and_refresh (el ,"on_event",v ))
            self .props_layout .addRow ("событие",e )

        known_fields =property_fields_for (el .tag )

        sep =QLabel (f"Свойства по документации Ren'Py ({el .tag }) - пусто = не используется")
        sep .setWordWrap (True )
        sep .setStyleSheet ("font-weight: 600; margin-top: 6px;")
        self .props_layout .addRow (sep )

        self ._known_rows_container =QVBoxLayout ()
        for key in known_fields :
            self ._add_known_property_row (el ,key )
        wrap_known =QWidget ()
        wrap_known .setLayout (self ._known_rows_container )
        self .props_layout .addRow (wrap_known )

        extra_keys =[k for k in el .properties .keys ()if k not in known_fields ]
        if extra_keys :
            sep2 =QLabel ("Прочие свойства (заданы вручную)")
            sep2 .setStyleSheet ("font-weight: 600; margin-top: 6px;")
            self .props_layout .addRow (sep2 )
            self ._prop_rows_container =QVBoxLayout ()
            for key in extra_keys :
                self ._add_property_row (el ,key )
            wrap =QWidget ()
            wrap .setLayout (self ._prop_rows_container )
            self .props_layout .addRow (wrap )
        else :
            self ._prop_rows_container =QVBoxLayout ()

        add_row =QHBoxLayout ()
        key_edit =QLineEdit ()
        key_edit .setPlaceholderText ("своё свойство (не из списка выше)")
        val_edit =QLineEdit ()
        val_edit .setPlaceholderText ("значение (0.5)")
        add_btn =QPushButton ("+")
        add_btn .setFixedWidth (28 )

        def add_prop ():
            k =key_edit .text ().strip ()
            v =val_edit .text ().strip ()
            if not k :
                return 
            el .properties [k ]=v 
            key_edit .clear ()
            val_edit .clear ()
            self ._build_properties_panel ()
            self ._rebuild_canvas_and_code ()

        add_btn .clicked .connect (add_prop )
        add_row .addWidget (key_edit )
        add_row .addWidget (val_edit )
        add_row .addWidget (add_btn )
        addw =QWidget ()
        addw .setLayout (add_row )
        self .props_layout .addRow (addw )

    def _add_known_property_row (self ,el :ScreenElement ,key :str ):

        row =QHBoxLayout ()
        k_lbl =QLabel (key )
        k_lbl .setFixedWidth (110 )
        k_lbl .setStyleSheet ("color:#9a9aa5;")
        v_edit =QLineEdit (el .properties .get (key ,""))
        v_edit .setPlaceholderText ("не используется")

        def on_change (v ,el =el ,key =key ):
            v =v .strip ()
            if v :
                el .properties [key ]=v 
            else :
                el .properties .pop (key ,None )
            self ._rebuild_canvas_and_code ()

        v_edit .textChanged .connect (on_change )
        row .addWidget (k_lbl )
        row .addWidget (v_edit )
        wrap =QWidget ()
        wrap .setLayout (row )
        self ._known_rows_container .addWidget (wrap )

    def _add_property_row (self ,el :ScreenElement ,key :str ):
        row =QHBoxLayout ()
        k_lbl =QLabel (key )
        k_lbl .setFixedWidth (90 )
        v_edit =QLineEdit (el .properties .get (key ,""))
        v_edit .textChanged .connect (lambda v ,el =el ,key =key :self ._set_prop_and_refresh (el ,key ,v ))
        rm_btn =QPushButton ("✕")
        rm_btn .setFixedWidth (24 )

        def remove ():
            el .properties .pop (key ,None )
            self ._build_properties_panel ()
            self ._rebuild_canvas_and_code ()

        rm_btn .clicked .connect (remove )
        row .addWidget (k_lbl )
        row .addWidget (v_edit )
        row .addWidget (rm_btn )
        wrap =QWidget ()
        wrap .setLayout (row )
        self ._prop_rows_container .addWidget (wrap )

    def _set_prop_and_refresh (self ,el :ScreenElement ,key :str ,value :str ):
        el .properties [key ]=value 
        self ._rebuild_canvas_and_code ()

    def _set_and_refresh (self ,el :ScreenElement ,attr :str ,value :str ):
        setattr (el ,attr ,value )
        self ._rebuild_canvas_and_code ()

    def _rebuild_canvas_and_code (self ):
        self ._render_canvas ()
        self ._render_tree ()
        self ._sync_tree_selection ()
        self ._update_code_preview ()




    def _update_code_preview (self ):
        try :
            code =generate_screen (self .current )
        except Exception as exc :
            code =f"# ошибка генерации кода: {exc }"
        self .code_view .setPlainText (code )

    def _export_rpy (self ):
        path ,_ =QFileDialog .getSaveFileName (
        self ,"Экспорт экранов","screens.rpy","Ren'Py script (*.rpy)")
        if not path :
            return 
        code =generate_document (self .document )
        try :
            with open (path ,"w",encoding ="utf-8")as f :
                f .write (code +"\n")
        except OSError as exc :
            QMessageBox .critical (self ,"Ошибка экспорта",str (exc ))
            return 
        if self ._on_export :
            try :
                self ._on_export (path ,self .document )
            except Exception :
                pass 
        QMessageBox .information (self ,"Экспорт",f"Экраны сохранены в:\n{path }")

    def _maybe_close (self ):
        self .close ()


def _num (s :str )->float :
    try :
        return float (str (s ).strip ().strip ('"'))
    except (TypeError ,ValueError ):
        return 0.0 


def _has_tr (key :str )->bool :
    try :
        from core .i18n import tr as _tr 
        val =_tr (key )
        return bool (val )and val !=key 
    except Exception :
        return False 
