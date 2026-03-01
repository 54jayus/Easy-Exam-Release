# -*- mode: python ; coding: utf-8 -*-

import os
import sys

# Get project root dynamically
if getattr(sys, 'frozen', False):
    project_root = os.path.dirname(sys.executable)
else:
    # When running from frontend/engine.spec, go up one level to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

a = Analysis(
    [os.path.join(project_root, 'backend', '__main__.py')],
    pathex=[project_root],
    binaries=[('D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\ffi.dll', '.'), ('D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\libcrypto-3-x64.dll', '.'), ('D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\libssl-3-x64.dll', '.'), ('D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\libexpat.dll', '.')],
    datas=[],
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
