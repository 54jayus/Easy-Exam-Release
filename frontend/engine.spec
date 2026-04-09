# -*- mode: python ; coding: utf-8 -*-

import os

from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs, collect_submodules

# Get project root dynamically
# SPECPATH is the directory containing this .spec file (frontend/)
# Project root is one level up
project_root = os.path.dirname(SPECPATH)

ortools_hiddenimports = []
ortools_datas = []
ortools_binaries = []
try:
    ortools_hiddenimports = collect_submodules("ortools")
    ortools_datas = collect_data_files("ortools")
    ortools_binaries = collect_dynamic_libs("ortools")
except Exception:
    ortools_hiddenimports = []
    ortools_datas = []
    ortools_binaries = []

a = Analysis(
    [os.path.join(project_root, "backend", "__main__.py")],
    pathex=[project_root],
    binaries=[
        ("D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\ffi.dll", "."),
        ("D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\libcrypto-3-x64.dll", "."),
        ("D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\libssl-3-x64.dll", "."),
        ("D:\\ANACONDA\\envs\\exam_scheduler\\Library\\bin\\libexpat.dll", "."),
    ]
    + ortools_binaries,
    datas=[
        (os.path.join(project_root, "backend", "resources"), "backend/resources"),
        (os.path.join(project_root, "浣跨敤璇存槑涔?pdf"), "."),
        (os.path.join(project_root, "浣跨敤璇存槑涔?md"), "."),
    ]
    + ortools_datas,
    hiddenimports=[
        "backend",
        "pandas",
        "openpyxl",
        "uvicorn",
        "fastapi",
        "ortools",
        "ortools.sat.python.cp_model",
    ]
    + ortools_hiddenimports,
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
    name="engine",
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
    name="engine",
)
