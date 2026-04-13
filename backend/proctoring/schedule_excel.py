from __future__ import annotations

from typing import List, Sequence

import pandas as pd

from .core.entities import is_exempt_slot_value
from .core.models import Exam, Schedule, Teacher


def _parse_room_numbers(df: pd.DataFrame) -> List[int]:
    room_headers = df["考场"].tolist() if "考场" in df.columns else []
    if not room_headers:
        room_headers = [f"考场{r}" for r in range(1, len(df) + 1)]

    rooms: List[int] = []
    for header in room_headers:
        text = str(header or "").strip()
        if text.startswith("考场"):
            text = text[2:]
        try:
            room = int(text)
        except (ValueError, TypeError):
            continue
        if room > 0:
            rooms.append(room)
    return rooms


def parse_schedule_from_excel(
    *,
    schedule: Schedule,
    df: pd.DataFrame,
    subject_names: Sequence[str] | None = None,
    exam_times: Sequence[str] | None = None,
) -> List[str]:
    errors: List[str] = []
    subject_names = list(subject_names or [])
    exam_times = list(exam_times or [])

    rooms = _parse_room_numbers(df)
    room_row_index = {room: idx for idx, room in enumerate(rooms)}

    if "考场" not in df.columns and "考场号" not in df.columns:
        errors.append("Excel文件缺少“考场”列。请使用正确的预设监考/监考安排模板。")
        return errors

    schedule.exams = []
    for subject_id in range(1, schedule.num_subjects + 1):
        schedule.exams.append(Exam(subject_id, list(schedule._get_subject_rooms(subject_id))))

    for teacher in schedule.teachers:
        teacher.assigned_sessions = []
        teacher.supervision_duration = 0

    required_slots = schedule.get_slot_count()

    for subject_id in range(1, schedule.num_subjects + 1):
        subject_name = (
            subject_names[subject_id - 1]
            if (subject_id - 1) < len(subject_names) and subject_names[subject_id - 1]
            else f"科目{subject_id}"
        )
        exam_time = (
            exam_times[subject_id - 1]
            if (subject_id - 1) < len(exam_times) and exam_times[subject_id - 1]
            else ""
        )
        expected_rooms = list(schedule._get_subject_rooms(subject_id))
        exam = next((item for item in schedule.exams if item.subject_id == subject_id), None)
        if exam is None:
            continue

        if schedule.mode == "double":
            col1_name = f"{subject_name}-监考员1\n{exam_time}"
            col2_name = f"{subject_name}-监考员2\n{exam_time}"
            if col1_name not in df.columns or col2_name not in df.columns:
                errors.append(f"科目 {subject_name} 缺少监考员信息")
                continue
        else:
            col_name = f"{subject_name}\n{exam_time}"
            if col_name not in df.columns:
                fallback_name = f"科目{subject_id}"
                if fallback_name not in df.columns:
                    errors.append(f"找不到科目 {subject_name} 对应的列")
                    continue
                col_name = fallback_name

        for room in expected_rooms:
            row_index = room_row_index.get(room)
            if row_index is None or row_index >= len(df):
                errors.append(f"缺少考场 {room} 对应的行，无法导入科目 {subject_name}")
                continue

            if schedule.mode == "double":
                teacher_names = [
                    str(df[col1_name].iloc[row_index]) if not pd.isna(df[col1_name].iloc[row_index]) else "",
                    str(df[col2_name].iloc[row_index]) if not pd.isna(df[col2_name].iloc[row_index]) else "",
                ]
            else:
                teacher_names = [
                    str(df[col_name].iloc[row_index]) if not pd.isna(df[col_name].iloc[row_index]) else ""
                ]

            teachers_list: list[Teacher | None] = [None] * required_slots
            exempt_slot_indexes: set[int] = set()
            for slot_index, teacher_name in enumerate(teacher_names):
                if not teacher_name:
                    continue
                if is_exempt_slot_value(teacher_name):
                    exempt_slot_indexes.add(slot_index)
                    schedule.mark_exempt_position(subject_id, room, slot_index)
                    continue

                teacher = next((t for t in schedule.teachers if t.name == teacher_name), None)
                if not teacher:
                    errors.append(
                        f"考场 {room} 科目 {subject_name} 中的教师 {teacher_name} 未在教师信息中找到"
                    )
                    continue
                if not teacher.can_supervise(subject_id):
                    errors.append(f"教师 {teacher.name} 不能监考科目 {subject_name}")
                    continue
                if len(teacher.assigned_sessions) >= teacher.max_sessions:
                    errors.append(
                        f"教师 {teacher.name} 的监考次数已达到最大限制 ({teacher.max_sessions})"
                    )
                    return errors
                teachers_list[slot_index] = teacher
                teacher.assign((subject_id, room), schedule._get_subject_duration(subject_id))
                schedule.mark_imported_position(subject_id, room, slot_index)

            if schedule.mode == "double":
                teacher1 = teachers_list[0]
                teacher2 = teachers_list[1]
                if (
                    teacher1
                    and teacher2
                    and schedule.room_requires_pair_constraints(subject_id, room)
                    and not schedule.is_valid_pair(teacher1, teacher2)
                ):
                    errors.append(f"考场 {room} 科目 {subject_name} 的教师搭配不满足约束条件")
                    continue
                if any(item is not None for item in teachers_list) or exempt_slot_indexes:
                    exam.schedule[room] = teachers_list
            else:
                teacher = teachers_list[0]
                if teacher is not None or exempt_slot_indexes:
                    exam.schedule[room] = [teacher]

    for teacher in schedule.teachers:
        if len(teacher.assigned_sessions) > teacher.max_sessions:
            errors.append(
                f"教师 {teacher.name} 的监考次数超过限制 ({len(teacher.assigned_sessions)} > {teacher.max_sessions})"
            )

    return errors
