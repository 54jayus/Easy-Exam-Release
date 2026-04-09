from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Sequence


@dataclass(frozen=True)
class Subject:
    name: str
    exam_date: str
    exam_time: str
    remark: str = ""
    duration_minutes: int = 0
    room_count: int = 0


@dataclass(frozen=True)
class SubjectImportResult:
    subjects: list[Subject]
    errors: list[str]


def _normalize_subject_name(value: object) -> str:
    return ("" if value is None else str(value)).strip()


def _parse_date(value: object) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    try:
        import pandas as pd

        if isinstance(value, pd.Timestamp):
            return value.strftime("%Y-%m-%d")
    except Exception:
        pass

    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None

    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue

    parts = s.split("/")
    if len(parts) == 3:
        try:
            y = int(parts[0])
            m = int(parts[1])
            d = int(parts[2])
            return date(y, m, d).strftime("%Y-%m-%d")
        except Exception:
            return None
    return None


def _parse_time_range(value: object) -> tuple[str, int, int] | None:
    s = ("" if value is None else str(value)).strip()
    if not s or s.lower() == "nan":
        return None
    if "-" not in s:
        return None
    start_raw, end_raw = [p.strip() for p in s.split("-", 1)]
    if not start_raw or not end_raw:
        return None

    def parse_one(x: str) -> time | None:
        for fmt in ("%H:%M",):
            try:
                return datetime.strptime(x, fmt).time()
            except Exception:
                continue
        return None

    start_t = parse_one(start_raw)
    end_t = parse_one(end_raw)
    if start_t is None or end_t is None:
        return None
    start_min = start_t.hour * 60 + start_t.minute
    end_min = end_t.hour * 60 + end_t.minute
    if start_min >= end_min:
        return None
    normalized = f"{start_t.strftime('%H:%M')}-{end_t.strftime('%H:%M')}"
    return normalized, start_min, end_min


def _coerce_non_negative_int(value: object) -> int | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    try:
        numeric = int(float(s))
        return numeric if numeric >= 0 else None
    except Exception:
        return None


def _coerce_duration_minutes(value: object) -> int | None:
    return _coerce_non_negative_int(value)


def _coerce_room_count(value: object) -> int | None:
    return _coerce_non_negative_int(value)


def validate_subjects(subjects: Sequence[Subject]) -> list[str]:
    errors: list[str] = []
    seen_names: set[str] = set()

    for idx, subject in enumerate(subjects):
        row = idx + 1
        name = _normalize_subject_name(subject.name)
        if not name:
            errors.append(f"第{row}行数据错误：科目名称不能为空")
            continue
        if name in seen_names:
            errors.append(f"第{row}行数据错误：科目名称重复（{name}）")
            continue
        seen_names.add(name)

        if not subject.exam_date:
            errors.append(f"第{row}行数据错误：考试日期不能为空")
            continue
        if not subject.exam_time:
            errors.append(f"第{row}行数据错误：考试时间不能为空")
            continue
        if _parse_time_range(subject.exam_time) is None:
            errors.append(
                f"第{row}行数据错误：考试时间格式不正确，应为HH:mm-HH:mm或H:mm-H:mm（如：9:00-11:30）"
            )
            continue

        room_count = _coerce_room_count(getattr(subject, "room_count", 0))
        if room_count is None:
            errors.append(f"第{row}行数据错误：考场数量必须是非负整数")

    return errors
