from __future__ import annotations

import os
import re

import pandas as pd


def merge_gaokao_results(arrangement) -> pd.DataFrame:
    """将高考模式各科编排结果合并为学生中心视图。"""
    unified_df = arrangement.gaokao_results["unified"]
    result_df = unified_df[["班级", "学号", "考号", "姓名", arrangement.subject_column]].copy()

    subjects = ["语文", "数学", "英语", "物理历史", "化学", "地理", "政治", "生物"]

    for subject in subjects:
        if subject in ["语文", "数学", "英语", "物理历史"]:
            if subject == "物理历史":
                result_df[f"{subject}科目"] = result_df[arrangement.subject_column].str[0].map({"物": "物理", "史": "历史"})
            else:
                result_df[f"{subject}科目"] = subject
            result_df[f"{subject}考场号"] = unified_df["考场号"]
            result_df[f"{subject}考场"] = unified_df["考场"]
            result_df[f"{subject}座位号"] = unified_df["座位号"]
            continue

        elective_df = arrangement.gaokao_results["electives"][subject]
        for idx, row in result_df.iterrows():
            exam_id = row["考号"]
            elective_row = elective_df[elective_df["考号"] == exam_id]
            if elective_row.empty:
                continue

            elective_row = elective_row.iloc[0]
            result_df.at[idx, f"{subject}科目"] = elective_row["科目类型"]
            result_df.at[idx, f"{subject}考场号"] = elective_row["考场号"]
            result_df.at[idx, f"{subject}考场"] = elective_row["考场"]
            result_df.at[idx, f"{subject}座位号"] = elective_row["座位号"]

    return result_df


def save_gaokao_results(arrangement, output_file: str = "高考编排结果.xlsx"):
    """导出高考模式的完整编排结果。"""
    if arrangement.arranged_students is None:
        return False, "请先编排考场"

    if arrangement.gaokao_results is None:
        return False, "高考模式编排结果不存在"

    try:
        with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
            export_gaokao_student_table(arrangement, writer)
            export_gaokao_seat_tables(arrangement, writer)
            export_gaokao_timeslot_tables(arrangement, writer)
            export_gaokao_stats_table(arrangement, writer)

        return True, f"高考编排结果已保存至 {os.path.abspath(output_file)}"
    except PermissionError:
        return False, f"文件被占用或没有写入权限: {output_file}"
    except Exception as exc:  # pragma: no cover - 保持原入口错误语义
        return False, f"保存结果失败: {exc}"


def export_gaokao_student_table(arrangement, writer) -> None:
    """导出学生中心视图。"""
    export_df = arrangement.arranged_students.copy()

    for col in ["班级", "学号", "考号"]:
        if col in export_df.columns:
            export_df[col] = export_df[col].astype(str)

    subjects = arrangement._get_subject_order()
    for subject in subjects:
        export_df[f"{subject}时间"] = arrangement._format_subject_time(subject)

    for subject in subjects:
        for suffix in ["考场号", "座位号"]:
            col_name = f"{subject}{suffix}"
            if col_name in export_df.columns:
                export_df[col_name] = export_df[col_name].astype(str)

    base_cols = ["班级", "学号", "考号", "姓名", arrangement.subject_column]
    subject_cols = []
    for subject in subjects:
        subject_cols.extend(
            [
                f"{subject}科目",
                f"{subject}时间",
                f"{subject}考场号",
                f"{subject}考场",
                f"{subject}座位号",
            ]
        )

    existing_base = [col for col in base_cols if col in export_df.columns]
    existing_subject = [col for col in subject_cols if col in export_df.columns]
    export_df = export_df[existing_base + existing_subject]

    if "班级" in export_df.columns and "学号" in export_df.columns:
        export_df["_班级_sort"] = pd.to_numeric(export_df["班级"], errors="coerce").fillna(float("inf"))
        export_df["_学号_sort"] = pd.to_numeric(export_df["学号"], errors="coerce").fillna(float("inf"))
        export_df = export_df.sort_values(["_班级_sort", "_学号_sort"]).drop(columns=["_班级_sort", "_学号_sort"])

    export_df.to_excel(writer, sheet_name="考场安排（学生）", index=False)


def export_gaokao_seat_tables(arrangement, writer) -> None:
    """导出座位中心视图。"""
    unified_df = arrangement.gaokao_results["unified"]
    electives = arrangement.gaokao_results["electives"]
    seats = unified_df[["考场号", "考场", "座位号"]].drop_duplicates().sort_values(["考场号", "座位号"])
    subjects = arrangement._get_subject_order()

    seat_records = []
    for _, seat_row in seats.iterrows():
        room_num = seat_row["考场号"]
        room_name = seat_row["考场"]
        seat_num = seat_row["座位号"]

        record = {"考场号": room_num, "考场": room_name, "座位号": seat_num}
        subjects_data = {
            "语文": unified_df,
            "数学": unified_df,
            "英语": unified_df,
            "物理历史": unified_df,
            "化学": electives["化学"],
            "地理": electives["地理"],
            "政治": electives["政治"],
            "生物": electives["生物"],
        }

        for subject in subjects:
            df = subjects_data[subject]
            student_row = df[(df["考场号"] == room_num) & (df["座位号"] == seat_num)]
            record[f"{subject}时间"] = arrangement._format_subject_time(subject)

            if student_row.empty:
                record[f"{subject}科目"] = ""
                record[f"{subject}姓名"] = ""
                record[f"{subject}考号"] = ""
                record[f"{subject}班级"] = ""
                record[f"{subject}学号"] = ""
                continue

            student_row = student_row.iloc[0]
            if subject in ["语文", "数学", "英语"]:
                record[f"{subject}科目"] = subject
            elif subject == "物理历史":
                student_subject = student_row.get(arrangement.subject_column, "")
                if str(student_subject).startswith("物"):
                    record[f"{subject}科目"] = "物理"
                elif str(student_subject).startswith("史"):
                    record[f"{subject}科目"] = "历史"
                else:
                    record[f"{subject}科目"] = subject
            else:
                record[f"{subject}科目"] = student_row.get("科目类型", "自习")

            record[f"{subject}姓名"] = student_row.get("姓名", "")
            record[f"{subject}考号"] = str(student_row.get("考号", ""))
            record[f"{subject}班级"] = str(student_row.get("班级", ""))
            record[f"{subject}学号"] = str(student_row.get("学号", ""))

        seat_records.append(record)

    base_cols = ["考场号", "考场", "座位号"]
    subject_cols = []
    for subject in subjects:
        subject_cols.extend(
            [
                f"{subject}时间",
                f"{subject}科目",
                f"{subject}姓名",
                f"{subject}考号",
                f"{subject}班级",
                f"{subject}学号",
            ]
        )

    seat_df = pd.DataFrame(seat_records)
    existing_cols = [col for col in (base_cols + subject_cols) if col in seat_df.columns]
    seat_df = seat_df[existing_cols]
    seat_df.to_excel(writer, sheet_name="考场安排（座位）", index=False)


def export_gaokao_timeslot_tables(arrangement, writer) -> None:
    """导出统考和各选考科目的时间段视图。"""
    unified_df = arrangement.gaokao_results["unified"].copy()
    unified_df["科目"] = unified_df[arrangement.subject_column].str[0].map({"物": "物理", "史": "历史"})
    unified_df["时间"] = arrangement._format_subject_time("物理历史")

    columns_order = ["考场号", "考场", "座位号", "考号", "姓名", "班级", "学号", "科目", "时间"]
    existing_cols = [col for col in columns_order if col in unified_df.columns]
    unified_export = unified_df[existing_cols].copy()

    for col in ["考场号", "座位号", "考号", "班级", "学号"]:
        if col in unified_export.columns:
            unified_export.loc[:, col] = unified_export[col].astype(str)

    unified_export.to_excel(writer, sheet_name="统考编排结果", index=False)

    for subject in ["化学", "地理", "政治", "生物"]:
        elective_df = arrangement.gaokao_results["electives"][subject].copy()
        elective_df["科目"] = elective_df["科目类型"]
        elective_df = elective_df.drop(columns=["科目类型"])
        elective_df["时间"] = arrangement._format_subject_time(subject)
        elective_export = elective_df[existing_cols].copy()

        for col in ["考场号", "座位号", "考号", "班级", "学号"]:
            if col in elective_export.columns:
                elective_export.loc[:, col] = elective_export[col].astype(str)

        elective_export.to_excel(writer, sheet_name=f"{subject}编排结果", index=False)


def export_gaokao_stats_table(arrangement, writer) -> None:
    """导出高考模式考场人数统计。"""
    unified_df = arrangement.gaokao_results["unified"]
    used_rooms = unified_df["考场号"].unique()
    room_list = [room for room in arrangement._get_room_list() if room in used_rooms]

    subjects = []
    for subject in arrangement._get_subject_order():
        if subject == "物理历史":
            subjects.extend(["物理", "历史"])
        else:
            subjects.append(subject)

    stats_records = []
    for room_num in room_list:
        record = {"考场号": room_num, "考场": arrangement._get_room_name(room_num)}
        room_counts = []

        for subject in subjects:
            if subject in ["语文", "数学", "英语"]:
                count = len(unified_df[unified_df["考场号"] == room_num])
                record[subject] = count
                room_counts.append(count)
                continue

            if subject in ["物理", "历史"]:
                prefix = "物" if subject == "物理" else "史"
                room_students = unified_df[unified_df["考场号"] == room_num]
                count = len(room_students[room_students[arrangement.subject_column].str.startswith(prefix)])
                record[subject] = count
                room_counts.append(count)
                continue

            elective_df = arrangement.gaokao_results["electives"][subject]
            room_df = elective_df[elective_df["考场号"] == room_num]
            exam_count = len(room_df[room_df["科目类型"] == subject])
            self_study_count = len(room_df[room_df["科目类型"] == "自习"])

            if exam_count > 0 and self_study_count > 0:
                record[subject] = f"{exam_count}+{self_study_count}（自习）"
                room_counts.append(exam_count + self_study_count)
            elif self_study_count > 0:
                record[subject] = f"{self_study_count}（自习）"
                room_counts.append(self_study_count)
            elif exam_count > 0:
                record[subject] = exam_count
                room_counts.append(exam_count)
            else:
                record[subject] = 0

        record["最大人数"] = max(room_counts) if room_counts else 0
        stats_records.append(record)

    stats_df = pd.DataFrame(stats_records)

    total_record = {"考场号": "总计", "考场": ""}
    for subject in subjects:
        total = 0
        for value in stats_df[subject]:
            if isinstance(value, (int, float)):
                total += int(value)
            elif isinstance(value, str):
                total += sum(int(num) for num in re.findall(r"\d+", value))
        total_record[subject] = total

    max_counts = stats_df["最大人数"]
    total_record["最大人数"] = sum(max_counts) if len(max_counts) > 0 else 0

    stats_df = pd.concat([stats_df, pd.DataFrame([total_record])], ignore_index=True)
    stats_df.to_excel(writer, sheet_name="考场人数统计", index=False)
