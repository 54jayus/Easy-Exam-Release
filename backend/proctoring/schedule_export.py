from __future__ import annotations

from typing import Any, Sequence

import pandas as pd

from .core.entities import EXEMPT_SLOT_MARKER
from .core.models import Schedule


_INVALID_SHEET_CHARS = ["\\", "/", "*", "?", ":", "[", "]"]


def _subject_name(subject_id: int, subject_names: Sequence[str]) -> str:
    if 0 <= subject_id - 1 < len(subject_names) and subject_names[subject_id - 1]:
        return str(subject_names[subject_id - 1])
    return f"科目{subject_id}"


def _exam_date(subject_id: int, exam_dates: Sequence[str]) -> str:
    if 0 <= subject_id - 1 < len(exam_dates) and exam_dates[subject_id - 1]:
        return str(exam_dates[subject_id - 1])
    return ""


def _exam_time(subject_id: int, exam_times: Sequence[str]) -> str:
    if 0 <= subject_id - 1 < len(exam_times) and exam_times[subject_id - 1]:
        return str(exam_times[subject_id - 1])
    return ""


def _subject_header(subject_id: int, subject_names: Sequence[str], exam_times: Sequence[str]) -> str:
    return f"{_subject_name(subject_id, subject_names)}\n{_exam_time(subject_id, exam_times)}"


def _double_subject_headers(
    subject_id: int,
    subject_names: Sequence[str],
    exam_times: Sequence[str],
) -> tuple[str, str]:
    base = _subject_header(subject_id, subject_names, exam_times)
    name, _, time_text = base.partition("\n")
    return f"{name}-监考员1\n{time_text}", f"{name}-监考员2\n{time_text}"


def _all_room_numbers(schedule: Schedule) -> list[int]:
    exams = schedule.exams or []
    rooms = sorted({int(room) for exam in exams for room in getattr(exam, "rooms", []) or [] if int(room) > 0})
    if rooms:
        return rooms
    return list(range(1, int(schedule.num_rooms or 0) + 1))


def _build_overview_dataframe(
    *,
    schedule: Schedule,
    subject_names: Sequence[str],
    exam_times: Sequence[str],
) -> pd.DataFrame:
    exams = schedule.exams or []
    num_subjects = max((exam.subject_id for exam in exams), default=int(schedule.num_subjects or 0))
    all_rooms = _all_room_numbers(schedule)

    rows: list[dict[str, str]] = []
    for room in all_rooms:
        row: dict[str, str] = {"考场": f"考场{room}"}
        for subject_id in range(1, num_subjects + 1):
            if schedule.mode == "double":
                col1, col2 = _double_subject_headers(subject_id, subject_names, exam_times)
                row[col1] = ""
                row[col2] = ""
            else:
                row[_subject_header(subject_id, subject_names, exam_times)] = ""
        rows.append(row)

    room_index_map = {room: idx for idx, room in enumerate(all_rooms)}
    for exam in exams:
        for room in getattr(exam, "rooms", []) or []:
            if room not in room_index_map:
                continue
            idx = room_index_map[room]
            teachers = list((exam.schedule or {}).get(room, []))
            if schedule.mode == "double":
                col1, col2 = _double_subject_headers(exam.subject_id, subject_names, exam_times)
                if schedule.is_position_exempt(exam.subject_id, room, 0):
                    rows[idx][col1] = EXEMPT_SLOT_MARKER
                elif len(teachers) >= 1 and teachers[0] is not None:
                    rows[idx][col1] = teachers[0].name

                if schedule.is_position_exempt(exam.subject_id, room, 1):
                    rows[idx][col2] = EXEMPT_SLOT_MARKER
                elif len(teachers) >= 2 and teachers[1] is not None:
                    rows[idx][col2] = teachers[1].name
            else:
                col = _subject_header(exam.subject_id, subject_names, exam_times)
                if schedule.is_position_exempt(exam.subject_id, room, 0):
                    rows[idx][col] = EXEMPT_SLOT_MARKER
                else:
                    rows[idx][col] = ", ".join(t.name for t in teachers if t is not None)

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _build_time_overview_dataframe(
    *,
    schedule: Schedule,
    subject_names: Sequence[str],
    exam_dates: Sequence[str],
    exam_times: Sequence[str],
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for exam in schedule.exams or []:
        date_text = _exam_date(exam.subject_id, exam_dates)
        time_text = _exam_time(exam.subject_id, exam_times)
        subject_name = _subject_name(exam.subject_id, subject_names)
        room_locations = getattr(exam, "room_locations", {}) or {}
        for room in sorted(getattr(exam, "rooms", []) or []):
            teachers = list((exam.schedule or {}).get(room, []))
            row: dict[str, Any] = {
                "日期": date_text,
                "时间": time_text,
                "科目": subject_name,
                "考场编号": room,
                "考场": room_locations.get(room) or f"考场{room}",
            }
            if schedule.mode == "double":
                row["监考教师1"] = (
                    EXEMPT_SLOT_MARKER
                    if schedule.is_position_exempt(exam.subject_id, room, 0)
                    else teachers[0].name if len(teachers) >= 1 and teachers[0] is not None else ""
                )
                row["监考教师2"] = (
                    EXEMPT_SLOT_MARKER
                    if schedule.is_position_exempt(exam.subject_id, room, 1)
                    else teachers[1].name if len(teachers) >= 2 and teachers[1] is not None else ""
                )
            else:
                row["监考教师"] = (
                    EXEMPT_SLOT_MARKER
                    if schedule.is_position_exempt(exam.subject_id, room, 0)
                    else ", ".join(t.name for t in teachers if t is not None)
                )
            rows.append(row)

    rows.sort(
        key=lambda item: (
            str(item.get("日期") or ""),
            str(item.get("时间") or ""),
            str(item.get("科目") or ""),
            int(item.get("考场编号") or 0),
        )
    )
    return pd.DataFrame(rows) if rows else pd.DataFrame()


def _build_stats_dataframe(
    *,
    schedule: Schedule,
    subject_names: Sequence[str],
) -> pd.DataFrame:
    stats_data: list[dict[str, str]] = []
    max_subject_id = max((exam.subject_id for exam in schedule.exams or []), default=int(schedule.num_subjects or 0))
    stats = schedule.get_statistics()
    for stat in stats:
        teacher = next((t for t in schedule.teachers if t.name == stat["name"]), None)
        if not teacher:
            continue
        stat_row: dict[str, str] = {
            "教师姓名": teacher.name,
            "性别": "男" if teacher.gender == "M" else ("女" if teacher.gender == "F" else ""),
            "是否本校": "是" if teacher.is_internal is True else ("否" if teacher.is_internal is False else ""),
            "最大监考科目数": str(teacher.max_sessions),
            "剩余监考次数": str((teacher.max_sessions or 0) - stat["count"]),
            "不监考科目": ",".join(map(str, teacher.unavailable_subjects)),
        }

        for subject_id in range(1, max_subject_id + 1):
            stat_row[_subject_name(subject_id, subject_names)] = str(
                1 if teacher.is_assigned_to_subject(subject_id) else 0
            )

        stat_row["监考次数"] = str(stat["count"])
        stat_row["监考时长(分钟)"] = str(teacher.supervision_duration)
        stat_row["历史监考时长(分钟)"] = str(teacher.previous_supervision_duration)
        stat_row["总监考时长(分钟)"] = str(
            int(teacher.supervision_duration or 0) + int(teacher.previous_supervision_duration or 0)
        )
        stats_data.append(stat_row)

    return pd.DataFrame(stats_data) if stats_data else pd.DataFrame()


def _build_subject_sheet_dataframes(*, schedule: Schedule) -> dict[str, pd.DataFrame]:
    subject_sheets: dict[str, pd.DataFrame] = {}
    for exam in schedule.exams or []:
        rows: list[dict[str, str]] = []
        room_locations = getattr(exam, "room_locations", {}) or {}
        if schedule.mode == "double":
            headers = [
                "考场编号",
                "考场",
                "监考教师1（姓名）",
                "监考教师1性别",
                "监考教师1来源",
                "监考教师2（姓名）",
                "监考教师2性别",
                "监考教师2来源",
            ]
        else:
            headers = ["考场编号", "考场", "监考教师（姓名）", "性别", "来源"]

        for room in sorted(getattr(exam, "rooms", []) or []):
            teachers = list((exam.schedule or {}).get(room, []))
            row = dict.fromkeys(headers, "")
            row["考场编号"] = str(room)
            row["考场"] = str(room_locations.get(room) or f"考场{room}")
            if schedule.mode == "double":
                if schedule.is_position_exempt(exam.subject_id, room, 0):
                    row["监考教师1（姓名）"] = EXEMPT_SLOT_MARKER
                elif len(teachers) >= 1 and teachers[0] is not None:
                    t1 = teachers[0]
                    row["监考教师1（姓名）"] = t1.name
                    row["监考教师1性别"] = "男" if t1.gender == "M" else ("女" if t1.gender == "F" else "")
                    row["监考教师1来源"] = "本校" if t1.is_internal is True else ("外校" if t1.is_internal is False else "")

                if schedule.is_position_exempt(exam.subject_id, room, 1):
                    row["监考教师2（姓名）"] = EXEMPT_SLOT_MARKER
                elif len(teachers) >= 2 and teachers[1] is not None:
                    t2 = teachers[1]
                    row["监考教师2（姓名）"] = t2.name
                    row["监考教师2性别"] = "男" if t2.gender == "M" else ("女" if t2.gender == "F" else "")
                    row["监考教师2来源"] = "本校" if t2.is_internal is True else ("外校" if t2.is_internal is False else "")
            else:
                row["监考教师（姓名）"] = (
                    EXEMPT_SLOT_MARKER
                    if schedule.is_position_exempt(exam.subject_id, room, 0)
                    else ", ".join(t.name for t in teachers if t is not None)
                )
                if not schedule.is_position_exempt(exam.subject_id, room, 0) and teachers and teachers[0] is not None:
                    teacher = teachers[0]
                    row["性别"] = "男" if teacher.gender == "M" else ("女" if teacher.gender == "F" else "")
                    row["来源"] = "本校" if teacher.is_internal is True else ("外校" if teacher.is_internal is False else "")
            rows.append(row)

        if rows:
            subject_sheets[f"科目{exam.subject_id}"] = pd.DataFrame(rows)
    return subject_sheets


def _autosize_sheet_columns(workbook, sheet_name: str, *, max_width: int = 50) -> None:
    if sheet_name not in workbook.sheetnames:
        return
    ws = workbook[sheet_name]
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                max_length = max(max_length, len(str(cell.value)))
            except Exception:
                pass
        ws.column_dimensions[column_letter].width = min(max(10, max_length * 2), max_width)


def _safe_sheet_name(name: str) -> str:
    safe_name = str(name or "")
    for char in _INVALID_SHEET_CHARS:
        safe_name = safe_name.replace(char, " ")
    safe_name = safe_name.strip() or "Sheet"
    return safe_name[:31]


def _unique_sheet_name(used_sheet_names: set[str], name: str) -> str:
    base_name = _safe_sheet_name(name)
    used_lower_names = {sheet_name.lower() for sheet_name in used_sheet_names}
    if base_name.lower() not in used_lower_names:
        return base_name

    index = 2
    while True:
        suffix = f"({index})"
        trimmed_base = base_name[: 31 - len(suffix)]
        candidate = f"{trimmed_base}{suffix}"
        if candidate.lower() not in used_lower_names:
            return candidate
        index += 1


def export_schedule_to_excel(
    file_path: str,
    *,
    schedule: Schedule,
    subject_names: Sequence[str] | None,
    exam_times: Sequence[str] | None = None,
    exam_dates: Sequence[str] | None = None,
) -> None:
    del exam_dates
    df = _build_overview_dataframe(
        schedule=schedule,
        subject_names=list(subject_names or []),
        exam_times=list(exam_times or []),
    )
    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="监考总览表", index=False)


def export_schedule_workbook_to_excel(
    file_path: str,
    *,
    schedule: Schedule,
    subject_names: Sequence[str] | None,
    exam_dates: Sequence[str] | None = None,
    exam_times: Sequence[str] | None = None,
) -> None:
    subject_names = list(subject_names or [])
    exam_dates = list(exam_dates or [])
    exam_times = list(exam_times or [])

    df_overview = _build_overview_dataframe(
        schedule=schedule,
        subject_names=subject_names,
        exam_times=exam_times,
    )
    df_time_overview = _build_time_overview_dataframe(
        schedule=schedule,
        subject_names=subject_names,
        exam_dates=exam_dates,
        exam_times=exam_times,
    )
    df_stats = _build_stats_dataframe(schedule=schedule, subject_names=subject_names)
    subject_sheets = _build_subject_sheet_dataframes(schedule=schedule)
    written_subject_sheet_names: dict[int, str] = {}
    reserved_sheet_names: set[str] = set()

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        if not df_overview.empty:
            df_overview.to_excel(writer, sheet_name="监考总览表", index=False)
            reserved_sheet_names.add("监考总览表")
        if not df_time_overview.empty:
            df_time_overview.to_excel(writer, sheet_name="按时段总览", index=False)
            reserved_sheet_names.add("按时段总览")
        if not df_stats.empty:
            df_stats.to_excel(writer, sheet_name="监考统计", index=False)
            reserved_sheet_names.add("监考统计")
        for exam in schedule.exams or []:
            df_subject = subject_sheets.get(f"科目{exam.subject_id}")
            if df_subject is not None:
                sheet_name = _unique_sheet_name(
                    reserved_sheet_names,
                    _subject_name(exam.subject_id, subject_names) or f"科目{exam.subject_id}",
                )
                df_subject.to_excel(writer, sheet_name=sheet_name, index=False)
                reserved_sheet_names.add(sheet_name)
                written_subject_sheet_names[exam.subject_id] = sheet_name

        workbook = writer.book
        if not df_overview.empty and "监考总览表" in workbook.sheetnames:
            worksheet = workbook["监考总览表"]
            try:
                from openpyxl.styles import Alignment

                worksheet.row_dimensions[1].height = 60
                for cell in worksheet[1]:
                    cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
            except Exception:
                pass
            for column in worksheet.columns:
                worksheet.column_dimensions[column[0].column_letter].width = 12

        _autosize_sheet_columns(workbook, "按时段总览", max_width=28)
        _autosize_sheet_columns(workbook, "监考统计")
        for exam in schedule.exams or []:
            sheet_name = written_subject_sheet_names.get(exam.subject_id)
            if sheet_name:
                _autosize_sheet_columns(workbook, sheet_name)
