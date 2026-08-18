
from dataclasses import dataclass 
from typing import Dict ,List ,Optional 

from PyQt6 .QtCore import QObject ,QPropertyAnimation ,QEasingCurve ,pyqtSignal 
from PyQt6 .QtGui import QPalette ,QColor 
from PyQt6 .QtWidgets import QApplication ,QWidget ,QGraphicsOpacityEffect 

try :
    from qfluentwidgets import Theme as _FluentTheme ,setTheme as _fw_set_theme ,setThemeColor as _fw_set_theme_color 
    QFLUENT_AVAILABLE =True 
except Exception :
    QFLUENT_AVAILABLE =False 






@dataclass (frozen =True )
class ThemeTokens :
    id :str 
    display_name :str 

    bg_window :str 
    window_gradient :str 

    glass_base :str 
    glass_base_2 :str 
    glass_surface :str 
    glass_surface2 :str 
    glass_hover :str 
    glass_border :str 
    glass_border_s :str 

    text :str 
    text_muted :str 
    text_dim :str 

    accent_1 :str 
    accent_2 :str 
    accent_soft :str 
    accent_soft_2 :str 
    accent_text :str 

    danger_1 :str 
    danger_2 :str 

    base_field :str ="#1a1a21"
    alt_base :str ="#202028"
    button_bg :str ="#232330"
    dropdown_bg :str ="#24242e"
    menu_bg :str ="#21212a"
    bar_bg :str ="rgba(20,20,26,190)"



    warning_1 :str ="#ffb84d"
    warning_bg :str ="rgba(255, 184, 77, 20)"
    error_text :str ="#ff8080"
    error_bg :str ="rgba(255, 60, 60, 18)"
    success_1 :str ="#6fd68f"
    success_bg :str ="rgba(111, 214, 143, 18)"
    info_1 :str ="#9fd6ff"
    info_bg :str ="rgba(159, 214, 255, 16)"





    extra_css :str =""





    flat_buttons :bool =False 


THEMES :Dict [str ,ThemeTokens ]={}


def register_theme (tokens :ThemeTokens )->None :

    THEMES [tokens .id ]=tokens 







register_theme (ThemeTokens (
id ="ember",
display_name ="Ember (по умолчанию)",
bg_window ="#15151b",
window_gradient ="stop:0 #17171e, stop:0.5 #14141a, stop:1 #1b141a",
glass_base ="rgba(255, 255, 255, 10)",
glass_base_2 ="rgba(255, 255, 255, 5)",
glass_surface ="rgba(255, 255, 255, 16)",
glass_surface2 ="rgba(255, 255, 255, 22)",
glass_hover ="rgba(255, 255, 255, 30)",
glass_border ="rgba(255, 255, 255, 28)",
glass_border_s ="rgba(255, 255, 255, 14)",
text ="#f1f1f4",
text_muted ="#a8a8b3",
text_dim ="#75757f",
accent_1 ="#ff5b3d",
accent_2 ="#ff8c3d",
accent_soft ="rgba(255, 91, 61, 40)",
accent_soft_2 ="rgba(255, 91, 61, 18)",
accent_text ="#180a06",
danger_1 ="#e0454a",
danger_2 ="#c22f36",
))

DEFAULT_THEME_ID ="ember"

_LIQUID_GLASS_CSS ="""
    /* ---------- "Liquid Glass": глянцевые блики, круглые пилюли, ---------
       более выраженная стеклянная кромка (по мотивам Apple Liquid Glass). */
    QMainWindow, QDialog {
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 rgba(30, 42, 58, 235), stop:0.35 rgba(13, 18, 26, 235),
            stop:1 rgba(9, 13, 20, 235));
    }

    QPushButton {
        border-radius: 16px;
        border-top: 1px solid rgba(255, 255, 255, 130);
        border-left: 1px solid rgba(255, 255, 255, 40);
        border-right: 1px solid rgba(255, 255, 255, 40);
        border-bottom: 1px solid rgba(0, 0, 0, 60);
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 rgba(120, 190, 255, 235), stop:0.12 rgba(72, 156, 255, 235),
            stop:1 rgba(10, 132, 255, 235));
    }
    QPushButton:hover {
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 rgba(150, 205, 255, 235), stop:0.12 rgba(90, 170, 255, 235),
            stop:1 rgba(30, 145, 255, 235));
    }
    QPushButton:pressed { padding-top: 9px; border-top-color: rgba(255,255,255,60); }

    QPushButton#btn_secondary, QPushButton#node_action_btn {
        border-radius: 16px;
        border-top: 1px solid rgba(255, 255, 255, 70);
        border-left: 1px solid rgba(255, 255, 255, 22);
        border-right: 1px solid rgba(255, 255, 255, 22);
        border-bottom: 1px solid rgba(0, 0, 0, 60);
    }

    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QLineEdit#dark_field, QComboBox#dark_field, QSpinBox#dark_field, QDoubleSpinBox#dark_field,
    QTextEdit#dark_field, QTextEdit#code_field, QWidget#code_box {
        border-radius: 14px;
        border-top: 1px solid rgba(255, 255, 255, 55);
        border-left: 1px solid rgba(255, 255, 255, 18);
        border-right: 1px solid rgba(255, 255, 255, 18);
        border-bottom: 1px solid rgba(0, 0, 0, 55);
    }

    QGroupBox, QListWidget, QTreeWidget, QTreeView, QTabWidget::pane,
    QFrame#surface_frame, QFrame#resource_card, QFrame#folder_card {
        border-radius: 18px;
        border-top: 1px solid rgba(255, 255, 255, 55);
        border-left: 1px solid rgba(255, 255, 255, 16);
        border-right: 1px solid rgba(255, 255, 255, 16);
        border-bottom: 1px solid rgba(0, 0, 0, 55);
    }
    QFrame#resource_card:hover, QFrame#folder_card:hover {
        border-radius: 18px;
        border-top: 1px solid rgba(255, 255, 255, 90);
        border-left: 1px solid rgba(255, 255, 255, 26);
        border-right: 1px solid rgba(255, 255, 255, 26);
        border-bottom: 1px solid rgba(0, 0, 0, 55);
    }
    QFrame#resource_card[selected="true"], QFrame#folder_card[selected="true"] {
        border-radius: 18px;
        border-top: 2px solid rgba(255, 255, 255, 130);
        border-left: 2px solid rgba(100, 210, 255, 160);
        border-right: 2px solid rgba(100, 210, 255, 160);
        border-bottom: 2px solid rgba(10, 132, 255, 200);
    }

    /* Маленькие кнопки-чипы тегов текста (курсив/жирный/пауза и т.п. над
       полем реплики) - слишком малы для полновесного "стеклянного" скоса,
       им нужен свой, более сдержанный вид. */
    QPushButton#tag_chip_btn {
        border-radius: 7px;
        border-top: 1px solid rgba(255, 255, 255, 70);
        border-left: 1px solid rgba(255, 255, 255, 20);
        border-right: 1px solid rgba(255, 255, 255, 20);
        border-bottom: 1px solid rgba(0, 0, 0, 55);
        padding: 0 6px;
    }
    QPushButton#tag_chip_btn:hover {
        border-top-color: rgba(255, 255, 255, 110);
        background: rgba(10, 132, 255, 60);
    }

    QMenuBar, QToolBar, QStatusBar {
        background: rgba(16, 22, 32, 150);
        border-bottom: 1px solid rgba(255, 255, 255, 45);
    }
    QMenu {
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 45);
        background: rgba(20, 27, 38, 225);
    }

    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
        border-radius: 6px;
        border-top: 1px solid rgba(255, 255, 255, 60);
    }
"""



register_theme (ThemeTokens (
id ="liquid_glass",
display_name ="Liquid Glass",
bg_window ="#0b0f16",
window_gradient ="stop:0 #17222f, stop:0.45 #0c1119, stop:1 #090d14",
glass_base ="rgba(255, 255, 255, 16)",
glass_base_2 ="rgba(255, 255, 255, 8)",
glass_surface ="rgba(255, 255, 255, 24)",
glass_surface2 ="rgba(255, 255, 255, 32)",
glass_hover ="rgba(255, 255, 255, 42)",
glass_border ="rgba(255, 255, 255, 60)",
glass_border_s ="rgba(255, 255, 255, 26)",
text ="#f4f9ff",
text_muted ="#aac2d8",
text_dim ="#72899d",
accent_1 ="#0a84ff",
accent_2 ="#64d2ff",
accent_soft ="rgba(10, 132, 255, 46)",
accent_soft_2 ="rgba(10, 132, 255, 20)",
accent_text ="#031524",
danger_1 ="#ff6b6f",
danger_2 ="#e0454a",
base_field ="#101825",
alt_base ="#141d2a",
button_bg ="#16212e",
dropdown_bg ="#131c27",
menu_bg ="#121b25",
bar_bg ="rgba(14, 20, 29, 165)",
extra_css =_LIQUID_GLASS_CSS ,
))


def qcolor (value :str )->QColor :

    value =value .strip ()
    if value .startswith ("rgba"):
        nums =value [value .index ("(")+1 :value .index (")")].split (",")
        r ,g ,b ,a =(int (float (n .strip ()))for n in nums )
        return QColor (r ,g ,b ,a )
    if value .startswith ("rgb"):
        nums =value [value .index ("(")+1 :value .index (")")].split (",")
        r ,g ,b =(int (float (n .strip ()))for n in nums )
        return QColor (r ,g ,b )
    return QColor (value )






def _cyberpunk_css (accent_1 :str ,accent_2 :str ,accent_1_dark :str ,btn_text :str )->str :

    return f"""
        /* ---------- Cyberpunk HUD: резкие углы, неоновая рамка ---------- */
        QPushButton {{
            border-radius: 2px;
            border: 2px solid {accent_1_dark };
            background: {accent_1 };
            color: {btn_text };
            font-weight: 700;
            text-transform: uppercase;
        }}
        QPushButton:hover {{ background: {accent_2 }; border-color: {accent_2 }; }}
        QPushButton:pressed {{ background: {accent_1_dark }; border-color: {accent_1_dark }; }}
        QPushButton:disabled {{ background: rgba(255,255,255,8); border-color: rgba(255,255,255,20); color: rgba(255,255,255,60); }}

        QPushButton#btn_secondary, QPushButton#node_action_btn, QPushButton#tag_chip_btn,
        QPushButton#link_btn {{
            border-radius: 2px;
            border: 1px solid {accent_2 };
            background: rgba(0, 0, 0, 130);
            color: {accent_2 };
            font-weight: 600;
            text-transform: uppercase;
        }}
        QPushButton#btn_secondary:hover, QPushButton#node_action_btn:hover,
        QPushButton#tag_chip_btn:hover, QPushButton#link_btn:hover {{
            background: rgba(255, 255, 255, 18); border-color: {accent_1 }; color: {accent_1 };
        }}

        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QLineEdit#dark_field, QComboBox#dark_field, QSpinBox#dark_field, QDoubleSpinBox#dark_field,
        QTextEdit#dark_field, QTextEdit#code_field, QWidget#code_box {{
            border-radius: 2px;
            border: 1px solid {accent_1_dark };
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
        QLineEdit#dark_field:focus, QTextEdit#dark_field:focus, QTextEdit#code_field:focus {{
            border: 1px solid {accent_1 };
        }}

        QGroupBox, QListWidget, QTreeWidget, QTreeView, QTabWidget::pane,
        QFrame#surface_frame, QFrame#resource_card, QFrame#folder_card {{
            border-radius: 3px;
            border-top: 2px solid {accent_1 };
        }}
        QFrame#resource_card:hover, QFrame#folder_card:hover {{
            border-radius: 3px; border-top: 2px solid {accent_2 };
        }}
        QFrame#resource_card[selected="true"], QFrame#folder_card[selected="true"] {{
            border-radius: 3px; border: 2px solid {accent_1 };
        }}
        QGroupBox::title {{ color: {accent_1 }; text-transform: uppercase; font-weight: 700; }}

        QTabBar::tab:selected {{ border-bottom: 2px solid {accent_1 }; color: {accent_1 }; }}
        QProgressBar::chunk {{ background: {accent_1 }; border-radius: 2px; }}
        QCheckBox::indicator:checked {{ background: {accent_1 }; border-color: {accent_1_dark }; }}
        QSlider::handle:horizontal {{ background: {accent_1 }; border: 1px solid {accent_1_dark }; border-radius: 2px; }}
        QSlider::sub-page:horizontal {{ background: {accent_1 }; }}
    """




register_theme (ThemeTokens (
id ="cyberpunk_yellow",
display_name ="Cyberpunk: Neon Grid",
bg_window ="#0a0c10",
window_gradient ="stop:0 #10131c, stop:0.5 #0a0c10, stop:1 #0d0a14",
glass_base ="rgba(0, 224, 255, 10)",
glass_base_2 ="rgba(0, 224, 255, 5)",
glass_surface ="rgba(0, 224, 255, 16)",
glass_surface2 ="rgba(0, 224, 255, 22)",
glass_hover ="rgba(252, 238, 10, 26)",
glass_border ="rgba(0, 224, 255, 55)",
glass_border_s ="rgba(0, 224, 255, 24)",
text ="#eef6ff",
text_muted ="#93aabd",
text_dim ="#5f7688",
accent_1 ="#fcee0a",
accent_2 ="#00e0ff",
accent_soft ="rgba(252, 238, 10, 40)",
accent_soft_2 ="rgba(252, 238, 10, 16)",
accent_text ="#0a0c05",
danger_1 ="#ff2e4d",
danger_2 ="#c9142e",
base_field ="#0e1218",
alt_base ="#131822",
button_bg ="#141a24",
dropdown_bg ="#12161f",
menu_bg ="#10141c",
bar_bg ="rgba(8, 10, 14, 210)",
extra_css =_cyberpunk_css ("#fcee0a","#00e0ff","#b8ad08","#0a0c05"),
flat_buttons =True ,
))


_MINIMAL_CSS ="""
    /* ---------- Minimal: почти без "стекла", тихая серая палитра, ---------
       один нейтральный акцент, минимум скруглений. */
    QPushButton {
        border-radius: 4px; border: 1px solid rgba(255,255,255,10);
        background: #c9c9c9; color: #141414; font-weight: 500;
    }
    QPushButton:hover { background: #dcdcdc; }
    QPushButton:pressed { background: #b0b0b0; }
    QPushButton:disabled { background: rgba(255,255,255,7); color: rgba(255,255,255,32); border-color: rgba(255,255,255,7); }

    QPushButton#btn_secondary, QPushButton#node_action_btn, QPushButton#tag_chip_btn, QPushButton#link_btn {
        border-radius: 4px; border: 1px solid rgba(255,255,255,13);
        background: rgba(255,255,255,4); color: #d8d8d8; font-weight: 500;
    }
    QPushButton#btn_secondary:hover, QPushButton#node_action_btn:hover,
    QPushButton#tag_chip_btn:hover, QPushButton#link_btn:hover {
        background: rgba(255,255,255,9); border-color: rgba(255,255,255,24);
    }

    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QLineEdit#dark_field, QComboBox#dark_field, QSpinBox#dark_field, QDoubleSpinBox#dark_field,
    QTextEdit#dark_field, QTextEdit#code_field, QWidget#code_box {
        border-radius: 4px; border: 1px solid rgba(255,255,255,10);
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
    QLineEdit#dark_field:focus, QTextEdit#dark_field:focus, QTextEdit#code_field:focus {
        border: 1px solid rgba(255,255,255,45);
    }

    QGroupBox, QListWidget, QTreeWidget, QTreeView, QTabWidget::pane,
    QFrame#surface_frame, QFrame#resource_card, QFrame#folder_card {
        border-radius: 6px; border: 1px solid rgba(255,255,255,8);
    }
    QFrame#resource_card:hover, QFrame#folder_card:hover { border-color: rgba(255,255,255,22); }
    QFrame#resource_card[selected="true"], QFrame#folder_card[selected="true"] {
        border: 1px solid rgba(255,255,255,60); background: rgba(255,255,255,8);
    }

    QTabBar::tab:selected { border-bottom: 2px solid #c9c9c9; color: #f0f0f0; }
    QProgressBar::chunk { background: #c9c9c9; border-radius: 3px; }
    QCheckBox::indicator:checked { background: #c9c9c9; border-color: #c9c9c9; }
    QSlider::handle:horizontal { background: #c9c9c9; border: 1px solid rgba(0,0,0,60); border-radius: 7px; }
    QSlider::sub-page:horizontal { background: #c9c9c9; }
    QMenu { border-radius: 6px; border: 1px solid rgba(255,255,255,10); }
    QMenuBar, QToolBar, QStatusBar { border-bottom: 1px solid rgba(255,255,255,8); }
"""



register_theme (ThemeTokens (
id ="minimal",
display_name ="Minimal",
bg_window ="#1a1a1a",
window_gradient ="stop:0 #1c1c1c, stop:1 #181818",
glass_base ="rgba(255, 255, 255, 6)",
glass_base_2 ="rgba(255, 255, 255, 3)",
glass_surface ="rgba(255, 255, 255, 10)",
glass_surface2 ="rgba(255, 255, 255, 14)",
glass_hover ="rgba(255, 255, 255, 18)",
glass_border ="rgba(255, 255, 255, 16)",
glass_border_s ="rgba(255, 255, 255, 8)",
text ="#e8e8e8",
text_muted ="#9a9a9a",
text_dim ="#666666",
accent_1 ="#c9c9c9",
accent_2 ="#e6e6e6",
accent_soft ="rgba(201, 201, 201, 30)",
accent_soft_2 ="rgba(201, 201, 201, 14)",
accent_text ="#141414",
danger_1 ="#d9534f",
danger_2 ="#b33a37",
base_field ="#151515",
alt_base ="#191919",
button_bg ="#1f1f1f",
dropdown_bg ="#1c1c1c",
menu_bg ="#1a1a1a",
bar_bg ="rgba(15, 15, 15, 220)",
warning_1 ="#c9a227",
success_1 ="#5a9c6e",
info_1 ="#7a95a8",
extra_css =_MINIMAL_CSS ,
flat_buttons =True ,
))

_WIN11_CSS ="""
    /* ---------- Windows 11 Dark: скруглённые Fluent-контролы, ---------
       плоская синяя акцентная заливка, тонкая единая обводка. */
    QPushButton {
        border-radius: 6px; border: 1px solid rgba(255,255,255,14);
        background: #0078D4; color: #ffffff; font-weight: 600;
    }
    QPushButton:hover { background: #106ebe; }
    QPushButton:pressed { background: #005a9e; }
    QPushButton:disabled { background: rgba(255,255,255,7); color: rgba(255,255,255,32); border-color: rgba(255,255,255,7); }

    QPushButton#btn_secondary, QPushButton#node_action_btn, QPushButton#tag_chip_btn, QPushButton#link_btn {
        border-radius: 6px; border: 1px solid rgba(255,255,255,16);
        background: rgba(255,255,255,6); color: #f0f0f0; font-weight: 500;
    }
    QPushButton#btn_secondary:hover, QPushButton#node_action_btn:hover,
    QPushButton#tag_chip_btn:hover, QPushButton#link_btn:hover {
        background: rgba(255,255,255,12); border-color: rgba(255,255,255,28);
    }

    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QLineEdit#dark_field, QComboBox#dark_field, QSpinBox#dark_field, QDoubleSpinBox#dark_field,
    QTextEdit#dark_field, QTextEdit#code_field, QWidget#code_box {
        border-radius: 6px; border: 1px solid rgba(255,255,255,14);
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
    QLineEdit#dark_field:focus, QTextEdit#dark_field:focus, QTextEdit#code_field:focus {
        border: 1px solid #60cdff;
    }

    QGroupBox, QListWidget, QTreeWidget, QTreeView, QTabWidget::pane,
    QFrame#surface_frame, QFrame#resource_card, QFrame#folder_card {
        border-radius: 8px; border: 1px solid rgba(255,255,255,12);
    }
    QFrame#resource_card:hover, QFrame#folder_card:hover { border-color: rgba(255,255,255,26); }
    QFrame#resource_card[selected="true"], QFrame#folder_card[selected="true"] {
        border: 2px solid #60cdff; background: rgba(96,205,255,16); border-radius: 8px;
    }

    QTabBar::tab:selected { border-bottom: 2px solid #60cdff; color: #60cdff; }
    QProgressBar::chunk { background: #60cdff; border-radius: 4px; }
    QCheckBox::indicator:checked { background: #0078D4; border-color: #0078D4; }
    QSlider::handle:horizontal { background: #60cdff; border: 1px solid #0078D4; border-radius: 8px; }
    QSlider::sub-page:horizontal { background: #0078D4; }
    QMenu { border-radius: 8px; border: 1px solid rgba(255,255,255,14); }
    QMenuBar, QToolBar, QStatusBar { border-bottom: 1px solid rgba(255,255,255,12); }
"""



register_theme (ThemeTokens (
id ="win11_dark",
display_name ="Windows 11 Dark",
bg_window ="#202020",
window_gradient ="stop:0 #242424, stop:0.5 #202020, stop:1 #1f1f1f",
glass_base ="rgba(255, 255, 255, 7)",
glass_base_2 ="rgba(255, 255, 255, 4)",
glass_surface ="rgba(255, 255, 255, 12)",
glass_surface2 ="rgba(255, 255, 255, 16)",
glass_hover ="rgba(255, 255, 255, 22)",
glass_border ="rgba(255, 255, 255, 18)",
glass_border_s ="rgba(255, 255, 255, 10)",
text ="#f5f5f5",
text_muted ="#c5c5c5",
text_dim ="#8a8a8a",
accent_1 ="#0078D4",
accent_2 ="#60cdff",
accent_soft ="rgba(96, 205, 255, 35)",
accent_soft_2 ="rgba(96, 205, 255, 15)",
accent_text ="#ffffff",
danger_1 ="#c42b1c",
danger_2 ="#a4262c",
base_field ="#2b2b2b",
alt_base ="#2d2d2d",
button_bg ="#2b2b2b",
dropdown_bg ="#2b2b2b",
menu_bg ="#2c2c2c",
bar_bg ="rgba(32, 32, 32, 235)",
warning_1 ="#ffb900",
success_1 ="#6ccb5f",
info_1 ="#60cdff",
extra_css =_WIN11_CSS ,
flat_buttons =True ,
))

_GOOGLE_LIGHT_CSS ="""
    /* ---------- Google Light: белый фон, синий Material-акцент, --------
       плоские кнопки без обводки-блика (нужны тёмные, а не белые рамки). */
    QPushButton {
        border-radius: 4px; border: none;
        background: #1a73e8; color: #ffffff; font-weight: 600;
    }
    QPushButton:hover { background: #1765cc; }
    QPushButton:pressed { background: #185abc; }
    QPushButton:disabled { background: #f1f3f4; color: #9aa0a6; border: none; }

    QPushButton#btn_secondary, QPushButton#node_action_btn, QPushButton#tag_chip_btn, QPushButton#link_btn {
        border-radius: 4px; border: 1px solid #dadce0;
        background: #ffffff; color: #1a73e8; font-weight: 600;
    }
    QPushButton#btn_secondary:hover, QPushButton#node_action_btn:hover,
    QPushButton#tag_chip_btn:hover, QPushButton#link_btn:hover {
        background: #f8f9fa; border-color: #c6c9cc;
    }

    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox,
    QLineEdit#dark_field, QComboBox#dark_field, QSpinBox#dark_field, QDoubleSpinBox#dark_field,
    QTextEdit#dark_field, QTextEdit#code_field, QWidget#code_box {
        border-radius: 4px; border: 1px solid #dadce0; background: #ffffff; color: #202124;
    }
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus,
    QLineEdit#dark_field:focus, QTextEdit#dark_field:focus, QTextEdit#code_field:focus {
        border: 1px solid #1a73e8;
    }
    QComboBox QAbstractItemView { background: #ffffff; color: #202124; border: 1px solid #dadce0; }

    QGroupBox, QListWidget, QTreeWidget, QTreeView, QTabWidget::pane,
    QFrame#surface_frame, QFrame#resource_card, QFrame#folder_card {
        border-radius: 8px; border: 1px solid #dadce0; background: #ffffff;
    }
    QFrame#resource_card:hover, QFrame#folder_card:hover { border-color: #1a73e8; background: #f8f9fa; }
    QFrame#resource_card[selected="true"], QFrame#folder_card[selected="true"] {
        border: 2px solid #1a73e8; background: #e8f0fe; border-radius: 8px;
    }

    QTabBar::tab { color: #5f6368; }
    QTabBar::tab:selected { border-bottom: 2px solid #1a73e8; color: #1a73e8; }
    QTabBar::tab:hover:!selected { background: #f1f3f4; color: #202124; }
    QProgressBar::chunk { background: #1a73e8; border-radius: 4px; }
    QCheckBox::indicator:checked { background: #1a73e8; border-color: #1a73e8; }
    QSlider::handle:horizontal { background: #1a73e8; border: 1px solid #1765cc; border-radius: 8px; }
    QSlider::sub-page:horizontal { background: #1a73e8; }

    QMenu { background: #ffffff; color: #202124; border: 1px solid #dadce0; border-radius: 8px; }
    QMenu::item:selected { background: #e8f0fe; color: #1a73e8; }
    QMenuBar { background: #ffffff; color: #202124; border-bottom: 1px solid #dadce0; }
    QMenuBar::item:selected { background: #f1f3f4; color: #1a73e8; }
    QToolBar { background: #ffffff; border-bottom: 1px solid #dadce0; }
    QStatusBar { background: #ffffff; color: #5f6368; border-top: 1px solid #dadce0; }
    QScrollBar::handle:vertical, QScrollBar::handle:horizontal { background: #dadce0; border: none; }
    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover { background: #bdc1c6; }
    QListWidget::item:selected, QTreeWidget::item:selected { background: #e8f0fe; border: 1px solid #1a73e8; color: #1a73e8; }
    QToolTip { background: #202124; color: #ffffff; border: none; }
"""






def _build_palette (t :ThemeTokens )->QPalette :
    palette =QPalette ()
    palette .setColor (QPalette .ColorRole .Window ,QColor (t .bg_window ))
    palette .setColor (QPalette .ColorRole .WindowText ,QColor (t .text ))
    palette .setColor (QPalette .ColorRole .Base ,QColor (t .base_field ))
    palette .setColor (QPalette .ColorRole .AlternateBase ,QColor (t .alt_base ))
    palette .setColor (QPalette .ColorRole .Text ,QColor (t .text ))
    palette .setColor (QPalette .ColorRole .Button ,QColor (t .button_bg ))
    palette .setColor (QPalette .ColorRole .ButtonText ,QColor (t .text ))
    palette .setColor (QPalette .ColorRole .ToolTipBase ,QColor (t .button_bg ))
    palette .setColor (QPalette .ColorRole .ToolTipText ,QColor (t .text ))
    palette .setColor (QPalette .ColorRole .Highlight ,QColor (t .accent_1 ))
    palette .setColor (QPalette .ColorRole .HighlightedText ,QColor (t .accent_text ))
    palette .setColor (QPalette .ColorRole .PlaceholderText ,QColor (t .text_dim ))
    return palette 


def _build_stylesheet (t :ThemeTokens )->str :
    return f"""
        QWidget {{
            font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
            font-size: 13px;
            color: {t .text };
        }}

        QMainWindow, QDialog {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, {t .window_gradient });
        }}

        QToolTip {{
            background: {t .glass_surface2 }; color: {t .text }; border: 1px solid {t .glass_border };
            border-radius: 8px; padding: 5px 9px;
        }}

        /* ---------- Progress bars (git commit и т.п.) ---------- */
        QProgressBar {{
            background: {t .glass_base }; color: {t .accent_text }; border: 1px solid {t .glass_border_s };
            border-radius: 6px; text-align: center; font-weight: 600;
        }}
        QProgressBar::chunk {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t .accent_1 }, stop:1 {t .accent_2 });
            border-radius: 6px;
        }}

        /* ---------- Buttons: glassy pill with accent glow ---------- */
        QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t .accent_1 }, stop:1 {t .accent_2 });
            color: {t .accent_text }; border: 1px solid rgba(255,255,255,45);
            border-radius: 10px; padding: 8px 18px; font-weight: 600;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t .accent_1 }, stop:1 {t .accent_2 });
        }}
        QPushButton:pressed {{
            background: {t .accent_soft };
            padding-top: 9px;
        }}
        QPushButton:disabled {{
            background: rgba(255,255,255,10); color: {t .text_dim }; border-color: {t .glass_border_s };
        }}
        QPushButton:focus {{ outline: none; border: 1px solid {t .accent_2 }; }}

        QPushButton#btn_secondary {{
            background: {t .glass_surface }; color: {t .text }; border: 1px solid {t .glass_border };
            font-weight: 500;
        }}
        QPushButton#btn_secondary:hover {{
            background: {t .glass_hover }; border-color: {t .accent_1 };
        }}
        QPushButton#btn_secondary:pressed {{ background: {t .glass_base }; }}

        QPushButton#btn_danger {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t .danger_1 }, stop:1 {t .danger_2 });
            color: #fff; border: 1px solid rgba(255,255,255,35);
        }}
        QPushButton#btn_danger:hover {{ background: #ea5d61; }}
        QPushButton#btn_danger:pressed {{ background: {t .danger_2 }; }}

        /* ---------- Labels ---------- */
        QLabel {{ color: {t .text }; background: transparent; }}
        QLabel#section_title {{
            color: {t .accent_2 }; font-weight: 700; font-size: 11px;
            letter-spacing: 0.6px; text-transform: uppercase;
        }}

        /* ---------- Inputs: frosted glass fields ---------- */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background: {t .glass_base }; color: {t .text }; border: 1px solid {t .glass_border_s };
            border-radius: 9px; padding: 7px 11px;
            selection-background-color: {t .accent_1 }; selection-color: #fff;
        }}
        QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{ border-color: {t .glass_border }; }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {t .accent_1 }; background: {t .glass_surface };
        }}
        QLineEdit:disabled {{ color: {t .text_dim }; background: {t .glass_base_2 }; }}

        QComboBox {{
            background: {t .glass_surface }; color: {t .text }; border: 1px solid {t .glass_border_s };
            border-radius: 9px; padding: 7px 11px;
        }}
        QComboBox:hover {{ border-color: {t .glass_border }; background: {t .glass_hover }; }}
        QComboBox:focus {{ border-color: {t .accent_1 }; }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox::down-arrow {{ width: 10px; height: 10px; }}
        QComboBox QAbstractItemView {{
            background: {t .dropdown_bg }; color: {t .text }; border: 1px solid {t .glass_border };
            border-radius: 10px; padding: 5px; outline: none;
            selection-background-color: {t .accent_1 }; selection-color: #fff;
        }}

        QSpinBox, QDoubleSpinBox {{
            background: {t .glass_base }; color: {t .text }; border: 1px solid {t .glass_border_s };
            border-radius: 8px; padding: 5px 9px;
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {t .accent_1 }; }}

        /* ---------- Checkboxes (styled as soft glass toggles) ---------- */
        QCheckBox {{ color: {t .text }; spacing: 9px; background: transparent; }}
        QCheckBox::indicator {{
            width: 34px; height: 19px; border-radius: 10px;
            border: 1px solid {t .glass_border_s };
            background: {t .glass_base };
        }}
        QCheckBox::indicator:hover {{ border-color: {t .accent_soft }; }}
        QCheckBox::indicator:checked {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {t .accent_1 }, stop:1 {t .accent_2 });
            border-color: rgba(255,255,255,40);
        }}

        /* ---------- Scrollbars ---------- */
        QScrollBar:vertical {{ background: transparent; width: 20px; margin: 2px; }}
        QScrollBar::handle:vertical {{
            background: {t .glass_surface2 }; border: 1px solid {t .glass_border_s }; border-radius: 5px; min-height: 26px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {t .accent_soft }; border-color: {t .accent_1 }; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{ background: transparent; height: 20px; margin: 2px; }}
        QScrollBar::handle:horizontal {{
            background: {t .glass_surface2 }; border: 1px solid {t .glass_border_s }; border-radius: 5px; min-width: 26px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: {t .accent_soft }; border-color: {t .accent_1 }; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        QScrollBar::corner {{ background: transparent; }}

        /* ---------- Lists / Trees: glass cards ---------- */
        QListWidget, QTreeWidget, QTreeView {{
            background: {t .glass_base_2 }; color: {t .text }; border: 1px solid {t .glass_border_s };
            border-radius: 12px; padding: 5px; outline: none;
        }}
        QListWidget::item, QTreeWidget::item {{
            padding: 6px 8px; border-radius: 8px; margin: 1px 0;
        }}
        QListWidget::item:selected, QTreeWidget::item:selected {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {t .accent_soft }, stop:1 {t .accent_soft_2 });
            border: 1px solid {t .accent_1 }; color: {t .text };
        }}
        QListWidget::item:hover:!selected, QTreeWidget::item:hover:!selected {{
            background: {t .glass_hover };
        }}

        /* ---------- Tabs ---------- */
        QTabWidget::pane {{
            border: 1px solid {t .glass_border_s }; border-radius: 12px; background: {t .glass_base_2 }; top: -1px;
        }}
        QTabBar::tab {{
            background: transparent; color: {t .text_muted }; padding: 9px 20px;
            margin-right: 3px; border: none; border-bottom: 2px solid transparent;
        }}
        QTabBar::tab:selected {{
            background: {t .glass_surface }; color: {t .accent_2 }; font-weight: 600;
            border: 1px solid {t .glass_border_s }; border-bottom: 2px solid {t .accent_1 };
            border-top-left-radius: 8px; border-top-right-radius: 8px;
        }}
        QTabBar::tab:hover:!selected {{ color: {t .text }; background: {t .glass_hover }; }}

        /* ---------- Group boxes: frosted panels ---------- */
        QGroupBox {{
            background: {t .glass_base_2 };
            border: 1px solid {t .glass_border_s }; border-radius: 14px; margin-top: 12px;
            padding-top: 14px; color: {t .accent_2 }; font-weight: 600;
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 6px; }}

        /* ---------- Menus ---------- */
        QMenuBar {{
            background: {t .bar_bg }; color: {t .text }; padding: 3px;
            border-bottom: 1px solid {t .glass_border_s };
        }}
        QMenuBar::item {{ padding: 5px 11px; border-radius: 7px; background: transparent; }}
        QMenuBar::item:selected {{ background: {t .glass_hover }; color: {t .accent_2 }; }}
        QMenu {{
            background: {t .menu_bg }; color: {t .text }; border: 1px solid {t .glass_border };
            border-radius: 10px; padding: 5px;
        }}
        QMenu::item {{ padding: 7px 16px; border-radius: 7px; }}
        QMenu::item:selected {{ background: {t .accent_soft }; color: {t .text }; }}
        QMenu::separator {{ height: 1px; background: {t .glass_border_s }; margin: 5px 7px; }}

        /* ---------- Toolbar / status bar ---------- */
        QToolBar {{
            background: {t .bar_bg }; border-bottom: 1px solid {t .glass_border_s };
            spacing: 6px; padding: 5px 7px;
        }}
        QToolButton {{ border-radius: 8px; padding: 5px 7px; background: transparent; }}
        QToolButton:hover {{ background: {t .glass_hover }; }}
        QStatusBar {{
            background: {t .bar_bg }; color: {t .text_muted }; font-size: 11px;
            border-top: 1px solid {t .glass_border_s };
        }}

        /* ---------- Misc containers ---------- */
        QSplitter::handle {{ background: {t .glass_border_s }; }}
        QSplitter::handle:hover {{ background: {t .accent_1 }; }}
        QScrollArea {{ border: none; background: transparent; }}

        /* ---------- Sliders ---------- */
        QSlider::groove:horizontal {{
            background: {t .glass_base }; height: 5px; border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {t .accent_1 }, stop:1 {t .accent_2 });
            width: 15px; height: 15px; margin: -6px 0; border-radius: 8px;
            border: 1px solid rgba(255,255,255,45);
        }}
        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {t .accent_1 }, stop:1 {t .accent_2 });
            border-radius: 3px;
        }}
        QSlider::add-page:horizontal {{
            background: {t .glass_base }; border-radius: 3px;
        }}

        /* ---------- Общие "служебные" стили по objectName ----------
           Используются вместо точечных hardcoded setStyleSheet(...) по
           всему проекту, чтобы такие подписи тоже подхватывали тему и
           обновлялись мгновенно при переключении. */
        QLabel#hint_text {{ color: {t .text_dim }; font-size: 11px; background: transparent; }}
        QLabel#hint_text_bright {{ color: {t .text_muted }; font-size: 11px; background: transparent; }}
        QLabel#accent_caption {{ color: {t .accent_2 }; font-weight: 600; background: transparent; }}
        QLabel#warning_hint {{ color: {t .warning_1 }; font-weight: 600; background: transparent; }}
        QLabel#warning_banner {{
            color: {t .warning_1 }; background: {t .warning_bg }; border-radius: 4px;
        }}
        QLabel#error_mono, QPlainTextEdit#error_mono {{
            font-family: Consolas, monospace; color: {t .error_text }; background: {t .error_bg };
        }}
        QGroupBox#plain_box {{
            color: {t .text_dim }; border: 1px solid {t .glass_border_s };
            border-radius: 4px; margin-top: 8px; padding-top: 8px; background: transparent;
        }}
        QWidget#code_box, QLabel#code_box, QPlainTextEdit#code_box, QTextEdit#code_box {{
            background: {t .base_field }; color: {t .text_muted };
            border: 1px solid {t .glass_border_s }; border-radius: 4px;
            font-family: Consolas, monospace;
        }}
        QLabel#success_hint {{ color: {t .success_1 }; background: transparent; }}
        QLabel#success_banner {{ color: {t .success_1 }; background: {t .success_bg }; border-radius: 4px; }}
        QLabel#danger_hint {{ color: {t .danger_1 }; background: transparent; }}
        QLabel#danger_banner {{ color: {t .danger_1 }; background: {t .error_bg }; border-radius: 4px; }}
        QLabel#info_hint {{ color: {t .info_1 }; background: transparent; }}
        QLabel#info_banner {{ color: {t .info_1 }; background: {t .info_bg }; border-radius: 4px; }}

        QFrame#surface_frame {{
            background: {t .glass_surface }; border-radius: 6px; border: none;
        }}
        QPushButton#link_btn {{
            background: transparent; color: {t .accent_2 }; border: none; text-align: left;
            padding: 2px 4px; font-weight: 500;
        }}
        QPushButton#link_btn:hover {{ color: {t .accent_1 }; background: transparent; }}
        QPushButton#node_action_btn {{
            background: {t .button_bg }; color: {t .accent_2 }; border: 1px solid {t .glass_border_s };
            border-radius: 4px; padding: 4px;
        }}
        QPushButton#node_action_btn:hover {{ background: {t .glass_hover }; }}

        QPushButton#tag_chip_btn {{
            background: {t .glass_surface }; color: {t .text }; border: 1px solid {t .glass_border_s };
            border-radius: 5px; padding: 0 6px; font-weight: 500;
        }}
        QPushButton#tag_chip_btn:hover {{ background: {t .glass_hover }; border-color: {t .accent_1 }; }}
        QPushButton#tag_chip_btn:pressed {{ background: {t .accent_soft }; }}

        QComboBox#dark_field, QDoubleSpinBox#dark_field, QSpinBox#dark_field, QLineEdit#dark_field, QTextEdit#dark_field {{
            background: {t .base_field }; color: {t .text }; border: 1px solid {t .glass_border_s };
            border-radius: 4px; padding: 4px;
        }}
        QLineEdit#dark_field:focus, QTextEdit#dark_field:focus {{ border-color: {t .accent_1 }; }}
        QScrollArea#surface_scroll {{ border: none; background: {t .base_field }; }}
        QGraphicsView#node_canvas {{ background: {t .bg_window }; border: none; }}

        QTextEdit#code_field {{
            background: {t .base_field }; color: {t .text_muted }; border: 1px solid {t .glass_border_s };
            border-radius: 4px; padding: 4px; font-family: Consolas, monospace; font-size: 11px;
        }}
        QTextEdit#code_field:focus {{ border-color: {t .accent_1 }; }}

        /* ---------- Карточки ресурсов/папок (ui/resource_carousel.py) ---------- */
        QFrame#resource_card, QFrame#folder_card {{
            background: {t .glass_base_2 }; border: 1px solid {t .glass_border_s }; border-radius: 6px;
        }}
        QFrame#resource_card:hover, QFrame#folder_card:hover {{
            border-color: {t .accent_1 }; background: {t .glass_hover };
        }}
        QFrame#resource_card[selected="true"], QFrame#folder_card[selected="true"] {{
            background: {t .accent_soft_2 }; border: 2px solid {t .accent_1 }; border-radius: 6px;
        }}
    """+t .extra_css 






def fade_in_widget (widget :QWidget ,duration :int =260 ,start :float =0.0 ,end :float =1.0 )->QPropertyAnimation :

    effect =QGraphicsOpacityEffect (widget )
    widget .setGraphicsEffect (effect )
    anim =QPropertyAnimation (effect ,b"opacity",widget )
    anim .setDuration (duration )
    anim .setStartValue (start )
    anim .setEndValue (end )
    anim .setEasingCurve (QEasingCurve .Type .OutCubic )

    def _cleanup ():

        if widget .graphicsEffect ()is effect :
            widget .setGraphicsEffect (None )

    anim .finished .connect (_cleanup )
    widget ._theme_fade_anim =anim 
    anim .start ()
    return anim 


def crossfade_theme_switch (widget :QWidget ,duration :int =180 )->None :

    fade_in_widget (widget ,duration =duration ,start =0.35 ,end =1.0 )






class ThemeManager (QObject ):


    themeChanged =pyqtSignal (str )

    def __init__ (self )->None :
        super ().__init__ ()
        self ._current_id :str =DEFAULT_THEME_ID 
        self ._app :Optional [QApplication ]=None 

    def available (self )->List [ThemeTokens ]:
        return list (THEMES .values ())

    def tokens (self ,theme_id :Optional [str ]=None )->ThemeTokens :
        return THEMES .get (theme_id or self ._current_id ,THEMES [DEFAULT_THEME_ID ])

    @property 
    def current_id (self )->str :
        return self ._current_id 

    def apply (self ,app :QApplication ,theme_id :str ,animate_widget :Optional [QWidget ]=None )->None :
        tokens =THEMES .get (theme_id ,THEMES [DEFAULT_THEME_ID ])
        self ._app =app 
        self ._current_id =tokens .id 

        app .setPalette (_build_palette (tokens ))
        app .setStyleSheet (_build_stylesheet (tokens ))

        if QFLUENT_AVAILABLE :
            try :
                _fw_set_theme (_FluentTheme .DARK )
                _fw_set_theme_color (QColor (tokens .accent_1 ))
            except Exception :
                pass 

        self .themeChanged .emit (tokens .id )

        if animate_widget is not None :
            crossfade_theme_switch (animate_widget )


theme_manager =ThemeManager ()


def apply_dark_theme (app :QApplication ,theme_id :str =DEFAULT_THEME_ID )->None :

    theme_manager .apply (app ,theme_id )


def fit_window_to_screen (widget :QWidget ,desired_w :int ,desired_h :int ,
min_w :Optional [int ]=None ,min_h :Optional [int ]=None ,
screen_fraction :float =0.92 )->None :

    if min_w is None :
        min_w =desired_w 
    if min_h is None :
        min_h =desired_h 
    screen =widget .screen ()if widget .isVisible ()else QApplication .primaryScreen ()
    avail =screen .availableGeometry ()if screen else None 
    if avail is not None :
        cap_w =max (480 ,int (avail .width ()*screen_fraction ))
        cap_h =max (360 ,int (avail .height ()*screen_fraction ))
        desired_w ,min_w =min (desired_w ,cap_w ),min (min_w ,cap_w )
        desired_h ,min_h =min (desired_h ,cap_h ),min (min_h ,cap_h )
    widget .setMinimumSize (min_w ,min_h )
    widget .resize (desired_w ,desired_h )
