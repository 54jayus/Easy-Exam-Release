from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Iterable, List, Optional, Sequence


@dataclass(frozen=True)
class Subject:
    name: str
    exam_date: str
    exam_time: str
    remark: str = ""
    duration_minutes: int = 0


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


def _coerce_duration_minutes(value: object) -> int | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s or s.lower() == "nan":
        return None
    try:
        minutes = int(float(s))
        return minutes if minutes >= 0 else None
    except Exception:
        return None


def validate_subjects(subjects: Sequence[Subject]) -> list[str]:
    errors: list[str] = []
    seen_names: set[str] = set()
    date_slots: dict[str, list[tuple[int, int, str, str, int]]] = {}

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

        tr = _parse_time_range(subject.exam_time)
        if tr is None:
            errors.append(
                f"第{row}行数据错误：考试时间格式不正确，应为HH:mm-HH:mm或H:mm-H:mm（如：09:00-11:30 或 9:00-11:30）"
            )
            continue
        normalized_time, start_min, end_min = tr
        exam_date = subject.exam_date
        for s_min, e_min, exist_name, exist_time, exist_row in date_slots.get(exam_date, []):
            if not (end_min <= s_min or start_min >= e_min):
                errors.append(
                    f"第{row}行（{name}）与第{exist_row}行（{exist_name}）在{exam_date}考试时间冲突：{normalized_time} 与 {exist_time}"
                )
                break
        date_slots.setdefault(exam_date, []).append((start_min, end_min, name, normalized_time, row))

    return errors

