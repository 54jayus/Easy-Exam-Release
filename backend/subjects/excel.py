from __future__ import annotations

import os
from dataclasses import asdict
from typing import Any, Sequence

import pandas as pd

from .core import Subject, SubjectImportResult, _coerce_duration_minutes, _normalize_subject_name, _parse_date, _parse_time_range


def import_subjects_from_excel(file_path: str) -> SubjectImportResult:
    errors: list[str] = []
    subjects: list[Subject] = []

    df = pd.read_excel(file_path)
    required_columns = ["科目名称", "考试日期", "考试时间"]
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        return SubjectImportResult(subjects=[], errors=[f"文件缺少必需的列: {', '.join(missing)}"])

    seen_names: set[str] = set()
    date_slots: dict[str, list[tuple[int, int, str, str, int]]] = {}

    for index, row in df.iterrows():
        row_no = index + 1

        name = _normalize_subject_name(row.get("科目名称", ""))
        if not name:
            errors.append(f"第{row_no}行数据错误：科目名称不能为空！")
            break
        if name in seen_names:
            errors.append(f"第{row_no}行数据错误：科目名称重复（{name}）")
            break
        seen_names.add(name)

        date_value = row.get("考试日期", None)
        exam_date = _parse_date(date_value)
        if not exam_date:
            errors.append(f"第{row_no}行数据错误：考试日期格式不正确，支持：yyyy-MM-dd 或 yyyy/M/d（如：2023-10-15 或 2025/8/21）")
            break

        time_value = row.get("考试时间", None)
        parsed = _parse_time_range(time_value)
        if parsed is None:
            errors.append(
                f"第{row_no}行数据错误：考试时间格式不正确，支持格式：HH:mm-HH:mm 或 H:mm-H:mm（如：09:00-11:30 或 9:00-11:30）"
            )
            break
        exam_time, start_min, end_min = parsed

        for s_min, e_min, exist_name, exist_time_str, exist_row in date_slots.get(exam_date, []):
            if not (end_min <= s_min or start_min >= e_min):
                errors.append(
                    f"第{row_no}行（{name}）与第{exist_row}行（{exist_name}）在{exam_date}考试时间冲突：{exam_time} 与 {exist_time_str}"
                )
                break
        if errors:
            break
        date_slots.setdefault(exam_date, []).append((start_min, end_min, name, exam_time, row_no))

        duration = _coerce_duration_minutes(row.get("考试时长（分钟）—可以留空", None))
        if duration is None:
            duration = max(0, end_min - start_min)

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
                "考试时长（分钟）—可以留空": int(s.duration_minutes or 0),
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
        worksheet.set_column(0, 4, None, center_format)

        worksheet.set_column(0, 0, 10)
        worksheet.set_column(1, 2, 15)
        worksheet.set_column(3, 3, 30)
        worksheet.set_column(4, 4, 20)


def generate_subject_template_xlsx(file_path: str) -> None:
    template_data = [
        {"科目名称": "语文", "考试日期": "2023-09-09", "考试时间": "08:00-10:00", "考试时长（分钟）—可以留空": 120, "备注": ""},
        {"科目名称": "数学", "考试日期": "2023-09-09", "考试时间": "14:30-16:30", "考试时长（分钟）—可以留空": 120, "备注": ""},
        {"科目名称": "英语", "考试日期": "2023-09-10", "考试时间": "08:00-10:00", "考试时长（分钟）—可以留空": 120, "备注": ""},
        {"科目名称": "物理", "考试日期": "2023-09-10", "考试时间": "15:00-16:00", "考试时长（分钟）—可以留空": 60, "备注": ""},
    ]
    df = pd.DataFrame(template_data)

    with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)

        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]

        center_format = workbook.add_format({"align": "center", "valign": "vcenter"})
        worksheet.set_column(0, 4, None, center_format)

        worksheet.set_column(0, 0, 10)
        worksheet.set_column(1, 2, 15)
        worksheet.set_column(3, 3, 30)
        worksheet.set_column(4, 4, 20)

        instructions = {
            "科目名称": "必填。\n示例：语文、数学、英语等。",
            "考试日期": "必填。\n支持：yyyy-MM-dd 或 yyyy/M/d（自动标准化）。\n示例：2025-10-14 或 2025/8/21。",
            "考试时间": "必填。\n支持：HH:mm-HH:mm 或 H:mm-H:mm。\n示例：08:00-10:00 或 9:00-11:30。",
            "考试时长（分钟）—可以留空": "选填。\n整数分钟；留空时按考试时间段自动计算。",
            "备注": "选填。\n可填特殊说明或补充信息。",
        }

        instruction_row = [{col: instructions.get(col, "") for col in df.columns}]
        df_desc = pd.DataFrame(instruction_row)
        df_desc.to_excel(writer, sheet_name="填写说明", index=False)

        desc_ws = writer.sheets["填写说明"]
        wrap_left = workbook.add_format({"text_wrap": True, "align": "left", "valign": "top"})
        required_cell = workbook.add_format({"text_wrap": True, "align": "left", "valign": "top", "bg_color": "#FFC7CE"})

        desc_ws.set_column(0, 0, 10, wrap_left)
        desc_ws.set_column(1, 2, 15, wrap_left)
        desc_ws.set_column(3, 3, 30, wrap_left)
        desc_ws.set_column(4, 4, 20, wrap_left)

        required_cols = {"科目名称", "考试日期", "考试时间"}
        for idx, col in enumerate(df.columns):
            value = instructions.get(col, "")
            if col in required_cols:
                desc_ws.write(1, idx, value, required_cell)
            else:
                desc_ws.write(1, idx, value, wrap_left)
        desc_ws.set_row(1, 100)

        required_header = workbook.add_format(
            {"text_wrap": True, "align": "center", "valign": "vcenter", "bg_color": "#FFC7CE", "bold": True, "border": 1}
        )
        normal_header = workbook.add_format({"text_wrap": True, "align": "center", "valign": "vcenter", "bold": True, "border": 1})
        for idx, col in enumerate(df.columns):
            fmt = required_header if col in required_cols else normal_header
            desc_ws.write(0, idx, col, fmt)

