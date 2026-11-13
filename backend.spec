# PyInstaller configuration for the Excel Data Visualizer backend.
#
# Produces a folder with one executable that runs the API and, when the React
# app was built first (`npm run build`), also serves the web page on the same
# port. Build from the repository root:
#
#   pyinstaller backend.spec --clean --noconfirm --workpath pyinstaller-work
#
# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

# The built React app. Only index.html, its sibling files and static/ are
# taken, so a PyInstaller work folder left inside build/ is never bundled.
frontend = []
if os.path.isfile(os.path.join('build', 'index.html')):
    for name in os.listdir('build'):
        if os.path.isfile(os.path.join('build', name)):
            frontend.append((os.path.join('build', name), 'frontend'))
    if os.path.isdir(os.path.join('build', 'static')):
        frontend.append((os.path.join('build', 'static'), os.path.join('frontend', 'static')))
else:
    print('WARNING: build/index.html not found; the package will not include the web page. '
          'Run "npm run build" first.')

a = Analysis(
    ['start_backend.py'],
    # start_backend imports `app` from backend/; analysing it from here
    # bundles every backend module and library it uses.
    pathex=['backend'],
    binaries=[],
    datas=frontend,
    hiddenimports=[
        # pandas loads these lazily when reading .xlsx / .xls files
        'openpyxl',
        'xlrd',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'IPython', 'pytest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='excel-visualizer-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='excel-visualizer-backend',
)
