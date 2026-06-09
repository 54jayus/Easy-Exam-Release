from __future__ import annotations

import pandas as pd

from backend.shared.template_utils import write_instruction_sheet


def generate_template(type_: str, path: str):
    try:
        with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
            if type_ == "settings":
                total_rooms = 30
                data = {
                    "序号": list(range(1, total_rooms + 1)),
                    "考场号": [f"{i:03d}" for i in range(1, total_rooms + 1)],
                    "考场": [f"第{i}考场" for i in range(1, total_rooms + 1)],
                    "考场人数": [30] * total_rooms,
                }
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name="Sheet1", index=False)
                ws = writer.sheets["Sheet1"]
                ws.set_column(0, 0, 8)
                ws.set_column(1, 1, 10)
                ws.set_column(2, 2, 12)
                ws.set_column(3, 3, 10)
                write_instruction_sheet(
                    writer, df.columns,
                    {
                        "序号": "必填。\n必须从1开始连续编号，不得缺失或重复。",
                        "考场号": "必填。\n建议为三位如001、002。",
                        "考场": "选填。\n设置考场名称，例如：高一1。",
                        "考场人数": "必填。\n正整数，表示每个考场允许的最大人数。",
                    },
                    required_cols={"序号", "考场号", "考场人数"},
                )

            elif type_ == "student_normal":
                data = {
                    "班级": ["1"] * 5,
                    "学号": ["1", "2", "3", "4", "5"],
                    "考号": ["240001", "240002", "240003", "240004", "240005"],
                    "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
                }
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name="Sheet1", index=False)
                ws = writer.sheets["Sheet1"]
                ws.set_column(0, 1, 10)
                ws.set_column(2, 3, 15)
                write_instruction_sheet(
                    writer, df.columns,
                    {
                        "班级": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                        "学号": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                        "考号": "必填。\n不允许重复。",
                        "姓名": "必填。\n示例：张三。",
                    },
                    required_cols={"班级", "学号", "考号", "姓名"},
                )

            elif type_ == "student_subject":
                data = {
                    "班级": ["1"] * 5,
                    "学号": ["1", "2", "3", "4", "5"],
                    "考号": ["240001", "240002", "240003", "240004", "240005"],
                    "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
                    "选科": ["物化生", "物化地", "史政地", "史化生", "物生地"],
                }
                df = pd.DataFrame(data)
                df.to_excel(writer, sheet_name="Sheet1", index=False)
                ws = writer.sheets["Sheet1"]
                ws.set_column(0, 1, 10)
                ws.set_column(2, 3, 15)
                ws.set_column(4, 4, 25)
                write_instruction_sheet(
                    writer, df.columns,
                    {
                        "班级": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                        "学号": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                        "考号": "必填。\n不允许重复。",
                        "姓名": "必填。\n示例：张三。",
                        "选科": "必填。\n支持缩写（如：物化生/史政地）或全称+分隔符。\n例如：物理+化学+生物",
                    },
                    required_cols={"班级", "学号", "考号", "姓名", "选科"},
                )

        return {}
    except Exception as exc:
        return {"error": str(exc)}
