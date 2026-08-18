

from dataclasses import dataclass ,field as dc_field 
from typing import Dict ,List ,Optional ,Tuple 

from PyQt6 .QtWidgets import (
QWidget ,QVBoxLayout ,QHBoxLayout ,QLabel ,QPushButton ,QCheckBox ,
QDoubleSpinBox ,QComboBox ,QFrame ,QSizePolicy ,QAbstractButton 
)
from PyQt6 .QtCore import Qt ,QRectF ,pyqtSignal ,QSize ,QPropertyAnimation ,QEasingCurve ,pyqtProperty 
from PyQt6 .QtGui import QPainter ,QColor ,QFont ,QPen ,QMouseEvent 


class ToggleSwitch (QAbstractButton ):


    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .setCheckable (True )
        self .setFixedSize (40 ,22 )
        self .setCursor (Qt .CursorShape .PointingHandCursor )
        self ._pos =0.0 
        self ._anim =QPropertyAnimation (self ,b"knob_pos",self )
        self ._anim .setDuration (120 )
        self ._anim .setEasingCurve (QEasingCurve .Type .OutCubic )
        self .toggled .connect (self ._animate )

    def _animate (self ,checked :bool ):
        self ._anim .stop ()
        self ._anim .setStartValue (self ._pos )
        self ._anim .setEndValue (1.0 if checked else 0.0 )
        self ._anim .start ()

    def setChecked (self ,checked :bool ):
        super ().setChecked (checked )





        if self .signalsBlocked ():
            self ._anim .stop ()
            self ._pos =1.0 if checked else 0.0 
            self .update ()

    def get_knob_pos (self )->float :
        return self ._pos 

    def set_knob_pos (self ,v :float ):
        self ._pos =v 
        self .update ()

    knob_pos =pyqtProperty (float ,get_knob_pos ,set_knob_pos )

    def sizeHint (self )->QSize :
        return QSize (40 ,22 )

    def paintEvent (self ,event ):
        p =QPainter (self )
        p .setRenderHint (QPainter .RenderHint .Antialiasing )
        r =self .rect ().adjusted (1 ,1 ,-1 ,-1 )
        track_on =QColor ("#ff8c3d")
        track_off =QColor ("#3a3f4a")
        track =QColor (
        int (track_off .red ()+(track_on .red ()-track_off .red ())*self ._pos ),
        int (track_off .green ()+(track_on .green ()-track_off .green ())*self ._pos ),
        int (track_off .blue ()+(track_on .blue ()-track_off .blue ())*self ._pos ),
        )
        p .setPen (Qt .PenStyle .NoPen )
        p .setBrush (track )
        p .drawRoundedRect (QRectF (r ),r .height ()/2 ,r .height ()/2 )
        knob_d =r .height ()-4 
        x =r .left ()+2 +(r .width ()-knob_d -4 )*self ._pos 
        p .setBrush (QColor ("#ffffff"))
        p .drawEllipse (QRectF (x ,r .top ()+2 ,knob_d ,knob_d ))


class ValueSlider (QWidget ):


    valueChanged =pyqtSignal (float )

    def __init__ (self ,lo :float ,hi :float ,step :float ,decimals :int =3 ,parent =None ):
        super ().__init__ (parent )
        self .lo =lo 
        self .hi =hi 
        self .step =step 
        self .decimals =decimals 
        self ._value =lo 
        self ._dragging =False 
        self ._editing =False 
        self ._edit_text =""
        self .setFixedHeight (40 )
        self .setMinimumWidth (320 )
        self .setCursor (Qt .CursorShape .PointingHandCursor )
        self .setFocusPolicy (Qt .FocusPolicy .ClickFocus )

    def value (self )->float :
        return self ._value 

    def setValue (self ,v :float ):
        v =max (self .lo ,min (self .hi ,v ))
        if abs (v -self ._value )>1e-9 :
            self ._value =v 
            self .update ()
            self .valueChanged .emit (self ._value )
        else :
            self ._value =v 
            self .update ()

    def _frac (self )->float :
        span =(self .hi -self .lo )or 1.0 
        return (self ._value -self .lo )/span 

    def _x_to_value (self ,x :int )->float :
        pad =8 
        w =max (self .width ()-2 *pad ,1 )
        frac =max (0.0 ,min (1.0 ,(x -pad )/w ))
        raw =self .lo +frac *(self .hi -self .lo )
        if self .step :
            raw =round (raw /self .step )*self .step 
        return max (self .lo ,min (self .hi ,raw ))

    def _fmt_value (self )->str :
        return f"{self ._value :.{self .decimals }f}".rstrip ('0').rstrip ('.')if self .decimals else f"{int (self ._value )}"

    def mousePressEvent (self ,event :QMouseEvent ):
        if not self .isEnabled ():
            return 
        self ._dragging =True 
        self .setValue (self ._x_to_value (int (event .position ().x ())))

    def mouseMoveEvent (self ,event :QMouseEvent ):
        if self ._dragging and self .isEnabled ():
            self .setValue (self ._x_to_value (int (event .position ().x ())))

    def mouseReleaseEvent (self ,event :QMouseEvent ):
        self ._dragging =False 

    def mouseDoubleClickEvent (self ,event :QMouseEvent ):
        if not self .isEnabled ():
            return 
        self ._editing =True 
        self ._edit_text =self ._fmt_value ()
        self .setFocus ()
        self .update ()

    def keyPressEvent (self ,event ):
        if not self ._editing :
            return super ().keyPressEvent (event )
        key =event .key ()
        if key in (Qt .Key .Key_Return ,Qt .Key .Key_Enter ):
            try :
                self .setValue (float (self ._edit_text ))
            except ValueError :
                pass 
            self ._editing =False 
            self .update ()
        elif key ==Qt .Key .Key_Escape :
            self ._editing =False 
            self .update ()
        elif key ==Qt .Key .Key_Backspace :
            self ._edit_text =self ._edit_text [:-1 ]
            self .update ()
        else :
            ch =event .text ()
            if ch and (ch .isdigit ()or ch in "-."):
                self ._edit_text +=ch 
                self .update ()

    def focusOutEvent (self ,event ):
        if self ._editing :
            try :
                self .setValue (float (self ._edit_text ))
            except ValueError :
                pass 
            self ._editing =False 
            self .update ()
        super ().focusOutEvent (event )

    def paintEvent (self ,event ):
        p =QPainter (self )
        p .setRenderHint (QPainter .RenderHint .Antialiasing )
        pad =10 
        bar_h =10 
        bar_y =self .height ()//2 -bar_h //2 
        track_rect =QRectF (pad ,bar_y ,self .width ()-2 *pad ,bar_h )
        p .setPen (Qt .PenStyle .NoPen )
        p .setBrush (QColor ("#3a3f4a")if self .isEnabled ()else QColor ("#2a2d33"))
        p .drawRoundedRect (track_rect ,bar_h /2 ,bar_h /2 )

        frac =max (0.0 ,min (1.0 ,self ._frac ()))
        fill_w =track_rect .width ()*frac 
        fill_rect =QRectF (track_rect .left (),track_rect .top (),fill_w ,bar_h )
        p .setBrush (QColor ("#d97a2b")if self .isEnabled ()else QColor ("#4a4033"))
        p .drawRoundedRect (fill_rect ,bar_h /2 ,bar_h /2 )

        knob_x =track_rect .left ()+fill_w 
        knob_r =11 
        p .setBrush (QColor ("#ffb84d")if self .isEnabled ()else QColor ("#6b6b6b"))
        p .setPen (QPen (QColor ("#ffffff"),1.5 ))
        p .drawEllipse (QRectF (knob_x -knob_r ,bar_y +bar_h /2 -knob_r ,knob_r *2 ,knob_r *2 ))

        p .setPen (QPen (QColor ("#e8e8e8")if self .isEnabled ()else QColor ("#767676")))
        p .setFont (QFont ("Segoe UI",9 ))
        text =self ._edit_text if self ._editing else self ._fmt_value ()
        p .drawText (self .rect ().adjusted (0 ,0 ,-pad ,0 ),Qt .AlignmentFlag .AlignRight |Qt .AlignmentFlag .AlignVCenter ,text )

from core import atl as atl_engine 
from core .i18n import tr 





PROP_DEFS :List [Tuple [str ,str ,float ,float ,float ,float ]]=[

("xalign","atl_steps.prop_xalign",0.5 ,-3.0 ,3.0 ,0.01 ),
("yalign","atl_steps.prop_yalign",1.0 ,-3.0 ,3.0 ,0.01 ),
("zoom","atl_steps.prop_zoom",1.0 ,0.01 ,5.0 ,0.01 ),
("rotate","atl_steps.prop_rotate",0.0 ,-360.0 ,360.0 ,1.0 ),
("alpha","atl_steps.prop_alpha",1.0 ,0.0 ,1.0 ,0.01 ),
]
PROP_NAMES =[p [0 ]for p in PROP_DEFS ]
PROP_DEFAULTS ={p [0 ]:p [2 ]for p in PROP_DEFS }

WARPERS =["linear","ease","easein","easeout"]


def _fmt (v :float )->str :
    s =f"{v :.3f}".rstrip ('0').rstrip ('.')
    return s if s not in ("","-0")else "0"


@dataclass 
class AtlStep :
    duration :float =1.0 
    warper :str ="linear"
    enabled :Dict [str ,bool ]=dc_field (default_factory =dict )
    values :Dict [str ,float ]=dc_field (default_factory =lambda :dict (PROP_DEFAULTS ))


def new_initial_step (base_xalign :float ,base_yalign :float ,base_zoom :float )->AtlStep :
    st =AtlStep (duration =0.0 ,warper ="linear")
    st .values .update ({"xalign":base_xalign ,"yalign":base_yalign ,"zoom":base_zoom })
    return st 






def steps_to_atl_text (steps :List [AtlStep ],repeat :bool ,repeat_count :Optional [int ]=None )->str :
    if not steps :
        return ""
    lines :List [str ]=[]
    step0 =steps [0 ]
    enabled0 ={k :step0 .values [k ]for k in PROP_NAMES if step0 .enabled .get (k )}
    if enabled0 :
        lines .append (" ".join (f"{k } {_fmt (v )}"for k ,v in enabled0 .items ()))
    for st in steps [1 :]:
        enabled ={k :st .values [k ]for k in PROP_NAMES if st .enabled .get (k )}
        if not enabled :
            lines .append (f"pause {_fmt (st .duration )}")
            continue 
        props_str =" ".join (f"{k } {_fmt (v )}"for k ,v in enabled .items ())
        lines .append (f"{st .warper } {_fmt (st .duration )} {props_str }")
    if repeat :
        lines .append (f"repeat {int (repeat_count )}"if repeat_count else "repeat")
    return "\n".join (lines )


def steps_from_atl_text (text :str ,base_xalign :float ,base_yalign :float ,
base_zoom :float )->Tuple [List [AtlStep ],bool ,Optional [int ],bool ]:

    steps =[new_initial_step (base_xalign ,base_yalign ,base_zoom )]
    repeat =False 
    repeat_count =None 
    lossy =False 
    seen_first_move =False 
    try :
        block =atl_engine .parse_atl_text (text )
    except Exception :
        return steps ,False ,None ,bool (text and text .strip ())

    for stmt in block .statements :
        if isinstance (stmt ,atl_engine .ATLSet ):
            known ={k :v for k ,v in stmt .props .items ()if k in PROP_NAMES and isinstance (v ,(int ,float ))}
            unknown =set (stmt .props )-set (known )
            if unknown :
                lossy =True 
            if not seen_first_move :
                steps [0 ].values .update (known )
                for k in known :
                    steps [0 ].enabled [k ]=True 
            else :
                lossy =True 
        elif isinstance (stmt ,atl_engine .ATLInterpolate ):
            seen_first_move =True 
            known ={k :v for k ,v in stmt .props .items ()if k in PROP_NAMES and isinstance (v ,(int ,float ))}
            unknown =set (stmt .props )-set (known )
            if unknown :
                lossy =True 
            new_step =AtlStep (duration =stmt .duration ,
            warper =stmt .warper if stmt .warper in WARPERS else "linear",
            values =dict (steps [-1 ].values ))
            new_step .values .update (known )
            for k in known :
                new_step .enabled [k ]=True 
            steps .append (new_step )
        elif isinstance (stmt ,atl_engine .ATLPause ):
            seen_first_move =True 
            steps .append (AtlStep (duration =stmt .duration ,warper ="linear",
            values =dict (steps [-1 ].values )))
        elif isinstance (stmt ,atl_engine .ATLRepeat ):
            repeat =True 
            repeat_count =stmt .count 
        else :
            lossy =True 
    return steps ,repeat ,repeat_count ,lossy 






class _StepTimeline (QWidget ):


    step_selected =pyqtSignal (int )
    duration_changed =pyqtSignal (int ,float )

    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .setFixedHeight (46 )
        self .setMinimumWidth (360 )
        self ._steps :List [AtlStep ]=[]
        self ._selected =0 
        self ._dragging :Optional [int ]=None 
        self ._drag_start_x =0 
        self ._drag_start_dur =0.0 

    def set_steps (self ,steps :List [AtlStep ],selected :int ):
        self ._steps =steps 
        self ._selected =selected 
        self .update ()

    def _total (self )->float :
        return max (sum (s .duration for s in self ._steps [1 :]),0.001 )

    def _marker_x (self ,idx :int )->int :
        total =self ._total ()
        t =sum (s .duration for s in self ._steps [1 :idx +1 ])
        pad =14 
        w =max (self .width ()-2 *pad ,10 )
        return pad +int (w *(t /total ))if len (self ._steps )>1 else pad 

    def paintEvent (self ,event ):
        p =QPainter (self )
        p .setRenderHint (QPainter .RenderHint .Antialiasing )
        bar_y =26 
        pad =14 
        p .setPen (Qt .PenStyle .NoPen )
        p .setBrush (QColor ("#3a3f4a"))
        p .drawRoundedRect (pad ,bar_y -3 ,self .width ()-2 *pad ,6 ,3 ,3 )
        p .setBrush (QColor ("#d97a2b"))
        p .drawRoundedRect (pad ,bar_y -3 ,self .width ()-2 *pad ,6 ,3 ,3 )

        for i in range (len (self ._steps )):
            x =self ._marker_x (i )
            selected =i ==self ._selected 
            color =QColor ("#ffb84d")if selected else QColor ("#8f7bd6")
            p .setBrush (color )
            p .setPen (QPen (QColor ("#ffffff"),1 ))
            r =7 if selected else 6 
            pts =[
            (x ,bar_y -r ),(x +r ,bar_y ),(x ,bar_y +r ),(x -r ,bar_y ),
            ]
            from PyQt6 .QtGui import QPolygonF 
            from PyQt6 .QtCore import QPointF 
            poly =QPolygonF ([QPointF (px ,py )for px ,py in pts ])
            p .drawPolygon (poly )
            p .setPen (QPen (QColor ("#cfcfcf")))
            p .setFont (QFont ("Segoe UI",8 ))
            p .drawText (x -8 ,bar_y +20 ,str (i ))

    def _hit_test (self ,x :int )->Optional [int ]:
        best ,best_d =None ,999 
        for i in range (len (self ._steps )):
            d =abs (self ._marker_x (i )-x )
            if d <best_d :
                best ,best_d =i ,d 
        return best if best_d <=10 else None 

    def mousePressEvent (self ,event :QMouseEvent ):
        idx =self ._hit_test (int (event .position ().x ()))
        if idx is not None :
            self ._selected =idx 
            self .step_selected .emit (idx )
            if idx >0 :
                self ._dragging =idx 
                self ._drag_start_x =int (event .position ().x ())
                self ._drag_start_dur =self ._steps [idx ].duration 
            self .update ()

    def mouseMoveEvent (self ,event :QMouseEvent ):
        if self ._dragging is None :
            return 
        pad =14 
        w =max (self .width ()-2 *pad ,10 )
        total =self ._total ()
        dx =int (event .position ().x ())-self ._drag_start_x 
        delta_t =(dx /w )*total 
        new_dur =max (0.05 ,self ._drag_start_dur +delta_t )
        self ._steps [self ._dragging ].duration =new_dur 
        self .duration_changed .emit (self ._dragging ,new_dur )
        self .update ()

    def mouseReleaseEvent (self ,event :QMouseEvent ):
        self ._dragging =None 






class AtlStepsPanel (QWidget ):


    changed =pyqtSignal ()

    def __init__ (self ,parent =None ):
        super ().__init__ (parent )
        self .steps :List [AtlStep ]=[new_initial_step (0.5 ,1.0 ,1.0 )]
        self .selected =0 
        self .repeat =False 
        self .repeat_count :Optional [int ]=None 
        self ._suspend =False 

        outer =QVBoxLayout (self )
        outer .setContentsMargins (0 ,0 ,0 ,0 )

        self .time_label =QLabel ("")
        self .time_label .setObjectName ("hint_text")
        outer .addWidget (self .time_label )

        self .timeline =_StepTimeline ()
        self .timeline .step_selected .connect (self ._on_step_selected )
        self .timeline .duration_changed .connect (self ._on_duration_dragged )
        outer .addWidget (self .timeline )

        step_row =QHBoxLayout ()
        self .step_label =QLabel ("")
        step_row .addWidget (self .step_label )
        step_row .addStretch ()
        self .warper_combo =QComboBox ()
        self .warper_combo .addItems (WARPERS )
        self .warper_combo .currentTextChanged .connect (self ._on_warper_changed )
        step_row .addWidget (QLabel (tr ("atl_steps.warper_label")))
        step_row .addWidget (self .warper_combo )
        self .duration_spin =QDoubleSpinBox ()
        self .duration_spin .setRange (0.05 ,60.0 )
        self .duration_spin .setSingleStep (0.1 )
        self .duration_spin .setDecimals (2 )
        self .duration_spin .valueChanged .connect (self ._on_duration_spin_changed )
        step_row .addWidget (QLabel (tr ("atl_steps.duration_label")))
        step_row .addWidget (self .duration_spin )
        outer .addLayout (step_row )

        sep =QFrame ()
        sep .setFrameShape (QFrame .Shape .HLine )
        outer .addWidget (sep )

        self ._prop_rows ={}
        for name ,key ,default ,lo ,hi ,step in PROP_DEFS :
            row =QHBoxLayout ()
            label =QLabel (tr (key ))
            label .setMinimumWidth (210 )
            cb =ToggleSwitch ()
            slider =ValueSlider (lo ,hi ,step ,decimals =(3 if step <1 else 0 ))
            slider .setValue (default )
            box =QDoubleSpinBox ()
            box .setMinimumWidth (110 )
            box .setRange (lo ,hi )
            box .setSingleStep (step )
            box .setDecimals (3 if step <1 else 0 )
            box .setValue (default )
            cb .toggled .connect (lambda checked ,n =name :self ._on_prop_toggled (n ,checked ))
            slider .valueChanged .connect (lambda v ,n =name :self ._on_slider_value_changed (n ,v ))
            box .valueChanged .connect (lambda v ,n =name :self ._on_box_value_changed (n ,v ))
            row .addWidget (label )
            row .addWidget (cb )
            row .addSpacing (16 )
            row .addWidget (slider ,1 )
            row .addSpacing (10 )
            row .addWidget (box )
            outer .addLayout (row )
            self ._prop_rows [name ]=(cb ,slider ,box )

        btn_row =QHBoxLayout ()
        self .add_btn =QPushButton (tr ("atl_steps.add_step"))
        self .add_btn .clicked .connect (self ._add_step )
        btn_row .addWidget (self .add_btn )
        self .remove_btn =QPushButton (tr ("atl_steps.remove_step"))
        self .remove_btn .clicked .connect (self ._remove_step )
        btn_row .addWidget (self .remove_btn )
        btn_row .addStretch ()
        btn_row .addWidget (QLabel (tr ("atl_steps.repeat_forever")))
        self .repeat_cb =ToggleSwitch ()
        self .repeat_cb .toggled .connect (self ._on_repeat_toggled )
        btn_row .addWidget (self .repeat_cb )
        outer .addLayout (btn_row )
        outer .addStretch ()

        self ._refresh_all ()





    def set_base (self ,base_xalign :float ,base_yalign :float ,base_zoom :float ):

        if len (self .steps )==1 and not any (self .steps [0 ].enabled .values ()):
            self .steps [0 ]=new_initial_step (base_xalign ,base_yalign ,base_zoom )
            self ._refresh_all ()

    def load_from_text (self ,text :str ,base_xalign :float ,base_yalign :float ,
    base_zoom :float )->bool :

        steps ,repeat ,repeat_count ,lossy =atl_steps_from_text_safe (
        text ,base_xalign ,base_yalign ,base_zoom )
        self .steps =steps 
        self .repeat =repeat 
        self .repeat_count =repeat_count 
        self .selected =0 
        self ._refresh_all ()
        return lossy 

    def to_atl_text (self )->str :
        return steps_to_atl_text (self .steps ,self .repeat ,self .repeat_count )





    def _emit_changed (self ):
        if not self ._suspend :
            self .changed .emit ()

    def _refresh_all (self ):
        self ._suspend =True 
        self .timeline .set_steps (self .steps ,self .selected )
        st =self .steps [self .selected ]
        is_first =self .selected ==0 
        self .step_label .setText (tr ("atl_steps.step_n",n =self .selected ))
        self .warper_combo .setVisible (not is_first )
        self .duration_spin .setVisible (not is_first )
        self .duration_spin .blockSignals (True )
        self .duration_spin .setValue (st .duration if not is_first else 0.0 )
        self .duration_spin .blockSignals (False )
        self .warper_combo .blockSignals (True )
        idx =WARPERS .index (st .warper )if st .warper in WARPERS else 0 
        self .warper_combo .setCurrentIndex (idx )
        self .warper_combo .blockSignals (False )
        for name ,(cb ,slider ,box )in self ._prop_rows .items ():
            cb .blockSignals (True )
            slider .blockSignals (True )
            box .blockSignals (True )
            cb .setChecked (bool (st .enabled .get (name )))
            v =st .values .get (name ,PROP_DEFAULTS [name ])
            slider .setValue (v )
            box .setValue (v )
            slider .setEnabled (cb .isChecked ())
            box .setEnabled (cb .isChecked ())
            cb .blockSignals (False )
            slider .blockSignals (False )
            box .blockSignals (False )
        total =sum (s .duration for s in self .steps [1 :])
        self .time_label .setText (tr ("atl_steps.timeline_total",total =f"{total :.2f}"))
        self .remove_btn .setEnabled (len (self .steps )>1 and self .selected >0 )
        self .repeat_cb .blockSignals (True )
        self .repeat_cb .setChecked (self .repeat )
        self .repeat_cb .blockSignals (False )
        self ._suspend =False 

    def _on_step_selected (self ,idx :int ):
        self .selected =idx 
        self ._refresh_all ()

    def _on_duration_dragged (self ,idx :int ,dur :float ):
        self .time_label .setText (tr ("atl_steps.timeline_total",
        total =f"{sum (s .duration for s in self .steps [1 :]):.2f}"))
        if idx ==self .selected :
            self .duration_spin .blockSignals (True )
            self .duration_spin .setValue (dur )
            self .duration_spin .blockSignals (False )
        self ._emit_changed ()

    def _on_duration_spin_changed (self ,v :float ):
        if self .selected >0 :
            self .steps [self .selected ].duration =v 
            self .timeline .update ()
            self ._emit_changed ()

    def _on_warper_changed (self ,text :str ):
        if self .selected >0 and text :
            self .steps [self .selected ].warper =text 
            self ._emit_changed ()

    def _on_prop_toggled (self ,name :str ,checked :bool ):
        st =self .steps [self .selected ]
        st .enabled [name ]=checked 
        cb ,slider ,box =self ._prop_rows [name ]
        slider .setEnabled (checked )
        box .setEnabled (checked )
        self ._emit_changed ()

    def _on_slider_value_changed (self ,name :str ,value :float ):
        _ ,_ ,box =self ._prop_rows [name ]
        box .blockSignals (True )
        box .setValue (value )
        box .blockSignals (False )
        self ._on_prop_value_changed (name ,value )

    def _on_box_value_changed (self ,name :str ,value :float ):
        _ ,slider ,_ =self ._prop_rows [name ]
        slider .blockSignals (True )
        slider .setValue (value )
        slider .blockSignals (False )
        self ._on_prop_value_changed (name ,value )

    def _on_prop_value_changed (self ,name :str ,value :float ):
        st =self .steps [self .selected ]
        st .values [name ]=value 
        self ._emit_changed ()

    def _add_step (self ):
        last_idx =len (self .steps )-1 
        last =self .steps [last_idx ]





        new_step =AtlStep (duration =1.0 ,warper =last .warper if last_idx >0 else "linear",
        enabled =dict (last .enabled ),
        values =dict (last .values ))
        self .steps .append (new_step )
        self .selected =len (self .steps )-1 
        self ._refresh_all ()
        self ._emit_changed ()

    def _remove_step (self ):
        if len (self .steps )>1 and self .selected >0 :
            del self .steps [self .selected ]
            self .selected =max (0 ,self .selected -1 )
            self ._refresh_all ()
            self ._emit_changed ()

    def _on_repeat_toggled (self ,checked :bool ):
        self .repeat =checked 
        self ._emit_changed ()


def atl_steps_from_text_safe (text :str ,base_xalign :float ,base_yalign :float ,
base_zoom :float ):
    return steps_from_atl_text (text ,base_xalign ,base_yalign ,base_zoom )
