                       
from PyQt6.QtGui import QPalette, QColor

                                                                             
                                                                     
                                                                           
                                                                           
                                                                           
                                                                             

BG_WINDOW      = "#15151b"
GLASS_BASE     = "rgba(255, 255, 255, 10)"
GLASS_BASE_2   = "rgba(255, 255, 255, 5)"
GLASS_SURFACE  = "rgba(255, 255, 255, 16)"
GLASS_SURFACE2 = "rgba(255, 255, 255, 22)"
GLASS_HOVER    = "rgba(255, 255, 255, 30)"
GLASS_BORDER   = "rgba(255, 255, 255, 28)"
GLASS_BORDER_S = "rgba(255, 255, 255, 14)"

TEXT           = "#f1f1f4"
TEXT_MUTED     = "#a8a8b3"
TEXT_DIM       = "#75757f"

ACCENT_1       = "#ff5b3d"                                   
ACCENT_2       = "#ff8c3d"           
ACCENT_GLOW    = "rgba(255, 91, 61, 90)"
ACCENT_SOFT    = "rgba(255, 91, 61, 40)"
ACCENT_SOFT_2  = "rgba(255, 91, 61, 18)"
ACCENT_TEXT    = "#180a06"

DANGER_1       = "#e0454a"
DANGER_2       = "#c22f36"


def apply_dark_theme(app):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(BG_WINDOW))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Base, QColor("#1a1a21"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#202028"))
    palette.setColor(QPalette.ColorRole.Text, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Button, QColor("#232330"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("#232330"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(TEXT))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(ACCENT_1))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(ACCENT_TEXT))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(TEXT_DIM))
    app.setPalette(palette)
    app.setStyleSheet(f"""
        QWidget {{
            font-family: 'Segoe UI', 'Inter', Arial, sans-serif;
            font-size: 13px;
            color: {TEXT};
        }}

        QMainWindow, QDialog {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                stop:0 #17171e, stop:0.5 #14141a, stop:1 #1b141a);
        }}

        QToolTip {{
            background: {GLASS_SURFACE2}; color: {TEXT}; border: 1px solid {GLASS_BORDER};
            border-radius: 8px; padding: 5px 9px;
        }}

        /* ---------- Buttons: glassy pill with accent glow ---------- */
        QPushButton {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {ACCENT_1}, stop:1 {ACCENT_2});
            color: {ACCENT_TEXT}; border: 1px solid rgba(255,255,255,45);
            border-radius: 10px; padding: 8px 18px; font-weight: 600;
        }}
        QPushButton:hover {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #ff7050, stop:1 #ffa050);
        }}
        QPushButton:pressed {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #e0452c, stop:1 #e0762c);
            padding-top: 9px;
        }}
        QPushButton:disabled {{
            background: rgba(255,255,255,10); color: {TEXT_DIM}; border-color: {GLASS_BORDER_S};
        }}
        QPushButton:focus {{ outline: none; border: 1px solid #ffb37a; }}

        QPushButton#btn_secondary {{
            background: {GLASS_SURFACE}; color: {TEXT}; border: 1px solid {GLASS_BORDER};
            font-weight: 500;
        }}
        QPushButton#btn_secondary:hover {{
            background: {GLASS_HOVER}; border-color: {ACCENT_1};
        }}
        QPushButton#btn_secondary:pressed {{ background: {GLASS_BASE}; }}

        QPushButton#btn_danger {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {DANGER_1}, stop:1 {DANGER_2});
            color: #fff; border: 1px solid rgba(255,255,255,35);
        }}
        QPushButton#btn_danger:hover {{ background: #ea5d61; }}
        QPushButton#btn_danger:pressed {{ background: {DANGER_2}; }}

        /* ---------- Labels ---------- */
        QLabel {{ color: {TEXT}; background: transparent; }}
        QLabel#section_title {{
            color: {ACCENT_2}; font-weight: 700; font-size: 11px;
            letter-spacing: 0.6px; text-transform: uppercase;
        }}

        /* ---------- Inputs: frosted glass fields ---------- */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background: {GLASS_BASE}; color: {TEXT}; border: 1px solid {GLASS_BORDER_S};
            border-radius: 9px; padding: 7px 11px;
            selection-background-color: {ACCENT_1}; selection-color: #fff;
        }}
        QLineEdit:hover, QTextEdit:hover, QPlainTextEdit:hover {{ border-color: {GLASS_BORDER}; }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 1px solid {ACCENT_1}; background: {GLASS_SURFACE};
        }}
        QLineEdit:disabled {{ color: {TEXT_DIM}; background: {GLASS_BASE_2}; }}

        QComboBox {{
            background: {GLASS_SURFACE}; color: {TEXT}; border: 1px solid {GLASS_BORDER_S};
            border-radius: 9px; padding: 7px 11px;
        }}
        QComboBox:hover {{ border-color: {GLASS_BORDER}; background: {GLASS_HOVER}; }}
        QComboBox:focus {{ border-color: {ACCENT_1}; }}
        QComboBox::drop-down {{ border: none; width: 24px; }}
        QComboBox::down-arrow {{ width: 10px; height: 10px; }}
        QComboBox QAbstractItemView {{
            background: #24242e; color: {TEXT}; border: 1px solid {GLASS_BORDER};
            border-radius: 10px; padding: 5px; outline: none;
            selection-background-color: {ACCENT_1}; selection-color: #fff;
        }}

        QSpinBox, QDoubleSpinBox {{
            background: {GLASS_BASE}; color: {TEXT}; border: 1px solid {GLASS_BORDER_S};
            border-radius: 8px; padding: 5px 9px;
        }}
        QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {ACCENT_1}; }}

        /* ---------- Checkboxes (styled as soft glass toggles) ---------- */
        QCheckBox {{ color: {TEXT}; spacing: 9px; background: transparent; }}
        QCheckBox::indicator {{
            width: 34px; height: 19px; border-radius: 10px;
            border: 1px solid {GLASS_BORDER_S};
            background: {GLASS_BASE};
        }}
        QCheckBox::indicator:hover {{ border-color: {ACCENT_SOFT}; }}
        QCheckBox::indicator:checked {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT_1}, stop:1 {ACCENT_2});
            border-color: rgba(255,255,255,40);
        }}

        /* ---------- Scrollbars ---------- */
        QScrollBar:vertical {{ background: transparent; width: 20px; margin: 2px; }}
        QScrollBar::handle:vertical {{
            background: {GLASS_SURFACE2}; border: 1px solid {GLASS_BORDER_S}; border-radius: 5px; min-height: 26px;
        }}
        QScrollBar::handle:vertical:hover {{ background: {ACCENT_SOFT}; border-color: {ACCENT_1}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QScrollBar:horizontal {{ background: transparent; height: 20px; margin: 2px; }}
        QScrollBar::handle:horizontal {{
            background: {GLASS_SURFACE2}; border: 1px solid {GLASS_BORDER_S}; border-radius: 5px; min-width: 26px;
        }}
        QScrollBar::handle:horizontal:hover {{ background: {ACCENT_SOFT}; border-color: {ACCENT_1}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
        QScrollBar::corner {{ background: transparent; }}

        /* ---------- Lists / Trees: glass cards ---------- */
        QListWidget, QTreeWidget, QTreeView {{
            background: {GLASS_BASE_2}; color: {TEXT}; border: 1px solid {GLASS_BORDER_S};
            border-radius: 12px; padding: 5px; outline: none;
        }}
        QListWidget::item, QTreeWidget::item {{
            padding: 6px 8px; border-radius: 8px; margin: 1px 0;
        }}
        QListWidget::item:selected, QTreeWidget::item:selected {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT_SOFT}, stop:1 {ACCENT_SOFT_2});
            border: 1px solid {ACCENT_1}; color: {TEXT};
        }}
        QListWidget::item:hover:!selected, QTreeWidget::item:hover:!selected {{
            background: {GLASS_HOVER};
        }}

        /* ---------- Tabs ---------- */
        QTabWidget::pane {{
            border: 1px solid {GLASS_BORDER_S}; border-radius: 12px; background: {GLASS_BASE_2}; top: -1px;
        }}
        QTabBar::tab {{
            background: transparent; color: {TEXT_MUTED}; padding: 9px 20px;
            margin-right: 3px; border: none; border-bottom: 2px solid transparent;
        }}
        QTabBar::tab:selected {{
            background: {GLASS_SURFACE}; color: {ACCENT_2}; font-weight: 600;
            border: 1px solid {GLASS_BORDER_S}; border-bottom: 2px solid {ACCENT_1};
            border-top-left-radius: 8px; border-top-right-radius: 8px;
        }}
        QTabBar::tab:hover:!selected {{ color: {TEXT}; background: {GLASS_HOVER}; }}

        /* ---------- Group boxes: frosted panels ---------- */
        QGroupBox {{
            background: {GLASS_BASE_2};
            border: 1px solid {GLASS_BORDER_S}; border-radius: 14px; margin-top: 12px;
            padding-top: 14px; color: {ACCENT_2}; font-weight: 600;
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 14px; padding: 0 6px; }}

        /* ---------- Menus ---------- */
        QMenuBar {{
            background: rgba(20,20,26,190); color: {TEXT}; padding: 3px;
            border-bottom: 1px solid {GLASS_BORDER_S};
        }}
        QMenuBar::item {{ padding: 5px 11px; border-radius: 7px; background: transparent; }}
        QMenuBar::item:selected {{ background: {GLASS_HOVER}; color: {ACCENT_2}; }}
        QMenu {{
            background: #21212a; color: {TEXT}; border: 1px solid {GLASS_BORDER};
            border-radius: 10px; padding: 5px;
        }}
        QMenu::item {{ padding: 7px 16px; border-radius: 7px; }}
        QMenu::item:selected {{ background: {ACCENT_SOFT}; color: {TEXT}; }}
        QMenu::separator {{ height: 1px; background: {GLASS_BORDER_S}; margin: 5px 7px; }}

        /* ---------- Toolbar / status bar ---------- */
        QToolBar {{
            background: rgba(20,20,26,190); border-bottom: 1px solid {GLASS_BORDER_S};
            spacing: 6px; padding: 5px 7px;
        }}
        QToolButton {{ border-radius: 8px; padding: 5px 7px; background: transparent; }}
        QToolButton:hover {{ background: {GLASS_HOVER}; }}
        QStatusBar {{
            background: rgba(20,20,26,190); color: {TEXT_MUTED}; font-size: 11px;
            border-top: 1px solid {GLASS_BORDER_S};
        }}

        /* ---------- Misc containers ---------- */
        QSplitter::handle {{ background: {GLASS_BORDER_S}; }}
        QSplitter::handle:hover {{ background: {ACCENT_1}; }}
        QScrollArea {{ border: none; background: transparent; }}

        /* ---------- Sliders ---------- */
        QSlider::groove:horizontal {{
            background: {GLASS_BASE}; height: 5px; border-radius: 3px;
        }}
        QSlider::handle:horizontal {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {ACCENT_1}, stop:1 {ACCENT_2});
            width: 15px; height: 15px; margin: -6px 0; border-radius: 8px;
            border: 1px solid rgba(255,255,255,45);
        }}
        QSlider::sub-page:horizontal {{
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {ACCENT_1}, stop:1 {ACCENT_2});
            border-radius: 3px;
        }}
    """)
