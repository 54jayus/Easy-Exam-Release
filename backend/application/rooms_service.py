from __future__ import annotations

from typing import Any

import pandas as pd

from backend.domain.state import AppState
from backend.repository.interfaces import IStateRepository
from backend.examroom.core.arrangement import ExamArrangement


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def _normalize_subject_priority_order(value: Any) -> list[str]:
    allowed = ["化学", "生物", "政治", "地理"]
    if not isinstance(value, list):
        return list(allowed)
    cleaned = [str(v or "").strip() for v in value]
    filtered = [v for v in cleaned if v in allowed]
    dedup: list[str] = []
    for v in filtered:
        if v not in dedup:
            dedup.append(v)
    for v in allowed:
        if v not in dedup:
            dedup.append(v)
    return dedup[: len(allowed)]


def _build_exam_arrangement(settings: list, config: dict, student_path: str) -> ExamArrangement:
    room_setting_data = {s["roomNum"]: s["roomName"] for s in settings}
    room_capacities = {s["roomNum"]: s["capacity"] for s in settings}
    room_setting_df = (
        pd.DataFrame([{"考场号": s["roomNum"], "考场": s["roomName"]} for s in settings])
        if settings else None
    )
    mode_map = {"3+1+2": "subject_mode", "normal": "normal_mode", "random": "random_mode", "gaokao": "gaokao_mode"}
    mode = mode_map.get(config.get("mode", "normal"), "normal_mode")

    ea = ExamArrangement(
        file_path=student_path,
        max_students_per_room=int(config.get("seatsPerRoom", 30)),
        total_rooms=int(config.get("totalRooms", 20)),
        room_setting_data=room_setting_data,
        arrangement_mode=mode,
        room_capacities=room_capacities,
    )
    try:
        setattr(ea, "subject_priority_order", _normalize_subject_priority_order(config.get("subjectPriorityOrder")))
    except Exception:
        pass
    if room_setting_df is not None:
        ea.room_setting_df = room_setting_df
    return ea


def _write_instructions(writer, columns, instructions, required_cols, wrap_left, required_cell, required_header, normal_header):
    instr_row = [{col: instructions.get(col, "") for col in columns}]
    df_desc = pd.DataFrame(instr_row)
    df_desc.to_excel(writer, sheet_name="填写说明", index=False)
    desc_ws = writer.sheets["填写说明"]
    for i, col in enumerate(columns):
        desc_ws.set_column(i, i, 20, wrap_left)
    for idx, col in enumerate(columns):
        fmt = required_header if col in required_cols else normal_header
        desc_ws.write(0, idx, col, fmt)
        text = instructions.get(col, "")
        fmt = required_cell if col in required_cols else wrap_left
        desc_ws.write(1, idx, text, fmt)
    desc_ws.set_row(1, 100)


class RoomsService:
    def __init__(self, state: AppState, repo: IStateRepository):
        self._state = state
        self._repo = repo

    def _ensure_exam_arrangement(self) -> bool:
        ea = self._state.exam_arrangement
        if ea and ea.arranged_students is not None:
            return True
        if not self._state.rooms.results:
            return False
        try:
            ea = _build_exam_arrangement(
                self._state.rooms.settings_data,
                self._state.rooms.config,
                self._state.rooms.student_path,
            )
            ea.arranged_students = pd.DataFrame(self._state.rooms.results)
            self._state.exam_arrangement = ea
            return True
        except Exception:
            return False

    def get_subject_priority(self, _params: dict) -> Any:
        order = _normalize_subject_priority_order((self._state.rooms.config or {}).get("subjectPriorityOrder"))
        return {"order": order}

    def set_subject_priority(self, params: dict) -> Any:
        order = _normalize_subject_priority_order(params.get("order"))
        merged = dict(self._state.rooms.config or {})
        merged["subjectPriorityOrder"] = order
        self._state.rooms.config = merged
        ea = self._state.exam_arrangement
        if ea is not None:
            try:
                setattr(ea, "subject_priority_order", order)
            except Exception:
                pass
        self._repo.save(self._state)
        return {"order": order}

    def reset_state(self, _params: dict) -> Any:
        from backend.domain.state import RoomsState
        self._state.exam_arrangement = None
        self._state.rooms = RoomsState()
        self._repo.save(self._state)
        return {}

    def get_state(self, _params: dict) -> Any:
        try:
            if self._state.exam_arrangement is None and self._state.rooms.results:
                self._ensure_exam_arrangement()
        except Exception:
            pass

        settings = self._state.rooms.settings_data
        students = self._state.rooms.students_preview
        results = []
        config = dict(self._state.rooms.config)
        path = self._state.rooms.student_path
        ea = self._state.exam_arrangement

        if ea:
            room_setting_df = getattr(ea, "room_setting_df", None)
            if not settings and room_setting_df is not None:
                settings = [
                    {
                        "roomNum": str(row["考场号"]),
                        "roomName": str(row["考场"]),
                        "capacity": ea.room_capacities.get(str(row["考场号"]), 30),
                    }
                    for _, row in room_setting_df.iterrows()
                ]
            if not students and ea.students is not None:
                students = ea.students.fillna("").to_dict("records")
            if ea.arranged_students is not None:
                results = ea.arranged_students.fillna("").to_dict("records")
            if not config:
                config = {"totalRooms": ea.total_rooms, "seatsPerRoom": ea.max_students_per_room, "mode": "normal"}
                if ea.arrangement_mode == "subject_mode":
                    config["mode"] = "3+1+2"
                elif ea.arrangement_mode == "random_mode":
                    config["mode"] = "random"
            if not path and hasattr(ea, "file_path") and ea.file_path:
                path = ea.file_path
        else:
            if self._state.rooms.results:
                results = self._state.rooms.results

        if not config.get("totalRooms") and settings:
            config["totalRooms"] = len(settings)
            if settings:
                config["seatsPerRoom"] = settings[0].get("capacity", 30)

        config["subjectPriorityOrder"] = _normalize_subject_priority_order(config.get("subjectPriorityOrder"))
        return {"settings": settings, "students": students, "results": results, "config": config, "studentPath": path}

    def generate_template(self, params: dict) -> Any:
        type_ = params["type"]
        path = params["path"]
        try:
            with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
                wb = writer.book
                wrap_left = wb.add_format({"text_wrap": True, "align": "left", "valign": "top"})
                required_cell = wb.add_format({"text_wrap": True, "align": "left", "valign": "top", "bg_color": "#FFC7CE"})
                required_header = wb.add_format({"text_wrap": True, "align": "center", "valign": "vcenter", "bg_color": "#FFC7CE", "bold": True, "border": 1})
                normal_header = wb.add_format({"text_wrap": True, "align": "center", "valign": "vcenter", "bold": 1, "border": 1})

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
                    ws.set_column(0, 0, 8); ws.set_column(1, 1, 10); ws.set_column(2, 2, 12); ws.set_column(3, 3, 10)
                    instructions = {
                        "序号": "必填。\n必须从1开始连续编号，不得缺失或重复。",
                        "考场号": "必填。\n建议为三位如001、002。",
                        "考场": "选填。\n设置考场名称，例如：高一1。",
                        "考场人数": "必填。\n正整数，表示每个考场允许的最大人数。",
                    }
                    _write_instructions(writer, df.columns, instructions, {"序号", "考场号", "考场人数"}, wrap_left, required_cell, required_header, normal_header)

                elif type_ == "student_normal":
                    data = {"班级": ["1"]*5, "学号": ["1","2","3","4","5"], "考号": ["240001","240002","240003","240004","240005"], "姓名": ["张三","李四","王五","赵六","钱七"]}
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name="Sheet1", index=False)
                    ws = writer.sheets["Sheet1"]
                    ws.set_column(0, 1, 10); ws.set_column(2, 3, 15)
                    instructions = {
                        "班级": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                        "学号": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                        "考号": "必填。\n不允许重复。",
                        "姓名": "必填。\n示例：张三。",
                    }
                    _write_instructions(writer, df.columns, instructions, {"班级", "学号", "考号", "姓名"}, wrap_left, required_cell, required_header, normal_header)

                elif type_ == "student_subject":
                    data = {"班级": ["1"]*5, "学号": ["1","2","3","4","5"], "考号": ["240001","240002","240003","240004","240005"], "姓名": ["张三","李四","王五","赵六","钱七"], "选科": ["物化生","物化地","史政地","史化生","物生地"]}
                    df = pd.DataFrame(data)
                    df.to_excel(writer, sheet_name="Sheet1", index=False)
                    ws = writer.sheets["Sheet1"]
                    ws.set_column(0, 1, 10); ws.set_column(2, 3, 15); ws.set_column(4, 4, 25)
                    instructions = {
                        "班级": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                        "学号": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                        "考号": "必填。\n不允许重复。",
                        "姓名": "必填。\n示例：张三。",
                        "选科": "必填。\n支持缩写（如：物化生/史政地）或全称+分隔符。\n例如：物理+化学+生物",
                    }
                    _write_instructions(writer, df.columns, instructions, {"班级", "学号", "考号", "姓名", "选科"}, wrap_left, required_cell, required_header, normal_header)

            return {}
        except Exception as e:
            return {"error": str(e)}

    def import_settings(self, params: dict) -> Any:
        path = params["path"]
        try:
            df = pd.read_excel(path, dtype=str)
            required_cols = ["序号", "考场号", "考场人数"]
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                return {"error": f"考场设置文件缺少必需的列: {', '.join(missing)}"}

            seq_series = pd.to_numeric(df["序号"], errors="coerce")
            if seq_series.isna().any():
                return {"error": '"\u5e8f\u53f7"\u5217\u5305\u542b\u975e\u6570\u5b57\u5185\u5bb9'}
            if seq_series.astype(int).tolist() != list(range(1, len(df) + 1)):
                return {"error": "序号列必须从1开始顺序编号，不能有缺失或重复"}

            cap_series = pd.to_numeric(df["考场人数"], errors="coerce")
            if cap_series.isna().any():
                return {"error": '"\u8003\u573a\u4eba\u6570"\u5217\u5305\u542b\u65e0\u6548\u6570\u636e\uff0c\u5fc5\u987b\u5168\u90e8\u4e3a\u6570\u5b57'}
            if (cap_series <= 0).any():
                return {"error": '"\u8003\u573a\u4eba\u6570"\u5fc5\u987b\u4e3a\u6b63\u6574\u6570'}

            settings = []
            for _, row in df.iterrows():
                room_num = str(row.get("考场号", "")).strip()
                room_name = str(row.get("考场", "")).strip()
                capacity = row.get("考场人数")
                if not room_num or room_num == "nan":
                    continue
                settings.append({
                    "roomNum": room_num,
                    "roomName": room_name if room_name and room_name != "nan" else f"第{room_num}考场",
                    "capacity": int(float(capacity)),
                })

            self._state.rooms.settings_data = settings
            merged_config = dict(self._state.rooms.config or {})
            if settings:
                merged_config["totalRooms"] = len(settings)
                merged_config["seatsPerRoom"] = int(settings[0]["capacity"])
            self._state.rooms.config = merged_config
            self._repo.save(self._state)
            return {"settings": settings}
        except Exception as e:
            return {"error": str(e)}

    def import_students(self, params: dict) -> Any:
        path = params["path"]
        try:
            ea = ExamArrangement(path)
            success, msg = ea.load_data()
            if not success:
                return {"error": msg}

            required_columns = ["班级", "学号", "考号", "姓名"]
            missing_columns = [col for col in required_columns if col not in ea.students.columns]
            if missing_columns:
                return {"error": f"导入失败：缺少必要的列: {', '.join(missing_columns)}"}

            if "考号" in ea.students.columns and not ea.students["考号"].is_unique:
                duplicates = ea.students[ea.students.duplicated("考号", keep=False)]["考号"].unique()
                return {"error": f"导入失败：存在重复的考号: {', '.join(map(str, duplicates[:5]))}{'...' if len(duplicates) > 5 else ''}"}

            def digit_check(col_name):
                if col_name in ea.students.columns:
                    def custom_validator(value, student_name, index):
                        val = str(value).strip()
                        if val.isdigit():
                            return True, ""
                        return False, f'第{index+1}行数据，学生{student_name}的"{col_name}"只能填写数字'
                    return ea.validate_column_data(col_name, {"custom_validator": custom_validator}, col_name)
                return True, ""

            for col in ["班级", "学号"]:
                ok, err = digit_check(col)
                if not ok:
                    return {"error": err}

            preview = ea.students.fillna("").to_dict("records")
            self._state.rooms.students_preview = preview
            self._state.rooms.student_path = path
            self._repo.save(self._state)
            return {"students": preview, "total": len(ea.students), "message": msg}
        except Exception as e:
            return {"error": str(e)}

    def arrange(self, params: dict) -> Any:
        student_path = params["studentPath"]
        settings = params.get("settings", [])
        config = params.get("config", {})
        if isinstance(config, dict):
            config["subjectPriorityOrder"] = _normalize_subject_priority_order(config.get("subjectPriorityOrder"))

        self._state.rooms.config = config
        self._state.rooms.settings_data = settings
        self._state.rooms.student_path = student_path
        self._repo.save(self._state)

        ea = _build_exam_arrangement(settings, config, student_path)
        self._state.exam_arrangement = ea

        success, msg = ea.load_data()
        if not success:
            return {"error": msg}

        success, msg = ea.arrange_exam_rooms()
        if not success:
            return {"error": msg}

        results = ea.arranged_students.fillna("").to_dict("records")
        self._state.rooms.results = results
        self._repo.save(self._state)
        return {"results": results, "message": msg}

    def export(self, params: dict) -> Any:
        self._ensure_exam_arrangement()
        ea = self._state.exam_arrangement
        if not ea or ea.arranged_students is None:
            return {"error": "请先进行编排"}

        try:
            setattr(ea, "subject_priority_order", _normalize_subject_priority_order((self._state.rooms.config or {}).get("subjectPriorityOrder")))
        except Exception:
            pass

        # 注意：不要覆盖gaokao_mode
        try:
            if getattr(ea, "arranged_students", None) is not None:
                if "选科" in list(ea.arranged_students.columns):
                    # 只有当前不是gaokao_mode时才设置为subject_mode
                    if ea.arrangement_mode != "gaokao_mode":
                        ea.arrangement_mode = "subject_mode"
        except Exception:
            pass

        path = params["path"]

        # 检查是否为高考模式
        if ea.arrangement_mode == "gaokao_mode":
            success, msg = ea.save_gaokao_results(path)
        else:
            success, msg = ea.save_results(path)

        return {} if success else {"error": msg}

    def import_results(self, params: dict) -> Any:
        path = params["path"]
        try:
            xl = pd.ExcelFile(path)
            sheet_name = None
            for cand in ["学生编排结果", "编排结果", "考场编排结果", "Sheet1"]:
                if cand in xl.sheet_names:
                    sheet_name = cand
                    break
            if sheet_name is None:
                sheet_name = xl.sheet_names[0]
            df = pd.read_excel(xl, sheet_name=sheet_name, dtype=str)
        except Exception as e:
            return {"error": f"读取Excel失败: {str(e)}"}

        df.columns = [str(c).strip() for c in df.columns]
        df = df.fillna("")
        if df.empty:
            return {"error": "导入失败：文件中没有可用数据"}

        required_cols = ["考号", "考场号", "座位号"]
        missing = [c for c in required_cols if c not in df.columns]
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

        pair_df = df[["考场号", "座位号"]].astype(str).apply(lambda s: s.str.strip())
        dup_mask = pair_df.duplicated(keep=False)
        if dup_mask.any():
            samples = (
                pair_df[dup_mask].head(5)
                .apply(lambda r: f"{r['考场号']}-{r['座位号']}", axis=1)
                .tolist()
            )
            return {"error": f"导入失败：存在重复的考场号+座位号: {', '.join(samples)}（请确保同一考场内座位号不重复）"}

        settings = self._state.rooms.settings_data
        config = self._state.rooms.config or {}
        student_path = self._state.rooms.student_path or ""

        mode_map = {"3+1+2": "subject_mode", "normal": "normal_mode", "random": "random_mode"}
        mode = mode_map.get(config.get("mode", "normal"), "normal_mode")
        if has_subject_column:
            mode = "subject_mode"
            merged_config = dict(self._state.rooms.config or {})
            merged_config["mode"] = "3+1+2"
            self._state.rooms.config = merged_config

        ea = _build_exam_arrangement(settings, {**config, "mode": "3+1+2" if has_subject_column else config.get("mode", "normal")}, student_path)
        ea.arranged_students = df.copy()
        try:
            ea._apply_room_names()
        except Exception:
            pass

        if mode == "subject_mode" and ea.subject_column in ea.arranged_students.columns:
            try:
                parsed_subjects = ea.arranged_students[ea.subject_column].apply(ea.parse_subject_combination)
                ea.arranged_students[["首选", "选科1", "选科2"]] = pd.DataFrame(parsed_subjects.tolist(), index=ea.arranged_students.index)
            except Exception:
                pass
            try:
                combo_map = (
                    ea.arranged_students.groupby("考场号")[ea.subject_column]
                    .apply(lambda s: ", ".join(sorted({str(v).strip() for v in s.tolist() if str(v).strip() and str(v).strip().lower() != "nan"})))
                    .to_dict()
                )
                ea.arranged_students["考场选科组合"] = ea.arranged_students["考场号"].map(combo_map).fillna("")
            except Exception:
                pass

        self._state.exam_arrangement = ea
        results = ea.arranged_students.fillna("").to_dict("records")
        self._state.rooms.results = results
        self._repo.save(self._state)
        return {"results": results, "message": f"导入成功，共 {len(results)} 人"}
