from PyInstaller.utils.hooks import collect_submodules

hiddenimports = (
    collect_submodules('core')
    + collect_submodules('ui')
)

a = Analysis(
    ['main.py'],
    hiddenimports=hiddenimports,
    datas=[],
    binaries=[],
    excludes=[
        'tkinter',
        'tests',
        'pytest'
    ]
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='RenPy Visual Editor',
    console=False,
    debug=False,
    strip=False,
    upx=False
)