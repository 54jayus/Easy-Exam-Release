from __future__ import annotations

import os
import sys
from pathlib import Path


def get_app_base_dir() -> Path:
    env_dir = os.getenv("EXAMFLOW_APP_DIR") or os.getenv("EXAMDESK_APP_DIR") or ""
    if env_dir.strip():
        return Path(env_dir).resolve()
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def _try_read_text(path: os.PathLike[str] | str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception:
        return ""


def load_manual_markdown() -> str:
    base = get_app_base_dir()
    candidates = [
        base / "backend" / "resources" / "使用说明书.md",
        base / "resources" / "使用说明书.md",
    ]
    for p in candidates:
        raw = _try_read_text(p)
        if raw.strip():
            return raw
    return "# 智能考务系统使用说明书\n\n（说明书内容未加载）\n"
