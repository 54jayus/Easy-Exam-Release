from __future__ import annotations

from typing import List, Sequence

import pandas as pd

from .core.models import Schedule, Teacher
from .schedule_excel import parse_schedule_from_excel


def import_schedule_from_excel(
    file_path: str,
    *,
    teachers: List[Teacher],
    num_subjects: int,
    num_rooms: int,
    mode: str,
    gender_mix: bool,
    internal_mix: bool,
    lock_imported: bool,
    highlight_imported: bool,
    subject_durations: Sequence[int] | None = None,
    subject_room_counts: Sequence[int] | None = None,
    subject_names: Sequence[str] | None = None,
    exam_times: Sequence[str] | None = None,
) -> tuple[Schedule, list[str]]:
    schedule = Schedule(teachers, num_subjects, num_rooms, mode)
    schedule.set_constraint("gender_mix", gender_mix)
    schedule.set_constraint("internal_mix", internal_mix)
    schedule.set_constraint("lock_imported", lock_imported)
    schedule.set_constraint("highlight_imported", highlight_imported)
    schedule.set_constraint("subject_durations", list(subject_durations or [120] * num_subjects))
    schedule.set_constraint("subject_room_counts", list(subject_room_counts or [num_rooms] * num_subjects))

    try:
        df = pd.read_excel(file_path, sheet_name="监考总览表")
    except ValueError as e:
        if "not found" in str(e):
            return schedule, ["Excel文件缺少“监考总览表”工作表。请使用正确的预设监考/监考安排模板。"]
        return schedule, [f"读取Excel失败: {str(e)}"]
    except Exception as e:
        return schedule, [f"读取Excel失败: {str(e)}"]

    errors = parse_schedule_from_excel(
        schedule=schedule,
        df=df,
        subject_names=subject_names or [],
        exam_times=exam_times or [],
    )
    return schedule, errors
