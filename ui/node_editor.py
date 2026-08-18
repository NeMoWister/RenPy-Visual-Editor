
import os 
import shutil 
from PyQt6 .QtWidgets import (
QWidget ,QVBoxLayout ,QHBoxLayout ,QLabel ,QLineEdit ,
QTextEdit ,QComboBox ,QPushButton ,QCheckBox ,QDoubleSpinBox ,
QGroupBox ,QScrollArea ,QFrame ,QSpinBox 
)
from PyQt6 .QtCore import Qt ,pyqtSignal ,QTimer 
from core .models import SceneNode ,NodeType ,ANCHOR_POSITIONS ,NAMED_SPRITE_POSITIONS ,nearest_anchor_name 
from core .i18n import tr ,plural 
from core .renpy_text_tags import strip_tags 
from core .spellcheck import check_text 
from ui .resource_carousel import ResourceCarousel ,FolderResourceCarousel ,CharacterGroupPicker ,CompositeSpriteCarousel 
from ui .audio_preview import get_player as get_audio_player 
from ui .waveform_widget import WaveformWidget 
from ui .theme import theme_manager ,fade_in_widget 
from ui .atl_editor_dialog import AtlEditorDialog 
from ui .pixmap_cache import get_pixmap ,get_composite 
from ui .transition_editor_dialog import TransitionEditorDialog 


TRANSITIONS =["","dissolve","fade","fade2","fade3","flash","pixellate",
"blinds","squares","wipeleft","wiperight","wipeup",
"wipedown","vpunch","hpunch","dspr"]

def _node_types ():
    return [
    ("dialogue",tr ("node_type.dialogue")),
    ("narration",tr ("node_type.narration")),
    ("scene",tr ("node_type.scene")),
    ("show_bg",tr ("node_type.show_bg")),
    ("show_cg",tr ("node_type.show_cg")),
    ("show_sprite",tr ("node_type.show_sprite")),
    ("hide_sprite",tr ("node_type.hide_sprite")),
    ("window",tr ("node_type.window")),
    ("with_transition",tr ("node_type.with_transition")),
    ("nvl_mode",tr ("node_type.nvl_mode")),
    ("play_music",tr ("node_type.play_music")),
    ("stop_music",tr ("node_type.stop_music")),
    ("play_sound",tr ("node_type.play_sound")),
    ("play_ambience",tr ("node_type.play_ambience")),
    ("stop_ambience",tr ("node_type.stop_ambience")),
    ("label",tr ("node_type.label")),
    ("jump",tr ("node_type.jump")),
    ("menu",tr ("node_type.menu")),
    ("pause",tr ("node_type.pause")),
    ("return_",tr ("node_type.return_")),
    ("python",tr ("node_type.python")),
    ("raw",tr ("node_type.raw")),
    ("custom",tr ("node_type.custom")),
    ]


NODE_TYPES =_node_types 


def _label (text :str )->QLabel :
    lbl =QLabel (text )
    lbl .setObjectName ("hint_text")
    return lbl 


def _field (placeholder :str ="")->QLineEdit :
    f =QLineEdit ()
    f .setPlaceholderText (placeholder )
    t =theme_manager .tokens ()
    f .setStyleSheet (f"""
        QLineEdit {{
            background:{t .base_field }; color:{t .text }; border:1px solid {t .glass_border_s };
            border-radius:4px; padding:4px 6px; font-size:12px;
        }}
        QLineEdit:focus {{ border-color:{t .accent_1 }; }}
    """)
    return f 


def _style_combo (cb :QComboBox ):
    t =theme_manager .tokens ()
    cb .setStyleSheet (f"""
        QComboBox {{
            background:{t .base_field }; color:{t .text }; border:1px solid {t .glass_border_s };
            border-radius:4px; padding:4px 6px; font-size:12px;
        }}
        QComboBox:focus {{ border-color:{t .accent_1 }; }}
        QComboBox QAbstractItemView {{
            background:{t .dropdown_bg }; color:{t .text }; selection-background-color:{t .accent_1 };
        }}
    """)


def _combo (items :list )->QComboBox :
    cb =QComboBox ()
    cb .addItems (items )
    _style_combo (cb )
    return cb 


def _transition_combo (current_value :str ="")->QComboBox :

    cb =QComboBox ()
    cb .addItems (TRANSITIONS )
    cb .setEditable (True )
    t =theme_manager .tokens ()
    cb .setStyleSheet (f"""
        QComboBox {{
            background:{t .base_field }; color:{t .text }; border:1px solid {t .glass_border_s };
            border-radius:4px; padding:4px 28px 4px 6px; font-size:12px;
        }}
        QComboBox:focus {{ border-color:{t .accent_1 }; }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 22px;
            border-left: 1px solid {t .glass_border_s };
            border-radius: 0 4px 4px 0;
            background: {t .button_bg };
        }}
        QComboBox::down-arrow {{
            width: 10px; height: 10px;
            border-left: 2px solid {t .text_muted };
            border-bottom: 2px solid {t .text_muted };
            transform: rotate(-45deg);
        }}
        QComboBox QAbstractItemView {{
            background:{t .dropdown_bg }; color:{t .text };
            selection-background-color:{t .accent_1 };
            border: 1px solid {t .glass_border_s };
        }}
        QComboBox QLineEdit {{
            background:{t .dropdown_bg }; color:{t .text };
            border: none; padding: 0;
        }}
    """)
    if current_value and current_value not in TRANSITIONS :
        cb .addItem (current_value )
    cb .setCurrentText (current_value )
    return cb 


CALL_VS_JUMP_TOOLTIP =tr ("ne.call_vs_jump_tooltip")


class MenuChoiceRow (QFrame ):
    removed =pyqtSignal ()
    changed =pyqtSignal ()
    open_branch =pyqtSignal ()

    def __init__ (self ,text ="",jump ="",use_call =False ,raw_body ="",nodes =None ):
        super ().__init__ ()





        self .branch_nodes =nodes if nodes is not None else []
        self .setObjectName ("surface_frame")
        self .setStyleSheet ("padding:2px;")
        outer =QVBoxLayout (self )
        outer .setContentsMargins (4 ,2 ,4 ,2 )
        outer .setSpacing (2 )

        row =QHBoxLayout ()
        self .text_edit =_field (tr ("ne.choice_text_placeholder"))
        self .text_edit .setText (text )
        self .text_edit .textChanged .connect (lambda *_ :self .changed .emit ())
        self .jump_edit =_field (tr ("ne.choice_label_placeholder"))
        self .jump_edit .setFixedWidth (150 )
        self .jump_edit .setText (jump )
        self .jump_edit .textChanged .connect (lambda *_ :self .changed .emit ())
        btn =QPushButton ("✕")
        btn .setFixedSize (24 ,24 )
        btn .setObjectName ("btn_danger")
        btn .clicked .connect (self .removed .emit )
        row .addWidget (self .text_edit )
        row .addWidget (_label ("→"))
        row .addWidget (self .jump_edit )
        row .addWidget (btn )
        outer .addLayout (row )

        call_row =QHBoxLayout ()
        call_row .setContentsMargins (0 ,0 ,0 ,0 )
        self .call_check =QCheckBox (tr ("ne.call_checkbox"))
        self .call_check .setChecked (bool (use_call ))
        self .call_check .setObjectName ("hint_text")
        self .call_check .setStyleSheet ("font-size:11px;")
        self .call_check .setToolTip (CALL_VS_JUMP_TOOLTIP )
        self .call_check .stateChanged .connect (lambda *_ :self .changed .emit ())
        call_row .addWidget (self .call_check )
        call_row .addStretch ()
        help_lbl =QLabel ("ⓘ")
        help_lbl .setObjectName ("hint_text")
        help_lbl .setStyleSheet ("font-weight:bold;")
        help_lbl .setToolTip (CALL_VS_JUMP_TOOLTIP )
        call_row .addWidget (help_lbl )
        outer .addLayout (call_row )


        branch_row =QHBoxLayout ()
        branch_row .setContentsMargins (0 ,2 ,0 ,0 )
        self ._branch_btn =QPushButton ()
        self ._branch_btn .setFlat (False )
        self ._branch_btn .setStyleSheet (
        "QPushButton { background:#2d4a3a; color:#6fd68f; font-size:11px;"
        " border-radius:4px; padding:4px 8px; text-align:left; }"
        "QPushButton:hover { background:#35573f; }"
        )
        self ._branch_btn .setToolTip (tr ("ne.branch_button_tooltip"))
        self ._branch_btn .clicked .connect (self .open_branch .emit )
        self ._update_branch_btn_text ()
        branch_row .addWidget (self ._branch_btn ,1 )
        outer .addLayout (branch_row )


        body_toggle_row =QHBoxLayout ()
        body_toggle_row .setContentsMargins (0 ,2 ,0 ,0 )
        self ._body_toggle_btn =QPushButton (tr ("ne.body_toggle_collapsed"))
        self ._body_toggle_btn .setFlat (True )
        self ._body_toggle_btn .setObjectName ("link_btn")
        self ._body_toggle_btn .setStyleSheet ("font-size:11px;")
        self ._body_toggle_btn .clicked .connect (self ._toggle_body )
        body_toggle_row .addWidget (self ._body_toggle_btn )
        body_toggle_row .addStretch ()
        outer .addLayout (body_toggle_row )

        self .body_edit =QTextEdit ()
        self .body_edit .setPlaceholderText (tr ("ne.body_placeholder"))
        self .body_edit .setPlainText (raw_body )
        self .body_edit .setMinimumHeight (90 )
        self .body_edit .setMaximumHeight (300 )
        self .body_edit .setObjectName ("code_field")
        self .body_edit .textChanged .connect (lambda :self .changed .emit ())
        outer .addWidget (self .body_edit )


        self ._body_visible =bool (raw_body and raw_body .strip ())
        self .body_edit .setVisible (self ._body_visible )
        self ._body_toggle_btn .setText (
        tr ("ne.body_toggle_expanded")if self ._body_visible 
        else tr ("ne.body_toggle_collapsed")
        )

    def _toggle_body (self ):
        self ._body_visible =not self ._body_visible 
        self .body_edit .setVisible (self ._body_visible )
        self ._body_toggle_btn .setText (
        tr ("ne.body_toggle_expanded")if self ._body_visible 
        else tr ("ne.body_toggle_collapsed")
        )

    def get_use_call (self )->bool :
        return self .call_check .isChecked ()

    def get_raw_body (self )->str :
        return self .body_edit .toPlainText ()

    def get_nodes (self )->list :
        return self .branch_nodes 

    def _update_branch_btn_text (self ):
        count =len (self .branch_nodes )
        if count :
            word =plural (count ,{"ru":("нода","ноды","нод"),"en":("node","nodes")})
            self ._branch_btn .setText (tr ("ne.branch_button_text",count =count ,word =word ))
        else :
            self ._branch_btn .setText (tr ("ne.branch_button_empty"))

    def refresh_branch_button (self ):
        self ._update_branch_btn_text ()


class NodeEditor (QWidget ):
    node_changed =pyqtSignal ()
    open_menu_branch =pyqtSignal (object ,int )

    def __init__ (self ,resource_manager =None ,parent =None ):
        super ().__init__ (parent )
        self .rm =resource_manager 
        self .tags_store =None 
        self .usage_store =None 
        self .custom_template_store =None 
        self ._spellcheck_whitelist =None 






        self .last_group_by_type :dict ={}
        self .node :SceneNode |None =None 
        self .characters :list =[]
        self .asset_vars :dict ={}
        self .choice_rows :list [MenuChoiceRow ]=[]
        self ._build ()
        self .refresh_resources ()
        theme_manager .themeChanged .connect (self ._on_theme_changed )

    def _style_apply_btn (self ):
        t =theme_manager .tokens ()
        if t .flat_buttons :
            bg =f"background:{t .accent_1 };"
            hover_bg =f"background:{t .accent_2 };"
        else :
            bg =f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t .accent_1 }, stop:1 {t .accent_2 });"
            hover_bg =f"background:{t .accent_1 };"
        self .apply_btn .setStyleSheet (f"""
            QPushButton#btn_apply_primary {{
                {bg }
                color:{t .accent_text }; font-weight:bold;
                padding:8px; font-size:12px;
            }}
            QPushButton#btn_apply_primary:hover {{ {hover_bg } }}
        """)

    def _on_theme_changed (self ,_theme_id :str ):

        self ._style_apply_btn ()
        _style_combo (self .type_combo )
        if self .node is not None :
            self ._rebuild_fields ()

    def _node_type_value (self ,node_type ):
        return node_type .value if hasattr (node_type ,'value')else node_type 

    def set_characters (self ,characters :list ):
        self .characters =characters 
        if self .node :
            self ._rebuild_fields ()

    def set_spellcheck_whitelist (self ,words :set ):
        self ._spellcheck_whitelist =words 
        if self .node and self ._node_type_value (self .node .node_type )in ("dialogue","narration"):
            self ._run_spellcheck_hint ()

    def refresh_resources (self ):
        asset_vars ={'bg':[],'cg':[],'sprites':[],'music':[],'sounds':[],'ambience':[]}
        if self .rm is not None :
            try :
                for cat in asset_vars :
                    asset_vars [cat ]=[e .var_name for e in self .rm .get (cat )]
            except Exception :
                pass 
        self .asset_vars =asset_vars 
        if self .node :
            self ._rebuild_fields ()

    def load_node (self ,node :SceneNode ):
        self .set_node (node ,self .characters ,self .asset_vars )

    def clear_node (self ):

        self .node =None 
        self ._clear_fields ()

    def sync_xalign_from_preview (self ,xalign :float ):

        if not self .node or self ._node_type_value (self .node .node_type )!="show_sprite":
            return 
        if not hasattr (self ,"xalign_spin"):
            return 
        name =nearest_anchor_name (xalign )
        idx =self .xalign_spin .findData (name )
        if idx <0 :
            return 
        self .xalign_spin .blockSignals (True )
        self .xalign_spin .setCurrentIndex (idx )
        self .xalign_spin .blockSignals (False )

    def _build (self ):
        self .setObjectName ("code_box")
        outer =QVBoxLayout (self )
        outer .setContentsMargins (8 ,8 ,8 ,8 )
        outer .setSpacing (6 )

        title =QLabel (tr ("ne.panel_title"))
        title .setObjectName ("accent_caption")
        title .setStyleSheet ("font-size:13px; padding:4px;")
        outer .addWidget (title )


        type_row =QHBoxLayout ()
        type_row .addWidget (_label (tr ("ne.node_type_label")))
        self .type_combo =_combo ([label for _ ,label in NODE_TYPES ()])
        self .type_combo .setToolTip (tr ("ne.node_type_tooltip"))
        self .type_combo .currentIndexChanged .connect (self ._on_type_changed )
        type_row .addWidget (self .type_combo )
        outer .addLayout (type_row )


        scroll =QScrollArea ()
        scroll .setWidgetResizable (True )
        scroll .setObjectName ("surface_scroll")
        self .fields_widget =QWidget ()
        self .fields_widget .setObjectName ("code_box")
        self .fields_layout =QVBoxLayout (self .fields_widget )
        self .fields_layout .setContentsMargins (0 ,4 ,0 ,4 )
        self .fields_layout .setSpacing (6 )
        self .fields_layout .addStretch ()
        scroll .setWidget (self .fields_widget )
        outer .addWidget (scroll )


        apply_btn =QPushButton (tr ("ne.apply_button"))
        apply_btn .setObjectName ("btn_apply_primary")
        self .apply_btn =apply_btn 
        self ._style_apply_btn ()
        apply_btn .clicked .connect (self ._apply )
        outer .addWidget (apply_btn )



    def set_node (self ,node :SceneNode ,characters :list ,asset_vars :dict ):
        self .node =node 
        self .characters =characters 
        self .asset_vars =asset_vars 
        type_keys =[k for k ,_ in NODE_TYPES ()]
        current =self ._node_type_value (node .node_type )
        idx =type_keys .index (current )if current in type_keys else 0 
        self .type_combo .blockSignals (True )
        self .type_combo .setCurrentIndex (idx )
        self .type_combo .blockSignals (False )
        self ._rebuild_fields ()

    def flush (self ):

        if self .node is not None :
            self ._apply ()



    def _on_type_changed (self ,idx :int ):
        if self .node :
            mapping ={
            'background':NodeType .SHOW_BG ,
            'cg':NodeType .SHOW_CG ,
            'music':NodeType .PLAY_MUSIC ,
            'sound':NodeType .PLAY_SOUND ,
            }
            value =[k for k ,_ in NODE_TYPES ()][idx ]
            self .node .node_type =mapping .get (value ,NodeType (value ))
        self ._rebuild_fields ()

    def _clear_fields (self ):
        self ._disconnect_waveform ()
        self ._stop_audio_preview ()
        self .choice_rows .clear ()
        while self .fields_layout .count ()>1 :
            item =self .fields_layout .takeAt (0 )
            if item .widget ():
                item .widget ().deleteLater ()






        for attr in (
        "fadein_spin","fadeout_spin","ambience_fadeout_spin","waveform",
        "audio_combo","loop_check","raw_edit","char_combo",
        ):
            if hasattr (self ,attr ):
                delattr (self ,attr )

    def _stop_audio_preview (self ):

        try :
            player =get_audio_player ()
            if player .is_playing ():
                player .stop ()
        except Exception :
            pass 

    def _rebuild_fields (self ):
        self ._clear_fields ()
        if not self .node :
            return 
        t =self ._node_type_value (self .node .node_type )

        if t in ("dialogue","narration"):
            self ._add_dialogue_fields ()
        elif t in ("show_bg","show_cg","scene"):
            self ._add_bg_fields (t )
        elif t =="show_sprite":
            self ._add_sprite_fields ()
        elif t =="hide_sprite":
            self ._add_hide_fields ()
        elif t =="window":
            self ._add_window_fields ()
        elif t =="with_transition":
            self ._add_with_transition_fields ()
        elif t =="nvl_mode":
            self ._add_nvl_mode_fields ()
        elif t in ("play_music","play_sound","play_ambience"):
            self ._add_audio_fields (t )
        elif t in ("stop_music","stop_ambience"):
            self ._add_stop_audio_fields (t )
        elif t =="label":
            self ._add_label_fields ()
        elif t =="jump":
            self ._add_jump_fields ()
        elif t =="menu":
            self ._add_menu_fields ()
        elif t =="pause":
            self ._add_pause_fields ()
        elif t =="return_":
            self ._add_return_fields ()
        elif t =="python":
            self ._add_python_fields ()
        elif t =="raw":
            self ._add_raw_fields ()
        elif t =="custom":
            self ._add_custom_fields ()

        fade_in_widget (self .fields_widget ,duration =160 )

    def _insert (self ,widget :QWidget ):
        self .fields_layout .insertWidget (self .fields_layout .count ()-1 ,widget )

    def _add_dialogue_fields (self ):
        n =self .node 
        if self ._node_type_value (n .node_type )=="dialogue":
            grp =QGroupBox (tr ("ne.character_group"))
            grp .setObjectName ("plain_box")
            g =QVBoxLayout (grp )
            self .char_combo =_combo ([tr ("ne.narrator_option")]+[c .name for c in self .characters ])
            self .char_combo .setToolTip (tr ("ne.character_combo_tooltip"))
            if n .character_var :
                vars =[c .variable for c in self .characters ]
                if n .character_var in vars :
                    self .char_combo .setCurrentIndex (vars .index (n .character_var )+1 )
            self .char_combo .currentIndexChanged .connect (lambda *_ :self ._apply ())
            g .addWidget (self .char_combo )
            self ._insert (grp )

        grp2 =QGroupBox (tr ("ne.dialogue_text_group"))
        grp2 .setObjectName ("plain_box")
        g2 =QVBoxLayout (grp2 )

        tag_row =QHBoxLayout ()
        tag_row .setSpacing (3 )

        def _tag_btn (label :str ,tooltip :str ,handler ):
            btn =QPushButton (label )
            btn .setObjectName ("tag_chip_btn")
            btn .setFixedHeight (24 )
            btn .setToolTip (tooltip )
            btn .setStyleSheet ("font-size:11px;")
            btn .clicked .connect (handler )
            tag_row .addWidget (btn )
            return btn 

        _tag_btn ("𝑖",tr ("ne.tag_italic_tooltip"),lambda :self ._wrap_selection_with_tag ("i"))
        _tag_btn ("𝐛",tr ("ne.tag_bold_tooltip"),lambda :self ._wrap_selection_with_tag ("b"))
        _tag_btn ("u̲",tr ("ne.tag_underline_tooltip"),lambda :self ._wrap_selection_with_tag ("u"))
        _tag_btn ("🤫",tr ("ne.tag_whisper_tooltip"),self ._insert_whisper_tag )
        _tag_btn ("A±",tr ("ne.tag_size_tooltip"),lambda :self ._wrap_selection_with_tag ("size=+10","size"))
        _tag_btn ("🎨",tr ("ne.tag_color_tooltip"),self ._insert_color_tag )
        _tag_btn ("⏳w",tr ("ne.tag_wait_tooltip"),lambda :self ._insert_at_cursor ("{w}"))
        _tag_btn ("⏭nw",tr ("ne.tag_nowait_tooltip"),lambda :self ._insert_at_cursor ("{nw}"))
        tag_row .addStretch ()
        g2 .addLayout (tag_row )

        self .text_edit =QTextEdit ()
        self .text_edit .setToolTip (tr ("ne.dialogue_text_tooltip"))
        self .text_edit .setPlaceholderText (tr ("ne.dialogue_text_placeholder"))
        self .text_edit .setText (n .text )
        self .text_edit .setMinimumHeight (80 )
        self .text_edit .setObjectName ("dark_field")
        self .text_edit .setStyleSheet ("QTextEdit#dark_field { font-size:12px; }")
        self .text_edit .textChanged .connect (lambda :self ._apply ())
        self .text_edit .textChanged .connect (self ._update_length_hint )
        self .text_edit .textChanged .connect (self ._update_spellcheck_hint )
        g2 .addWidget (self .text_edit )

        self .length_hint_lbl =QLabel ()
        self .length_hint_lbl .setStyleSheet ("font-size:11px; padding:2px 0;")
        self .length_hint_lbl .setWordWrap (True )
        g2 .addWidget (self .length_hint_lbl )
        self ._update_length_hint ()

        self .spellcheck_hint_lbl =QLabel ()
        self .spellcheck_hint_lbl .setObjectName ("warning_hint")
        self .spellcheck_hint_lbl .setStyleSheet ("padding:2px 0;")
        self .spellcheck_hint_lbl .setWordWrap (True )
        g2 .addWidget (self .spellcheck_hint_lbl )
        self ._update_spellcheck_hint ()

        self ._insert (grp2 )



    DIALOGUE_LEN_OK =200 
    DIALOGUE_LEN_UGLY =340 

    def _wrap_selection_with_tag (self ,open_inner :str ,close_name :str =None ):

        close_name =close_name or open_inner 
        cursor =self .text_edit .textCursor ()
        open_tag ,close_tag ="{%s}"%open_inner ,"{/%s}"%close_name 
        if cursor .hasSelection ():
            selected =cursor .selectedText ()
            cursor .insertText (open_tag +selected +close_tag )
        else :
            pos =cursor .position ()
            cursor .insertText (open_tag +close_tag )
            cursor .setPosition (pos +len (open_tag ))
            self .text_edit .setTextCursor (cursor )
        self .text_edit .setFocus ()

    def _insert_whisper_tag (self ):

        cursor =self .text_edit .textCursor ()
        open_tag ="{size=-4}{alpha=0.75}{i}"
        close_tag ="{/i}{/alpha}{/size}"
        if cursor .hasSelection ():
            selected =cursor .selectedText ()
            cursor .insertText (open_tag +selected +close_tag )
        else :
            pos =cursor .position ()
            cursor .insertText (open_tag +close_tag )
            cursor .setPosition (pos +len (open_tag ))
            self .text_edit .setTextCursor (cursor )
        self .text_edit .setFocus ()

    def _insert_color_tag (self ):
        from PyQt6 .QtWidgets import QColorDialog 
        color =QColorDialog .getColor ()
        if not color .isValid ():
            return 
        self ._wrap_selection_with_tag (f"color={color .name ()}","color")

    def _insert_at_cursor (self ,text :str ):
        cursor =self .text_edit .textCursor ()
        cursor .insertText (text )
        self .text_edit .setFocus ()

    def _update_length_hint (self ):
        if not hasattr (self ,"length_hint_lbl"):
            return 
        raw =self .text_edit .toPlainText ()
        count =len (strip_tags (raw ))
        tag_count =len (raw )-count 
        tag_note =tr ("ne.tag_symbols_note",count =tag_count )if tag_count else ""
        if count <=self .DIALOGUE_LEN_OK :
            color ="#7ed957"
            msg =tr ("ne.length_ok",count =count ,note =tag_note )
        elif count <=self .DIALOGUE_LEN_UGLY :
            color ="#ffb84d"
            msg =tr ("ne.length_ugly",count =count ,note =tag_note )
        else :
            color ="#ff6b6b"
            msg =tr ("ne.length_overflow",count =count ,note =tag_note )
        self .length_hint_lbl .setStyleSheet (f"font-size:11px; padding:2px 0; color:{color };")
        self .length_hint_lbl .setText (msg )

    def _update_spellcheck_hint (self ):

        if not hasattr (self ,"spellcheck_hint_lbl"):
            return 
        if not hasattr (self ,"_spellcheck_hint_timer"):
            self ._spellcheck_hint_timer =QTimer (self )
            self ._spellcheck_hint_timer .setSingleShot (True )
            self ._spellcheck_hint_timer .timeout .connect (self ._run_spellcheck_hint )
        self ._spellcheck_hint_timer .start (400 )

    def _run_spellcheck_hint (self ):
        if not hasattr (self ,"spellcheck_hint_lbl"):
            return 
        try :
            raw =self .text_edit .toPlainText ()
        except RuntimeError :


            return 
        whitelist =None 
        if self .rm is not None and getattr (self ,"_spellcheck_whitelist",None )is not None :
            whitelist =self ._spellcheck_whitelist 
        issues =check_text (raw ,whitelist =whitelist )if raw else []
        if not issues :
            self .spellcheck_hint_lbl .setText ("")
            return 
        preview ="; ".join (i .message for i in issues [:3 ])
        more =f" (+{len (issues )-3 })"if len (issues )>3 else ""
        self .spellcheck_hint_lbl .setText (f"⚠ {preview }{more }")

    def _add_bg_fields (self ,t :str ):
        n =self .node 
        cat ="cg"if t =="show_cg"else "bg"
        label =tr ("ne.select_cg")if t =="show_cg"else tr ("ne.select_bg")
        current =n .cg_var if t =="show_cg"else n .bg_var 

        grp =QGroupBox (label )
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )

        entries =self .rm .get (cat )if self .rm is not None else []
        last_group =self .last_group_by_type .get (t )
        self .bg_carousel =ResourceCarousel (
        thumb_size =160 ,tags_store =self .tags_store ,
        initial_group_id =last_group ,category =cat ,usage_store =self .usage_store ,rm =self .rm 
        )
        self .bg_carousel .group_changed .connect (lambda gid :self ._on_bg_group_changed (gid ,t ))
        self .bg_carousel .set_entries (entries )
        if current :
            self .bg_carousel .select_by_var (current )
        self .bg_carousel .selection_changed .connect (lambda *_ :self ._apply ())
        g .addWidget (self .bg_carousel )

        if not entries :
            empty =QLabel (tr ("ne.no_files_in_resources",cat =cat ))
            empty .setObjectName ("hint_text")
            empty .setWordWrap (True )
            g .addWidget (empty )

        g .addWidget (_label (tr ("ne.transition_label")))
        self .trans_combo =_transition_combo (n .transition )
        self .trans_combo .setToolTip (tr ("ne.transition_tooltip"))
        self .trans_combo .currentIndexChanged .connect (lambda *_ :self ._apply ())
        g .addWidget (self .trans_combo )
        trans_btn =QPushButton (tr ("ne.transition_button"))
        trans_btn .clicked .connect (lambda :self ._open_transition_editor (self .trans_combo ,n .bg_var or n .cg_var or ""))
        g .addWidget (trans_btn )

        self .atl_btn =QPushButton (
        tr ("ne.atl_button_active")if n .atl_script .strip ()else tr ("ne.atl_button"))
        self .atl_btn .setToolTip (tr ("ne.atl_hint"))
        self .atl_btn .clicked .connect (lambda :self ._open_atl_editor (is_bg =True ))
        g .addWidget (self .atl_btn )

        self ._insert (grp )

    def _resolve_pixmap_by_var (self ,var :str ):

        if not var or self .rm is None :
            return None 
        composite =self .rm .find_composite_by_name (var )
        if composite is not None :
            try :
                layer_paths =[
                (self .rm .resolve_layer_path (layer .rel_path ,composite .source ),layer .offset_x ,layer .offset_y )
                for layer in composite .layers 
                ]
                return get_composite (layer_paths ,composite .width ,composite .height )
            except Exception :
                return None 
        entry =self .rm .find_by_var (var )
        if entry :
            return get_pixmap (entry .abs_path )
        return None 

    def _resolve_mask_path (self ,rel_path :str ):

        if not rel_path or self .rm is None :
            return None 
        if os .path .isabs (rel_path )and os .path .isfile (rel_path ):
            return rel_path 
        for source in ("custom","default"):
            candidate =os .path .join (self .rm .get_source_root (source ),rel_path )
            if os .path .isfile (candidate ):
                return candidate 
        return None 

    def _import_transition_mask (self ,src_abs_path :str ):

        if not src_abs_path or self .rm is None :
            return None 
        dest_dir =os .path .join (self .rm .get_source_root ("custom"),"transitions")
        os .makedirs (dest_dir ,exist_ok =True )
        base_name =os .path .basename (src_abs_path )
        stem ,ext =os .path .splitext (base_name )
        dest_name =base_name 
        counter =2 
        while os .path .exists (os .path .join (dest_dir ,dest_name )):
            dest_name =f"{stem }_{counter }{ext }"
            counter +=1 
        dest_path =os .path .join (dest_dir ,dest_name )
        try :
            shutil .copy2 (src_abs_path ,dest_path )
        except OSError :
            return None 
        return f"transitions/{dest_name }"

    def _open_transition_editor (self ,combo :QComboBox ,base_pixmap_var :str =""):

        base_pixmap =self ._resolve_pixmap_by_var (base_pixmap_var )if base_pixmap_var else None 
        dlg =TransitionEditorDialog (
        combo .currentText (),base_pixmap =base_pixmap ,
        mask_resolver =self ._resolve_mask_path ,
        mask_import_fn =self ._import_transition_mask ,rm =self .rm ,parent =self ,
        )
        if dlg .exec ():
            combo .setCurrentText (dlg .result_text ())
            self ._apply ()

    def _open_atl_editor (self ,is_bg :bool ):

        n =self .node 
        if n is None :
            return 
        if is_bg :
            base_xalign ,base_yalign ,base_zoom =0.5 ,0.5 ,1.0 
            label =n .bg_var or n .cg_var or ""
            base_pixmap =self ._resolve_pixmap_by_var (label )
        else :
            base_xalign ,base_yalign ,base_zoom =n .xalign ,n .yalign ,n .zoom 
            label =n .sprite_var or ""
            base_pixmap =self ._resolve_pixmap_by_var (label )
        dlg =AtlEditorDialog (
        n .atl_script ,base_xalign =base_xalign ,base_yalign =base_yalign ,
        base_zoom =base_zoom ,is_bg =is_bg ,label =label ,parent =self ,
        base_pixmap =base_pixmap ,resolve_image_fn =self ._resolve_pixmap_by_var ,
        )
        if dlg .exec ():
            n .atl_script =dlg .atl_text ()
            if hasattr (self ,"atl_btn"):
                self .atl_btn .setText (
                tr ("ne.atl_button_active")if n .atl_script .strip ()else tr ("ne.atl_button"))
            self ._apply ()

    def _on_bg_group_changed (self ,category_id ,t :str ):
        self .last_group_by_type [t ]=category_id 

    def _add_sprite_fields (self ):
        n =self .node 
        grp =QGroupBox (tr ("ne.sprite_group"))
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )

        has_composite =bool (self .rm and self .rm .composite_sprites )
        entries =self .rm .get ("sprites")if self .rm is not None else []

        self .composite_sprite_carousel =None 
        self .sprite_carousel =None 

        self .composite_label =None 
        self .plain_label =None 

        if has_composite :
            self .composite_label =QLabel (tr ("ne.composite_sprites_label"))
            self .composite_label .setObjectName ("hint_text")
            g .addWidget (self .composite_label )
            self .composite_sprite_carousel =CompositeSpriteCarousel (self .rm ,thumb_size =160 )
            self .composite_sprite_carousel .set_resource_manager (self .rm )
            if n .sprite_var :
                self .composite_sprite_carousel .select_by_name (n .sprite_var )
            self .composite_sprite_carousel .selection_changed .connect (self ._on_composite_sprite_selected )
            self .composite_sprite_carousel .browsing_changed .connect (self ._on_composite_browsing_changed )
            g .addWidget (self .composite_sprite_carousel )

        if entries or not has_composite :
            if has_composite :
                self .plain_label =QLabel (tr ("ne.plain_sprites_label"))
                self .plain_label .setObjectName ("hint_text")
                self .plain_label .setStyleSheet ("padding-top:6px;")
                g .addWidget (self .plain_label )
            self .sprite_carousel =FolderResourceCarousel (self .rm ,category ="sprites",thumb_size =160 )
            self .sprite_carousel .set_resource_manager (self .rm ,"sprites")
            if n .sprite_var :
                self .sprite_carousel .select_by_var (n .sprite_var )
            self .sprite_carousel .selection_changed .connect (self ._on_plain_sprite_selected )
            g .addWidget (self .sprite_carousel )


        if has_composite and self .composite_sprite_carousel .current_path :
            self ._on_composite_browsing_changed (True )

        if not entries and not has_composite :
            empty =QLabel (tr ("ne.no_sprite_files"))
            empty .setObjectName ("hint_text")
            empty .setWordWrap (True )
            g .addWidget (empty )

        g .addWidget (_label (tr ("ne.sprite_anchor_label")))
        self .xalign_spin =QComboBox ()
        for name ,label in ANCHOR_POSITIONS :
            self .xalign_spin .addItem (label ,name )
        current_name =nearest_anchor_name (n .xalign )
        idx =self .xalign_spin .findData (current_name )
        if idx >=0 :
            self .xalign_spin .setCurrentIndex (idx )
        self .xalign_spin .setObjectName ("dark_field")
        self .xalign_spin .currentIndexChanged .connect (lambda *_ :self ._apply ())
        g .addWidget (self .xalign_spin )

        g .addWidget (_label (tr ("ne.transition_label")))
        self .sprite_trans_combo =_transition_combo (n .transition )
        self .sprite_trans_combo .currentIndexChanged .connect (lambda *_ :self ._apply ())
        g .addWidget (self .sprite_trans_combo )
        sprite_trans_btn =QPushButton (tr ("ne.transition_button"))
        sprite_trans_btn .clicked .connect (
        lambda :self ._open_transition_editor (self .sprite_trans_combo ,n .sprite_var or ""))
        g .addWidget (sprite_trans_btn )

        self .atl_btn =QPushButton (
        tr ("ne.atl_button_active")if n .atl_script .strip ()else tr ("ne.atl_button"))
        self .atl_btn .setToolTip (tr ("ne.atl_hint"))
        self .atl_btn .clicked .connect (lambda :self ._open_atl_editor (is_bg =False ))
        g .addWidget (self .atl_btn )

        hint =QLabel (tr ("ne.sprite_group_hint"))
        hint .setWordWrap (True )
        hint .setObjectName ("hint_text")
        hint .setStyleSheet ("padding-top:2px;")
        g .addWidget (hint )

        self ._insert (grp )

    def _on_composite_browsing_changed (self ,entered :bool ):

        if self .sprite_carousel is not None :
            self .sprite_carousel .setVisible (not entered )
        if self .plain_label is not None :
            self .plain_label .setVisible (not entered )

    def _on_composite_sprite_selected (self ,sprite ):


        if self .sprite_carousel is not None :
            self .sprite_carousel .selected_entry =None 
            self .sprite_carousel ._refresh_view ()
        self ._apply ()

    def _on_plain_sprite_selected (self ,*_ ):
        if self .composite_sprite_carousel is not None :
            self .composite_sprite_carousel .reset_silent ()
            self ._on_composite_browsing_changed (False )
        self ._apply ()

    def _add_hide_fields (self ):
        n =self .node 
        grp =QGroupBox (tr ("ne.hide_sprite_group"))
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )

        g .addWidget (_label (tr ("ne.hide_whole_char")))
        self .hide_group_picker =CharacterGroupPicker (self .rm ,category ="sprites",thumb_size =160 )
        self .hide_group_picker .set_resource_manager (self .rm ,"sprites")
        if n .hide_group :
            self .hide_group_picker .select_folder (n .hide_group )
        self .hide_group_picker .selection_changed .connect (self ._on_hide_group_selected )
        g .addWidget (self .hide_group_picker )

        sep =QLabel (tr ("ne.or_pick_specific_sprite"))
        sep .setAlignment (Qt .AlignmentFlag .AlignCenter )
        sep .setObjectName ("hint_text")
        sep .setStyleSheet ("padding:4px;")
        g .addWidget (sep )

        self .hide_carousel =FolderResourceCarousel (self .rm ,category ="sprites",thumb_size =160 )
        self .hide_carousel .set_resource_manager (self .rm ,"sprites")
        if n .hide_var :
            self .hide_carousel .select_by_var (n .hide_var )
        self .hide_carousel .selection_changed .connect (self ._on_hide_entry_selected )
        g .addWidget (self .hide_carousel )
        self ._insert (grp )

    def _on_hide_group_selected (self ,folder_name :str ):



        if hasattr (self ,"hide_carousel"):
            self .hide_carousel .selected_entry =None 
            self .hide_carousel ._refresh_view ()
        self ._apply ()

    def _on_hide_entry_selected (self ,*_ ):
        if hasattr (self ,"hide_group_picker"):
            self .hide_group_picker .selected_folder =""
            for card in self .hide_group_picker .cards :
                card .set_selected (False )
        self ._apply ()

    def _add_window_fields (self ):
        n =self .node 
        grp =QGroupBox (tr ("ne.textbox_group"))
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )

        g .addWidget (_label (tr ("ne.action_label")))
        self .window_action_combo =_combo (["show","hide"])
        self .window_action_combo .setCurrentText (n .window_action or "show")
        self .window_action_combo .currentIndexChanged .connect (lambda *_ :self ._apply ())
        g .addWidget (self .window_action_combo )

        g .addWidget (_label (tr ("ne.transition_optional_label")))
        self .window_trans_combo =_transition_combo (n .transition )
        self .window_trans_combo .currentIndexChanged .connect (lambda *_ :self ._apply ())
        g .addWidget (self .window_trans_combo )
        window_trans_btn =QPushButton (tr ("ne.transition_button"))
        window_trans_btn .clicked .connect (lambda :self ._open_transition_editor (self .window_trans_combo ,""))
        g .addWidget (window_trans_btn )

        self ._insert (grp )

    def _add_with_transition_fields (self ):
        n =self .node 
        grp =QGroupBox (tr ("ne.with_effect_group"))
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )

        hint =QLabel (tr ("ne.with_effect_hint"))
        hint .setWordWrap (True )
        hint .setObjectName ("hint_text")
        g .addWidget (hint )

        g .addWidget (_label (tr ("ne.transition_label")))
        self .with_trans_combo =_transition_combo (n .transition )
        self .with_trans_combo .currentIndexChanged .connect (lambda *_ :self ._apply ())
        g .addWidget (self .with_trans_combo )
        with_trans_btn =QPushButton (tr ("ne.transition_button"))
        with_trans_btn .clicked .connect (lambda :self ._open_transition_editor (self .with_trans_combo ,""))
        g .addWidget (with_trans_btn )

        self ._insert (grp )

    def _add_nvl_mode_fields (self ):
        n =self .node 
        grp =QGroupBox (tr ("ne.nvl_mode_group"))
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )

        hint =QLabel (tr ("ne.nvl_mode_hint"))
        hint .setWordWrap (True )
        hint .setObjectName ("hint_text")
        g .addWidget (hint )

        g .addWidget (_label (tr ("ne.action_label")))
        self .nvl_action_combo =_combo ([
        tr ("ne.nvl_action_enter"),
        tr ("ne.nvl_action_clear"),
        tr ("ne.nvl_action_exit"),
        ])
        current_map ={"enter":0 ,"clear":1 ,"exit":2 }
        self .nvl_action_combo .setCurrentIndex (current_map .get (n .nvl_action ,0 ))
        self .nvl_action_combo .currentIndexChanged .connect (lambda *_ :self ._apply ())
        g .addWidget (self .nvl_action_combo )

        note =QLabel (tr ("ne.nvl_clear_hint"))
        note .setWordWrap (True )
        note .setObjectName ("hint_text")
        g .addWidget (note )

        self ._insert (grp )

    def _add_raw_fields (self ):
        n =self .node 
        grp =QGroupBox (tr ("ne.raw_code_group"))
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )

        hint =QLabel (tr ("ne.raw_code_hint"))
        hint .setWordWrap (True )
        hint .setObjectName ("accent_caption")
        hint .setStyleSheet ("font-size:11px; font-weight:normal;")
        g .addWidget (hint )

        self .raw_edit =QTextEdit ()
        self .raw_edit .setPlainText (n .python_code )
        self .raw_edit .setMinimumHeight (120 )
        self .raw_edit .setObjectName ("code_field")
        self .raw_edit .textChanged .connect (lambda :self ._apply ())
        g .addWidget (self .raw_edit )

        self ._insert (grp )

    def _add_custom_fields (self ):
        n =self .node 
        grp =QGroupBox (tr ("ne.custom_node_group"))
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )

        self .custom_param_widgets ={}
        templates =self .custom_template_store .templates if self .custom_template_store else []

        if not templates :
            empty =QLabel (tr ("ne.no_custom_templates"))
            empty .setWordWrap (True )
            empty .setObjectName ("accent_caption")
            empty .setStyleSheet ("font-size:11px; font-weight:normal;")
            g .addWidget (empty )
            self ._insert (grp )
            return 

        g .addWidget (_label (tr ("ne.template_label")))
        self .custom_template_combo =_combo ([t .name for t in templates ])
        ids =[t .template_id for t in templates ]
        if n .custom_template_id in ids :
            self .custom_template_combo .setCurrentIndex (ids .index (n .custom_template_id ))
        else :
            n .custom_template_id =ids [0 ]
            n .custom_params =templates [0 ].default_params ()
        self .custom_template_combo .currentIndexChanged .connect (self ._on_custom_template_changed )
        g .addWidget (self .custom_template_combo )

        current =self .custom_template_store .get (n .custom_template_id )
        self .custom_desc_label =QLabel (current .description if current and current .description else "")
        self .custom_desc_label .setWordWrap (True )
        self .custom_desc_label .setObjectName ("hint_text")
        self .custom_desc_label .setVisible (bool (current and current .description ))
        g .addWidget (self .custom_desc_label )

        self .custom_params_box =QVBoxLayout ()
        g .addLayout (self .custom_params_box )
        self ._rebuild_custom_param_fields (current )

        self ._insert (grp )

    def _rebuild_custom_param_fields (self ,template ):
        while self .custom_params_box .count ():
            item =self .custom_params_box .takeAt (0 )
            if item .widget ():
                item .widget ().deleteLater ()
        self .custom_param_widgets ={}
        if not template :
            return 
        n =self .node 
        values =dict (template .default_params ())
        values .update (n .custom_params or {})
        for p in template .params :
            row =QHBoxLayout ()
            row .addWidget (_label ((p .label or p .name )+":"))
            if p .param_type =="bool":
                w =QCheckBox ()
                w .setChecked (bool (values .get (p .name ,p .default )))
                w .toggled .connect (lambda *_ :self ._apply ())
            elif p .param_type in ("int","float"):
                w =QLineEdit (str (values .get (p .name ,p .default )))
                w .editingFinished .connect (self ._apply )
            else :
                w =QLineEdit (str (values .get (p .name ,p .default )))
                w .editingFinished .connect (self ._apply )
            self .custom_param_widgets [p .name ]=(w ,p )
            row .addWidget (w )
            container =QWidget ()
            container .setLayout (row )
            self .custom_params_box .addWidget (container )

    def _on_custom_template_changed (self ,idx :int ):
        templates =self .custom_template_store .templates if self .custom_template_store else []
        if 0 <=idx <len (templates ):
            template =templates [idx ]
            self .node .custom_template_id =template .template_id 
            self .node .custom_params =template .default_params ()
            self ._rebuild_custom_param_fields (template )
            if hasattr (self ,"custom_desc_label"):
                self .custom_desc_label .setText (template .description or "")
                self .custom_desc_label .setVisible (bool (template .description ))
            self ._apply ()

    def _add_audio_fields (self ,t :str ):
        n =self .node 
        cat ={"play_music":"music","play_sound":"sounds","play_ambience":"ambience"}[t ]
        title ={"play_music":tr ("ne.audio_music_title"),"play_sound":tr ("ne.audio_sound_title"),
        "play_ambience":tr ("ne.audio_ambience_title")}[t ]
        grp =QGroupBox (title )
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )
        vars_list =self .asset_vars .get (cat ,[])
        g .addWidget (_label (tr ("ne.file_label")))

        combo_row =QHBoxLayout ()
        self .audio_combo =_combo (vars_list )
        if n .audio_var in vars_list :
            self .audio_combo .setCurrentText (n .audio_var )
        self .audio_combo .currentTextChanged .connect (self ._on_audio_file_changed )
        combo_row .addWidget (self .audio_combo ,1 )

        btn_play =QPushButton ("▶️")
        btn_play .setToolTip (
        tr ("ne.listen_file_tooltip")+
        (tr ("ne.listen_from_fifth")if cat =="music"else tr ("ne.listen_from_start"))
        )
        btn_play .setObjectName ("btn_secondary")
        btn_play .setFixedWidth (48 )
        btn_play .clicked .connect (self ._play_audio_preview )
        combo_row .addWidget (btn_play )

        btn_stop =QPushButton ("⏹️")
        btn_stop .setToolTip (tr ("ne.stop_listening_tooltip"))
        btn_stop .setObjectName ("btn_secondary")
        btn_stop .setFixedWidth (48 )
        btn_stop .clicked .connect (lambda :get_audio_player ().stop ())
        combo_row .addWidget (btn_stop )

        g .addLayout (combo_row )

        if t =="play_music":
            self .loop_check =QCheckBox (tr ("ne.loop_checkbox"))
            self .loop_check .setChecked (n .audio_loop )
            self .loop_check .setObjectName ("hint_text_bright")
            g .addWidget (self .loop_check )

        if t in ("play_music","play_ambience"):
            value_fadein =n .music_fadein if t =="play_music"else n .ambience_fadein 
            value_fadeout =n .music_fadeout if t =="play_music"else n .ambience_fadeout 

            fade_row =QHBoxLayout ()
            fade_row .addWidget (_label (tr ("ne.fadein_sec_label")))
            self .fadein_spin =QDoubleSpinBox ()
            self .fadein_spin .setRange (0.0 ,60.0 )
            self .fadein_spin .setSingleStep (0.5 )
            self .fadein_spin .setDecimals (1 )
            self .fadein_spin .setValue (value_fadein )
            self .fadein_spin .setToolTip (tr ("ne.fadein_tooltip"))
            self .fadein_spin .valueChanged .connect (self ._on_fadein_spin_changed )
            fade_row .addWidget (self .fadein_spin )

            fade_row .addSpacing (12 )
            fade_row .addWidget (_label (tr ("ne.fadeout_sec_label")))
            self .fadeout_spin =QDoubleSpinBox ()
            self .fadeout_spin .setRange (0.0 ,60.0 )
            self .fadeout_spin .setSingleStep (0.5 )
            self .fadeout_spin .setDecimals (1 )
            self .fadeout_spin .setValue (value_fadeout )
            self .fadeout_spin .setToolTip (tr ("ne.fadeout_tooltip"))
            self .fadeout_spin .valueChanged .connect (self ._on_fadeout_spin_changed )
            fade_row .addWidget (self .fadeout_spin )
            fade_row .addStretch ()
            g .addLayout (fade_row )


            self .ambience_fadeout_spin =self .fadeout_spin 

        g .addWidget (_label (tr ("ne.waveform_label")))
        self .waveform =WaveformWidget ()
        g .addWidget (self .waveform )
        self ._wire_waveform (t ,n )

        self ._insert (grp )

    def _on_audio_file_changed (self ,var_name :str ):
        self ._apply ()
        entry =self .rm .find_by_var (var_name )if (self .rm and var_name )else None 
        if hasattr (self ,"waveform"):
            self .waveform .set_audio (entry .abs_path if entry else "")

    def _wire_waveform (self ,t :str ,n ):

        self ._disconnect_waveform ()
        player =get_audio_player ().player 
        conns =[
        player .positionChanged .connect (self .waveform .set_position_ms ),
        player .durationChanged .connect (self .waveform .set_duration_ms ),
        player .playbackStateChanged .connect (
        lambda state :self .waveform .set_playing (state ==player .PlaybackState .PlayingState )
        ),
        self .waveform .seek_requested .connect (self ._on_waveform_seek ),
        ]
        if hasattr (self ,"fadein_spin"):
            conns .append (self .waveform .fadein_changed .connect (self ._on_waveform_fadein_dragged ))
        if hasattr (self ,"fadeout_spin"):
            conns .append (self .waveform .fadeout_changed .connect (self ._on_waveform_fadeout_dragged ))
        self ._waveform_conns =conns 
        self ._waveform_player =player 

        fadein_sec =self .fadein_spin .value ()if hasattr (self ,"fadein_spin")else 0.0 
        fadeout_sec =self .fadeout_spin .value ()if hasattr (self ,"fadeout_spin")else 0.0 
        self .waveform .set_fades (fadein_sec ,fadeout_sec )



        current_var =self .audio_combo .currentText ()if hasattr (self ,"audio_combo")else (n .audio_var or "")
        entry =self .rm .find_by_var (current_var )if (self .rm and current_var )else None 
        if entry :
            self .waveform .set_audio (entry .abs_path )

    def _disconnect_waveform (self ):

        player =getattr (self ,"_waveform_player",None )
        conns =getattr (self ,"_waveform_conns",None )
        if player is not None and conns :
            for c in conns :
                try :
                    player .disconnect (c )
                except (TypeError ,RuntimeError ):

                    pass 
        self ._waveform_conns =[]
        self ._waveform_player =None 

    def _on_fadein_spin_changed (self ,*_ ):
        self .waveform .set_fades (self .fadein_spin .value (),
        self .fadeout_spin .value ()if hasattr (self ,"fadeout_spin")else 0.0 )
        self ._apply ()

    def _on_fadeout_spin_changed (self ,*_ ):
        self .waveform .set_fades (self .fadein_spin .value ()if hasattr (self ,"fadein_spin")else 0.0 ,
        self .fadeout_spin .value ())
        self ._apply ()

    def _on_waveform_fadein_dragged (self ,seconds :float ):
        if hasattr (self ,"fadein_spin"):
            self .fadein_spin .blockSignals (True )
            self .fadein_spin .setValue (round (seconds ,1 ))
            self .fadein_spin .blockSignals (False )
            self ._apply ()

    def _on_waveform_fadeout_dragged (self ,seconds :float ):
        if hasattr (self ,"fadeout_spin"):
            self .fadeout_spin .blockSignals (True )
            self .fadeout_spin .setValue (round (seconds ,1 ))
            self .fadeout_spin .blockSignals (False )
            self ._apply ()

    def _on_waveform_seek (self ,seconds :float ):
        player =get_audio_player ().player 
        if player .duration ()>0 :
            player .setPosition (int (seconds *1000 ))
            if player .playbackState ()!=player .PlaybackState .PlayingState :
                player .play ()

    def _add_stop_audio_fields (self ,t :str ):

        n =self .node 
        title =tr ("ne.stop_music_title")if t =="stop_music"else tr ("ne.stop_ambience_title")
        grp =QGroupBox (title )
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )

        fadeout_row =QHBoxLayout ()
        fadeout_row .addWidget (_label ("Fade out (сек):"))
        self .stop_fadeout_spin =QDoubleSpinBox ()
        self .stop_fadeout_spin .setRange (0.0 ,60.0 )
        self .stop_fadeout_spin .setSingleStep (0.5 )
        self .stop_fadeout_spin .setDecimals (1 )
        self .stop_fadeout_spin .setValue (n .music_fadeout if t =="stop_music"else n .ambience_fadeout )
        self .stop_fadeout_spin .valueChanged .connect (lambda *_ :self ._apply ())
        fadeout_row .addWidget (self .stop_fadeout_spin )
        fadeout_row .addStretch ()
        g .addLayout (fadeout_row )

        self ._insert (grp )

    def _play_audio_preview (self ):
        var_name =self .audio_combo .currentText ()if hasattr (self ,"audio_combo")else ""
        if not var_name or self .rm is None :
            return 
        entry =self .rm .find_by_var (var_name )
        if not entry :
            return 


        is_music =self ._node_type_value (self .node .node_type )=="play_music"
        get_audio_player ().play (entry .abs_path ,start_fraction =0.2 if is_music else 0.0 )

    def _add_label_fields (self ):
        n =self .node 
        grp =QGroupBox (tr ("ne.label_group"))
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )
        g .addWidget (_label (tr ("ne.label_name_field")))
        self .label_edit =_field ("start, intro_scene, ...")
        self .label_edit .setText (n .label_name )
        g .addWidget (self .label_edit )
        self ._insert (grp )

    def _add_jump_fields (self ):
        n =self .node 
        grp =QGroupBox (tr ("ne.jump_group"))
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )
        g .addWidget (_label (tr ("ne.jump_target_label")))
        self .jump_edit =_field (tr ("ne.label_name_placeholder"))
        self .jump_edit .setToolTip (tr ("ne.jump_target_tooltip"))
        self .jump_edit .setText (n .jump_target )
        g .addWidget (self .jump_edit )
        self ._insert (grp )

    def _add_menu_fields (self ):
        n =self .node 
        grp =QGroupBox (tr ("ne.menu_group"))
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )
        g .addWidget (_label (tr ("ne.menu_question_label")))
        self .menu_q =_field (tr ("ne.optional_placeholder"))
        self .menu_q .setText (n .menu_question )
        self .menu_q .textChanged .connect (lambda *_ :self ._apply ())
        g .addWidget (self .menu_q )

        g .addWidget (_label (tr ("ne.menu_options_label")))
        self .choices_container =QWidget ()
        self .choices_layout =QVBoxLayout (self .choices_container )
        self .choices_layout .setContentsMargins (0 ,0 ,0 ,0 )
        self .choices_layout .setSpacing (4 )
        for text ,jump ,use_call ,raw_body ,nodes in n .normalized_menu_choices ():
            self ._add_choice_row (text ,jump ,use_call ,raw_body ,nodes )
        g .addWidget (self .choices_container )

        add_btn =QPushButton (tr ("ne.add_choice_button"))
        add_btn .setObjectName ("node_action_btn")
        add_btn .clicked .connect (lambda :self ._add_choice_row ())
        g .addWidget (add_btn )

        info =QLabel (
        tr ("ne.menu_call_hint")
        )
        info .setWordWrap (True )
        info .setObjectName ("hint_text")
        info .setStyleSheet ("padding-top:4px;")
        g .addWidget (info )

        self ._insert (grp )

    def _add_choice_row (self ,text ="",jump ="",use_call =False ,raw_body ="",nodes =None ):
        row =MenuChoiceRow (text ,jump ,use_call ,raw_body ,nodes if nodes is not None else [])
        self .choice_rows .append (row )
        row .removed .connect (lambda :self ._remove_choice (row ))
        row .changed .connect (lambda *_ :self ._apply ())
        row .open_branch .connect (lambda r =row :self ._on_open_branch (r ))
        self .choices_layout .addWidget (row )
        self ._apply ()

    def _on_open_branch (self ,row :"MenuChoiceRow"):
        if self .node is None or row not in self .choice_rows :
            return 
        idx =self .choice_rows .index (row )
        self .open_menu_branch .emit (self .node ,idx )

    def _remove_choice (self ,row :MenuChoiceRow ):
        self .choice_rows .remove (row )
        row .deleteLater ()
        self ._apply ()

    def _add_python_fields (self ):
        n =self .node 
        grp =QGroupBox ("Python код ($ prefix)")
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )
        self .py_edit =QTextEdit ()
        self .py_edit .setPlaceholderText ("score += 1\nflag = True")
        self .py_edit .setText (n .python_code )
        self .py_edit .setMinimumHeight (100 )
        t =theme_manager .tokens ()
        self .py_edit .setStyleSheet (f"""
            QTextEdit {{
                background:{t .base_field }; color:#7ec8e3; border:1px solid {t .glass_border_s };
                font-family:Consolas,monospace; font-size:12px; border-radius:4px; padding:4px;
            }}
        """)
        g .addWidget (self .py_edit )
        self ._insert (grp )

    def _add_pause_fields (self ):
        n =self .node 
        grp =QGroupBox (tr ("ne.pause_group"))
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )
        g .addWidget (_label (tr ("ne.pause_duration_label")))
        self .pause_spin =QDoubleSpinBox ()
        self .pause_spin .setToolTip (tr ("ne.pause_duration_tooltip"))
        self .pause_spin .setRange (0.0 ,600.0 )
        self .pause_spin .setSingleStep (0.5 )
        self .pause_spin .setDecimals (1 )
        self .pause_spin .setValue (n .pause_duration )
        self .pause_spin .setObjectName ("dark_field")
        self .pause_spin .valueChanged .connect (lambda *_ :self ._apply ())
        g .addWidget (self .pause_spin )
        hint =QLabel (tr ("ne.pause_hint"))
        hint .setWordWrap (True )
        hint .setObjectName ("hint_text")
        hint .setStyleSheet ("padding-top:2px;")
        g .addWidget (hint )
        self ._insert (grp )

    def _add_return_fields (self ):
        grp =QGroupBox ("Return")
        grp .setObjectName ("plain_box")
        g =QVBoxLayout (grp )
        hint =QLabel (tr ("ne.return_hint"))
        hint .setWordWrap (True )
        hint .setObjectName ("hint_text")
        hint .setStyleSheet ("padding:4px;")
        g .addWidget (hint )
        self ._insert (grp )



    def _apply (self ):
        if not self .node :
            return 
        t =self ._node_type_value (self .node .node_type )

        if t =="dialogue":
            idx =self .char_combo .currentIndex ()
            self .node .character_var =self .characters [idx -1 ].variable if idx >0 else ""
            self .node .text =self .text_edit .toPlainText ()
        elif t =="narration":
            self .node .text =self .text_edit .toPlainText ()
        elif t in ("show_bg","show_cg","scene"):
            selected =self .bg_carousel .get_selected ()
            var =selected .var_name if selected else ""
            if t =="show_cg":
                self .node .cg_var =var 
            else :


                self .node .bg_var =var 
            self .node .transition =self .trans_combo .currentText ()
        elif t =="show_sprite":
            composite_selected =self .composite_sprite_carousel .get_selected ()if self .composite_sprite_carousel else None 
            plain_selected =self .sprite_carousel .get_selected ()if self .sprite_carousel else None 
            if composite_selected is not None :
                self .node .sprite_var =composite_selected .full_name 
                self .node .sprite_expression =None 
            elif plain_selected is not None :
                self .node .sprite_var =plain_selected .var_name 
                self .node .sprite_expression =None 
            else :
                self .node .sprite_var =""
                self .node .sprite_expression =None 
            anchor_name =self .xalign_spin .currentData ()
            self .node .xalign =NAMED_SPRITE_POSITIONS [anchor_name ].xalign if anchor_name else 0.5 
            self .node .transition =self .sprite_trans_combo .currentText ()
        elif t =="hide_sprite":
            group =self .hide_group_picker .get_selected ()if hasattr (self ,"hide_group_picker")else ""
            if group :
                self .node .hide_group =group 
                self .node .sprite_tag =None 
            else :
                selected =self .hide_carousel .get_selected ()
                self .node .hide_var =selected .var_name if selected else ""
                self .node .hide_group =None 
        elif t in ("play_music","play_sound","play_ambience"):
            self .node .audio_var =self .audio_combo .currentText ()
            if t =="play_music":
                self .node .audio_loop =self .loop_check .isChecked ()
                self .node .music_fadein =self .fadein_spin .value ()
                self .node .music_fadeout =self .fadeout_spin .value ()
            elif t =="play_ambience":
                self .node .ambience_fadein =self .fadein_spin .value ()
                self .node .ambience_fadeout =self .fadeout_spin .value ()
        elif t in ("stop_music","stop_ambience"):
            if t =="stop_music":
                self .node .music_fadeout =self .stop_fadeout_spin .value ()
            else :
                self .node .ambience_fadeout =self .stop_fadeout_spin .value ()
        elif t =="window":
            self .node .window_action =self .window_action_combo .currentText ()
            self .node .transition =self .window_trans_combo .currentText ()
        elif t =="with_transition":
            self .node .transition =self .with_trans_combo .currentText ()
        elif t =="nvl_mode":
            action =self .nvl_action_combo .currentText ().split (" - ")[0 ].strip ()
            self .node .nvl_action =action 
        elif t =="label":
            self .node .label_name =self .label_edit .text ().strip ()
        elif t =="jump":
            self .node .jump_target =self .jump_edit .text ().strip ()
        elif t =="menu":
            self .node .menu_question =self .menu_q .text ()
            self .node .menu_choices =[
            {
            "text":r .text_edit .text (),"jump":r .jump_edit .text (),
            "use_call":r .get_use_call (),"raw_body":r .get_raw_body (),
            "nodes":r .get_nodes (),
            }
            for r in self .choice_rows 
            ]
        elif t =="pause":
            self .node .pause_duration =self .pause_spin .value ()
        elif t =="python":
            self .node .python_code =self .py_edit .toPlainText ()
        elif t =="raw":
            self .node .python_code =self .raw_edit .toPlainText ()
        elif t =="custom":
            params ={}
            for name ,(widget ,pdef )in getattr (self ,"custom_param_widgets",{}).items ():
                if pdef .param_type =="bool":
                    raw_value =widget .isChecked ()
                else :
                    raw_value =widget .text ()
                params [name ]=pdef .coerce (raw_value )
            self .node .custom_params =params 

        self .node_changed .emit ()
