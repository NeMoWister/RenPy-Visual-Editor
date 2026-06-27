from PyQt6.QtGui import QPalette, QColor

def apply_dark_theme(app):
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(30, 30, 35))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Base, QColor(22, 22, 28))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(35, 35, 42))
    palette.setColor(QPalette.ColorRole.Text, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Button, QColor(45, 45, 55))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(220, 220, 220))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(255, 140, 0))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(20, 20, 20))
    app.setPalette(palette)
    app.setStyleSheet("""
        QWidget { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; }
        QPushButton {
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #ff8c00,stop:1 #e07000);
            color: #111; border: none; border-radius: 5px; padding: 6px 14px; font-weight: bold;
        }
        QPushButton:hover { background: #ffaa33; }
        QPushButton:pressed { background: #c05a00; }
        QPushButton:disabled { background: #555; color: #888; }
        QPushButton#btn_secondary {
            background: #2d2d37; color: #ddd; border: 1px solid #ff8c00;
        }
        QPushButton#btn_secondary:hover { background: #3a3a48; }
        QPushButton#btn_danger {
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #cc3333,stop:1 #aa2222);
            color: white;
        }
        QLabel { color: #ddd; }
        QLabel#section_title { color: #ff8c00; font-weight: bold; font-size: 11px; }
        QLineEdit, QTextEdit, QPlainTextEdit {
            background: #16161c; color: #ddd; border: 1px solid #3a3a4a;
            border-radius: 4px; padding: 4px 8px;
            selection-background-color: #ff8c00; selection-color: #111;
        }
        QLineEdit:focus, QTextEdit:focus { border-color: #ff8c00; }
        QComboBox {
            background: #2d2d37; color: #ddd; border: 1px solid #3a3a4a;
            border-radius: 4px; padding: 4px 8px;
        }
        QComboBox:focus { border-color: #ff8c00; }
        QComboBox::drop-down { border: none; width: 20px; }
        QComboBox QAbstractItemView {
            background: #2d2d37; color: #ddd; border: 1px solid #ff8c00;
            selection-background-color: #ff8c00; selection-color: #111;
        }
        QScrollBar:vertical { background: #1e1e23; width: 8px; border-radius: 4px; }
        QScrollBar::handle:vertical { background: #ff8c00; border-radius: 4px; min-height: 20px; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QScrollBar:horizontal { background: #1e1e23; height: 8px; }
        QScrollBar::handle:horizontal { background: #ff8c00; border-radius: 4px; }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
        QListWidget {
            background: #16161c; color: #ddd; border: 1px solid #3a3a4a; border-radius: 4px;
        }
        QListWidget::item:selected { background: #ff8c00; color: #111; }
        QListWidget::item:hover { background: #2d2d37; }
        QTabWidget::pane { border: 1px solid #3a3a4a; background: #1e1e23; }
        QTabBar::tab { background: #2d2d37; color: #aaa; padding: 6px 16px; margin-right: 2px; border: none; }
        QTabBar::tab:selected { background: #ff8c00; color: #111; font-weight: bold; }
        QTabBar::tab:hover { background: #3a3a48; }
        QGroupBox {
            border: 1px solid #3a3a4a; border-radius: 6px; margin-top: 8px;
            padding-top: 8px; color: #ff8c00; font-weight: bold;
        }
        QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
        QSpinBox, QDoubleSpinBox {
            background: #16161c; color: #ddd; border: 1px solid #3a3a4a; border-radius: 4px; padding: 3px 6px;
        }
        QCheckBox { color: #ddd; }
        QCheckBox::indicator { width: 14px; height: 14px; border: 1px solid #3a3a4a; border-radius: 3px; background: #16161c; }
        QCheckBox::indicator:checked { background: #ff8c00; border-color: #ff8c00; }
        QMenuBar { background: #16161c; color: #ddd; }
        QMenuBar::item:selected { background: #ff8c00; color: #111; }
        QMenu { background: #2d2d37; color: #ddd; border: 1px solid #3a3a4a; }
        QMenu::item:selected { background: #ff8c00; color: #111; }
        QToolBar { background: #16161c; border-bottom: 1px solid #3a3a4a; spacing: 4px; }
        QStatusBar { background: #16161c; color: #888; font-size: 11px; }
        QSplitter::handle { background: #3a3a4a; }
        QMainWindow { background: #1e1e23; }
        QScrollArea { border: none; background: transparent; }
        QDialog { background: #1e1e23; }
    """)
