from __future__ import annotations

import os

import pandas as pd


def save_results(arrangement, output_file: str = "考场编排结果.xlsx"):
    """导出普通/选科模式的编排结果。"""
    if arrangement.arranged_students is None:
        return False, "请先编排考场"

    try:
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            if arrangement.subject_column in arrangement.arranged_students.columns:
                parsed_subjects = arrangement.arranged_students[arrangement.subject_column].apply(
                    arrangement.parse_subject_combination
                )
                arrangement.arranged_students[["首选", "再选1", "再选2"]] = pd.DataFrame(
                    parsed_subjects.tolist(),
                    index=arrangement.arranged_students.index,
                )

            export_df = arrangement.arranged_students.copy()
            export_df = export_df.drop(columns=["选科1", "选科2"], errors="ignore")
            text_columns = ["班级", "学号", "考号", "考场号", "座位号"]
            for col in text_columns:
                if col in export_df.columns:
                    export_df[col] = export_df[col].astype(str)

            core_columns = [
                "班级",
                "学号",
                "姓名",
                "考号",
                "选科",
                "首选",
                "再选1",
                "再选2",
                "考场",
                "考场号",
                "座位号",
                "考场选科组合",
            ]
            existing_core_cols = [col for col in core_columns if col in export_df.columns]
            extra_cols = [col for col in export_df.columns if col not in core_columns]
            export_df = export_df[existing_core_cols + extra_cols]

            export_df.to_excel(writer, sheet_name="学生编排结果", index=False)

            if arrangement.subject_column in arrangement.arranged_students.columns:
                arrangement._create_stats_sheet_with_formulas(writer, export_df)

        return True, f"编排结果已保存到: {os.path.abspath(output_file)}"
    except FileNotFoundError:
        return False, "输出目录不存在"
    except PermissionError:
        return False, f"文件被占用或没有写入权限: {output_file}"
    except OSError as exc:
        return False, f"磁盘空间不足或文件系统错误: {exc}"
    except Exception as exc:  # pragma: no cover - 保持入口错误语义
        return False, f"保存结果失败: {exc}"
