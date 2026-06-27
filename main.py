
"""
RenPy Visual Script Editor
Визуальный конструктор сценариев для Ren'Py
"""
import sys

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
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
