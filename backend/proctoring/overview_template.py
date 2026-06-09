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

        # 填写说明 sheet
        workbook = writer.book
        ws = workbook.add_worksheet('填写说明')

        title_fmt = workbook.add_format({'bold': True, 'font_size': 12, 'bottom': 1})
        wrap_fmt = workbook.add_format({'text_wrap': True, 'valign': 'top'})

        instructions = [
            ('使用说明', None),
            ('', ''),
            ('1. 基本规则', ''),
            ('', '在对应科目的列中填写监考教师的姓名。'),
            ('', '教师姓名必须与已导入的教师名册完全一致。'),
            ('', '每个考场每个科目必须安排一位监考教师。'),
            ('', ''),
            ('2. 双教师监考模式', ''),
            ('', '每个科目分为“监考员1”和“监考员2”两列。'),
            ('', '监考员1通常安排本校教师，监考员2通常安排外校教师（若开启本外校搭配）。'),
            ('', '同一考场的两位监考员需满足男女搭配和本外校搭配的约束（若开启）。'),
            ('', ''),
            ('3. 无需编排标记', ''),
            ('', '若某个考场某科目不需要安排监考，在对应单元格填写：“#无需编排”'),
            ('', '系统在智能编排时会自动跳过该位置。'),
            ('', ''),
            ('4. 注意事项', ''),
            ('', '教师的“不监考科目”约束仍会生效，系统会校验。'),
            ('', '教师的“最大监考段数”不能超出，系统会校验。'),
            ('', '导入预设后点击“智能编排”，系统会自动填充未安排的位置。'),
        ]

        for row_idx, (col_a, col_b) in enumerate(instructions):
            if col_b is None:
                ws.write(row_idx, 0, col_a, title_fmt)
            else:
                ws.write(row_idx, 0, col_a, wrap_fmt)
                ws.write(row_idx, 1, col_b, wrap_fmt)

        ws.set_column(0, 0, 4)
        ws.set_column(1, 1, 70)
