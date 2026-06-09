from __future__ import annotations

import pandas as pd

from backend.shared.template_utils import write_instruction_sheet_openpyxl


def write_teacher_template_xlsx(file_path: str) -> None:
    template_data = [
        {
            "姓名": "张三",
            "性别": "男",
            "是否本校": "是",
            "最大监考段数": 3,
            "不监考科目": "1,3",
            "历次监考时长": 0,
            "预设监考考场": "1",
            "回避考场": "",
        },
        {
            "姓名": "李四",
            "性别": "女",
            "是否本校": "是",
            "最大监考段数": 2,
            "不监考科目": "2",
            "历次监考时长": 0,
            "预设监考考场": "2",
            "回避考场": "",
        },
        {
            "姓名": "王五",
            "性别": "男",
            "是否本校": "否",
            "最大监考段数": 4,
            "不监考科目": "",
            "历次监考时长": 0,
            "预设监考考场": "",
            "回避考场": "3,5",
        },
        {
            "姓名": "赵六",
            "性别": "女",
            "是否本校": "否",
            "最大监考段数": 3,
            "不监考科目": "1,2,4",
            "历次监考时长": 0,
            "预设监考考场": "",
            "回避考场": "1,2",
        },
    ]

    df = pd.DataFrame(template_data)

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        sheet_name = "Sheet1"
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        workbook = writer.book
        worksheet = workbook[sheet_name]

        for column in worksheet.columns:
            header_cell = column[0]
            header_text = str(header_cell.value) if header_cell.value is not None else ""
            adjusted_width = max(len(header_text), 0) * 3
            worksheet.column_dimensions[header_cell.column_letter].width = min(adjusted_width, 50)

        instructions = {
            '姓名': '必填。\n示例：张三、李四。',
            '性别': '条件必填。\n若启用“双教师监考”且设置“男女搭配”约束，则必填。\n填写要求：男/女。',
            '是否本校': '条件必填。\n若启用“双教师监考”且设置“本校外搭配”约束，则必填。\n填写要求：是/否。',
            '最大监考段数': '选填。\n留空表示不设置监考段数限制。\n填写要求：为非负整数，且不超过科目数。',
            '不监考科目': '选填。\n支持科目编号或科目名称；多个项可用英文/中文逗号、分号、中文分号、顿号或空格分隔，例如：\n1,3\n语文、数学\n科目1 科目2\n科目名称需与已导入科目信息一致。',
            '历次监考时长': '选填。\n单位：分钟；留空默认0。\n支持填写负数，用于历史监考时长补偿。',
            '预设监考考场': '选填。\n数字范围：1..考场数；越界或非法值将被忽略。',
            '回避考场': '选填。\n填写不希望被分配到的考场编号，多个用逗号、顿号或分号分隔，例如：3,5\n数字范围：1..考场数。\n注意：不能与“预设监考考场”冲突。',
        }

        write_instruction_sheet_openpyxl(
            workbook, list(df.columns), instructions,
            required_cols={'姓名'},
            conditional_cols={'性别', '是否本校'},
        )

