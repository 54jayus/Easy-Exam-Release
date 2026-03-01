from __future__ import annotations

from typing import Sequence

import pandas as pd


def build_empty_overview_template_df(
    num_subjects: int,
    num_rooms: int,
    mode: str,
    subject_names: Sequence[str] | None,
    exam_times: Sequence[str] | None,
) -> pd.DataFrame:
    subject_names = list(subject_names or [])
    exam_times = list(exam_times or [])

    columns = ["考场"]
    for subject_id in range(1, num_subjects + 1):
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
        if mode == "double":
            columns.append(f"{subject_name}-监考员1\n{exam_time}")
            columns.append(f"{subject_name}-监考员2\n{exam_time}")
        else:
            columns.append(f"{subject_name}\n{exam_time}")

    data = []
    for room in range(1, num_rooms + 1):
        row = {"考场": f"考场{room}"}
        for col in columns[1:]:
            row[col] = ""
        data.append(row)
    return pd.DataFrame(data, columns=columns)


def write_empty_overview_template_xlsx(
    file_path: str,
    *,
    num_subjects: int,
    num_rooms: int,
    mode: str,
    subject_names: Sequence[str] | None,
    exam_times: Sequence[str] | None,
) -> None:
    df = build_empty_overview_template_df(
        num_subjects=num_subjects,
        num_rooms=num_rooms,
        mode=mode,
        subject_names=subject_names,
        exam_times=exam_times,
    )
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="监考总览表", index=False)
