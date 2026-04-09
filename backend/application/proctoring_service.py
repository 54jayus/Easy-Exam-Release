from __future__ import annotations

import time
from typing import Any

import pandas as pd

from backend.domain.state import AppState
from backend.proctoring.core.cp_sat import solve_schedule_with_cp_sat
from backend.proctoring.core.models import Schedule
from backend.proctoring.schedule_export import export_schedule_workbook_to_excel
from backend.proctoring.schedule_import import import_schedule_from_excel
from backend.proctoring.teacher_import import import_teachers_with_validation
from backend.proctoring.teacher_template import write_teacher_template_xlsx
from backend.repository.interfaces import IStateRepository

from .proctoring_jobs import ProctoringJobManager
from .proctoring_support import (
    _build_cp_sat_optimization_payload,
    _build_cp_sat_run_log,
    _build_empty_preset_dataframe,
    _build_export_workbook_payload,
    _build_subject_contexts,
    _configure_schedule,
    _detect_overview_mode,
    _detect_overview_room_count,
    _extract_subject_durations,
    _extract_subject_room_counts,
    _format_schedule_result,
    _has_locked_positions,
    _log_cp_sat_run,
    _merge_subjects_with_state,
    _reconstruct_schedule,
    _sort_subjects,
    _teacher_from_dict,
    _teachers_from_list,
    _to_int,
)

class ProctoringService:
    def __init__(self, state: AppState, repo: IStateRepository):
        self._state = state
        self._repo = repo
        self._job_manager = ProctoringJobManager(self._execute_job_operation)

    def _merge_config(self, incoming: dict) -> dict:
        merged = dict(self._state.proctoring.config or {})
        merged.update(incoming or {})
        return merged

    def _run_cp_sat(
        self,
        *,
        schedule: Schedule,
        subjects_data: list[dict],
        config: dict,
        fix_existing_assignments: bool,
        use_current_solution_as_hint: bool,
        default_time_limit_seconds: float,
        progress_observer=None,
    ) -> dict[str, Any]:
        subject_contexts = _build_subject_contexts(subjects_data)
        raw_time_limit = config.get("cpSatTimeLimitSeconds", default_time_limit_seconds)
        try:
            time_limit_seconds = float(raw_time_limit)
        except Exception:
            time_limit_seconds = float(default_time_limit_seconds)
        if time_limit_seconds <= 0:
            time_limit_seconds = float(default_time_limit_seconds)
        raw_progress_interval = config.get("cpSatProgressIntervalSeconds", 5)
        try:
            progress_interval_seconds = float(raw_progress_interval)
        except Exception:
            progress_interval_seconds = 5.0
        if progress_interval_seconds < 0:
            progress_interval_seconds = 5.0
        raw_no_improvement_limit = config.get("cpSatNoImprovementSeconds", 3)
        try:
            no_improvement_limit_seconds = float(raw_no_improvement_limit)
        except Exception:
            no_improvement_limit_seconds = 0.0
        if no_improvement_limit_seconds <= 0:
            no_improvement_limit_seconds = None

        return solve_schedule_with_cp_sat(
            schedule,
            subject_contexts,
            fix_existing_assignments=fix_existing_assignments,
            use_current_solution_as_hint=use_current_solution_as_hint,
            time_limit_seconds=time_limit_seconds,
            num_workers=max(1, _to_int(config.get("cpSatNumWorkers"), 8)),
            room_repeat_preference=(config.get("roomRepeatPreference") or "").strip() or None,
            avoid_consecutive_sessions=bool(config.get("avoidConsecutiveSessions", False)),
            consecutive_gap_minutes=max(0, _to_int(config.get("consecutiveGapMinutes"), 0)),
            log_search_progress=bool(config.get("cpSatLogSearchProgress", False)),
            progress_interval_seconds=progress_interval_seconds,
            no_improvement_limit_seconds=no_improvement_limit_seconds,
            progress_observer=progress_observer,
        )

    def start_solver_job(self, params: dict) -> Any:
        return self._job_manager.start_solver_job(params)

    def get_job_status(self, params: dict) -> Any:
        return self._job_manager.get_job_status(params)

    def _execute_job_operation(self, operation: str, params: dict, *, progress_observer=None) -> Any:
        if operation == "generate":
            return self._generate_schedule_impl(params, progress_observer=progress_observer)
        if operation == "continue":
            return self._continue_schedule_impl(params, progress_observer=progress_observer)
        raise ValueError(f"Unsupported proctoring job operation: {operation}")

    def _persist_proctoring_result(self, result: dict[str, Any], *, config: dict | None = None) -> None:
        self._state.proctoring.schedule = result["schedule"]
        self._state.proctoring.teachers = result["teachers"]
        if config is not None:
            self._state.proctoring.config = config
        self._repo.save(self._state)

    def _finalize_solver_result(
        self,
        *,
        schedule: Schedule,
        subjects_data: list[dict],
        report: dict[str, Any],
        config: dict,
        failure_message: str,
        operation_label: str,
        wall_seconds: float,
        meta: dict[str, Any],
    ) -> Any:
        if "metrics" not in report:
            return {"error": report.get("message", failure_message)}

        result = _format_schedule_result(schedule, subjects_data)
        optimization, details = _build_cp_sat_optimization_payload(report=report, before_metrics=None)
        result["meta"] = {
            "complete": True,
            "solver": "cp_sat",
            "solverStatus": report.get("status"),
            "optimal": bool(report.get("optimal", False)),
            **meta,
        }
        result["optimization"] = optimization
        result["optimizationDetails"] = details

        self._persist_proctoring_result(result, config=config)
        _log_cp_sat_run(
            operation_label=operation_label,
            report=report,
            teacher_count=len(result["teachers"]),
            subject_count=len(subjects_data),
            wall_seconds=wall_seconds,
        )
        return result

    def _import_schedule_workbook(
        self,
        *,
        path: str,
        teachers_data: list[dict],
        subjects_data: list[dict],
        config: dict,
        detect_mode: bool = False,
    ) -> Any:
        config = dict(config)
        config["lockImported"] = True

        detected_room_count = _detect_overview_room_count(path)
        if detected_room_count is not None:
            config["roomCount"] = detected_room_count

        detected_mode = None
        if detect_mode:
            detected_mode = _detect_overview_mode(path)
            if detected_mode is not None:
                config["mode"] = detected_mode

        teachers = _teachers_from_list(teachers_data)
        num_subjects = len(subjects_data)
        default_room_count = _to_int(config.get("roomCount"), 0)
        subject_room_counts = _extract_subject_room_counts(subjects_data, default_room_count)
        num_rooms = max(subject_room_counts, default=0)
        mode = config.get("mode", "single")
        subject_names = [
            str(subject.get("name") or subject.get("subjectName") or f"科目{index + 1}")
            for index, subject in enumerate(subjects_data)
        ]
        exam_times = [str(subject.get("exam_time") or subject.get("time") or "") for subject in subjects_data]
        subject_durations = config.get("subjectDurations", []) or _extract_subject_durations(subjects_data)

        schedule, errors = import_schedule_from_excel(
            file_path=path,
            teachers=teachers,
            num_subjects=num_subjects,
            num_rooms=num_rooms,
            mode=mode,
            gender_mix=config.get("genderMix", False),
            internal_mix=config.get("internalMix", False),
            lock_imported=True,
            highlight_imported=True,
            subject_durations=subject_durations,
            subject_room_counts=subject_room_counts,
            subject_names=subject_names,
            exam_times=exam_times,
        )

        if errors:
            return {"error": "\n".join(errors)}

        result = _format_schedule_result(schedule, subjects_data)
        self._persist_proctoring_result(result, config=config)
        if detected_room_count is not None:
            result["detectedRoomCount"] = detected_room_count
        if detected_mode is not None:
            result["detectedMode"] = detected_mode
        return result

    def get_state(self, _params: dict) -> Any:
        return {
            "teachers": self._state.proctoring.teachers,
            "schedule": self._state.proctoring.schedule or [],
            "config": self._state.proctoring.config,
        }

    def clear_state(self, params: dict) -> Any:
        from backend.domain.state import ProctoringState
        clear_teachers = params.get("clearTeachers", True)
        clear_schedule = params.get("clearSchedule", True)
        clear_config = params.get("clearConfig", True)

        if clear_teachers or clear_schedule or clear_config:
            # 如果需要清除部分数据，手动处理
            if clear_teachers:
                self._state.proctoring.teachers = []
            if clear_schedule:
                self._state.proctoring.schedule = None
            if clear_config:
                self._state.proctoring.config = {}
        else:
            # 全部清除
            self._state.proctoring = ProctoringState()

        self._repo.save(self._state)
        return {"success": True}

    def import_teachers(self, params: dict) -> Any:
        path = params["path"]
        config = params.get("config", {})
        subjects_data = params.get("subjects", [])
        mode = config.get("mode", "single")
        gender_mix = bool(config.get("genderMix", False))
        internal_mix = bool(config.get("internalMix", False))
        subject_count = len(subjects_data)
        default_room_count = _to_int(config.get("roomCount"), 0)
        subject_room_counts = _extract_subject_room_counts(subjects_data, default_room_count)
        num_rooms = max(subject_room_counts, default=0)

        if subject_count <= 0:
            return {
                "teachers": [],
                "errors": ['请先在\u201c科目设置\u201d页面导入科目后，再导入教师信息'],
                "warnings": [],
            }

        subject_names = [str(s.get("name") or s.get("subjectName") or "") for s in subjects_data]
        teachers, errors, warnings = import_teachers_with_validation(
            path, mode=mode, gender_mix=gender_mix, internal_mix=internal_mix,
            subject_count=subject_count, subject_names=subject_names,
            num_rooms=num_rooms if num_rooms > 0 else None,
        )

        teachers_data = [{
            "id": t.name, "name": t.name, "gender": t.gender, "isInternal": t.is_internal,
            "sessions": 0, "maxSessions": t.max_sessions,
            "unavailableSubjects": t.unavailable_subjects, "presetRoom": t.preset_room,
            "previousSupervisionDuration": t.previous_supervision_duration,
        } for t in teachers]

        if errors:
            return {"teachers": [], "errors": errors, "warnings": warnings}

        self._state.proctoring.teachers = teachers_data
        self._state.proctoring.config = self._merge_config(config)
        self._repo.save(self._state)
        return {"teachers": teachers_data, "errors": errors, "warnings": warnings}

    def _generate_schedule_impl(self, params: dict, *, progress_observer=None) -> Any:
        teachers_data = params.get("teachers", [])
        subjects_data = _merge_subjects_with_state(params.get("subjects", []) or [], self._state.subjects)
        config = self._merge_config(params.get("config", {}))
        self._state.proctoring.config = config

        teachers = _teachers_from_list(teachers_data)
        for t in teachers:
            t.assigned_sessions = []

        invalid_max = [t.name for t in teachers if not isinstance(t.max_sessions, int) or t.max_sessions < 0]
        if invalid_max:
            raise ValueError(
                f"以下教师\u201c最大监考段数\u201d无效（为空或为负数）：{', '.join(invalid_max)}。"
                "请在导入教师时完成数据校验，或在教师表中补全该列后重新导入。"
            )

        num_subjects = len(subjects_data)
        if num_subjects == 0:
            raise ValueError("未检测到考试科目信息，请先在科目设置页面导入或添加科目")

        default_room_count = _to_int(config.get("roomCount"), 0)
        subject_room_counts = _extract_subject_room_counts(subjects_data, default_room_count)
        if not subject_room_counts or any(room_count <= 0 for room_count in subject_room_counts):
            raise ValueError("请先为每个科目提供考场数量，或在监考编排页填写默认考场数量。")
        num_rooms = max(subject_room_counts)

        schedule = Schedule(teachers, num_subjects, num_rooms, mode=config.get("mode", "single"))

        subject_durations = _extract_subject_durations(subjects_data)
        if not any(subject_durations) and self._state.subjects:
            fallback = _merge_subjects_with_state([], self._state.subjects)
            subject_durations = _extract_subject_durations(fallback)

        config_durations = config.get("subjectDurations", [])
        _configure_schedule(
            schedule,
            config=config,
            subject_durations=config_durations if config_durations else subject_durations,
            subject_room_counts=subject_room_counts,
            lock_imported=False,
        )

        cp_sat_started = time.perf_counter()
        report = self._run_cp_sat(
            schedule=schedule,
            subjects_data=subjects_data,
            config=config,
            fix_existing_assignments=False,
            use_current_solution_as_hint=False,
            default_time_limit_seconds=90.0,
            progress_observer=progress_observer,
        )
        cp_sat_wall_seconds = max(0.0, time.perf_counter() - cp_sat_started)
        return self._finalize_solver_result(
            schedule=schedule,
            subjects_data=subjects_data,
            report=report,
            config=config,
            failure_message="CP-SAT failed to generate a schedule.",
            operation_label="智能编排",
            wall_seconds=cp_sat_wall_seconds,
            meta={
                "initialUnassigned": 0,
                "continueSuccess": True,
                "continueMessage": report.get("message", ""),
            },
        )

    def template(self, params: dict) -> Any:
        write_teacher_template_xlsx(params["path"])
        return {}

    def export(self, params: dict) -> Any:
        schedule, subject_names, exam_dates, exam_times = _build_export_workbook_payload(
            params["schedule"],
            params["teachers"],
            params.get("subjects", []),
            mode=params.get("config", {}).get("mode", "single"),
        )

        export_schedule_workbook_to_excel(
            params["path"],
            schedule=schedule,
            subject_names=subject_names,
            exam_dates=exam_dates,
            exam_times=exam_times,
        )
        return {}

    def import_schedule(self, params: dict) -> Any:
        subjects_data = _merge_subjects_with_state(params.get("subjects", []) or [], self._state.subjects)
        return self._import_schedule_workbook(
            path=params["path"],
            teachers_data=params.get("teachers", []),
            subjects_data=subjects_data,
            config=params.get("config", {}),
        )

    def _continue_schedule_impl(self, params: dict, *, progress_observer=None) -> Any:
        params = dict(params)
        params["subjects"] = _merge_subjects_with_state(params.get("subjects", []) or [], self._state.subjects)
        schedule = _reconstruct_schedule(params, self._state.subjects)
        subjects_data = params.get("subjects", [])
        config = self._merge_config(params.get("config", {}))
        cp_sat_started = time.perf_counter()
        report = self._run_cp_sat(
            schedule=schedule,
            subjects_data=subjects_data,
            config=config,
            fix_existing_assignments=True,
            use_current_solution_as_hint=True,
            default_time_limit_seconds=90.0,
            progress_observer=progress_observer,
        )
        cp_sat_wall_seconds = max(0.0, time.perf_counter() - cp_sat_started)
        return self._finalize_solver_result(
            schedule=schedule,
            subjects_data=subjects_data,
            report=report,
            config=config,
            failure_message="CP-SAT failed to complete the imported schedule.",
            operation_label="补全编排",
            wall_seconds=cp_sat_wall_seconds,
            meta={"continueMessage": report.get("message", "")},
        )

    def continue_schedule(self, params: dict) -> Any:
        return self._continue_schedule_impl(params)

    def generate_schedule(self, params: dict) -> Any:
        return self._generate_schedule_impl(params)

    def swap(self, params: dict) -> Any:
        schedule = _reconstruct_schedule(params, self._state.subjects)
        p1, p2 = params["p1"], params["p2"]
        pos1 = (int(p1["subId"]), int(p1["room"]), int(p1["tIdx"]))
        pos2 = (int(p2["subId"]), int(p2["room"]), int(p2["tIdx"]))
        success, msg = schedule.swap_teachers(pos1, pos2)
        if not success:
            return {"success": False, "message": msg}

        subjects_data = params.get("subjects", [])
        result = dict(_format_schedule_result(schedule, subjects_data), success=True)
        self._persist_proctoring_result(result, config=self._merge_config(params.get("config", {})))
        return result

    def export_empty_preset(self, params: dict) -> Any:
        dataframe, error = _build_empty_preset_dataframe(
            params.get("subjects", []),
            _to_int(params.get("roomCount"), 0),
            mode=params.get("mode", "single"),
        )
        if error:
            return {"error": error}

        assert dataframe is not None
        with pd.ExcelWriter(params["path"], engine="xlsxwriter") as writer:
            dataframe.to_excel(writer, sheet_name="监考总览表", index=False)
            worksheet = writer.sheets["监考总览表"]
            worksheet.set_column(0, len(dataframe.columns) - 1, 15)
        return {}

    def import_preset(self, params: dict) -> Any:
        subjects_data = _merge_subjects_with_state(params.get("subjects", []) or [], self._state.subjects)
        return self._import_schedule_workbook(
            path=params["path"],
            teachers_data=params.get("teachers", []),
            subjects_data=subjects_data,
            config=params.get("config", {}),
            detect_mode=True,
        )
