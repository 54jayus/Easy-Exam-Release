from __future__ import annotations

import sys
from pathlib import Path


def _maybe_add_legacy_v35_to_sys_path() -> None:
    project_root = Path(__file__).resolve().parent.parent
    legacy_root = project_root / "v35（增加台角纸）"
    if legacy_root.exists() and legacy_root.is_dir():
        legacy_str = str(legacy_root)
        if legacy_str not in sys.path:
            sys.path.append(legacy_str)


_maybe_add_legacy_v35_to_sys_path()

