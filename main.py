"""
RenPy Visual Script Editor
Визуальный конструктор сценариев для Ren'Py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from core.paths import get_base_dir
from core.app_settings import AppSettings
from core.i18n import init_translator
from ui.main_window import MainWindow


def main():                                                                
    app_settings = AppSettings.load(get_base_dir())
    init_translator(app_settings.language)                                               
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("RenPy Visual Script Editor")
    app.setStyle("Fusion")
    from ui.theme import theme_manager, fade_in_widget
    theme_manager.apply(app, app_settings.theme)
    window = MainWindow()
    if getattr(window, "_restored_geometry", False):
        window.show()
    else:
        window.showMaximized()
    fade_in_widget(window, duration=320)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
