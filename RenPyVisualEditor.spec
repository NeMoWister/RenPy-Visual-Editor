import os
import glob
from PyInstaller.utils.hooks import collect_data_files

spellchecker_datas = collect_data_files('spellchecker')
pymorphy_datas = collect_data_files('pymorphy3_dicts_ru')

# --------------------------------------------------------------------
# miniaudio и soundfile НЕ являются пакетами (это просто miniaudio.py /
# soundfile.py в корне site-packages + сопутствующие бинарники рядом), а
# не package/__init__.py - поэтому collect_data_files/collect_dynamic_libs/
# collect_all для них ничего не находят ("skipping ... as it is not a
# package" в логе сборки). Собираем нужные файлы вручную.
#
# Если сборка падает на "ModuleNotFoundError: No module named 'miniaudio'"
# прямо на этих строчках - значит pyinstaller запущен из другого
# окружения/venv, где miniaudio/soundfile не установлены (см. пояснение в
# конце файла).
# --------------------------------------------------------------------
import miniaudio as _miniaudio_probe
import soundfile as _soundfile_probe

_miniaudio_dir = os.path.dirname(os.path.abspath(_miniaudio_probe.__file__))
_soundfile_dir = os.path.dirname(os.path.abspath(_soundfile_probe.__file__))

# Скомпилированное CFFI-расширение _miniaudio* (.pyd/.so) лежит рядом с
# miniaudio.py в корне site-packages - кладём его тоже в корень бандла.
miniaudio_binaries = [
    (p, '.') for p in glob.glob(os.path.join(_miniaudio_dir, '_miniaudio*'))
    if os.path.isfile(p)
]

# soundfile грузит бинарный libsndfile через cffi по пути
# <рядом_с_soundfile.py>/_soundfile_data/... - это НЕ python-импорт, а
# dlopen() по строке, поэтому обычный анализ импортов PyInstaller его в
# принципе не может найти. Копируем всю папку _soundfile_data целиком,
# сохраняя её относительное расположение ('_soundfile_data'), иначе
# soundfile её на диске просто не найдёт.
_soundfile_data_dir = os.path.join(_soundfile_dir, '_soundfile_data')
soundfile_binaries = [
    (p, '_soundfile_data') for p in glob.glob(os.path.join(_soundfile_data_dir, '*'))
    if os.path.isfile(p)
]

if not miniaudio_binaries:
    print("!!! WARNING: не найден скомпилированный _miniaudio*.pyd/.so рядом с miniaudio.py "
          f"в {_miniaudio_dir} - waveform-декодер miniaudio в сборке работать не будет.")
if not soundfile_binaries:
    print("!!! WARNING: не найдена папка _soundfile_data рядом с soundfile.py "
          f"в {_soundfile_dir} - waveform-декодер soundfile в сборке работать не будет.")

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=miniaudio_binaries + soundfile_binaries,
    datas=spellchecker_datas + pymorphy_datas,
    # Подстраховка: miniaudio/soundfile импортируются лениво внутри
    # try/except в core/audio_waveform.py, а не при старте программы -
    # явно просим PyInstaller включить их в граф зависимостей.
    hiddenimports=['miniaudio', 'soundfile', 'cffi', '_cffi_backend'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RenPyVisualEditor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='D:/soft/renpy_visual_editor/favicon.ico'
)
