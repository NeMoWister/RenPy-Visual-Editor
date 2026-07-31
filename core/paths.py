                       
"""
Определение «базовой папки» приложения - места, где должны лежать
resources/, resources_config.json, app_settings.json и т.п.

Это НЕ то же самое, что папка с исходным кодом/.exe внутри (для PyInstaller
--onefile код распаковывается во временную папку _MEIPASS при каждом
запуске, и писать туда что-либо бессмысленно - изменения исчезнут).

Правило:
- Запуск из собранного .exe (PyInstaller, sys.frozen == True) -
  базовая папка = папка, где лежит сам .exe (sys.executable).
- Запуск как обычный .py-скрипт - базовая папка = корень проекта
  (папка, где лежит main.py), как и было раньше.
"""
import sys
import os


def get_base_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(os.path.abspath(sys.executable))
                                                         
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def is_frozen() -> bool:
    return bool(getattr(sys, 'frozen', False))
