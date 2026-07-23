"""
RenPy Visual Script Editor
Визуальный конструктор сценариев для Ren'Py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RenPy Visual Script Editor")
    app.setStyle("Fusion")
    from ui.theme import apply_dark_theme
    apply_dark_theme(app)
    window = MainWindow()
    if getattr(window, "_restored_geometry", False):
        window.show()
    else:
        window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
