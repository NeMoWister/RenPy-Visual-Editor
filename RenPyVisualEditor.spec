from PyInstaller.utils.hooks import collect_data_files

spellchecker_datas = collect_data_files('spellchecker')
pymorphy_datas = collect_data_files('pymorphy3_dicts_ru')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=spellchecker_datas + pymorphy_datas,
    hiddenimports=[],
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