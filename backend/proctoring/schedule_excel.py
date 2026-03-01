from __future__ import annotations

from typing import Iterable, List, Sequence

import pandas as pd

from .core.models import Exam, Schedule, Teacher


def _parse_room_numbers(df: pd.DataFrame) -> List[int]:
    room_headers = df["考场"].tolist() if "考场" in df.columns else []
    if not room_headers:
        room_headers = [f"考场{r}" for r in range(1, len(df) + 1)]

    rooms: List[int] = []
    for header in room_headers:
        if isinstance(header, str) and header.startswith("考场"):
            try:
                rooms.append(int(header[2:]))
            except ValueError:
                continue
        else:
            try:
                rooms.append(int(header))
            except (ValueError, TypeError):
                continue
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
    
    # 校验表头：必须包含“考场”列
    # 如果没有“考场”且没有“考场号”，则认为是错误的表格
    if "考场" not in df.columns and "考场号" not in df.columns:
        errors.append("Excel文件缺少“考场”列。请使用正确的预设监考/监考安排模板。")
        return errors

    schedule.exams = []
    for subject_id in range(1, schedule.num_subjects + 1):
        schedule.exams.append(Exam(subject_id, list(range(1, schedule.num_rooms + 1))))

    for teacher in schedule.teachers:
        teacher.assigned_sessions = []
        teacher.supervision_duration = 0

    if schedule.mode == "double":
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
            col1_name = f"{subject_name}-监考员1\n{exam_time}"
            col2_name = f"{subject_name}-监考员2\n{exam_time}"

            if col1_name not in df.columns or col2_name not in df.columns:
                errors.append(f"科目{subject_name}缺少监考员信息")
                continue

            for i, room in enumerate(rooms):
                if i >= len(df):
                    continue

                teacher1_name = str(df[col1_name].iloc[i]) if not pd.isna(df[col1_name].iloc[i]) else ""
                teacher2_name = str(df[col2_name].iloc[i]) if not pd.isna(df[col2_name].iloc[i]) else ""

                teacher1: Teacher | None = None
                teacher2: Teacher | None = None

                if teacher1_name:
                    teacher1 = next((t for t in schedule.teachers if t.name == teacher1_name), None)
                    if not teacher1:
                        errors.append(
                            f"考场{room}科目{subject_name}中的监考员1({teacher1_name})未在教师信息中找到"
                        )
                        continue
                    if not teacher1.can_supervise(subject_id):
                        errors.append(f"教师 {teacher1.name} 不能监考科目 {subject_name}")
                        continue
                    if len(teacher1.assigned_sessions) >= teacher1.max_sessions:
                        errors.append(f"教师 {teacher1.name} 的监考次数已达到最大限制 ({teacher1.max_sessions})")
                        return errors
                    subject_durations = schedule.get_constraint("subject_durations", [])
                    duration = subject_durations[subject_id - 1] if (subject_id - 1) < len(subject_durations) else 0
                    teacher1.assign((subject_id, room), duration)

                if teacher2_name:
                    teacher2 = next((t for t in schedule.teachers if t.name == teacher2_name), None)
                    if not teacher2:
                        errors.append(
                            f"考场{room}科目{subject_name}中的监考员2({teacher2_name})未在教师信息中找到"
                        )
                        continue
                    if not teacher2.can_supervise(subject_id):
                        errors.append(f"教师 {teacher2.name} 不能监考科目 {subject_name}")
                        continue
                    if len(teacher2.assigned_sessions) >= teacher2.max_sessions:
                        errors.append(f"教师 {teacher2.name} 的监考次数已达到最大限制 ({teacher2.max_sessions})")
                        return errors
                    subject_durations = schedule.get_constraint("subject_durations", [])
                    duration = subject_durations[subject_id - 1] if (subject_id - 1) < len(subject_durations) else 0
                    teacher2.assign((subject_id, room), duration)

                if teacher1 and teacher2 and not schedule.is_valid_pair(teacher1, teacher2):
                    error_detail = ""
                    if schedule.get_constraint("gender_mix") and teacher1.gender == teacher2.gender:
                        error_detail = "（性别不匹配）"
                    elif schedule.get_constraint("internal_mix") and teacher1.is_internal == teacher2.is_internal:
                        error_detail = "（本外校不匹配）"
                    errors.append(f"考场{room}科目{subject_name}的教师搭配不满足约束条件{error_detail}")
                    continue

                exam = next((e for e in schedule.exams if e.subject_id == subject_id), None)
                if not exam:
                    continue

                teachers_list: list[Teacher | None] = []
                if teacher1:
                    teachers_list.append(teacher1)
                if teacher2:
                    if not teacher1 and len(teachers_list) == 0:
                        teachers_list.append(None)
                        teachers_list.append(teacher2)
                    else:
                        teachers_list.append(teacher2)
                exam.schedule[room] = teachers_list

                if teacher1:
                    schedule.mark_imported_position(subject_id, room, 0)
                if teacher2:
                    schedule.mark_imported_position(subject_id, room, 1)
    else:
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
            col_name = f"{subject_name}\n{exam_time}"
            if col_name not in df.columns:
                col_name = f"科目{subject_id}"
                if col_name not in df.columns:
                    errors.append(f"找不到科目 {subject_name} 对应的列")
                    continue

            for i, room in enumerate(rooms):
                if i >= len(df):
                    continue

                teacher_name = str(df[col_name].iloc[i]) if not pd.isna(df[col_name].iloc[i]) else ""
                if not teacher_name:
                    continue

                teacher = next((t for t in schedule.teachers if t.name == teacher_name), None)
                if not teacher:
                    errors.append(f"考场{room}科目{subject_name}中的教师未在教师信息中找到")
                    continue
                if not teacher.can_supervise(subject_id):
                    errors.append(f"教师 {teacher.name} 不能监考科目 {subject_name}")
                    continue
                if len(teacher.assigned_sessions) >= teacher.max_sessions:
                    errors.append(f"教师 {teacher.name} 的监考次数已达到最大限制 ({teacher.max_sessions})")
                    return errors

                exam = next((e for e in schedule.exams if e.subject_id == subject_id), None)
                if not exam:
                    continue
                exam.schedule[room] = [teacher]
                subject_durations = schedule.get_constraint("subject_durations", [])
                duration = subject_durations[subject_id - 1] if (subject_id - 1) < len(subject_durations) else 0
                teacher.assign((subject_id, room), duration)
                schedule.mark_imported_position(subject_id, room, 0)

    for teacher in schedule.teachers:
        if len(teacher.assigned_sessions) > teacher.max_sessions:
            errors.append(
                f"教师 {teacher.name} 的监考次数超过限制 ({len(teacher.assigned_sessions)} > {teacher.max_sessions})"
            )

    return errors
