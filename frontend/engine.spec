# -*- mode: python ; coding: utf-8 -*-

import os
import sys

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

# Collect pandas and numpy bundled shared libraries
# pandas.libs is at site-packages/pandas.libs/, not inside the pandas package
pandas_binaries = []
numpy_binaries = []
_shared_lib_exts = (".dll",) if sys.platform == "win32" else (".dylib", ".so")
try:
    import pandas as pd
    site_packages = os.path.dirname(os.path.dirname(pd.__file__))
    pandas_libs_dir = os.path.join(site_packages, "pandas.libs")
    if os.path.isdir(pandas_libs_dir):
        for f in os.listdir(pandas_libs_dir):
            if any(f.endswith(ext) for ext in _shared_lib_exts):
                pandas_binaries.append((os.path.join(pandas_libs_dir, f), "."))
except Exception:
    pass
try:
    numpy_binaries = collect_dynamic_libs("numpy")
except Exception:
    pass


def _build_env_binaries():
    if sys.platform == "win32":
        env_bin_dir = os.path.join(sys.prefix, "Library", "bin")
        dll_names = [
            "ffi.dll",
            "libcrypto-3-x64.dll",
            "libssl-3-x64.dll",
            "libexpat.dll",
            # Visual C++ runtime (required by pandas C extensions)
            "vcomp140.dll",
            "vcruntime140_threads.dll",
            "msvcp140.dll",
            "msvcp140_1.dll",
            "msvcp140_2.dll",
            "msvcp140_atomic_wait.dll",
            "msvcp140_codecvt_ids.dll",
            "concrt140.dll",
            "vccorlib140.dll",
            "vcamp140.dll",
        ]
        binaries = []
        for dll_name in dll_names:
            candidate = os.path.join(env_bin_dir, dll_name)
            if os.path.exists(candidate):
                binaries.append((candidate, "."))
        return binaries

    # macOS / Linux: collect shared libraries from common locations
    binaries = []
    lib_dirs = [
        os.path.join(sys.prefix, "lib"),
        os.path.join(sys.prefix, "lib", "python" + ".".join(map(str, sys.version_info[:2])), "lib-dynload"),
    ]
    for lib_dir in lib_dirs:
        if not os.path.isdir(lib_dir):
            continue
        for f in os.listdir(lib_dir):
            if f.endswith(".dylib") or f.endswith(".so"):
                candidate = os.path.join(lib_dir, f)
                if os.path.isfile(candidate):
                    binaries.append((candidate, "."))
    return binaries


env_binaries = _build_env_binaries()

a = Analysis(
    [os.path.join(project_root, "backend", "__main__.py")],
    pathex=[project_root],
    binaries=env_binaries + ortools_binaries + pandas_binaries + numpy_binaries,
    datas=[
        (os.path.join(project_root, "backend", "resources"), "backend/resources"),
        (os.path.join(project_root, "\u4f7f\u7528\u8bf4\u660e\u4e66.pdf"), "."),
        (os.path.join(project_root, "\u4f7f\u7528\u8bf4\u660e\u4e66.md"), "."),
    ]
    + ortools_datas,
    hiddenimports=[
        "backend",
        "pandas",
        "openpyxl",
        "ortools",
        "ortools.sat.python.cp_model",
    ]
    + ortools_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "matplotlib",
        "matplotlib_inline",
        "contourpy",
        "kiwisolver",
        "fastapi",
        "starlette",
        "uvicorn",
        "websockets",
        "watchfiles",
        "werkzeug",
        "jinja2",
        "pyarrow",
        "fsspec",
        "pandas.plotting._matplotlib",
    ],
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
