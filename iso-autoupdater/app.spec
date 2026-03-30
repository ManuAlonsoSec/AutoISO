# app.spec
import sys
from PyInstaller.building.build_main import Analysis, PYZ, EXE, BUNDLE, COLLECT

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('icon.ico', '.'),          # bundle the app icon
    ],
    hiddenimports=[
        'PyQt6.sip',
        'qt_material',
        'bs4',
        'lxml',
    ],
    hookspath=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='ISOAutoupdater',
    debug=False,
    strip=False,
    upx=True,
    console=False,        # no console window on Windows
    icon='icon.ico',
)

# macOS only — wraps into a .app bundle
app = BUNDLE(
    exe,
    name='ISOAutoupdater.app',
    icon='icon.icns',     # Note: normally .icns, fallback to .ico if not converted
    bundle_identifier='com.manualonsosec.isoautoupdater',
)
