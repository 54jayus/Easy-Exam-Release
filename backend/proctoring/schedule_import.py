from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence, Tuple

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
    auto_postprocess_optimize: bool = False,
    show_optimize_button: bool = False,
    subject_durations: Sequence[int] | None = None,
    subject_names: Sequence[str] | None = None,
    exam_times: Sequence[str] | None = None,
) -> tuple[Schedule, list[str]]:
    schedule = Schedule(teachers, num_subjects, num_rooms, mode)
    schedule.set_constraint("gender_mix", gender_mix)
    schedule.set_constraint("internal_mix", internal_mix)
    schedule.set_constraint("lock_imported", lock_imported)
    schedule.set_constraint("highlight_imported", highlight_imported)
    schedule.set_constraint("auto_postprocess_optimize", auto_postprocess_optimize)
    schedule.set_constraint("show_optimize_button", show_optimize_button)
    schedule.set_constraint("subject_durations", list(subject_durations or [120] * num_subjects))

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
