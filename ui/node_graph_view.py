
import json 
from typing import Optional ,List 
from PyQt6 .QtWidgets import (
QWidget ,QVBoxLayout ,QHBoxLayout ,QGraphicsView ,QGraphicsScene ,
QGraphicsObject ,QGraphicsItem ,QGraphicsPathItem ,QLineEdit ,QPushButton ,
QMenu ,QColorDialog ,QInputDialog ,QLabel ,QToolButton ,QGraphicsRectItem ,
QSplitter ,QScrollArea ,QPlainTextEdit ,QFormLayout ,QFrame ,
QComboBox ,QCheckBox ,QDoubleSpinBox 
)
from PyQt6 .QtCore import (
Qt ,QRectF ,QPointF ,pyqtSignal ,QSizeF ,QPropertyAnimation ,QEasingCurve ,pyqtProperty ,QTimer 
)
from PyQt6 .QtGui import (
QPainter ,QPen ,QBrush ,QColor ,QFont ,QPainterPath ,QWheelEvent ,
QMouseEvent ,QLinearGradient ,QPolygonF ,QKeySequence ,QPixmap ,QKeyEvent ,
QPainterPathStroker 
)

from core .models import Scene ,SceneNode ,NodeType ,NodeGroup 
from core .i18n import tr 
from ui .theme import theme_manager ,qcolor 
from ui .pixmap_cache import get_pixmap 
from ui .resource_carousel import ResourceCarousel ,FolderResourceCarousel ,CharacterGroupPicker 
from core .renpy_text_tags import strip_tags 
from ui .audio_preview import get_player as get_audio_player 

NODE_W =280 
NODE_H =150 
HEADER_H =26 
GAP_Y =34 
GROUP_HEADER_H =26 
GROUP_PAD =14 
LEFT_X =40 
PORT_R =6.0 
SNAP_RADIUS =46.0 

DEFAULT_COLORS =["#ff5b3d","#ff8c3d","#ffd23f","#4cd97b","#3fb6ff","#a78bfa","#ff6fb0","#8a8a94"]


def _clip (text :str ,n :int )->str :
    text =text .replace ("\n"," ")
    return text [:n ]+("…"if len (text )>n else "")


_TYPE_ICON ={
NodeType .DIALOGUE :"💬",NodeType .NARRATION :"📖",NodeType .SHOW_BG :"🖼",
NodeType .SCENE :"🖼",NodeType .SHOW_SPRITE :"🧍",NodeType .HIDE_SPRITE :"🧍",
NodeType .SHOW_CG :"🎴",NodeType .HIDE_CG :"🎴",NodeType .PLAY_MUSIC :"🎵",
NodeType .STOP_MUSIC :"🎵",NodeType .PLAY_SOUND :"🔊",NodeType .PLAY_AMBIENCE :"🌫",
NodeType .STOP_AMBIENCE :"🌫",NodeType .LABEL :"🏷",NodeType .JUMP :"↪",
NodeType .MENU :"❓",NodeType .PYTHON :"🐍",NodeType .PAUSE :"⏸",
NodeType .RETURN :"⏎",NodeType .COMMENT :"💭",NodeType .WINDOW :"🪟",
NodeType .WITH_TRANSITION :"✨",NodeType .NVL_MODE :"📜",NodeType .RAW :"⌨",
NodeType .CUSTOM :"🧬",
}


_ADD_NODE_TYPES =[
NodeType .DIALOGUE ,NodeType .NARRATION ,NodeType .LABEL ,NodeType .JUMP ,NodeType .MENU ,
NodeType .SHOW_BG ,NodeType .SCENE ,NodeType .SHOW_SPRITE ,NodeType .HIDE_SPRITE ,
NodeType .SHOW_CG ,NodeType .HIDE_CG ,NodeType .PLAY_MUSIC ,NodeType .STOP_MUSIC ,
NodeType .PLAY_SOUND ,NodeType .PLAY_AMBIENCE ,NodeType .STOP_AMBIENCE ,
NodeType .PYTHON ,NodeType .PAUSE ,NodeType .RETURN ,NodeType .COMMENT ,
NodeType .WINDOW ,NodeType .WITH_TRANSITION ,
]


def _node_header (node :SceneNode )->str :

    icon =_TYPE_ICON .get (node .node_type ,"•")
    label =node .node_type .value .upper ()
    ref =""
    if node .node_type ==NodeType .LABEL :
        ref =node .label_name or "?"
    elif node .node_type ==NodeType .JUMP :
        ref =f"→ {node .jump_target or '?'}"
    elif node .node_type in (NodeType .SHOW_BG ,NodeType .SCENE ):
        ref =node .bg_var or "?"
    elif node .node_type in (NodeType .SHOW_SPRITE ,NodeType .HIDE_SPRITE ):
        ref =node .sprite_var or node .sprite_tag or "?"
    elif node .node_type in (NodeType .SHOW_CG ,NodeType .HIDE_CG ):
        ref =node .cg_var or "?"
    elif node .node_type in (NodeType .PLAY_MUSIC ,NodeType .STOP_MUSIC ):
        ref =node .music_var or ""
    elif node .node_type ==NodeType .PLAY_SOUND :
        ref =node .sound_var or "?"
    elif node .node_type in (NodeType .PLAY_AMBIENCE ,NodeType .STOP_AMBIENCE ):
        ref =node .ambience_var or ""
    elif node .node_type ==NodeType .DIALOGUE :
        ref =node .character_var or "?"
    elif node .node_type ==NodeType .MENU :
        ref =f"{max (1 ,len (node .menu_choices ))} choices"
    return f"{icon } {label }"+(f"  {ref }"if ref else "")


def _node_image_var (node :SceneNode )->Optional [str ]:

    if node .node_type in (NodeType .SHOW_BG ,NodeType .SCENE ):
        return node .bg_var 
    if node .node_type ==NodeType .SHOW_SPRITE :
        return node .sprite_var 
    if node .node_type ==NodeType .SHOW_CG :
        return node .cg_var 
    return None 


def _node_body_text (node :SceneNode )->str :

    if node .node_type ==NodeType .DIALOGUE :
        return node .text or ""
    if node .node_type ==NodeType .NARRATION :
        return node .text or ""
    if node .node_type ==NodeType .MENU :
        lines =[node .menu_prompt or ""]
        for ch in node .normalized_menu_choices ():
            lines .append (f"• {ch [0 ]}")
        return "\n".join (lines )
    if node .node_type ==NodeType .PYTHON :
        return node .python_code or ""
    if node .node_type ==NodeType .RAW :
        return node .python_code or ""
    if node .node_type ==NodeType .COMMENT :
        return node .comment_text or ""
    return ""


class NodeBoxItem (QGraphicsObject ):
    clicked =pyqtSignal (int )
    context_requested =pyqtSignal (int ,object )
    moved =pyqtSignal (int ,QPointF )
    port_press =pyqtSignal (int ,int ,QPointF )
    double_clicked =pyqtSignal (int )

    def __init__ (self ,row :int ,node :SceneNode ,is_current :bool =False ,matched :bool =False ,rm =None ):
        super ().__init__ ()
        self .row =row 
        self .node =node 
        self .is_current =is_current 
        self .matched =matched 
        self .rm =rm 
        self ._snap_highlight =False 
        self .setAcceptHoverEvents (True )
        self ._hover =False 
        self ._pulse =0.0 
        self ._pulse_anim =QPropertyAnimation (self ,b"pulse",self )
        self ._pulse_anim .setDuration (320 )
        self ._pulse_anim .setStartValue (1.0 )
        self ._pulse_anim .setEndValue (0.0 )
        self ._pulse_anim .setEasingCurve (QEasingCurve .Type .OutCubic )
        self .setFlag (QGraphicsItem .GraphicsItemFlag .ItemIsSelectable ,True )
        self .setFlag (QGraphicsItem .GraphicsItemFlag .ItemIsFocusable ,True )
        self .setFlag (QGraphicsItem .GraphicsItemFlag .ItemIsMovable ,True )
        self .setFlag (QGraphicsItem .GraphicsItemFlag .ItemSendsGeometryChanges ,True )
        self .setZValue (10 )
        self .setCacheMode (QGraphicsItem .CacheMode .DeviceCoordinateCache )
        self ._cached_pixmap =self ._resolve_preview_pixmap ()

    def itemChange (self ,change ,value ):
        if change ==QGraphicsItem .GraphicsItemChange .ItemPositionHasChanged :
            self .moved .emit (self .row ,value )
        return super ().itemChange (change ,value )

    def ports (self )->List [QPointF ]:

        if self .node .node_type ==NodeType .JUMP :
            return [QPointF (NODE_W /2 ,NODE_H )]
        if self .node .node_type ==NodeType .MENU :
            n =max (1 ,len (self .node .menu_choices ))
            margin =26.0 
            usable =NODE_W -margin *2 
            pts =[]
            for i in range (n ):
                x =margin +(usable *(i +0.5 )/n )if n >1 else NODE_W /2 
                pts .append (QPointF (x ,NODE_H ))
            return pts 
        return []

    def _get_pulse (self ):
        return self ._pulse 

    def _set_pulse (self ,value ):
        self ._pulse =value 
        self .update ()

    pulse =pyqtProperty (float ,_get_pulse ,_set_pulse )

    def play_click_pulse (self ):

        self ._pulse_anim .stop ()
        self ._pulse_anim .start ()

    def boundingRect (self )->QRectF :
        return QRectF (0 ,0 ,NODE_W ,NODE_H )

    def paint (self ,painter :QPainter ,option ,widget =None ):
        painter .setRenderHint (QPainter .RenderHint .Antialiasing )
        rect =self .boundingRect ()
        t =theme_manager .tokens ()

        base =QColor (t .button_bg ).lighter (115 )if not self ._hover else QColor (t .button_bg ).lighter (130 )
        painter .setBrush (QBrush (base ))
        border_color =QColor (t .accent_1 )if self .isSelected ()else qcolor (t .glass_border )
        pen =QPen (border_color ,2.4 if self .isSelected ()else 1.2 )
        painter .setPen (pen )
        painter .drawRoundedRect (rect .adjusted (1 ,1 ,-1 ,-1 ),10 ,10 )

        if self .node .color_tag :
            painter .setPen (Qt .PenStyle .NoPen )
            painter .setBrush (QBrush (QColor (self .node .color_tag )))
            painter .drawRoundedRect (QRectF (0 ,0 ,6 ,NODE_H ),3 ,3 )


        header_rect =QRectF (1 ,1 ,NODE_W -2 ,HEADER_H )
        head_bg =QColor (t .accent_1 if self .node .node_type ==NodeType .LABEL else t .button_bg )
        head_bg =head_bg .darker (112 )if self .node .node_type !=NodeType .LABEL else head_bg 
        head_bg .setAlpha (95 if self .node .node_type ==NodeType .LABEL else 60 )
        painter .setPen (Qt .PenStyle .NoPen )
        painter .setBrush (QBrush (head_bg ))
        painter .drawRoundedRect (header_rect ,9 ,9 )
        painter .drawRect (QRectF (header_rect .x (),header_rect .y ()+9 ,header_rect .width (),9 ))

        painter .setPen (QColor (t .text ))
        f =QFont ()
        f .setPointSize (8 )
        f .setBold (True )
        painter .setFont (f )
        painter .drawText (header_rect .adjusted (10 ,0 ,-8 ,0 ),
        Qt .AlignmentFlag .AlignLeft |Qt .AlignmentFlag .AlignVCenter ,
        _clip (_node_header (self .node ),36 ))


        body_rect =QRectF (8 ,HEADER_H +8 ,NODE_W -16 ,NODE_H -HEADER_H -16 )
        pix =self ._cached_pixmap 
        if pix is not None and not pix .isNull ():
            painter .setPen (QPen (qcolor (t .glass_border ),1 ))
            painter .setBrush (QBrush (QColor (0 ,0 ,0 ,40 )))
            painter .drawRoundedRect (body_rect ,6 ,6 )
            scaled =pix .scaled (int (body_rect .width ()),int (body_rect .height ()),
            Qt .AspectRatioMode .KeepAspectRatio ,Qt .TransformationMode .SmoothTransformation )
            px =body_rect .x ()+(body_rect .width ()-scaled .width ())/2 
            py =body_rect .y ()+(body_rect .height ()-scaled .height ())/2 
            painter .drawPixmap (int (px ),int (py ),scaled )
        else :
            body_text =_node_body_text (self .node )
            painter .setPen (QPen (qcolor (t .glass_border ),1 ,Qt .PenStyle .DashLine ))
            painter .setBrush (QBrush (QColor (0 ,0 ,0 ,18 )))
            painter .drawRoundedRect (body_rect ,6 ,6 )
            painter .setPen (QColor (t .text_muted ))
            fb =QFont ()
            fb .setPointSize (8 )
            painter .setFont (fb )
            painter .drawText (body_rect .adjusted (8 ,6 ,-8 ,-6 ),
            Qt .AlignmentFlag .AlignLeft |Qt .AlignmentFlag .AlignTop |Qt .TextFlag .TextWordWrap ,
            _clip (body_text ,220 )if body_text else "-")


        ports =self .ports ()
        if ports :
            painter .setPen (QPen (QColor (t .accent_2 ),1.4 ))
            painter .setBrush (QBrush (QColor (t .accent_2 )))
            for pt in ports :
                painter .drawEllipse (pt ,PORT_R ,PORT_R )

        if self .is_current :
            painter .setPen (QPen (QColor (t .accent_2 ),2 ))
            painter .setBrush (Qt .BrushStyle .NoBrush )
            painter .drawRoundedRect (rect .adjusted (1 ,1 ,-1 ,-1 ),10 ,10 )

        if self .matched and not self .isSelected ():
            painter .setPen (QPen (QColor (t .warning_1 ),1.6 ,Qt .PenStyle .DashLine ))
            painter .setBrush (Qt .BrushStyle .NoBrush )
            painter .drawRoundedRect (rect .adjusted (2 ,2 ,-2 ,-2 ),8 ,8 )

        if self ._snap_highlight :
            painter .setPen (QPen (QColor (t .accent_2 ),3.0 ))
            painter .setBrush (Qt .BrushStyle .NoBrush )
            painter .drawRoundedRect (rect .adjusted (-3 ,-3 ,3 ,3 ),12 ,12 )

        if self ._pulse >0.01 :
            glow =QColor (t .accent_1 )
            glow .setAlphaF (self ._pulse *0.55 )
            pen =QPen (glow ,2.4 +3.0 *self ._pulse )
            painter .setPen (pen )
            painter .setBrush (Qt .BrushStyle .NoBrush )
            grow =3.0 *self ._pulse 
            painter .drawRoundedRect (rect .adjusted (1 -grow ,1 -grow ,-1 +grow ,-1 +grow ),10 ,10 )

    def _resolve_preview_pixmap (self )->Optional [QPixmap ]:
        var =_node_image_var (self .node )
        if not var or self .rm is None :
            return None 
        try :
            entry =self .rm .find_by_var (var )
            if entry is None :
                return None 
            return get_pixmap (entry .abs_path )
        except Exception :
            return None 

    def hoverEnterEvent (self ,e ):
        self ._hover =True 
        self .update ()

    def hoverLeaveEvent (self ,e ):
        self ._hover =False 
        self .update ()

    def mousePressEvent (self ,e :QMouseEvent ):
        if e .button ()==Qt .MouseButton .LeftButton :
            for idx ,pt in enumerate (self .ports ()):
                if (pt -e .pos ()).manhattanLength ()<=PORT_R +9 :
                    self .port_press .emit (self .row ,idx ,self .mapToScene (pt ))
                    e .accept ()
                    return 


        super ().mousePressEvent (e )
        if e .button ()==Qt .MouseButton .LeftButton :
            self .play_click_pulse ()
            self .clicked .emit (self .row )

    def mouseDoubleClickEvent (self ,e :QMouseEvent ):
        if e .button ()==Qt .MouseButton .LeftButton :
            self .double_clicked .emit (self .row )
            e .accept ()
            return 
        super ().mouseDoubleClickEvent (e )

    def contextMenuEvent (self ,e ):
        if not self .isSelected ():
            if self .scene ()is not None :
                self .scene ().clearSelection ()
            self .setSelected (True )
            self .clicked .emit (self .row )
        self .context_requested .emit (self .row ,e .screenPos ())
        e .accept ()


class GroupFrameItem (QGraphicsObject ):
    toggle_requested =pyqtSignal (str )
    header_context =pyqtSignal (str ,object )

    def __init__ (self ,group :NodeGroup ,rect :QRectF ,count :int ):
        super ().__init__ ()
        self .group =group 
        self ._rect =rect 
        self .count =count 
        self .setZValue (0 )
        self .setAcceptHoverEvents (True )

    def boundingRect (self )->QRectF :
        return self ._rect 

    def paint (self ,painter :QPainter ,option ,widget =None ):
        painter .setRenderHint (QPainter .RenderHint .Antialiasing )
        color =QColor (self .group .color )
        header =QRectF (self ._rect .x (),self ._rect .y (),self ._rect .width (),GROUP_HEADER_H )

        body_brush =QColor (color )
        body_brush .setAlpha (18 )
        painter .setBrush (QBrush (body_brush ))
        painter .setPen (QPen (color ,1.4 ))
        painter .drawRoundedRect (self ._rect ,12 ,12 )

        head_brush =QColor (color )
        head_brush .setAlpha (70 )
        painter .setBrush (QBrush (head_brush ))
        painter .setPen (Qt .PenStyle .NoPen )
        painter .drawRoundedRect (header ,12 ,12 )
        painter .drawRect (QRectF (header .x (),header .y ()+10 ,header .width (),10 ))

        painter .setPen (QColor ("#101014"))
        f =QFont ()
        f .setPointSize (9 )
        f .setBold (True )
        painter .setFont (f )
        arrow ="▾"if not self .group .collapsed else "▸"
        label =f"{arrow }  {self .group .title }  ({self .count })"
        painter .drawText (header .adjusted (10 ,0 ,-10 ,0 ),
        Qt .AlignmentFlag .AlignLeft |Qt .AlignmentFlag .AlignVCenter ,label )

    def mousePressEvent (self ,e :QMouseEvent ):
        header =QRectF (self ._rect .x (),self ._rect .y (),self ._rect .width (),GROUP_HEADER_H )
        if header .contains (e .pos ())and e .button ()==Qt .MouseButton .LeftButton :
            self .toggle_requested .emit (self .group .group_id )
            return 
        e .ignore ()

    def contextMenuEvent (self ,e ):
        header =QRectF (self ._rect .x (),self ._rect .y (),self ._rect .width (),GROUP_HEADER_H )
        if header .contains (e .pos ()):
            self .header_context .emit (self .group .group_id ,e .screenPos ())


def _arrow_path (p1 :QPointF ,p2 :QPointF ,dashed :bool =False ,curve :bool =False )->QPainterPath :
    path =QPainterPath (p1 )
    if curve :
        dx =max (60.0 ,abs (p2 .x ()-p1 .x ())*0.6 )
        c1 =QPointF (p1 .x ()+dx ,p1 .y ())
        c2 =QPointF (p2 .x ()+dx ,p2 .y ())
        path .cubicTo (c1 ,c2 ,p2 )
    else :
        mid_y =(p1 .y ()+p2 .y ())/2 
        path .cubicTo (QPointF (p1 .x (),mid_y ),QPointF (p2 .x (),mid_y ),p2 )
    return path 


class ConnectionArrowItem (QGraphicsPathItem ):


    def __init__ (self ,path :QPainterPath ,row :int ,choice_idx :Optional [int ],base_color :QColor ):
        super ().__init__ (path )
        self .row =row 
        self .choice_idx =choice_idx 
        self ._base_color =base_color 
        self .setFlag (QGraphicsItem .GraphicsItemFlag .ItemIsSelectable ,True )
        self .setZValue (2 )
        self ._apply_pen ()

    def _apply_pen (self ):
        if self .isSelected ():
            pen =QPen (QColor ("#ff5c5c"),3.0 ,Qt .PenStyle .DashLine )
        else :
            pen =QPen (self ._base_color ,1.4 ,Qt .PenStyle .DashLine )
        self .setPen (pen )

    def shape (self )->QPainterPath :

        stroker =QPainterPathStroker ()
        stroker .setWidth (14 )
        return stroker .createStroke (self .path ())

    def paint (self ,painter ,option ,widget =None ):
        self ._apply_pen ()
        super ().paint (painter ,option ,widget )


class GraphScene (QGraphicsScene ):
    pass 


class MiniMapView (QWidget ):

    navigate =pyqtSignal (QPointF )

    def __init__ (self ,canvas :"NodeGraphCanvas",parent =None ):
        super ().__init__ (parent )
        self .canvas =canvas 
        self .setFixedSize (190 ,220 )
        self .setObjectName ("minimap_view")
        self ._apply_style ()

    def _apply_style (self ):
        t =theme_manager .tokens ()
        self .setStyleSheet (f"""
            QWidget#minimap_view {{ background: {t .bar_bg }; border: 1px solid {t .glass_border };
                             border-radius: 10px; }}
        """)

    def refresh (self ):
        self .update ()

    def _scene_bounds (self )->Optional [QRectF ]:
        nodes =self .canvas .scene .nodes if self .canvas .scene else []
        xs =[n .pos_x for n in nodes if n .pos_x is not None ]
        ys =[n .pos_y for n in nodes if n .pos_y is not None ]
        if not xs or not ys :
            return None 
        return QRectF (min (xs )-40 ,min (ys )-40 ,
        (max (xs )-min (xs ))+NODE_W +80 ,(max (ys )-min (ys ))+NODE_H +80 )

    def _scale_and_bounds (self ):
        bounds =self ._scene_bounds ()
        if bounds is None or bounds .width ()<=0 or bounds .height ()<=0 :
            return None ,None ,0.0 
        pad =6.0 
        avail_w ,avail_h =self .width ()-pad *2 ,self .height ()-pad *2 
        scale =min (avail_w /bounds .width (),avail_h /bounds .height ())
        return bounds ,pad ,scale 

    def paintEvent (self ,e ):
        painter =QPainter (self )
        painter .setRenderHint (QPainter .RenderHint .Antialiasing )
        bounds ,pad ,scale =self ._scale_and_bounds ()
        if bounds is None or scale <=0 :
            return 
        t =theme_manager .tokens ()

        def to_widget (x ,y ):
            return pad +(x -bounds .x ())*scale ,pad +(y -bounds .y ())*scale 

        painter .setPen (Qt .PenStyle .NoPen )
        min_w ,min_h =3.0 ,3.0 
        for n in self .canvas .scene .nodes :
            if n .pos_x is None :
                continue 
            wx ,wy =to_widget (n .pos_x ,n .pos_y )
            w =max (min_w ,NODE_W *scale )
            h =max (min_h ,NODE_H *scale )
            color =QColor (n .color_tag )if n .color_tag else QColor (t .accent_1 )
            color .setAlpha (210 )
            painter .setBrush (QBrush (color ))
            painter .drawRoundedRect (QRectF (wx ,wy ,w ,h ),1.5 ,1.5 )


        view =self .canvas .view 
        try :
            vp_rect =view .mapToScene (view .viewport ().rect ()).boundingRect ()
            x1 ,y1 =to_widget (vp_rect .x (),vp_rect .y ())
            x2 ,y2 =to_widget (vp_rect .x ()+vp_rect .width (),vp_rect .y ()+vp_rect .height ())
            painter .setPen (QPen (QColor (t .accent_2 ),1.4 ))
            painter .setBrush (Qt .BrushStyle .NoBrush )
            painter .drawRect (QRectF (x1 ,y1 ,x2 -x1 ,y2 -y1 ))
        except Exception :
            pass 

    def _emit_nav (self ,e ):
        bounds ,pad ,scale =self ._scale_and_bounds ()
        if bounds is None or scale <=0 :
            return 
        pos =e .pos ()
        x =bounds .x ()+(pos .x ()-pad )/scale 
        y =bounds .y ()+(pos .y ()-pad )/scale 
        self .navigate .emit (QPointF (x ,y ))

    def mousePressEvent (self ,e ):
        self ._emit_nav (e )

    def mouseMoveEvent (self ,e ):
        if e .buttons ()&Qt .MouseButton .LeftButton :
            self ._emit_nav (e )


class GraphCanvasView (QGraphicsView ):
    def __init__ (self ,scene :QGraphicsScene ,parent =None ):
        super ().__init__ (scene ,parent )
        self .setRenderHint (QPainter .RenderHint .Antialiasing )
        self .setDragMode (QGraphicsView .DragMode .RubberBandDrag )
        self .setTransformationAnchor (QGraphicsView .ViewportAnchor .AnchorUnderMouse )
        self .setFocusPolicy (Qt .FocusPolicy .StrongFocus )
        self ._panning =False 
        self ._pan_start =QPointF ()
        self ._zoom =1.0 
        self .owner =None 
        self .setObjectName ("node_canvas")

    def wheelEvent (self ,e :QWheelEvent ):
        factor =1.15 if e .angleDelta ().y ()>0 else (1 /1.15 )
        new_zoom =self ._zoom *factor 
        if 0.25 <=new_zoom <=2.5 :
            self ._zoom =new_zoom 
            self .scale (factor ,factor )
        e .accept ()

    def mousePressEvent (self ,e :QMouseEvent ):
        if e .button ()==Qt .MouseButton .MiddleButton :
            self ._panning =True 
            self ._pan_start =e .position ()
            self .setCursor (Qt .CursorShape .ClosedHandCursor )
            e .accept ()
            return 
        if e .button ()==Qt .MouseButton .LeftButton and self .itemAt (e .pos ())is None :


            self .setDragMode (QGraphicsView .DragMode .ScrollHandDrag )
        else :
            self .setDragMode (QGraphicsView .DragMode .RubberBandDrag )
        super ().mousePressEvent (e )
        self .setFocus (Qt .FocusReason .MouseFocusReason )

    def mouseMoveEvent (self ,e :QMouseEvent ):
        if self .owner is not None and getattr (self .owner ,"_connecting",None )is not None :
            self .owner ._update_connecting (self .mapToScene (e .position ().toPoint ()))
            e .accept ()
            return 
        if self ._panning :
            delta =e .position ()-self ._pan_start 
            self ._pan_start =e .position ()
            self .horizontalScrollBar ().setValue (self .horizontalScrollBar ().value ()-int (delta .x ()))
            self .verticalScrollBar ().setValue (self .verticalScrollBar ().value ()-int (delta .y ()))
            e .accept ()
            return 
        super ().mouseMoveEvent (e )

    def mouseReleaseEvent (self ,e :QMouseEvent ):
        if self .owner is not None and getattr (self .owner ,"_connecting",None )is not None :
            self .owner ._finish_connecting (self .mapToScene (e .position ().toPoint ()))
            e .accept ()
            return 
        if e .button ()==Qt .MouseButton .MiddleButton :
            self ._panning =False 
            self .setCursor (Qt .CursorShape .ArrowCursor )
            e .accept ()
            return 
        super ().mouseReleaseEvent (e )
        if e .button ()==Qt .MouseButton .LeftButton :
            self .setDragMode (QGraphicsView .DragMode .RubberBandDrag )

    def contextMenuEvent (self ,e ):
        if self .owner is not None and self .itemAt (e .pos ())is None :
            self .owner ._show_add_node_menu_at (self .mapToGlobal (e .pos ()))
            e .accept ()
            return 
        super ().contextMenuEvent (e )

    def keyPressEvent (self ,e ):
        if self .owner is not None :
            if e .key ()==Qt .Key .Key_Escape and getattr (self .owner ,"_connecting",None )is not None :
                self .owner ._cancel_connecting ()
                e .accept ()
                return 
            if e .key ()in (Qt .Key .Key_Delete ,Qt .Key .Key_Backspace ):
                self .owner ._delete_selection ()
                e .accept ()
                return 
            if e .matches (QKeySequence .StandardKey .Copy ):
                self .owner .copy_selection ()
                e .accept ()
                return 
            if e .matches (QKeySequence .StandardKey .Paste ):
                self .owner .paste_after (self .owner ._current_row )
                e .accept ()
                return 
        super ().keyPressEvent (e )


class NodePreviewOverlay (QLabel ):


    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .setMinimumHeight (170 )
        self .setWordWrap (True )
        self .setAlignment (Qt .AlignmentFlag .AlignLeft |Qt .AlignmentFlag .AlignTop )
        self .setScaledContents (False )
        self ._apply_style ()
        self .hide ()

    def _apply_style (self ):
        t =theme_manager .tokens ()
        self .setStyleSheet (f"""
            QLabel {{ background: {t .bar_bg }; border: 1px solid {t .glass_border };
                      border-radius: 10px; color: {t .text }; padding: 8px; font-size: 11px; }}
        """)

    def show_node (self ,node :Optional [SceneNode ],rm =None ):
        if node is None :
            self .hide ()
            return 
        self ._apply_style ()
        pix =None 
        var =_node_image_var (node )
        if var and rm is not None :
            try :
                entry =rm .find_by_var (var )
                if entry is not None :
                    pix =get_pixmap (entry .abs_path )
            except Exception :
                pix =None 
        if pix is not None and not pix .isNull ():
            self .setText ("")
            self .setPixmap (pix .scaled (self .width ()-18 ,self .height ()-18 ,
            Qt .AspectRatioMode .KeepAspectRatio ,
            Qt .TransformationMode .SmoothTransformation ))
        else :
            self .setPixmap (QPixmap ())
            body =_node_body_text (node )or node .preview_text ()
            self .setText (f"{_node_header (node )}\n\n{body }")
        self .show ()


_EDIT_FIELDS ={
NodeType .DIALOGUE :[("character_var","node_edit.character","combo_character"),
("text","node_edit.text","text_validated")],
NodeType .NARRATION :[("text","node_edit.text","text_validated")],
NodeType .LABEL :[("label_name","node_edit.label_name","line")],
NodeType .JUMP :[("jump_target","node_edit.jump_target","line")],
NodeType .SHOW_BG :[("bg_var","node_edit.bg_var","carousel_bg"),
("transition","node_edit.transition","combo_transition")],
NodeType .SCENE :[("bg_var","node_edit.bg_var","carousel_bg"),
("transition","node_edit.transition","combo_transition")],
NodeType .SHOW_SPRITE :[("sprite_var","node_edit.sprite_var","carousel_sprite"),
("sprite_expression","node_edit.sprite_expression","line"),
("sprite_tag","node_edit.sprite_tag","line")],
NodeType .HIDE_SPRITE :[("hide_group","node_edit.hide_group","picker_hide_group"),
("hide_var","node_edit.hide_var","carousel_sprite")],
NodeType .SHOW_CG :[("cg_var","node_edit.cg_var","carousel_cg")],
NodeType .PLAY_MUSIC :[("audio_var","node_edit.music_var","audio_music"),
("audio_loop","node_edit.loop","checkbox"),
("music_fadein","node_edit.fadein","spin_float"),
("music_fadeout","node_edit.fadeout","spin_float")],
NodeType .STOP_MUSIC :[("music_fadeout","node_edit.fadeout","spin_float")],
NodeType .PLAY_SOUND :[("audio_var","node_edit.sound_var","audio_sound")],
NodeType .PLAY_AMBIENCE :[("audio_var","node_edit.ambience_var","audio_ambience"),
("ambience_fadein","node_edit.fadein","spin_float"),
("ambience_fadeout","node_edit.fadeout","spin_float")],
NodeType .STOP_AMBIENCE :[("ambience_fadeout","node_edit.fadeout","spin_float")],
NodeType .PYTHON :[("python_code","node_edit.python_code","multiline")],
NodeType .RAW :[("python_code","node_edit.raw_code","multiline")],
NodeType .PAUSE :[("pause_duration","node_edit.pause_duration","spin_float")],
NodeType .COMMENT :[("comment_text","node_edit.comment_text","multiline")],
NodeType .WINDOW :[("window_action","node_edit.window_action","combo_window_action"),
("transition","node_edit.transition","combo_transition")],
NodeType .WITH_TRANSITION :[("transition","node_edit.transition","combo_transition")],
NodeType .MENU :[("menu_prompt","node_edit.menu_prompt","multiline")],
}

_NARRATOR_OPTION ="__narrator__"
_WINDOW_ACTIONS =["show","hide"]
_DIALOGUE_LEN_OK =200 
_DIALOGUE_LEN_UGLY =340 
TRANSITIONS =["","dissolve","fade","fade2","fade3","flash","pixellate",
"blinds","squares","wipeleft","wiperight","wipeup",
"wipedown","vpunch","hpunch","dspr"]


class GraphNodeEditor (QWidget ):


    field_changed =pyqtSignal (int ,dict )

    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self ._row =-1 
        self .rm =None 
        self .tags_store =None 
        self .characters =None 
        self .usage_store =None 
        self ._last_group_by_kind ={}
        self ._node :Optional [SceneNode ]=None 
        self ._inputs ={}
        self ._suspend =False 
        self ._debounce =QTimer (self )
        self ._debounce .setSingleShot (True )
        self ._debounce .setInterval (400 )
        self ._debounce .timeout .connect (self ._emit_pending )
        self ._pending :dict ={}

        outer =QVBoxLayout (self )
        outer .setContentsMargins (4 ,4 ,4 ,4 )
        outer .setSpacing (6 )

        self .header =QLabel ("-")
        self .header .setObjectName ("hint_text_bright")
        self .header .setWordWrap (True )
        outer .addWidget (self .header )

        self .form_host =QWidget ()
        self .form_layout =QFormLayout (self .form_host )
        self .form_layout .setContentsMargins (0 ,0 ,0 ,0 )
        self .form_layout .setSpacing (6 )
        outer .addWidget (self .form_host )


        self .menu_host =QWidget ()
        self .menu_layout =QVBoxLayout (self .menu_host )
        self .menu_layout .setContentsMargins (0 ,0 ,0 ,0 )
        self .menu_layout .setSpacing (4 )
        outer .addWidget (self .menu_host )
        self .menu_host .hide ()

        outer .addStretch (1 )
        self .setEnabled (False )

    def flush (self ):

        self ._debounce .stop ()
        if self ._pending :
            self ._emit_pending ()

    def clear (self ):
        self .flush ()
        self ._row =-1 
        self ._node =None 
        self .header .setText ("-")
        self ._clear_layout (self .form_layout )
        self ._clear_layout (self .menu_layout )
        self .menu_host .hide ()
        self ._inputs ={}
        self .setEnabled (False )

    @staticmethod 
    def _clear_layout (layout ):
        while layout .count ():
            item =layout .takeAt (0 )
            w =item .widget ()
            if w is not None :
                w .setParent (None )
                w .deleteLater ()

    def set_node (self ,row :int ,node :Optional [SceneNode ]):
        self .flush ()
        self ._suspend =True 
        try :
            self ._row =row 
            self ._node =node 
            self ._clear_layout (self .form_layout )
            self ._inputs ={}
            if node is None :
                self .header .setText ("-")
                self .menu_host .hide ()
                self .setEnabled (False )
                return 
            self .setEnabled (True )
            self .header .setText (_node_header (node ))
            fields =_EDIT_FIELDS .get (node .node_type ,[])
            for attr ,label_key ,kind in fields :
                value =getattr (node ,attr ,"")
                if kind in ("carousel_bg","carousel_cg","carousel_sprite","picker_hide_group","audio_music",
                "audio_sound","audio_ambience"):
                    w =self ._build_wide_field (attr ,kind ,value ,node )
                    self ._inputs [attr ]=w 
                    lbl =QLabel (tr (label_key ))
                    lbl .setObjectName ("hint_text")
                    self .form_layout .addRow (lbl )
                    self .form_layout .addRow (w )
                    continue 
                if kind =="multiline":
                    w =QPlainTextEdit ()
                    w .setPlainText (""if value is None else str (value ))
                    w .setMaximumHeight (120 )
                    w .textChanged .connect (lambda a =attr ,wid =w :self ._on_field_edited (a ,wid .toPlainText ()))
                    self ._inputs [attr ]=w 
                    self .form_layout .addRow (tr (label_key ),w )
                elif kind =="text_validated":
                    container =self ._build_validated_text (attr ,value )
                    self .form_layout .addRow (tr (label_key ))
                    self .form_layout .addRow (container )
                elif kind =="combo_character":
                    w =self ._build_character_combo (value )
                    w .currentIndexChanged .connect (lambda *_a ,wid =w ,a =attr :self ._on_field_edited (a ,wid .currentData ()))
                    self ._inputs [attr ]=w 
                    self .form_layout .addRow (tr (label_key ),w )
                elif kind =="combo_transition":
                    w =self ._build_transition_combo (value )
                    w .currentTextChanged .connect (lambda text ,a =attr :self ._on_field_edited (a ,text ))
                    self ._inputs [attr ]=w 
                    self .form_layout .addRow (tr (label_key ),w )
                elif kind =="combo_window_action":
                    w =QComboBox ()
                    w .addItems (_WINDOW_ACTIONS )
                    if value in _WINDOW_ACTIONS :
                        w .setCurrentIndex (_WINDOW_ACTIONS .index (value ))
                    w .currentTextChanged .connect (lambda text ,a =attr :self ._on_field_edited (a ,text ))
                    self ._inputs [attr ]=w 
                    self .form_layout .addRow (tr (label_key ),w )
                elif kind =="checkbox":
                    w =QCheckBox (tr (label_key ))
                    w .setChecked (bool (value ))
                    w .toggled .connect (lambda checked ,a =attr :self ._on_field_edited (a ,checked ))
                    self ._inputs [attr ]=w 
                    self .form_layout .addRow (w )
                elif kind =="spin_float":
                    w =QDoubleSpinBox ()
                    w .setRange (0.0 ,60.0 )
                    w .setSingleStep (0.5 )
                    w .setDecimals (1 )
                    try :
                        w .setValue (float (value )if value else 0.0 )
                    except (TypeError ,ValueError ):
                        w .setValue (0.0 )
                    w .valueChanged .connect (lambda v ,a =attr :self ._on_field_edited (a ,v ))
                    self ._inputs [attr ]=w 
                    self .form_layout .addRow (tr (label_key ),w )
                else :
                    w =QLineEdit ()
                    w .setText (""if value is None else str (value ))
                    w .textEdited .connect (lambda text ,a =attr :self ._on_field_edited (a ,text ))
                    self ._inputs [attr ]=w 
                    self .form_layout .addRow (tr (label_key ),w )

            if node .node_type ==NodeType .MENU :
                self ._build_menu_editor (node )
                self .menu_host .show ()
            else :
                self .menu_host .hide ()
        finally :
            self ._suspend =False 

    def _build_wide_field (self ,attr :str ,kind :str ,current_value ,node :SceneNode ):

        if kind in ("carousel_bg","carousel_cg","carousel_sprite"):
            return self ._build_carousel (attr ,kind ,current_value )
        if kind =="picker_hide_group":
            w =CharacterGroupPicker (self .rm ,category ="sprites",thumb_size =110 )
            w .set_resource_manager (self .rm ,"sprites")
            if current_value :
                try :
                    w .select_folder (current_value )
                except Exception :
                    pass 
            w .selection_changed .connect (lambda folder ,a =attr :self ._on_field_edited (a ,folder ))
            return w 
        if kind in ("audio_music","audio_sound","audio_ambience"):
            cat ={"audio_music":"music","audio_sound":"sounds","audio_ambience":"ambience"}[kind ]
            return self ._build_audio_row (attr ,cat ,current_value )
        w =QLabel ("?")
        return w 

    def _build_carousel (self ,attr :str ,kind :str ,current_value :str ):

        thumb =150 
        if kind =="carousel_sprite":
            w =FolderResourceCarousel (self .rm ,category ="sprites",thumb_size =thumb )
            w .set_resource_manager (self .rm ,"sprites")
        else :
            cat ="bg"if kind =="carousel_bg"else "cg"
            entries =self .rm .get (cat )if self .rm is not None else []
            last_group =self ._last_group_by_kind .get (kind )
            w =ResourceCarousel (thumb_size =thumb ,tags_store =self .tags_store ,
            initial_group_id =last_group ,category =cat ,
            usage_store =self .usage_store ,rm =self .rm )
            w .set_entries (entries )
            w .group_changed .connect (lambda gid ,k =kind :self ._last_group_by_kind .__setitem__ (k ,gid ))
        if current_value :
            try :
                w .select_by_var (current_value )
            except Exception :
                pass 
        w .selection_changed .connect (lambda entry ,a =attr :self ._on_carousel_selected (a ,entry ))
        return w 

    def _build_audio_row (self ,attr :str ,category :str ,current_var :str ):

        container =QWidget ()
        row =QHBoxLayout (container )
        row .setContentsMargins (0 ,0 ,0 ,0 )
        row .setSpacing (4 )
        entries =self .rm .get (category )if self .rm is not None else []
        combo =QComboBox ()
        combo .addItem ("","")
        for e in entries :
            combo .addItem (e .display_name or e .var_name ,e .var_name )
        if current_var :
            idx =combo .findData (current_var )
            if idx >=0 :
                combo .setCurrentIndex (idx )
        combo .currentIndexChanged .connect (
        lambda *_a ,c =combo ,a =attr :self ._on_field_edited (a ,c .currentData ()or ""))
        row .addWidget (combo ,1 )

        btn_play =QToolButton ()
        btn_play .setText ("▶️")
        btn_play .setToolTip (tr ("node_edit.play_tooltip"))

        def _play ():
            idx =combo .currentIndex ()
            var =combo .itemData (idx )
            if not var or self .rm is None :
                return 
            entry =self .rm .find_by_var (var )
            if entry is None :
                return 
            get_audio_player ().play (entry .abs_path ,start_fraction =0.2 if category =="music"else 0.0 )

        btn_play .clicked .connect (_play )
        row .addWidget (btn_play )

        btn_stop =QToolButton ()
        btn_stop .setText ("⏹️")
        btn_stop .setToolTip (tr ("node_edit.stop_tooltip"))
        btn_stop .clicked .connect (lambda :get_audio_player ().stop ())
        row .addWidget (btn_stop )
        return container 

    def _build_character_combo (self ,current_var :str )->QComboBox :

        w =QComboBox ()
        w .addItem (tr ("node_edit.narrator_option"),"")
        characters =self .characters ()if callable (self .characters )else (self .characters or [])
        for c in characters :
            w .addItem (getattr (c ,"name",""),getattr (c ,"variable",""))
        if current_var :
            idx =w .findData (current_var )
            if idx >=0 :
                w .setCurrentIndex (idx )
        return w 

    def _build_transition_combo (self ,current_value :str )->QComboBox :

        w =QComboBox ()
        w .addItems (TRANSITIONS )
        w .setEditable (True )
        if current_value and current_value not in TRANSITIONS :
            w .addItem (current_value )
        w .setCurrentText (current_value or "")
        return w 

    def _build_validated_text (self ,attr :str ,value )->QWidget :

        container =QWidget ()
        lay =QVBoxLayout (container )
        lay .setContentsMargins (0 ,0 ,0 ,0 )
        lay .setSpacing (2 )
        text_edit =QPlainTextEdit ()
        text_edit .setPlainText (""if value is None else str (value ))
        text_edit .setMaximumHeight (120 )
        hint =QLabel ()
        hint .setWordWrap (True )
        hint .setStyleSheet ("font-size:11px; padding:2px 0;")

        def _update_hint ():
            raw =text_edit .toPlainText ()
            count =len (strip_tags (raw ))
            if count <=_DIALOGUE_LEN_OK :
                color ,key ="#7ed957","node_edit.length_ok"
            elif count <=_DIALOGUE_LEN_UGLY :
                color ,key ="#ffb84d","node_edit.length_ugly"
            else :
                color ,key ="#ff6b6b","node_edit.length_overflow"
            hint .setStyleSheet (f"font-size:11px; padding:2px 0; color:{color };")
            hint .setText (tr (key ,count =count ))

        text_edit .textChanged .connect (lambda :self ._on_field_edited (attr ,text_edit .toPlainText ()))
        text_edit .textChanged .connect (_update_hint )
        _update_hint ()
        lay .addWidget (text_edit )
        lay .addWidget (hint )
        self ._inputs [attr ]=text_edit 
        return container 

    def _on_carousel_selected (self ,attr :str ,entry ):
        if self ._suspend or self ._node is None :
            return 
        value =getattr (entry ,"var_name","")if entry is not None else ""
        self ._pending [attr ]=value 
        self ._debounce .start ()

    def _on_field_edited (self ,attr :str ,value ):
        if self ._suspend or self ._node is None :
            return 
        self ._pending [attr ]=value 
        self ._debounce .start ()

    def _emit_pending (self ):
        if self ._row <0 or not self ._pending :
            return 
        self .field_changed .emit (self ._row ,dict (self ._pending ))
        self ._pending ={}

    def _build_menu_editor (self ,node :SceneNode ):
        self ._clear_layout (self .menu_layout )
        choices =node .normalized_menu_choices ()
        for idx ,choice in enumerate (choices ):
            row_w =QWidget ()
            row_l =QHBoxLayout (row_w )
            row_l .setContentsMargins (0 ,0 ,0 ,0 )
            row_l .setSpacing (4 )
            text_edit =QLineEdit (choice [0 ]if choice [0 ]else "")
            text_edit .setPlaceholderText (tr ("node_edit.choice_text"))
            jump_edit =QLineEdit (choice [1 ]if choice [1 ]else "")
            jump_edit .setPlaceholderText (tr ("node_edit.choice_jump"))
            text_edit .textEdited .connect (lambda t ,i =idx :self ._on_choice_edited (i ,text =t ))
            jump_edit .textEdited .connect (lambda t ,i =idx :self ._on_choice_edited (i ,jump =t ))
            btn_del =QToolButton ()
            btn_del .setText ("🗑")
            btn_del .clicked .connect (lambda checked =False ,i =idx :self ._on_choice_delete (i ))
            row_l .addWidget (text_edit ,2 )
            row_l .addWidget (jump_edit ,1 )
            row_l .addWidget (btn_del )
            self .menu_layout .addWidget (row_w )
        btn_add =QPushButton ("+ "+tr ("node_edit.choice_add"))
        btn_add .clicked .connect (self ._on_choice_add )
        self .menu_layout .addWidget (btn_add )

    def _on_choice_edited (self ,idx :int ,text :Optional [str ]=None ,jump :Optional [str ]=None ):
        if self ._node is None :
            return 
        choices =self ._node .menu_choices 
        if not (0 <=idx <len (choices )):
            return 
        ch =choices [idx ]
        if isinstance (ch ,dict ):
            if text is not None :
                ch ["text"]=text 
            if jump is not None :
                ch ["jump"]=jump 
        else :
            ch =list (ch )+[""]*max (0 ,2 -len (ch ))
            if text is not None :
                ch [0 ]=text 
            if jump is not None :
                ch [1 ]=jump 
            choices [idx ]=tuple (ch )
        self ._pending ["menu_choices"]=choices 
        self ._debounce .start ()

    def _on_choice_add (self ):
        if self ._node is None :
            return 
        self ._node .menu_choices .append (("","",False ,"",[]))
        self .field_changed .emit (self ._row ,{"menu_choices":self ._node .menu_choices })
        self ._build_menu_editor (self ._node )

    def _on_choice_delete (self ,idx :int ):
        if self ._node is None or not (0 <=idx <len (self ._node .menu_choices )):
            return 
        self ._node .menu_choices .pop (idx )
        self .field_changed .emit (self ._row ,{"menu_choices":self ._node .menu_choices })
        self ._build_menu_editor (self ._node )


class NodeGraphCanvas (QWidget ):


    node_clicked =pyqtSignal (int )
    node_double_clicked =pyqtSignal (int )

    def __init__ (self ,panel ,parent =None ):
        super ().__init__ (parent )
        self .panel =panel 
        self .rm =getattr (panel ,"rm",None )
        self .scene :Optional [Scene ]=None 
        self ._current_row =-1 
        self ._row_items ={}
        self ._clipboard :List [dict ]=[]
        self ._connecting =None 
        self ._connect_line :Optional [QGraphicsPathItem ]=None 
        self ._connect_snap_box :Optional [NodeBoxItem ]=None 

        self .gscene =GraphScene (self )
        self .gscene .setBackgroundBrush (qcolor (theme_manager .tokens ().bg_window ))

        layout =QVBoxLayout (self )
        layout .setContentsMargins (0 ,0 ,0 ,0 )
        layout .setSpacing (4 )

        search_row =QHBoxLayout ()
        self .search_edit =QLineEdit ()
        self .search_edit .setPlaceholderText ("🔎 Поиск по репликам / спрайтам / персонажам...")
        self .search_edit .setObjectName ("dark_field")
        self .search_edit .setStyleSheet ("font-size:12px;")
        self .search_edit .textChanged .connect (self ._on_search )
        self .search_edit .returnPressed .connect (self ._search_next )
        search_row .addWidget (self .search_edit ,1 )
        self .search_status =QLabel ("")
        self .search_status .setObjectName ("hint_text_bright")
        search_row .addWidget (self .search_status )

        self .btn_align =QToolButton ()
        self .btn_align .setText ("⇱ "+tr ("node_graph.align_nodes"))
        self .btn_align .setObjectName ("btn_secondary")
        self .btn_align .setToolTip (tr ("node_graph.align_nodes_tooltip"))
        self .btn_align .clicked .connect (self .align_nodes )
        search_row .addWidget (self .btn_align )

        self .btn_add_node =QToolButton ()
        self .btn_add_node .setText ("➕ "+tr ("node_graph.add_node"))
        self .btn_add_node .setObjectName ("btn_secondary")
        self .btn_add_node .setToolTip (tr ("node_graph.add_node_tooltip"))
        self .btn_add_node .clicked .connect (self ._show_add_node_menu )
        search_row .addWidget (self .btn_add_node )
        layout .addLayout (search_row )

        self .view =GraphCanvasView (self .gscene )
        self .view .owner =self 
        self .view .setMinimumHeight (300 )

        content_row =QHBoxLayout ()
        content_row .setSpacing (6 )
        content_row .addWidget (self .view ,1 )

        right_col =QVBoxLayout ()
        right_col .setSpacing (6 )

        self .preview_overlay =NodePreviewOverlay ()
        self .preview_overlay .setFixedHeight (220 )
        right_col .addWidget (self .preview_overlay )

        self .minimap =MiniMapView (self ,self )
        self .minimap .navigate .connect (self ._on_minimap_navigate )
        right_col .addWidget (self .minimap )

        editor_frame =QFrame ()
        editor_frame .setObjectName ("graph_editor_frame")
        editor_frame_layout =QVBoxLayout (editor_frame )
        editor_frame_layout .setContentsMargins (8 ,8 ,8 ,8 )
        editor_frame_layout .setSpacing (4 )
        editor_hdr =QLabel ("✎ "+tr ("node_graph.edit_node"))
        editor_hdr .setObjectName ("hint_text_bright")
        editor_frame_layout .addWidget (editor_hdr )
        self .node_editor =GraphNodeEditor ()
        self .node_editor .field_changed .connect (self ._on_editor_field_changed )
        editor_scroll =QScrollArea ()
        editor_scroll .setWidgetResizable (True )
        editor_scroll .setWidget (self .node_editor )
        editor_frame_layout .addWidget (editor_scroll ,1 )
        self ._apply_editor_frame_style (editor_frame )
        right_col .addWidget (editor_frame ,1 )

        right_container =QWidget ()
        right_container .setFixedWidth (480 )
        right_container .setLayout (right_col )
        content_row .addWidget (right_container )

        layout .addLayout (content_row ,1 )

        self ._search_matches :List [int ]=[]
        self ._search_pos =-1 

        theme_manager .themeChanged .connect (self ._on_theme_changed )

    def _on_theme_changed (self ,_theme_id :str ):

        self .gscene .setBackgroundBrush (qcolor (theme_manager .tokens ().bg_window ))
        self .minimap ._apply_style ()
        self ._rebuild ()

    def _apply_editor_frame_style (self ,frame :QFrame ):
        t =theme_manager .tokens ()
        frame .setStyleSheet (f"""
            QFrame#graph_editor_frame {{ background: {t .bar_bg }; border: 1px solid {t .glass_border };
                                          border-radius: 10px; }}
        """)

    def _on_editor_field_changed (self ,row :int ,fields :dict ):
        if hasattr (self .panel ,"update_node_fields"):
            self .panel .update_node_fields (row ,**fields )

    def refresh_node_box (self ,row :int ):

        box =self ._row_items .get (row )
        if box is not None :
            box ._cached_pixmap =box ._resolve_preview_pixmap ()
            box .update ()
        try :
            self ._redraw_arrows ()
        except Exception :
            pass 
        if not self .scene or not (0 <=row <len (self .scene .nodes )):
            return 
        node =self .scene .nodes [row ]
        if row ==self ._current_row :
            self .preview_overlay .show_node (node ,self .rm )
        if self .node_editor ._row ==row :
            self .node_editor .header .setText (_node_header (node ))

    def _on_minimap_navigate (self ,scene_pt :QPointF ):
        self .view .centerOn (scene_pt )



    def set_scene (self ,scene :Optional [Scene ],current_row :int ,selected_rows =None ):
        self .node_editor .flush ()
        self .rm =getattr (self .panel ,"rm",None )
        self .node_editor .rm =self .rm 
        self .node_editor .tags_store =getattr (self .panel ,"tags_store",None )
        self .node_editor .usage_store =getattr (self .panel ,"usage_store",None )
        self .node_editor .characters =getattr (self .panel ,"get_characters",None )
        self .scene =scene 
        self ._current_row =current_row 
        self ._rebuild ()
        if scene and 0 <=current_row <len (scene .nodes ):
            self .preview_overlay .show_node (scene .nodes [current_row ],self .rm )
            if self .node_editor ._row !=current_row :
                self .node_editor .set_node (current_row ,scene .nodes [current_row ])
        else :
            self .preview_overlay .hide ()
            self .node_editor .clear ()

    def _group_for_node (self ,node_id :str )->Optional [NodeGroup ]:
        if not self .scene :
            return None 
        for g in self .scene .groups :
            if node_id in g .node_ids :
                return g 
        return None 

    def _rebuild (self ):
        try :
            self ._rebuild_impl ()
        except Exception :
            import traceback 
            traceback .print_exc ()
            self ._rebuild_fallback ()

    def _rebuild_fallback (self ):

        self .gscene .clear ()
        self ._row_items ={}
        self ._arrow_items =[]
        nodes =self .scene .nodes if self .scene else []
        y =20.0 
        for r ,node in enumerate (nodes ):
            try :
                box =NodeBoxItem (r ,node ,is_current =(r ==self ._current_row ),rm =self .rm )
                box .setPos (LEFT_X ,y )
                box .clicked .connect (self ._on_node_clicked )
                box .context_requested .connect (self ._on_node_context )
                box .moved .connect (self ._on_node_moved )
                box .port_press .connect (self ._start_connecting )
                box .double_clicked .connect (self ._on_node_double_clicked )
                self .gscene .addItem (box )
                self ._row_items [r ]=box 
                y +=NODE_H +GAP_Y 
            except Exception :
                import traceback 
                traceback .print_exc ()
                continue 
        try :
            self .gscene .setSceneRect (self .gscene .itemsBoundingRect ().adjusted (-2000 ,-2000 ,2000 ,2000 ))
        except Exception :
            pass 
        self .minimap .refresh ()

    def _rebuild_impl (self ):
        self .gscene .clear ()
        self ._row_items ={}
        self ._arrow_items =[]
        if not self .scene or not self .scene .nodes :
            self .minimap .refresh ()
            return 

        nodes =self .scene .nodes 


        if all (n .pos_x is None for n in nodes ):
            self ._auto_layout_tree ()

        hidden_rows =set ()
        for g in self .scene .groups :
            if g .collapsed :
                for i ,n in enumerate (nodes ):
                    if n .node_id in g .node_ids :
                        hidden_rows .add (i )
        visible_rows =[r for r in range (len (nodes ))if r not in hidden_rows ]




        last_x ,last_y =LEFT_X ,20.0 -(NODE_H +GAP_Y )
        for r in visible_rows :
            node =nodes [r ]
            if node .pos_x is not None and node .pos_y is not None :
                px ,py =node .pos_x ,node .pos_y 
            else :
                px ,py =last_x ,last_y +NODE_H +GAP_Y 
                node .pos_x ,node .pos_y =px ,py 
            last_x ,last_y =px ,py 

            box =NodeBoxItem (r ,node ,is_current =(r ==self ._current_row ),matched =(r in self ._search_matches ),
            rm =self .rm )
            box .setPos (px ,py )
            if r ==self ._current_row :
                box .setSelected (True )
            box .clicked .connect (self ._on_node_clicked )
            box .context_requested .connect (self ._on_node_context )
            box .moved .connect (self ._on_node_moved )
            box .port_press .connect (self ._start_connecting )
            box .double_clicked .connect (self ._on_node_double_clicked )
            self .gscene .addItem (box )
            self ._row_items [r ]=box 


        rendered_group_ids =set ()
        for g in self .scene .groups :
            if g .collapsed or g .group_id in rendered_group_ids :
                continue 
            member_rows =[r for r in visible_rows if nodes [r ].node_id in g .node_ids ]
            if not member_rows :
                continue 
            rendered_group_ids .add (g .group_id )
            xs =[self ._row_items [r ].pos ().x ()for r in member_rows ]
            ys =[self ._row_items [r ].pos ().y ()for r in member_rows ]
            rect =QRectF (min (xs )-GROUP_PAD ,min (ys )-GROUP_HEADER_H -10 ,
            (max (xs )-min (xs ))+NODE_W +GROUP_PAD *2 ,
            (max (ys )-min (ys ))+NODE_H +GROUP_HEADER_H +18 )
            item =GroupFrameItem (g ,rect ,len (member_rows ))
            item .setPos (0 ,0 )
            item .setZValue (0 )
            item .toggle_requested .connect (self ._toggle_group )
            item .header_context .connect (self ._group_context_menu )
            self .gscene .addItem (item )

        self ._redraw_arrows ()
        self .gscene .setSceneRect (self .gscene .itemsBoundingRect ().adjusted (-2000 ,-2000 ,2000 ,2000 ))
        self .minimap .refresh ()

    def _redraw_arrows (self ):

        for it in self ._arrow_items :
            if it .scene ()is not None :
                self .gscene .removeItem (it )
        self ._arrow_items =[]
        if not self .scene :
            return 
        nodes =self .scene .nodes 

        def top (box ):
            p =box .pos ()
            return QPointF (p .x ()+NODE_W /2 ,p .y ())

        def bottom (box ):
            p =box .pos ()
            return QPointF (p .x ()+NODE_W /2 ,p .y ()+NODE_H )

        def left_mid (box ):
            p =box .pos ()
            return QPointF (p .x (),p .y ()+NODE_H /2 )


        rows_sorted =sorted (self ._row_items .keys ())
        for a ,b in zip (rows_sorted ,rows_sorted [1 :]):
            if b !=a +1 :
                continue 
            if nodes [a ].node_type in (NodeType .JUMP ,NodeType .RETURN )or nodes [b ].node_type ==NodeType .LABEL :
                continue 
            path =_arrow_path (bottom (self ._row_items [a ]),top (self ._row_items [b ]))
            pen =QPen (qcolor (theme_manager .tokens ().glass_border ),1.6 )
            pitem =QGraphicsPathItem (path )
            pitem .setPen (pen )
            pitem .setZValue (1 )
            self .gscene .addItem (pitem )
            self ._arrow_items .append (pitem )


        label_row ={}
        for r ,n in enumerate (nodes ):
            if n .node_type ==NodeType .LABEL and n .label_name :
                label_row [n .label_name ]=r 

        for r ,n in enumerate (nodes ):
            if r not in self ._row_items :
                continue 
            targets =[]
            if n .node_type ==NodeType .JUMP and n .jump_target in label_row :
                targets .append ((label_row [n .jump_target ],None ))
            elif n .node_type ==NodeType .MENU :
                for ci ,choice in enumerate (n .normalized_menu_choices ()):
                    jump =choice [1 ]
                    if jump and jump in label_row :
                        targets .append ((label_row [jump ],ci ))
            if not targets :
                continue 
            src_pt =left_mid (self ._row_items [r ])
            for tr ,ci in targets :
                if tr ==r or tr not in self ._row_items :
                    continue 
                tp =left_mid (self ._row_items [tr ])
                path =_arrow_path (src_pt ,tp ,dashed =True ,curve =True )
                pitem =ConnectionArrowItem (path ,r ,ci ,QColor (theme_manager .tokens ().accent_2 ))
                self .gscene .addItem (pitem )
                self ._arrow_items .append (pitem )

    def _on_node_moved (self ,row :int ,pos :QPointF ):

        if not self .scene or not (0 <=row <len (self .scene .nodes )):
            return 
        self .scene .nodes [row ].pos_x =pos .x ()
        self .scene .nodes [row ].pos_y =pos .y ()
        self ._redraw_arrows ()
        self .gscene .setSceneRect (self .gscene .itemsBoundingRect ().adjusted (-2000 ,-2000 ,2000 ,2000 ))
        self .minimap .refresh ()

    def _start_connecting (self ,row :int ,port_idx :int ,scene_pos :QPointF ):

        self ._connecting =(row ,port_idx )
        pen =QPen (QColor (theme_manager .tokens ().accent_2 ),2.0 ,Qt .PenStyle .DashLine )
        self ._connect_line =QGraphicsPathItem (_arrow_path (scene_pos ,scene_pos ))
        self ._connect_line .setPen (pen )
        self ._connect_line .setZValue (50 )
        self .gscene .addItem (self ._connect_line )
        self .view .setCursor (Qt .CursorShape .CrossCursor )

    def _nearest_label_box (self ,scene_pos :QPointF )->Optional [NodeBoxItem ]:
        best =None 
        best_dist =SNAP_RADIUS 
        for r ,box in self ._row_items .items ():
            if not self .scene or self .scene .nodes [r ].node_type !=NodeType .LABEL :
                continue 
            center =box .pos ()+QPointF (NODE_W /2 ,NODE_H /2 )
            d =((center .x ()-scene_pos .x ())**2 +(center .y ()-scene_pos .y ())**2 )**0.5 
            if d <best_dist :
                best_dist =d 
                best =box 
        return best 

    def _update_connecting (self ,scene_pos :QPointF ):
        if self ._connecting is None or self ._connect_line is None :
            return 
        row ,port_idx =self ._connecting 
        box =self ._row_items .get (row )
        if box is None :
            return 
        src =box .pos ()+box .ports ()[port_idx ]if port_idx <len (box .ports ())else box .pos ()
        target =self ._nearest_label_box (scene_pos )
        if target is not self ._connect_snap_box :
            if self ._connect_snap_box is not None :
                self ._connect_snap_box ._snap_highlight =False 
                self ._connect_snap_box .update ()
            self ._connect_snap_box =target 
            if target is not None :
                target ._snap_highlight =True 
                target .update ()
        end_pt =(target .pos ()+QPointF (NODE_W /2 ,NODE_H /2 ))if target is not None else scene_pos 
        self ._connect_line .setPath (_arrow_path (src ,end_pt ,dashed =True ,curve =True ))

    def _finish_connecting (self ,scene_pos :QPointF ):
        if self ._connecting is None :
            self ._cancel_connecting ()
            return 
        row ,port_idx =self ._connecting 
        target =self ._connect_snap_box 
        if target is not None and self .scene is not None :
            label_name =self .scene .nodes [target .row ].label_name 
            if hasattr (self .panel ,"set_node_jump_target"):
                self .panel .set_node_jump_target (row ,label_name ,port_idx )
        self ._cancel_connecting ()

    def _cancel_connecting (self ):
        if self ._connect_line is not None and self ._connect_line .scene ()is not None :
            self .gscene .removeItem (self ._connect_line )
        self ._connect_line =None 
        self ._connecting =None 
        if self ._connect_snap_box is not None :
            try :
                self ._connect_snap_box ._snap_highlight =False 
                self ._connect_snap_box .update ()
            except RuntimeError :

                pass 
        self ._connect_snap_box =None 
        self .view .setCursor (Qt .CursorShape .ArrowCursor )
        try :
            self ._redraw_arrows ()
        except Exception :
            pass 

    def _show_add_node_menu (self ):

        pos =self .btn_add_node .mapToGlobal (self .btn_add_node .rect ().bottomLeft ())
        self ._show_add_node_menu_at (pos )

    def _show_add_node_menu_at (self ,global_pos ):
        menu =QMenu (self )
        for nt in _ADD_NODE_TYPES :
            icon =_TYPE_ICON .get (nt ,"•")
            act =menu .addAction (f"{icon }  {nt .value .upper ()}")
            act .triggered .connect (lambda checked =False ,t =nt :self ._add_node_of_type (t ))
        menu .exec (global_pos )

    def _add_node_of_type (self ,node_type :NodeType ):
        if hasattr (self .panel ,"add_node_of_type"):
            self .panel .add_node_of_type (node_type )


    def align_nodes (self ):

        if not self .scene or not self .scene .nodes :
            return 
        if hasattr (self .panel ,"before_change"):
            try :
                self .panel .before_change .emit (tr ("node_graph.align_nodes"))
            except Exception :
                pass 
        self ._auto_layout_tree ()
        self ._rebuild ()

    def _auto_layout_tree (self ):

        try :
            self ._auto_layout_tree_impl ()
        except Exception :
            import traceback 
            traceback .print_exc ()
            self ._auto_layout_fallback ()

    def _auto_layout_fallback (self ):
        nodes =self .scene .nodes if self .scene else []
        y =20.0 
        for n in nodes :
            n .pos_x =LEFT_X 
            n .pos_y =y 
            y +=NODE_H +GAP_Y 

    @staticmethod 
    def _assign_columns_iterative (segments ,children ):

        column ={}
        counter =[0 ]
        for seg in segments :
            root =seg ["key"]
            if root in column :
                continue 
            stack =[(root ,False )]
            queued ={root }
            while stack :
                key ,processed =stack .pop ()
                if processed :
                    if key in column :
                        continue 
                    kids_resolved =[column [c ]for c in children .get (key ,[])
                    if c !=key and c in column ]
                    if not kids_resolved :
                        column [key ]=counter [0 ]
                        counter [0 ]+=1 
                    else :
                        column [key ]=sum (kids_resolved )/len (kids_resolved )
                    continue 
                if key in column :
                    continue 
                stack .append ((key ,True ))
                for c in children .get (key ,[]):
                    if c ==key or c in column or c in queued :
                        continue 
                    queued .add (c )
                    stack .append ((c ,False ))
        return column 

    def _auto_layout_tree_impl (self ):

        nodes =self .scene .nodes if self .scene else []
        if not nodes :
            return 


        segments =[]
        cur_key ="__root__"
        cur_rows :List [int ]=[]
        for i ,n in enumerate (nodes ):
            if n .node_type ==NodeType .LABEL :
                if cur_rows :
                    segments .append ({"key":cur_key ,"rows":cur_rows })
                cur_key =n .label_name or f"__label_{i }__"
                cur_rows =[]
            cur_rows .append (i )
        segments .append ({"key":cur_key ,"rows":cur_rows })
        seg_index ={seg ["key"]:seg for seg in segments }


        children ={}
        for seg in segments :
            for i in seg ["rows"]:
                n =nodes [i ]
                targets =[]
                if n .node_type ==NodeType .JUMP and n .jump_target :
                    targets .append (n .jump_target )
                elif n .node_type ==NodeType .MENU :
                    for choice in n .normalized_menu_choices ():
                        jump =choice [1 ]
                        if jump :
                            targets .append (jump )
                for t in targets :
                    if t in seg_index and t !=seg ["key"]:
                        lst =children .setdefault (seg ["key"],[])
                        if t not in lst :
                            lst .append (t )


        referenced =set ()
        for kids in children .values ():
            referenced .update (kids )
        roots =[segments [0 ]["key"]]
        for seg in segments [1 :]:
            if seg ["key"]not in referenced and seg ["key"]not in roots :
                roots .append (seg ["key"])

        from collections import deque 
        depth ={}
        dq =deque ()
        for r in roots :
            depth [r ]=0 
            dq .append (r )
        while dq :
            k =dq .popleft ()
            for c in children .get (k ,[]):
                if c not in depth :
                    depth [c ]=depth [k ]+1 
                    dq .append (c )
        for seg in segments :
            depth .setdefault (seg ["key"],0 )


        column =self ._assign_columns_iterative (segments ,children )


        col_w =NODE_W +90 
        level_h =NODE_H +90 
        for seg in segments :
            base_x =LEFT_X +column [seg ["key"]]*col_w 
            y =20.0 +depth [seg ["key"]]*level_h 
            for i in seg ["rows"]:
                nodes [i ].pos_x =base_x 
                nodes [i ].pos_y =y 
                y +=NODE_H +GAP_Y 

    def _on_node_clicked (self ,row :int ):
        self .node_clicked .emit (row )
        self ._current_row =row 
        for r ,box in self ._row_items .items ():
            new_is_current =(r ==row )
            if box .is_current !=new_is_current :
                box .is_current =new_is_current 
                box .update ()
        self .view .setFocus (Qt .FocusReason .MouseFocusReason )
        if self .scene and 0 <=row <len (self .scene .nodes ):
            self .preview_overlay .show_node (self .scene .nodes [row ],self .rm )
            if self .node_editor ._row !=row :
                self .node_editor .set_node (row ,self .scene .nodes [row ])

    def _on_node_double_clicked (self ,row :int ):
        self ._on_node_clicked (row )
        self .node_double_clicked .emit (row )

    def focus_row (self ,row :int ):
        if row in self ._row_items :
            self .view .centerOn (self ._row_items [row ])

    def _selected_rows_list (self )->List [int ]:
        return sorted ({item .row for item in self .gscene .selectedItems ()if isinstance (item ,NodeBoxItem )})

    def _delete_selection (self ):

        if not self .scene :
            return 
        selected =self .gscene .selectedItems ()
        connections =[(it .row ,it .choice_idx )for it in selected if isinstance (it ,ConnectionArrowItem )]
        node_rows =sorted ({it .row for it in selected if isinstance (it ,NodeBoxItem )})
        if not connections and not node_rows :
            return 
        for row ,choice_idx in connections :
            if hasattr (self .panel ,"set_node_jump_target"):
                self .panel .set_node_jump_target (row ,"",choice_idx )
        if node_rows and hasattr (self .panel ,"delete_nodes"):
            self .panel .delete_nodes (node_rows )



    def _on_node_context (self ,row :int ,screen_pos ):
        rows =self ._selected_rows_list ()
        if row not in rows :
            rows =[row ]
        self ._current_row =row 
        menu =QMenu (self )
        act_color =menu .addMenu ("🎨 Цвет метки")
        for c in DEFAULT_COLORS :
            a =act_color .addAction ("   ")
            a .setData (c )
            pm_icon =QColor (c )
            from PyQt6 .QtGui import QIcon ,QPixmap 
            pix =QPixmap (16 ,16 )
            pix .fill (pm_icon )
            a .setIcon (QIcon (pix ))
            a .triggered .connect (lambda checked =False ,col =c ,rows =rows :self .panel .set_nodes_color (rows ,col ))
        act_color .addSeparator ()
        act_clear =act_color .addAction (tr ("mw.ctx.no_label"))
        act_clear .triggered .connect (lambda checked =False ,rows =rows :self .panel .set_nodes_color (rows ,None ))

        menu .addSeparator ()
        act_copy =menu .addAction ("📋 Копировать (Ctrl+C)")
        act_copy .triggered .connect (self .copy_selection )
        act_paste =menu .addAction ("📥 Вставить после (Ctrl+V)")
        act_paste .setEnabled (bool (self ._clipboard )or bool (self ._read_system_clipboard ()))
        act_paste .triggered .connect (lambda checked =False ,row =row :self .paste_after (row ))

        act_dup_branch =menu .addAction ("🔁 Дублировать блок диалога (до label/return/конца)")
        act_dup_branch .triggered .connect (lambda checked =False ,row =row :self .panel .duplicate_branch (row ))

        if len (rows )>=2 :
            menu .addSeparator ()
            act_group =menu .addAction (f"🗂 Сгруппировать выбранные ноды ({len (rows )})")
            act_group .triggered .connect (lambda checked =False ,rows =rows :self ._make_group (rows ))

        menu .exec (screen_pos .toPoint ()if hasattr (screen_pos ,"toPoint")else screen_pos )

    def _group_context_menu (self ,group_id :str ,screen_pos ):
        menu =QMenu (self )
        act_rename =menu .addAction (tr ("mw.ctx.rename_group"))
        act_rename .triggered .connect (lambda :self ._rename_group (group_id ))
        act_recolor =menu .addMenu (tr ("node_graph.border_color_menu"))
        for c in DEFAULT_COLORS :
            a =act_recolor .addAction ("   ")
            a .setData (c )
            from PyQt6 .QtGui import QIcon ,QPixmap 
            pix =QPixmap (16 ,16 )
            pix .fill (QColor (c ))
            a .setIcon (QIcon (pix ))
            a .triggered .connect (lambda checked =False ,col =c :self .panel .recolor_group (group_id ,col ))
        act_ungroup =menu .addAction (tr ("mw.ctx.ungroup"))
        act_ungroup .triggered .connect (lambda :self .panel .ungroup (group_id ))
        menu .exec (screen_pos .toPoint ()if hasattr (screen_pos ,"toPoint")else screen_pos )

    def _rename_group (self ,group_id :str ):
        grp =next ((g for g in (self .scene .groups if self .scene else [])if g .group_id ==group_id ),None )
        if not grp :
            return 
        title ,ok =QInputDialog .getText (self ,tr ("mw.group_title_dialog"),tr ("mw.name_label"),text =grp .title )
        if ok and title .strip ():
            self .panel .rename_group (group_id ,title .strip ())

    def _toggle_group (self ,group_id :str ):
        self .panel .toggle_group_collapsed (group_id )

    def _make_group (self ,rows :List [int ]):
        if not self .scene :
            return 

        if rows !=list (range (rows [0 ],rows [-1 ]+1 )):
            from PyQt6 .QtWidgets import QMessageBox 
            QMessageBox .warning (self ,tr ("mw.cannot_group_title"),
            tr ("mw.cannot_group_text"))
            return 
        title ,ok =QInputDialog .getText (self ,tr ("mw.new_group_title"),tr ("mw.new_group_name_label"),text =tr ("mw.new_group_default"))
        if ok and title .strip ():
            self .panel .create_group (rows ,title .strip ())



    def copy_selection (self ):
        if not self .scene :
            return 
        rows =self ._selected_rows_list ()
        if not rows and self ._current_row >=0 :
            rows =[self ._current_row ]
        if not rows :
            return 
        from core .project_manager import node_to_dict 
        nodes_data =[node_to_dict (self .scene .nodes [r ])for r in rows if 0 <=r <len (self .scene .nodes )]
        self ._clipboard =nodes_data 
        try :
            from PyQt6 .QtWidgets import QApplication 
            QApplication .clipboard ().setText (json .dumps ({"renpy_editor_nodes":nodes_data },ensure_ascii =False ))
        except Exception :
            pass 

    def paste_after (self ,row :int ):
        clip =self ._read_system_clipboard ()or self ._clipboard 
        if not clip :
            return 
        self .panel .paste_nodes_after (row ,clip )

    def _read_system_clipboard (self ):
        try :
            from PyQt6 .QtWidgets import QApplication 
            txt =QApplication .clipboard ().text ()
            data =json .loads (txt )
            nodes =data .get ("renpy_editor_nodes")
            if isinstance (nodes ,list )and nodes :
                return nodes 
        except Exception :
            pass 
        return None 



    def _on_search (self ,text :str ):
        text =text .strip ().lower ()
        self ._search_matches =[]
        self ._search_pos =-1 
        if text and self .scene :
            for r ,n in enumerate (self .scene .nodes ):
                haystack =" ".join (filter (None ,[
                n .text ,n .character_var ,n .sprite_var ,n .label_name ,
                n .jump_target ,n .bg_var ,n .cg_var ,n .menu_prompt ,
                ])).lower ()
                if text in haystack :
                    self ._search_matches .append (r )
        self .search_status .setText (f"{len (self ._search_matches )} совп."if text else "")
        if self ._search_matches :
            self ._search_pos =0 
            self ._goto_search_match ()
        else :
            self ._rebuild ()

    def _search_next (self ):
        if not self ._search_matches :
            return 
        self ._search_pos =(self ._search_pos +1 )%len (self ._search_matches )
        self ._goto_search_match ()

    def _goto_search_match (self ):
        row =self ._search_matches [self ._search_pos ]
        self .node_clicked .emit (row )
        self ._current_row =row 
        self ._rebuild ()
        self .focus_row (row )
        self .search_status .setText (f"{self ._search_pos +1 }/{len (self ._search_matches )}")


class GraphWindow (QWidget ):

    closed =pyqtSignal ()

    def __init__ (self ,canvas :"NodeGraphCanvas",parent =None ):
        flags =(Qt .WindowType .Window |Qt .WindowType .WindowTitleHint |
        Qt .WindowType .WindowSystemMenuHint |Qt .WindowType .WindowMinMaxButtonsHint |
        Qt .WindowType .WindowCloseButtonHint )
        super ().__init__ (parent ,flags )
        self .canvas =canvas 
        self .setWindowTitle (tr ("node_graph.graph_mode"))
        outer =QVBoxLayout (self )
        outer .setContentsMargins (0 ,0 ,0 ,0 )
        outer .setSpacing (0 )

        top_bar =QHBoxLayout ()
        top_bar .setContentsMargins (10 ,8 ,10 ,4 )
        title =QLabel ("🕸 "+tr ("node_graph.graph_mode"))
        title .setObjectName ("hint_text_bright")
        top_bar .addWidget (title )
        hint =QLabel (tr ("node_graph.double_click_hint"))
        top_bar .addWidget (hint )
        top_bar .addStretch (1 )
        self .btn_close =QToolButton ()
        self .btn_close .setText ("✕  Esc")
        self .btn_close .setObjectName ("btn_secondary")
        self .btn_close .clicked .connect (self .close )
        top_bar .addWidget (self .btn_close )
        outer .addLayout (top_bar )
        outer .addWidget (canvas ,1 )

    def showEvent (self ,e ):
        super ().showEvent (e )
        if self .canvas .scene is not None :
            self .canvas .set_scene (self .canvas .scene ,self .canvas ._current_row )

    def keyPressEvent (self ,e ):
        if e .key ()==Qt .Key .Key_Escape :
            self .close ()
            return 
        if e .key ()==Qt .Key .Key_F11 :


            if self .isMaximized ():
                self .showNormal ()
            else :
                self .showMaximized ()
            return 
        super ().keyPressEvent (e )

    def closeEvent (self ,e ):

        if getattr (self .canvas ,"node_editor",None )is not None :
            self .canvas .node_editor .flush ()
        self .canvas .setParent (None )
        self .closed .emit ()
        super ().closeEvent (e )

