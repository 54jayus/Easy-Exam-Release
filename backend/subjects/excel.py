from __future__ import annotations

from typing import Any, Sequence

import pandas as pd

from backend.shared.template_utils import write_instruction_sheet
from .core import (
    Subject,
    SubjectImportResult,
    _coerce_duration_minutes,
    _coerce_room_count,
    _normalize_subject_name,
    _parse_date,
    _parse_time_range,
)


ROOM_COUNT_COLUMN = "考场数量"
DURATION_COLUMN = "考试时长（分钟）"

# Backward-compatible aliases for old template column names
_ROOM_COUNT_COLUMN_LEGACY = "考场数量（可留空）"
_DURATION_COLUMN_LEGACY = "考试时长（分钟）-可留空"


def import_subjects_from_excel(file_path: str) -> SubjectImportResult:
    errors: list[str] = []
    subjects: list[Subject] = []

    df = pd.read_excel(file_path)
    # Normalize legacy column names to current names
    if _DURATION_COLUMN_LEGACY in df.columns and DURATION_COLUMN not in df.columns:
        df.rename(columns={_DURATION_COLUMN_LEGACY: DURATION_COLUMN}, inplace=True)
    if _ROOM_COUNT_COLUMN_LEGACY in df.columns and ROOM_COUNT_COLUMN not in df.columns:
        df.rename(columns={_ROOM_COUNT_COLUMN_LEGACY: ROOM_COUNT_COLUMN}, inplace=True)

    required_columns = ["科目名称", "考试日期", "考试时间"]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        return SubjectImportResult(subjects=[], errors=[f"文件缺少必需的列: {', '.join(missing)}"])

    seen_names: set[str] = set()

    for index, row in df.iterrows():
        row_no = index + 1

        name = _normalize_subject_name(row.get("科目名称", ""))
        if not name:
            errors.append(f"第{row_no}行数据错误：科目名称不能为空")
            continue
        if name in seen_names:
            errors.append(f"第{row_no}行数据错误：科目名称重复（{name}）")
            continue
        seen_names.add(name)

        exam_date = _parse_date(row.get("考试日期"))
        if not exam_date:
            errors.append(
                f"第{row_no}行数据错误：考试日期格式不正确，支持 yyyy-MM-dd 或 yyyy/M/d（如：2025-10-15 或 2025/8/21）"
            )
            continue

        parsed = _parse_time_range(row.get("考试时间"))
        if parsed is None:
            errors.append(
                f"第{row_no}行数据错误：考试时间格式不正确，支持 HH:mm-HH:mm 或 H:mm-H:mm（如：9:00-11:30）"
            )
            continue
        exam_time, start_min, end_min = parsed

        duration = _coerce_duration_minutes(row.get(DURATION_COLUMN))
        if duration is None:
            duration = max(0, end_min - start_min)

        room_count_raw = row.get(ROOM_COUNT_COLUMN)
        room_count = _coerce_room_count(room_count_raw)
        room_count_text = "" if room_count_raw is None else str(room_count_raw).strip()
        if room_count is None and room_count_text and room_count_text.lower() != "nan":
            errors.append(f"第{row_no}行数据错误：考场数量必须是非负整数")
            continue
        room_count = room_count or 0

        remark = ""
        if "备注" in df.columns:
            remark_value = row.get("备注", "")
            remark = "" if remark_value is None or str(remark_value).lower() == "nan" else str(remark_value)

        subjects.append(
            Subject(
                name=name,
                exam_date=exam_date,
                exam_time=exam_time,
                remark=remark,
                duration_minutes=duration,
                room_count=room_count,
            )
        )

    return SubjectImportResult(subjects=subjects if not errors else [], errors=errors)


def _subjects_to_df(subjects: Sequence[Subject]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for s in subjects:
        rows.append(
            {
                "科目名称": s.name,
                "考试日期": s.exam_date,
                "考试时间": s.exam_time,
                DURATION_COLUMN: int(s.duration_minutes or 0),
                ROOM_COUNT_COLUMN: int(s.room_count or 0),
                "备注": s.remark,
            }
        )
    return pd.DataFrame(rows)


def export_subjects_to_excel(file_path: str, *, subjects: Sequence[Subject]) -> None:
    df = _subjects_to_df(subjects)
    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)
        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]

        center_format = workbook.add_format({"align": "center", "valign": "vcenter"})
        worksheet.set_column(0, 5, None, center_format)

        worksheet.set_column(0, 0, 16)
        worksheet.set_column(1, 2, 18)
        worksheet.set_column(3, 4, 18)
        worksheet.set_column(5, 5, 24)


def generate_subject_template_xlsx(file_path: str) -> None:
    template_data = [
        {
            "科目名称": "语文",
            "考试日期": "2026-06-07",
            "考试时间": "09:00-11:30",
            DURATION_COLUMN: 150,
            ROOM_COUNT_COLUMN: 20,
            "备注": "",
        },
        {
            "科目名称": "数学",
            "考试日期": "2026-06-07",
            "考试时间": "15:00-17:00",
            DURATION_COLUMN: 120,
            ROOM_COUNT_COLUMN: 18,
            "备注": "",
        },
        {
            "科目名称": "英语",
            "考试日期": "2026-06-08",
            "考试时间": "09:00-11:00",
            DURATION_COLUMN: 120,
            ROOM_COUNT_COLUMN: "",
            "备注": "",
        },
        {
            "科目名称": "物理",
            "考试日期": "2026-06-08",
            "考试时间": "15:00-16:00",
            DURATION_COLUMN: 60,
            ROOM_COUNT_COLUMN: "",
            "备注": "",
        },
    ]
    df = pd.DataFrame(template_data)

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)

        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]

        center_format = workbook.add_format({"align": "center", "valign": "vcenter"})
        worksheet.set_column(0, 5, None, center_format)

        worksheet.set_column(0, 0, 16)
        worksheet.set_column(1, 2, 18)
        worksheet.set_column(3, 4, 18)
        worksheet.set_column(5, 5, 24)

        instructions = {
            "科目名称": "必填。\n示例：语文、数学、英语等。",
            "考试日期": "必填。\n支持：yyyy-MM-dd 或 yyyy/M/d（自动标准化）。\n示例：2026-06-07 或 2026/6/7。",
            "考试时间": "必填。\n支持：HH:mm-HH:mm 或 H:mm-H:mm。\n示例：9:00-11:30 或 15:00-17:00。",
            DURATION_COLUMN: "选填。\n整数分钟；留空时按考试时间段自动计算。",
            ROOM_COUNT_COLUMN: "选填。\n填写该科单独使用的考场数量；留空时可在监考编排页使用默认考场数量。",
            "备注": "选填。\n可填写特殊说明或补充信息。",
        }

        write_instruction_sheet(
            writer, df.columns, instructions,
            required_cols={"科目名称", "考试日期", "考试时间"},
        )
