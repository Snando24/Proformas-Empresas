# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\andy_\\Documents\\Taller\\APP_TALLER\\desktop_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\andy_\\Documents\\Taller\\APP_TALLER\\static', 'static'), ('C:\\Users\\andy_\\Documents\\Taller\\APP_TALLER\\proforma_app', 'proforma_app')],
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
    name='ProformasTractotec',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\Users\\andy_\\Documents\\Taller\\APP_TALLER\\static\\assets\\app-icon.ico'],
)
