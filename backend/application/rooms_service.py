from __future__ import annotations

from typing import Any

import pandas as pd

from backend.domain.state import AppState
from backend.repository.interfaces import IStateRepository
from backend.examroom.core.arrangement import ExamArrangement
from backend.examroom.core.gaokao_defaults import (
    GAOKAO_SUBJECT_ORDER,
    build_gaokao_time_defaults,
    normalize_gaokao_time_settings,
)
from backend.application.rooms_result_importers import (
    import_gaokao_results,
    import_normal_results,
    is_gaokao_results_dataframe,
    load_results_dataframe,
)
from backend.application.rooms_input_importers import (
    import_settings as import_room_settings,
    import_students as import_room_students,
)
from backend.application.rooms_templates import generate_template as generate_rooms_template


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
    # 设置高考时间配置
    try:
        gaokao_settings = normalize_gaokao_time_settings(config.get("gaokaoTimeSettings"))
        setattr(ea, "gaokao_time_settings", gaokao_settings)
    except Exception:
        pass
    if room_setting_df is not None:
        ea.room_setting_df = room_setting_df
    return ea


def _validate_gaokao_time_settings(settings: dict) -> str | None:
    exam_times = settings.get("examTimes", {})
    self_study_times = settings.get("selfStudyTimes", {})

    subject_names: list[str] = []
    for subject in GAOKAO_SUBJECT_ORDER:
        time_config = exam_times.get(subject)
        if not isinstance(time_config, dict):
            return f"{subject}的考试时间配置无效"

        subject_name = str(time_config.get("subjectName") or "").strip()
        if not subject_name:
            return f"{subject}的科目名称不能为空"
        subject_names.append(subject_name)

        if not str(time_config.get("date") or "").strip():
            return f"{subject}的考试日期不能为空"
        if not str(time_config.get("startTime") or "").strip():
            return f"{subject}的开始时间不能为空"
        if not str(time_config.get("endTime") or "").strip():
            return f"{subject}的结束时间不能为空"

    duplicate_names = sorted({name for name in subject_names if subject_names.count(name) > 1})
    if duplicate_names:
        return f"科目名称不能重复：{'、'.join(duplicate_names)}"

    for subject in ["化学", "地理", "政治", "生物"]:
        time_config = self_study_times.get(subject)
        if not isinstance(time_config, dict):
            return f"{subject}的自习时间配置无效"

        if not str(time_config.get("date") or "").strip():
            return f"{subject}的自习日期不能为空"
        if not str(time_config.get("startTime") or "").strip():
            return f"{subject}的自习开始时间不能为空"
        if not str(time_config.get("endTime") or "").strip():
            return f"{subject}的自习结束时间不能为空"

    return None


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

            # 恢复 gaokao_results
            if self._state.rooms.gaokao_results:
                ea.gaokao_results = self._state.rooms.gaokao_results

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

    def get_gaokao_time_settings(self, _params: dict) -> Any:
        """获取高考模式时间设置"""
        settings = normalize_gaokao_time_settings((self._state.rooms.config or {}).get("gaokaoTimeSettings"))
        return {"settings": settings}

    def set_gaokao_time_settings(self, params: dict) -> Any:
        """保存高考模式时间设置"""
        if "settings" not in params:
            return {"error": "缺少 settings 参数"}
        settings = params.get("settings")

        # 验证数据结构
        if not isinstance(settings, dict):
            return {"error": "settings 必须是字典类型"}

        if "examTimes" not in settings or "selfStudyTimes" not in settings:
            return {"error": "settings 缺少必要字段"}

        normalized_settings = normalize_gaokao_time_settings(settings)
        validation_error = _validate_gaokao_time_settings(normalized_settings)
        if validation_error:
            return {"error": validation_error}

        # 保存到 config
        merged = dict(self._state.rooms.config or {})
        merged["gaokaoTimeSettings"] = normalized_settings
        self._state.rooms.config = merged

        # 如果 exam_arrangement 存在，更新其时间设置
        ea = self._state.exam_arrangement
        if ea is not None:
            try:
                setattr(ea, "gaokao_time_settings", normalized_settings)
            except Exception:
                pass

        self._repo.save(self._state)
        return {}

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
        config["gaokaoTimeSettings"] = normalize_gaokao_time_settings(config.get("gaokaoTimeSettings"))
        return {"settings": settings, "students": students, "results": results, "config": config, "studentPath": path}

    def generate_template(self, params: dict) -> Any:
        return generate_rooms_template(params["type"], params["path"])

    def import_settings(self, params: dict) -> Any:
        return import_room_settings(self._state, self._repo, params["path"])

    def import_students(self, params: dict) -> Any:
        return import_room_students(self._state, self._repo, params["path"])

    def arrange(self, params: dict) -> Any:
        student_path = params["studentPath"]
        settings = params.get("settings", [])
        config = params.get("config", {})
        if isinstance(config, dict):
            config["subjectPriorityOrder"] = _normalize_subject_priority_order(config.get("subjectPriorityOrder"))
            # 确保高考时间设置存在
            config["gaokaoTimeSettings"] = normalize_gaokao_time_settings(config.get("gaokaoTimeSettings"))

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

        # 保存 gaokao_results
        if ea.arrangement_mode == "gaokao_mode" and ea.gaokao_results:
            self._state.rooms.gaokao_results = ea.gaokao_results
        else:
            self._state.rooms.gaokao_results = None

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

        # 确保高考时间设置被传递
        try:
            gaokao_settings = (self._state.rooms.config or {}).get(
                "gaokaoTimeSettings", build_gaokao_time_defaults()
            )
            setattr(ea, "gaokao_time_settings", normalize_gaokao_time_settings(gaokao_settings))
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
            df = load_results_dataframe(path)
        except ValueError as exc:
            return {"error": str(exc)}

        if is_gaokao_results_dataframe(df):
            return self._import_gaokao_results(df, params)
        return self._import_normal_results(df, params)

    def _import_gaokao_results(self, df: pd.DataFrame, params: dict) -> Any:
        return import_gaokao_results(self._state, self._repo, _build_exam_arrangement, df, params)

    def _import_normal_results(self, df: pd.DataFrame, params: dict) -> Any:
        return import_normal_results(self._state, self._repo, _build_exam_arrangement, df, params)
