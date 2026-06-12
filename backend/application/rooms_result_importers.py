from __future__ import annotations

from typing import Callable

import pandas as pd


def load_results_dataframe(path: str) -> pd.DataFrame:
    try:
        excel_file = pd.ExcelFile(path)
        sheet_name = None
        for candidate in ["考场安排（学生）", "学生编排结果", "编排结果", "考场编排结果", "Sheet1"]:
            if candidate in excel_file.sheet_names:
                sheet_name = candidate
                break
        if sheet_name is None:
            sheet_name = excel_file.sheet_names[0]
        df = pd.read_excel(excel_file, sheet_name=sheet_name, dtype=str)
    except Exception as exc:
        raise ValueError(f"读取Excel失败: {str(exc)}") from exc

    df.columns = [str(col).strip() for col in df.columns]
    df = df.fillna("")
    if df.empty:
        raise ValueError("导入失败：文件中没有可用数据")
    return df


def is_gaokao_results_dataframe(df: pd.DataFrame) -> bool:
    gaokao_subjects = ["语文", "数学", "物理历史", "英语", "化学", "地理", "政治", "生物"]
    return any(f"{subject}考场号" in df.columns for subject in gaokao_subjects)


def import_gaokao_results(state, repo, build_exam_arrangement: Callable, df: pd.DataFrame, params: dict):
    required_cols = ["考号"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        return {"error": f"导入失败：缺少必要的列: {', '.join(missing)}"}

    exam_id_series = df["考号"].astype(str).str.strip()
    if not exam_id_series.is_unique:
        duplicates = df[df.duplicated("考号", keep=False)]["考号"].astype(str).unique().tolist()
        head = duplicates[:5]
        suffix = "..." if len(duplicates) > 5 else ""
        return {"error": f"导入失败：存在重复的考号: {', '.join(head)}{suffix}"}

    settings = state.rooms.settings_data
    config = state.rooms.config or {}
    student_path = state.rooms.student_path or ""

    merged_config = dict(config)
    merged_config["mode"] = "gaokao"
    state.rooms.config = merged_config

    arrangement = build_exam_arrangement(settings, merged_config, student_path)
    arrangement.arranged_students = df.copy()
    arrangement.arrangement_mode = "gaokao_mode"

    try:
        unified_records = []
        elective_records = {"化学": [], "地理": [], "政治": [], "生物": []}

        for _, row in df.iterrows():
            base_info = {
                "班级": str(row.get("班级", "")),
                "学号": str(row.get("学号", "")),
                "姓名": str(row.get("姓名", "")),
                "考号": str(row.get("考号", "")),
                "选科": str(row.get("选科", "")),
            }

            unified_subject = "语文"
            room_no_col = f"{unified_subject}考场号"
            room_col = f"{unified_subject}考场"
            seat_col = f"{unified_subject}座位号"

            if room_no_col in df.columns and seat_col in df.columns:
                record = base_info.copy()
                record["考场号"] = str(row.get(room_no_col, ""))
                record["考场"] = str(row.get(room_col, ""))
                record["座位号"] = str(row.get(seat_col, ""))
                unified_records.append(record)

            for subject in ["化学", "地理", "政治", "生物"]:
                room_no_col = f"{subject}考场号"
                room_col = f"{subject}考场"
                seat_col = f"{subject}座位号"
                subject_type_col = f"{subject}科目"

                if room_no_col not in df.columns or seat_col not in df.columns:
                    continue

                room_no = str(row.get(room_no_col, "")).strip()
                seat_no = str(row.get(seat_col, "")).strip()
                if not room_no or not seat_no:
                    continue

                record = base_info.copy()
                record["考场号"] = room_no
                record["考场"] = str(row.get(room_col, ""))
                record["座位号"] = seat_no

                subject_type = str(row.get(subject_type_col, subject)).strip()
                if not subject_type or subject_type == "nan":
                    subject_type = subject
                record["科目类型"] = subject_type
                elective_records[subject].append(record)

        unified_df = pd.DataFrame(unified_records) if unified_records else pd.DataFrame()
        elective_dfs = {
            subject: pd.DataFrame(records) if records else pd.DataFrame()
            for subject, records in elective_records.items()
        }

        arrangement.gaokao_results = {"unified": unified_df, "electives": elective_dfs}
    except Exception as exc:
        return {"error": f"重建高考模式数据结构失败: {str(exc)}"}

    state.exam_arrangement = arrangement
    results = arrangement.arranged_students.fillna("").to_dict("records")
    state.rooms.results = results
    state.rooms.gaokao_results = arrangement.gaokao_results
    repo.save(state)
    return {"results": results, "message": f"导入成功（高考模式），共 {len(results)} 人"}


def import_normal_results(state, repo, build_exam_arrangement: Callable, df: pd.DataFrame, params: dict):
    required_cols = ["考号", "考场号", "座位号"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        return {"error": f"导入失败：缺少必要的列: {', '.join(missing)}（请使用系统导出的结果文件作为模板）"}

    has_subject_column = "选科" in df.columns

    for col in ["班级", "学号", "考号", "考场号", "座位号"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    exam_id_series = df["考号"].astype(str).str.strip()
    if not exam_id_series.is_unique:
        duplicates = df[df.duplicated("考号", keep=False)]["考号"].astype(str).unique().tolist()
        head = duplicates[:5]
        suffix = "..." if len(duplicates) > 5 else ""
        return {"error": f"导入失败：存在重复的考号: {', '.join(head)}{suffix}"}

    pair_df = df[["考场号", "座位号"]].astype(str).apply(lambda series: series.str.strip())
    dup_mask = pair_df.duplicated(keep=False)
    if dup_mask.any():
        samples = pair_df[dup_mask].head(5).apply(lambda row: f"{row['考场号']}-{row['座位号']}", axis=1).tolist()
        return {"error": f"导入失败：存在重复的考场号+座位号: {', '.join(samples)}（请确保同一考场内座位号不重复）"}

    settings = state.rooms.settings_data
    config = state.rooms.config or {}
    student_path = state.rooms.student_path or ""

    mode_map = {"3+1+2": "subject_mode", "normal": "normal_mode", "random": "random_mode"}
    mode = mode_map.get(config.get("mode", "normal"), "normal_mode")
    if has_subject_column:
        mode = "subject_mode"
        merged_config = dict(state.rooms.config or {})
        merged_config["mode"] = "3+1+2"
        state.rooms.config = merged_config

    arrangement = build_exam_arrangement(
        settings,
        {**config, "mode": "3+1+2" if has_subject_column else config.get("mode", "normal")},
        student_path,
    )
    arrangement.arranged_students = df.copy()
    try:
        arrangement._apply_room_names()
    except Exception:
        pass

    if mode == "subject_mode" and arrangement.subject_column in arrangement.arranged_students.columns:
        try:
            parsed_subjects = arrangement.arranged_students[arrangement.subject_column].apply(arrangement.parse_subject_combination)
            arrangement.arranged_students[["首选", "再选1", "再选2"]] = pd.DataFrame(
                parsed_subjects.tolist(),
                index=arrangement.arranged_students.index,
            )
            arrangement.arranged_students.drop(columns=["选科1", "选科2"], errors="ignore", inplace=True)
        except Exception:
            pass
        try:
            combo_map = (
                arrangement.arranged_students.groupby("考场号")[arrangement.subject_column]
                .apply(lambda series: ", ".join(sorted({str(value).strip() for value in series.tolist() if str(value).strip() and str(value).strip().lower() != "nan"})))
                .to_dict()
            )
            arrangement.arranged_students["考场选科组合"] = arrangement.arranged_students["考场号"].map(combo_map).fillna("")
        except Exception:
            pass

    state.exam_arrangement = arrangement
    results = arrangement.arranged_students.fillna("").to_dict("records")
    state.rooms.results = results
    repo.save(state)
    return {"results": results, "message": f"导入成功，共 {len(results)} 人"}
