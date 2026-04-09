from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

try:
    from ortools.sat.python import cp_model
except Exception:  # pragma: no cover - handled at runtime
    cp_model = None

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubjectContext:
    subject_id: int
    name: str
    exam_date: str
    exam_time: str
    duration_minutes: int
    start_minute: int
    end_minute: int
    sort_key: tuple[int, int]

def _normalize_report_number(value: float | int | None) -> int | float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except Exception:
        return value
    rounded = round(numeric)
    if abs(numeric - rounded) < 1e-9:
        return int(rounded)
    return round(numeric, 6)

def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        return int(float(str(value).strip()))
    except Exception:
        return default
