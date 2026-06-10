from __future__ import annotations

from collections import OrderedDict
from typing import Any

import pandas as pd

from backend.printing.core.adapters.exam_bag_common import safe_int_sort_key
from backend.printing.core.seat_layout import get_seat_mapping, layout_for_room


COMMON_SUBJECTS = {"语文", "数学", "英语"}
ELECTIVE_SUBJECTS = {"物理", "历史", "化学", "生物", "政治", "地理"}


def _clean(value: Any) -> str:
    text = str(value if value is not None else "").strip()
    return "" if text.lower() == "nan" else text


def _student(row: Any) -> dict:
    return {
        "name": _clean(row.get("姓名", "")),
        "examNo": _clean(row.get("考号", "")),
        "className": _clean(row.get("班级", "")),
        "seatNo": _clean(row.get("座位号", "")),
    }


def _subject_names(subjects: list[dict]) -> list[str]:
    result = []
    for item in subjects or []:
        name = _clean(item.get("name") if isinstance(item, dict) else item)
        if name and name not in result:
            result.append(name)
    return result


def _gaokao_display_names(exam_arrangement) -> dict[str, str]:
    settings = getattr(exam_arrangement, "gaokao_time_settings", {}) or {}
    exam_times = settings.get("examTimes", {}) if isinstance(settings, dict) else {}
    return {
        key: _clean((exam_times.get(key) or {}).get("subjectName")) or key
        for key in ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "政治", "地理"]
    }


def _append(groups, subject, room_name, room_no, row):
    key = (subject, room_no, room_name)
    if key not in groups:
        groups[key] = []
    groups[key].append(_student(row))


def _build_regular(exam_arrangement, subject_names: list[str]):
    df = exam_arrangement.arranged_students.fillna("")
    mode = getattr(exam_arrangement, "arrangement_mode", "normal_mode")
    groups = OrderedDict()
    for subject in subject_names:
        for _, row in df.iterrows():
            if mode == "subject_mode" and subject in ELECTIVE_SUBJECTS:
                selected = {_clean(row.get("首选")), _clean(row.get("选科1")), _clean(row.get("选科2"))}
                if subject not in selected:
                    continue
            _append(groups, subject, _clean(row.get("考场")), _clean(row.get("考场号")), row)
    return groups


def _build_gaokao(exam_arrangement):
    results = getattr(exam_arrangement, "gaokao_results", {}) or {}
    unified = results.get("unified")
    electives = results.get("electives") or {}
    display_names = _gaokao_display_names(exam_arrangement)
    groups = OrderedDict()

    if isinstance(unified, pd.DataFrame):
        for canonical in ["语文", "数学", "英语"]:
            for _, row in unified.fillna("").iterrows():
                _append(groups, display_names[canonical], _clean(row.get("考场")), _clean(row.get("考场号")), row)
        for canonical in ["物理", "历史"]:
            for _, row in unified.fillna("").iterrows():
                selected = _clean(row.get("物理历史科目")) or _clean(row.get("首选"))
                if not selected:
                    choice = _clean(row.get("选科"))
                    selected = "物理" if "物" in choice else ("历史" if "史" in choice else "")
                if selected == canonical:
                    _append(groups, display_names[canonical], _clean(row.get("考场")), _clean(row.get("考场号")), row)

    for canonical in ["化学", "生物", "政治", "地理"]:
        df = electives.get(canonical)
        if not isinstance(df, pd.DataFrame):
            continue
        for _, row in df.fillna("").iterrows():
            if _clean(row.get("科目类型")) == "自习":
                continue
            _append(groups, display_names[canonical], _clean(row.get("考场")), _clean(row.get("考场号")), row)
    return groups


def build_roll_call_groups(exam_arrangement, subjects: list[dict], seat_layout: dict) -> list[dict]:
    if getattr(exam_arrangement, "arrangement_mode", "") == "gaokao_mode" and getattr(exam_arrangement, "gaokao_results", None):
        grouped = _build_gaokao(exam_arrangement)
    else:
        names = _subject_names(subjects)
        if getattr(exam_arrangement, "arrangement_mode", "") == "subject_mode":
            names = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "政治", "地理"]
        if not names:
            names = ["考试科目"]
        grouped = _build_regular(exam_arrangement, names)

    ordered_names = []
    for subject, _, _ in grouped.keys():
        if subject not in ordered_names:
            ordered_names.append(subject)
    subject_order = {name: index for index, name in enumerate(ordered_names)}
    result = []
    errors = []
    for (subject, room_no, room_name), students in grouped.items():
        layout = layout_for_room(seat_layout, room_no)
        mapping = get_seat_mapping(layout)
        seen = set()
        for student in students:
            raw = student["seatNo"]
            try:
                seat_no = int(float(raw))
            except (TypeError, ValueError):
                errors.append(f"{subject}-{room_no or room_name}：座位号“{raw}”无法识别")
                continue
            if seat_no in seen:
                errors.append(f"{subject}-{room_no or room_name}：座位号 {seat_no} 重复")
            elif seat_no not in mapping:
                errors.append(f"{subject}-{room_no or room_name}：座位号 {seat_no} 超出布局容量")
            seen.add(seat_no)
            student["seatNo"] = seat_no

        result.append({
            "subject": subject,
            "roomName": room_name,
            "roomNo": room_no,
            "students": sorted(students, key=lambda item: int(item["seatNo"]) if isinstance(item["seatNo"], int) else 999999),
            "seatLayout": layout,
        })

    if errors:
        raise ValueError("；".join(errors[:20]) + ("；……" if len(errors) > 20 else ""))

    return sorted(
        result,
        key=lambda item: (subject_order.get(item["subject"], len(subject_order)), item["subject"], safe_int_sort_key(item["roomNo"]), item["roomName"]),
    )
