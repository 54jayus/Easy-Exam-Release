# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Get project root dynamically
# SPECPATH is the directory containing this .spec file (frontend/)
# Project root is one level up
project_root = os.path.dirname(SPECPATH)

a = Analysis(
    [os.path.join(project_root, 'backend', '__main__.py')],
    pathex=[project_root],
    binaries=[('D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\ffi.dll', '.'), ('D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\libcrypto-3-x64.dll', '.'), ('D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\libssl-3-x64.dll', '.'), ('D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\libexpat.dll', '.')],
    datas=[(os.path.join(project_root, 'backend', 'resources'), 'backend/resources')],
    hiddenimports=['backend', 'pandas', 'openpyxl', 'uvicorn', 'fastapi'],
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
    [],
    exclude_binaries=True,
    name='engine',
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='engine',
)
