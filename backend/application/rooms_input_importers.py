from __future__ import annotations

import pandas as pd

from backend.examroom.core.arrangement import ExamArrangement


def import_settings(state, repo, path: str):
    try:
        df = pd.read_excel(path, dtype=str)
        required_cols = ["序号", "考场号", "考场人数"]
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            return {"error": f"考场设置文件缺少必需的列: {', '.join(missing)}"}

        seq_series = pd.to_numeric(df["序号"], errors="coerce")
        if seq_series.isna().any():
            return {"error": '"序号"列包含非数字内容'}
        if seq_series.astype(int).tolist() != list(range(1, len(df) + 1)):
            return {"error": "序号列必须从1开始顺序编号，不能有缺失或重复"}

        cap_series = pd.to_numeric(df["考场人数"], errors="coerce")
        if cap_series.isna().any():
            return {"error": '"考场人数"列包含无效数据，必须全部为数字'}
        if (cap_series <= 0).any():
            return {"error": '"考场人数"必须为正整数'}

        settings = []
        for _, row in df.iterrows():
            room_num = str(row.get("考场号", "")).strip()
            room_name = str(row.get("考场", "")).strip()
            capacity = row.get("考场人数")
            if not room_num or room_num == "nan":
                continue
            settings.append(
                {
                    "roomNum": room_num,
                    "roomName": room_name if room_name and room_name != "nan" else f"第{room_num}考场",
                    "capacity": int(float(capacity)),
                }
            )

        state.rooms.settings_data = settings
        merged_config = dict(state.rooms.config or {})
        if settings:
            merged_config["totalRooms"] = len(settings)
            merged_config["seatsPerRoom"] = int(settings[0]["capacity"])
        state.rooms.config = merged_config
        repo.save(state)
        return {"settings": settings}
    except Exception as exc:
        return {"error": str(exc)}


def import_students(state, repo, path: str):
    try:
        arrangement = ExamArrangement(path)
        success, message = arrangement.load_data()
        if not success:
            return {"error": message}

        required_columns = ["班级", "学号", "考号", "姓名"]
        missing_columns = [col for col in required_columns if col not in arrangement.students.columns]
        if missing_columns:
            return {"error": f"导入失败：缺少必要的列: {', '.join(missing_columns)}"}

        if "考号" in arrangement.students.columns and not arrangement.students["考号"].is_unique:
            duplicates = arrangement.students[arrangement.students.duplicated("考号", keep=False)]["考号"].unique()
            suffix = "..." if len(duplicates) > 5 else ""
            return {"error": f"导入失败：存在重复的考号: {', '.join(map(str, duplicates[:5]))}{suffix}"}

        def digit_check(column_name):
            if column_name not in arrangement.students.columns:
                return True, ""

            def custom_validator(value, student_name, index):
                val = str(value).strip()
                if val.isdigit():
                    return True, ""
                return False, f'第{index+1}行数据，学生{student_name}的"{column_name}"只能填写数字'

            return arrangement.validate_column_data(column_name, {"custom_validator": custom_validator}, column_name)

        for col in ["班级", "学号"]:
            ok, error = digit_check(col)
            if not ok:
                return {"error": error}

        preview = arrangement.students.fillna("").to_dict("records")
        state.rooms.students_preview = preview
        state.rooms.student_path = path
        repo.save(state)
        return {"students": preview, "total": len(arrangement.students), "message": message}
    except Exception as exc:
        return {"error": str(exc)}
