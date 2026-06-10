from __future__ import annotations

from copy import deepcopy
from typing import Any


DEFAULT_LAYOUT = {
    "layoutName": "7行×6列",
    "layoutRows": 7,
    "layoutCols": 6,
    "layoutPattern": "S型竖排",
    "startPos": "left",
    "customColCounts": None,
}


def normalize_layout(value: Any) -> dict:
    source = value if isinstance(value, dict) else {}
    result = deepcopy(DEFAULT_LAYOUT)
    result.update({key: source[key] for key in DEFAULT_LAYOUT if key in source})

    custom = result.get("customColCounts")
    if isinstance(custom, list):
        custom = [max(0, int(item or 0)) for item in custom]
        custom = custom if any(custom) else None
    else:
        custom = None

    if custom:
        result["layoutName"] = "自定义"
        result["layoutCols"] = len(custom)
        result["layoutRows"] = max(custom)
        result["customColCounts"] = custom
    else:
        result["layoutRows"] = max(1, int(result.get("layoutRows") or 7))
        result["layoutCols"] = max(1, int(result.get("layoutCols") or 6))
        result["customColCounts"] = None

    if result.get("layoutPattern") not in {"S型横排", "S型竖排", "Z型横排", "Z型竖排"}:
        result["layoutPattern"] = DEFAULT_LAYOUT["layoutPattern"]
    result["startPos"] = "right" if result.get("startPos") == "right" else "left"
    return result


def normalize_seat_layout(value: Any, legacy_default: Any = None) -> dict:
    source = value if isinstance(value, dict) else {}
    default_source = source.get("defaultLayout")
    if not isinstance(default_source, dict):
        default_source = legacy_default

    overrides = {}
    raw_overrides = source.get("roomOverrides")
    if isinstance(raw_overrides, dict):
        for room_no, layout in raw_overrides.items():
            key = str(room_no or "").strip()
            if key and isinstance(layout, dict):
                overrides[key] = normalize_layout(layout)

    return {
        "defaultLayout": normalize_layout(default_source),
        "roomOverrides": overrides,
    }


def layout_for_room(seat_layout: Any, room_no: Any) -> dict:
    normalized = normalize_seat_layout(seat_layout)
    key = str(room_no or "").strip()
    return deepcopy(normalized["roomOverrides"].get(key, normalized["defaultLayout"]))


def layout_capacity(layout: Any) -> int:
    normalized = normalize_layout(layout)
    custom = normalized.get("customColCounts")
    if custom:
        return sum(custom)
    return normalized["layoutRows"] * normalized["layoutCols"]


def get_seat_mapping(layout: Any) -> dict[int, tuple[int, int]]:
    normalized = normalize_layout(layout)
    rows = normalized["layoutRows"]
    cols = normalized["layoutCols"]
    pattern = normalized["layoutPattern"]
    start_pos = normalized["startPos"]
    custom = normalized.get("customColCounts")
    mapping: dict[int, tuple[int, int]] = {}
    current_seat = 1

    def valid(row: int, col: int) -> bool:
        return custom is None or (0 <= col < len(custom) and row < custom[col])

    def actual_col(logical_col: int) -> int:
        return cols - 1 - logical_col if start_pos == "left" else logical_col

    def add(row: int, logical_col: int) -> None:
        nonlocal current_seat
        col = actual_col(logical_col)
        if valid(row, col):
            mapping[current_seat] = (row, col)
            current_seat += 1

    if pattern == "Z型横排":
        for row in range(rows):
            for col in range(cols):
                add(row, col)
    elif pattern == "S型横排":
        for row in range(rows):
            columns = range(cols) if row % 2 == 0 else range(cols - 1, -1, -1)
            for col in columns:
                add(row, col)
    elif pattern == "Z型竖排":
        for col in range(cols):
            for row in range(rows):
                add(row, col)
    else:
        for col in range(cols):
            rows_iter = range(rows) if col % 2 == 0 else range(rows - 1, -1, -1)
            for row in rows_iter:
                add(row, col)
    return mapping


def mirror_layout_start_pos(layout: Any, mirrored: bool = False) -> dict:
    normalized = normalize_layout(layout)
    if not mirrored:
        return normalized
    normalized["startPos"] = "left" if normalized["startPos"] == "right" else "right"
    return normalized
