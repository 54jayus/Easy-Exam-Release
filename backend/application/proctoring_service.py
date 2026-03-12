from __future__ import annotations

import traceback
from typing import Any

from backend.domain.state import AppState
from backend.repository.interfaces import IStateRepository
from backend.proctoring.core.models import Teacher, Schedule, Exam
from backend.proctoring.teacher_import import import_teachers_with_validation
from backend.proctoring.teacher_template import write_teacher_template_xlsx
from backend.proctoring.schedule_export import export_schedule_workbook_to_excel
from backend.proctoring.schedule_import import import_schedule_from_excel

import pandas as pd
import xlsxwriter


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        return int(float(str(value).strip()))
    except Exception:
        return default


def _teacher_from_dict(td: dict) -> Teacher:
    t = Teacher(
        name=td["name"],
        gender=td.get("gender"),
        is_internal=td.get("isInternal"),
        max_sessions=td.get("maxSessions"),
        unavailable_subjects=td.get("unavailableSubjects", []),
        previous_supervision_duration=td.get("previousSupervisionDuration", 0),
    )
    t.preset_room = td.get("presetRoom")
    t.supervision_duration = td.get("supervisionDuration", 0)
    return t


def _teachers_from_list(teachers_data: list) -> list[Teacher]:
    return [_teacher_from_dict(td) for td in (teachers_data or [])]


def _sort_subjects(subjects_data: list[dict]) -> list[dict]:
    def key_fn(s: dict) -> int:
        return _to_int(s.get("id"), 10**9)
    try:
        if all(str(s.get("id", "")).strip() for s in subjects_data):
            return sorted(subjects_data, key=key_fn)
    except Exception:
        pass
    return subjects_data


def _has_locked_positions(schedule_data: Any) -> bool:
    if not isinstance(schedule_data, list):
        return False
    for subj in schedule_data:
        for room in (subj.get("rooms") or []):
            for t in (room.get("teachers") or []):
                if isinstance(t, dict) and t.get("isLocked"):
                    return True
    return False


def _extract_subject_durations(subjects_data: list[dict]) -> list[int]:
    durations: list[int] = []
    for s in subjects_data:
        d = (
            s.get("durationMinutes")
            if "durationMinutes" in s
            else s.get("duration_minutes")
            if "duration_minutes" in s
            else s.get("duration")
            if "duration" in s
            else s.get("duration_minutes", 0)
        )
        durations.append(_to_int(d, 0))
    return durations


def _format_schedule_result(schedule: Schedule, subjects_data: list) -> dict:
    result = []
    for exam in schedule.exams:
        subj_idx = exam.subject_id - 1
        subj_info = subjects_data[subj_idx] if subj_idx < len(subjects_data) else {}
        rooms_res = []
        original_rooms = subj_info.get("rooms", [])
        for room_num in exam.rooms:
            room_idx = room_num - 1
            location = f"第 {room_num} 考场"
            r_id = room_num
            if room_idx < len(original_rooms):
                r_id = original_rooms[room_idx].get("id", room_num)
                location = original_rooms[room_idx].get("location", location)
            assigned = exam.schedule.get(room_num, [])
            assigned_data = []
            for idx, t in enumerate(assigned):
                if t:
                    is_imported = schedule.is_position_imported(exam.subject_id, room_num, idx)
                    is_locked = is_imported and schedule.get_constraint("lock_imported")
                    assigned_data.append({
                        "id": t.name, "name": t.name, "gender": t.gender,
                        "isInternal": t.is_internal, "sessions": t.assigned_count(),
                        "maxSessions": t.max_sessions, "isLocked": is_locked,
                        "presetRoom": t.preset_room,
                    })
                else:
                    assigned_data.append(None)
            rooms_res.append({"id": r_id, "roomNum": room_num, "location": location, "teachers": assigned_data})
        result.append({
            "subjectId": subj_info.get("id", f"sub{exam.subject_id}"),
            "subjectName": subj_info.get("name", subj_info.get("subjectName", f"科目{exam.subject_id}")),
            "time": subj_info.get("exam_time", subj_info.get("time", "")),
            "rooms": rooms_res,
        })
    teachers_source = getattr(schedule, "original_teachers_order", schedule.teachers)
    teachers_res = [{
        "id": t.name, "name": t.name, "gender": t.gender, "isInternal": t.is_internal,
        "sessions": t.assigned_count(), "maxSessions": t.max_sessions,
        "supervisionDuration": t.supervision_duration,
        "previousSupervisionDuration": t.previous_supervision_duration,
        "unavailableSubjects": t.unavailable_subjects, "presetRoom": t.preset_room,
    } for t in teachers_source]
    return {"schedule": result, "teachers": teachers_res}


def _reconstruct_schedule(params: dict, state_subjects: list) -> Schedule:
    teachers_data = params.get("teachers", [])
    subjects_data = _sort_subjects(params.get("subjects", []) or [])
    schedule_data = params.get("schedule", [])
    config = params.get("config", {})

    teachers = []
    teacher_map = {}
    for td in teachers_data:
        t = _teacher_from_dict(td)
        teachers.append(t)
        teacher_map[t.name] = t

    num_subjects = len(subjects_data)
    num_rooms = 0
    if schedule_data:
        for s in schedule_data:
            for r in s.get("rooms", []):
                num_rooms = max(num_rooms, r.get("id", 0))
    if num_rooms == 0 and subjects_data:
        num_rooms = max([len(s.get("rooms", [])) for s in subjects_data])

    mode = config.get("mode", "single")
    schedule = Schedule(teachers, num_subjects, num_rooms, mode)
    schedule.set_constraint("gender_mix", config.get("genderMix", False))
    schedule.set_constraint("internal_mix", config.get("internalMix", False))
    schedule.set_constraint("balance_mode", config.get("balanceMode", "session"))
    schedule.set_constraint(
        "subject_durations",
        config.get("subjectDurations", []) or _extract_subject_durations(subjects_data),
    )
    schedule.set_constraint(
        "lock_imported",
        bool(config.get("lockImported", False)) or _has_locked_positions(schedule_data),
    )

    schedule.exams = []
    subj_id_map = {s["id"]: i + 1 for i, s in enumerate(subjects_data)}
    for i in range(num_subjects):
        schedule.exams.append(Exam(i + 1, list(range(1, num_rooms + 1))))

    # 重置教师的已分配场次和监考时长，避免重复累加
    for teacher in teachers:
        teacher.assigned_sessions = []
        teacher.supervision_duration = 0

    for subj in schedule_data:
        s_id_str = subj.get("subjectId")
        if s_id_str not in subj_id_map:
            continue
        subject_id = subj_id_map[s_id_str]
        exam = schedule.exams[subject_id - 1]
        for room_data in subj.get("rooms", []):
            room_num = _to_int(room_data.get("roomNum", room_data.get("id")), 0)
            r_id = room_num if room_num > 0 else room_data.get("id")
            assigned_teachers = []
            for t_data in room_data.get("teachers", []):
                if t_data and t_data.get("name") in teacher_map:
                    t = teacher_map[t_data["name"]]
                    assigned_teachers.append(t)
                    t.assign((subject_id, r_id), schedule._get_subject_duration(subject_id))
                    if isinstance(t_data, dict) and t_data.get("isLocked"):
                        schedule.mark_imported_position(subject_id, r_id, len(assigned_teachers) - 1)
                else:
                    assigned_teachers.append(None)
            if assigned_teachers:
                exam.schedule[r_id] = assigned_teachers

    return schedule


class ProctoringService:
    def __init__(self, state: AppState, repo: IStateRepository):
        self._state = state
        self._repo = repo

    def _merge_config(self, incoming: dict) -> dict:
        merged = dict(self._state.proctoring.config or {})
        merged.update(incoming or {})
        return merged

    def get_state(self, _params: dict) -> Any:
        return {
            "teachers": self._state.proctoring.teachers,
            "schedule": self._state.proctoring.schedule or [],
            "config": self._state.proctoring.config,
        }

    def clear_state(self, _params: dict) -> Any:
        from backend.domain.state import ProctoringState
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
        num_rooms = int(config.get("roomCount", 0) or 0)

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

    def generate_schedule(self, params: dict) -> Any:
        teachers_data = params.get("teachers", [])
        subjects_data = _sort_subjects(params.get("subjects", []) or [])
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

        num_rooms = 0
        if subjects_data:
            num_rooms = max([len(s.get("rooms", [])) for s in subjects_data])
        if num_rooms == 0:
            num_rooms = int(config.get("roomCount", 30))

        schedule = Schedule(teachers, num_subjects, num_rooms, mode=config.get("mode", "single"))
        schedule.set_constraint("gender_mix", config.get("genderMix", False))
        schedule.set_constraint("internal_mix", config.get("internalMix", False))
        schedule.set_constraint("balance_mode", config.get("balanceMode", "session"))
        schedule.set_constraint("lock_imported", False)

        subject_durations = _extract_subject_durations(subjects_data)
        if not any(subject_durations) and self._state.subjects:
            fallback = _sort_subjects([dict(s) for s in self._state.subjects])
            subject_durations = _extract_subject_durations(fallback)

        config_durations = config.get("subjectDurations", [])
        schedule.set_constraint(
            "subject_durations", config_durations if config_durations else subject_durations
        )

        _exams, initial_unassigned = schedule.generate_schedule()
        continue_success, continue_message = schedule.continue_schedule()
        complete = schedule.is_schedule_complete()

        result = _format_schedule_result(schedule, subjects_data)
        result["meta"] = {
            "complete": complete,
            "initialUnassigned": initial_unassigned,
            "continueSuccess": continue_success,
            "continueMessage": continue_message,
        }

        self._state.proctoring.schedule = result["schedule"]
        self._state.proctoring.teachers = result["teachers"]
        self._repo.save(self._state)
        return result

    def template(self, params: dict) -> Any:
        write_teacher_template_xlsx(params["path"])
        return {}

    def export(self, params: dict) -> Any:
        path = params["path"]
        schedule_data = params["schedule"]
        teachers_data = params["teachers"]
        subjects_data = params.get("subjects", [])

        teachers = []
        teacher_map = {}
        for td in teachers_data:
            t = _teacher_from_dict(td)
            teachers.append(t)
            teacher_map[t.name] = t

        num_subjects = len(subjects_data)
        num_rooms = 0
        if schedule_data:
            for s in schedule_data:
                for r in s.get("rooms", []):
                    num_rooms = max(num_rooms, r.get("id", 0))

        mode = params.get("config", {}).get("mode", "single")
        schedule = Schedule(teachers, num_subjects, num_rooms, mode)
        schedule.exams = []
        subject_names = []
        exam_times = []

        for idx, subj in enumerate(schedule_data):
            subject_id = idx + 1
            subject_names.append(subj.get("subjectName", f"科目{subject_id}"))
            exam_times.append(subj.get("time", ""))
            exam = Exam(subject_id, list(range(1, num_rooms + 1)))
            for room_data in subj.get("rooms", []):
                r_id = room_data.get("id")
                assigned_teachers = []
                for t_data in room_data.get("teachers", []):
                    if t_data and t_data.get("name") in teacher_map:
                        t = teacher_map[t_data["name"]]
                        assigned_teachers.append(t)
                        t.assign((subject_id, r_id), 0)
                    else:
                        assigned_teachers.append(None)
                if assigned_teachers:
                    exam.schedule[r_id] = assigned_teachers
            schedule.exams.append(exam)

        export_schedule_workbook_to_excel(
            path, schedule=schedule, subject_names=subject_names, exam_times=exam_times
        )
        return {}

    def import_schedule(self, params: dict) -> Any:
        path = params["path"]
        teachers_data = params.get("teachers", [])
        subjects_data = _sort_subjects(params.get("subjects", []) or [])
        config = params.get("config", {})
        config["lockImported"] = True

        teachers = _teachers_from_list(teachers_data)
        num_subjects = len(subjects_data)
        num_rooms = int(config.get("roomCount", 30))
        mode = config.get("mode", "single")
        subject_names = [(s.get("name") or s.get("subjectName") or f"科目{i+1}") for i, s in enumerate(subjects_data)]
        exam_times = [(s.get("exam_time") or s.get("time") or "") for s in subjects_data]
        subject_durations = config.get("subjectDurations", []) or _extract_subject_durations(subjects_data)

        schedule, errors = import_schedule_from_excel(
            file_path=path, teachers=teachers, num_subjects=num_subjects,
            num_rooms=num_rooms, mode=mode, gender_mix=config.get("genderMix", False),
            internal_mix=config.get("internalMix", False), lock_imported=True,
            highlight_imported=True, subject_durations=subject_durations,
            subject_names=subject_names, exam_times=exam_times,
        )

        if errors:
            return {"error": "\n".join(errors)}

        result = _format_schedule_result(schedule, subjects_data)
        self._state.proctoring.schedule = result["schedule"]
        self._state.proctoring.teachers = result["teachers"]
        self._state.proctoring.config = config
        self._repo.save(self._state)
        return result

    def continue_schedule(self, params: dict) -> Any:
        params = dict(params)
        params["subjects"] = _sort_subjects(params.get("subjects", []) or [])
        schedule = _reconstruct_schedule(params, self._state.subjects)
        schedule.continue_schedule()
        subjects_data = params.get("subjects", [])
        result = _format_schedule_result(schedule, subjects_data)
        self._state.proctoring.schedule = result["schedule"]
        self._state.proctoring.teachers = result["teachers"]
        self._state.proctoring.config = self._merge_config(params.get("config", {}))
        self._repo.save(self._state)
        return result

    def optimize(self, params: dict) -> Any:
        params = dict(params)
        params["subjects"] = _sort_subjects(params.get("subjects", []) or [])
        schedule = _reconstruct_schedule(params, self._state.subjects)
        schedule.set_constraint("log_optimization_swaps", False)
        schedule.set_constraint("respect_preset_on_swap", True)

        if not schedule.is_schedule_complete():
            return {
                "error": '当前安排未排满，无法执行二次均衡优化。请先"补全监考安排"，确保每科每考场都已分配教师。'
            }

        try:
            report = schedule.optimize_duration_postprocess(max_passes=40)
            preset_report = schedule.enforce_preset_room_postprocess()
            schedule.rebalance_double_roles_postprocess()
        except Exception as e:
            return {"error": f"{type(e).__name__}: {str(e)}", "trace": traceback.format_exc()[-4000:]}

        subjects_data = params.get("subjects", [])
        result = _format_schedule_result(schedule, subjects_data)
        result["optimization"] = {
            "swapCount": report.get("swap_count", 0) if isinstance(report, dict) else 0,
            "before": report.get("before") if isinstance(report, dict) else None,
            "after": report.get("after") if isinstance(report, dict) else None,
            "earlyStopReason": report.get("early_stop_reason") if isinstance(report, dict) else None,
            "presetMoves": preset_report.get("moves", 0) if isinstance(preset_report, dict) else 0,
        }
        swaps = (report.get("swaps", []) or [])[:300] if isinstance(report, dict) else []
        preset_details = (preset_report.get("details", []) or [])[:300] if isinstance(preset_report, dict) else []
        result["optimizationDetails"] = {"swaps": swaps, "presetDetails": preset_details}

        self._state.proctoring.schedule = result["schedule"]
        self._state.proctoring.teachers = result["teachers"]
        self._state.proctoring.config = self._merge_config(params.get("config", {}))
        self._repo.save(self._state)
        return result

    def swap(self, params: dict) -> Any:
        schedule = _reconstruct_schedule(params, self._state.subjects)
        p1, p2 = params["p1"], params["p2"]
        pos1 = (int(p1["subId"]), int(p1["room"]), int(p1["tIdx"]))
        pos2 = (int(p2["subId"]), int(p2["room"]), int(p2["tIdx"]))
        success, msg = schedule.swap_teachers(pos1, pos2)
        if success:
            subjects_data = params.get("subjects", [])
            result = dict(_format_schedule_result(schedule, subjects_data), success=True)
            self._state.proctoring.schedule = result["schedule"]
            self._state.proctoring.teachers = result["teachers"]
            self._state.proctoring.config = self._merge_config(params.get("config", {}))
            self._repo.save(self._state)
            return result
        return {"success": False, "message": msg}

    def export_empty_preset(self, params: dict) -> Any:
        path = params["path"]
        subjects_data = params.get("subjects", [])
        num_rooms = int(params.get("roomCount", 30))
        mode = params.get("mode", "single")

        columns = ["考场"]
        subject_names = [s.get("name", f"科目{s['id']}") for s in subjects_data]
        exam_times = [s.get("time", "") for s in subjects_data]
        for idx, name in enumerate(subject_names):
            time = exam_times[idx] if idx < len(exam_times) else ""
            if mode == "double":
                columns.append(f"{name}-监考员1\n{time}")
                columns.append(f"{name}-监考员2\n{time}")
            else:
                columns.append(f"{name}\n{time}")

        data = []
        for room in range(1, num_rooms + 1):
            row = {"考场": f"考场{room}"}
            for col in columns[1:]:
                row[col] = ""
            data.append(row)

        df = pd.DataFrame(data, columns=columns)
        with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="监考总览表", index=False)
            worksheet = writer.sheets["监考总览表"]
            worksheet.set_column(0, len(columns) - 1, 15)
        return {}

    def import_preset(self, params: dict) -> Any:
        path = params["path"]
        teachers_data = params.get("teachers", [])
        subjects_data = params.get("subjects", [])
        config = params.get("config", {})
        config["lockImported"] = True

        teachers = _teachers_from_list(teachers_data)
        num_subjects = len(subjects_data)
        num_rooms = int(config.get("roomCount", 30))
        mode = config.get("mode", "single")
        subject_names = [s.get("name", f"科目{s['id']}") for s in subjects_data]
        exam_times = [s.get("time", "") for s in subjects_data]

        def _detect_preset_overview_mode(file_path: str):
            try:
                df = pd.read_excel(file_path, sheet_name="监考总览表", nrows=1)
            except Exception:
                return None
            for c in df.columns:
                if "监考员1" in str(c) or "监考员2" in str(c):
                    return "double"
            return "single"

        schedule, errors = import_schedule_from_excel(
            file_path=path, teachers=teachers, num_subjects=num_subjects,
            num_rooms=num_rooms, mode=mode, gender_mix=config.get("genderMix", False),
            internal_mix=config.get("internalMix", False), lock_imported=True,
            highlight_imported=True, subject_durations=config.get("subjectDurations", []),
            subject_names=subject_names, exam_times=exam_times,
        )

        if errors:
            detected_mode = _detect_preset_overview_mode(path)
            if detected_mode and detected_mode != mode:
                _, alt_errors = import_schedule_from_excel(
                    file_path=path, teachers=teachers, num_subjects=num_subjects,
                    num_rooms=num_rooms, mode=detected_mode,
                    gender_mix=config.get("genderMix", False),
                    internal_mix=config.get("internalMix", False),
                    lock_imported=True, highlight_imported=True,
                    subject_durations=config.get("subjectDurations", []),
                    subject_names=subject_names, exam_times=exam_times,
                )
                if not alt_errors:
                    return {"error": "\n".join(errors), "modeMismatch": {"current": mode, "detected": detected_mode}}
            return {"error": "\n".join(errors)}

        result = _format_schedule_result(schedule, subjects_data)
        self._state.proctoring.schedule = result["schedule"]
        self._state.proctoring.teachers = result["teachers"]
        self._state.proctoring.config = config
        self._repo.save(self._state)
        return result
