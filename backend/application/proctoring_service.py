from __future__ import annotations

import copy
from datetime import date
import logging
import threading
import time
import traceback
import uuid
from typing import Any

from backend.domain.state import AppState
from backend.proctoring.core.cp_sat_solver import (
    SubjectContext,
    solve_schedule_with_cp_sat,
)
from backend.repository.interfaces import IStateRepository
from backend.proctoring.core.models import Teacher, Schedule, Exam
from backend.proctoring.teacher_import import import_teachers_with_validation
from backend.proctoring.teacher_template import write_teacher_template_xlsx
from backend.proctoring.schedule_export import export_schedule_workbook_to_excel
from backend.proctoring.schedule_import import import_schedule_from_excel
from backend.subjects.core import _parse_time_range

import pandas as pd
import xlsxwriter

logger = logging.getLogger(__name__)


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
    unavailable_subjects = []
    for raw_value in td.get("unavailableSubjects", []) or []:
        text = str(raw_value).strip()
        if not text:
            continue
        numeric = _to_int(text, 0)
        unavailable_subjects.append(numeric if numeric > 0 else text)
    t = Teacher(
        name=td["name"],
        gender=td.get("gender"),
        is_internal=td.get("isInternal"),
        max_sessions=_to_int(td.get("maxSessions"), -1),
        unavailable_subjects=unavailable_subjects,
        previous_supervision_duration=_to_int(td.get("previousSupervisionDuration"), 0),
    )
    preset_room = _to_int(td.get("presetRoom"), 0)
    t.preset_room = preset_room if preset_room > 0 else None
    t.supervision_duration = _to_int(td.get("supervisionDuration"), 0)
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


def _room_count_from_subject(subject: dict, default_room_count: int = 0) -> int:
    explicit = (
        subject.get("roomCount")
        if "roomCount" in subject
        else subject.get("room_count")
        if "room_count" in subject
        else None
    )
    explicit_count = _to_int(explicit, 0)
    if explicit_count > 0:
        return explicit_count

    rooms = subject.get("rooms") or []
    if isinstance(rooms, list) and rooms:
        return len(rooms)

    return max(0, int(default_room_count))


def _extract_subject_room_counts(subjects_data: list[dict], default_room_count: int = 0) -> list[int]:
    return [_room_count_from_subject(subject, default_room_count) for subject in subjects_data]


def _build_subject_room_numbers(subjects_data: list[dict], default_room_count: int = 0) -> list[list[int]]:
    room_counts = _extract_subject_room_counts(subjects_data, default_room_count)
    return [list(range(1, room_count + 1)) for room_count in room_counts]


def _state_subjects_with_ids(state_subjects: list[dict]) -> list[dict]:
    result = []
    for index, subject in enumerate(state_subjects or []):
        item = dict(subject)
        item["id"] = str(index + 1)
        if not item.get("time") and item.get("exam_time"):
            item["time"] = item.get("exam_time")
        if not item.get("exam_time") and item.get("time"):
            item["exam_time"] = item.get("time")
        if "roomCount" not in item:
            if "room_count" in item:
                item["roomCount"] = item.get("room_count")
            else:
                item["roomCount"] = _room_count_from_subject(item, 0)
        result.append(item)
    return result


def _merge_subjects_with_state(subjects_data: list[dict], state_subjects: list[dict]) -> list[dict]:
    incoming = _sort_subjects(subjects_data or [])
    state_items = _sort_subjects(_state_subjects_with_ids(state_subjects))
    if not incoming:
        return state_items
    if not state_items:
        return incoming

    state_by_id = {str(item.get("id")): item for item in state_items if str(item.get("id", "")).strip()}
    merged: list[dict] = []
    for index, subject in enumerate(incoming):
        subject_id = str(subject.get("id", "")).strip()
        base = state_by_id.get(subject_id) or (state_items[index] if index < len(state_items) else {})
        item = dict(base)
        for key, value in subject.items():
            if value is None:
                continue
            if isinstance(value, str) and not value.strip() and key in {"exam_date", "exam_time", "time"}:
                continue
            item[key] = value
        if not item.get("id"):
            item["id"] = subject_id or str(index + 1)
        if not item.get("time") and item.get("exam_time"):
            item["time"] = item.get("exam_time")
        if not item.get("exam_time") and item.get("time"):
            item["exam_time"] = item.get("time")
        if "durationMinutes" not in item:
            if "duration_minutes" in item:
                item["durationMinutes"] = item.get("duration_minutes")
            elif "duration" in item:
                item["durationMinutes"] = item.get("duration")
        if "roomCount" not in item:
            if "room_count" in item:
                item["roomCount"] = item.get("room_count")
            else:
                item["roomCount"] = _room_count_from_subject(item, 0)
        duration = _to_int(item.get("durationMinutes"), 0)
        parsed = _parse_time_range(item.get("exam_time") or item.get("time") or "")
        if duration <= 0 and parsed is not None:
            duration = parsed[2] - parsed[1]
        item["durationMinutes"] = duration
        item["roomCount"] = _room_count_from_subject(item, 0)
        merged.append(item)
    return merged


def _build_subject_contexts(subjects_data: list[dict]) -> list[SubjectContext]:
    contexts: list[SubjectContext] = []
    for index, subject in enumerate(subjects_data):
        subject_id = index + 1
        name = str(subject.get("name") or subject.get("subjectName") or f"科目{subject_id}")
        exam_date = str(subject.get("exam_date") or "").strip()
        exam_time = str(subject.get("exam_time") or subject.get("time") or "").strip()
        parsed = _parse_time_range(exam_time)
        duration = _to_int(subject.get("durationMinutes"), 0)
        if parsed is not None:
            exam_time = parsed[0]
            start_minute = parsed[1]
            end_minute = parsed[2]
            if duration <= 0:
                duration = end_minute - start_minute
        else:
            start_minute = 0
            duration = duration if duration > 0 else 1
            end_minute = duration

        if exam_date:
            try:
                sort_day = date.fromisoformat(exam_date).toordinal()
            except Exception:
                sort_day = 10**7 + index
        else:
            exam_date = f"__subject_{subject_id}"
            sort_day = 10**7 + index

        contexts.append(
            SubjectContext(
                subject_id=subject_id,
                name=name,
                exam_date=exam_date,
                exam_time=exam_time,
                duration_minutes=duration,
                start_minute=start_minute,
                end_minute=end_minute,
                sort_key=(sort_day, start_minute),
            )
        )
    return contexts


def _configure_schedule(
    schedule: Schedule,
    *,
    config: dict,
    subject_durations: list[int],
    subject_room_counts: list[int],
    lock_imported: bool,
) -> None:
    schedule.set_constraint("gender_mix", bool(config.get("genderMix", False)))
    schedule.set_constraint("internal_mix", bool(config.get("internalMix", False)))
    schedule.set_constraint("balance_mode", config.get("balanceMode", "duration"))
    schedule.set_constraint("subject_durations", list(subject_durations))
    schedule.set_constraint("subject_room_counts", list(subject_room_counts))
    schedule.set_constraint("lock_imported", bool(lock_imported))


def _build_cp_sat_optimization_payload(
    *,
    report: dict[str, Any],
    before_metrics: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    stages = report.get("stages", []) or []
    progress_samples: list[dict[str, Any]] = []
    for stage in stages:
        for sample in stage.get("progress_samples", []) or []:
            progress_samples.append(sample)
    message = report.get("message", "")
    optimization = {
        "solver": "cp_sat",
        "status": report.get("status"),
        "optimal": bool(report.get("optimal", False)),
        "swapCount": 0,
        "presetMoves": 0,
        "before": before_metrics,
        "after": report.get("metrics"),
        "earlyStopReason": None if report.get("optimal", False) else message,
    }
    details = {
        "swaps": [],
        "presetDetails": [],
        "stages": stages,
        "progressSamples": progress_samples,
        "message": message,
    }
    return optimization, details


def _format_log_number(value: Any, *, digits: int = 4) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if abs(value - round(value)) < 1e-9:
            return str(int(round(value)))
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return str(value)


def _format_metric_summary(
    *,
    label: str,
    metrics: dict[str, Any] | None,
    prefix: str,
    unit: str = "",
) -> str | None:
    if not metrics:
        return None
    min_value = metrics.get(f"{prefix}_min")
    max_value = metrics.get(f"{prefix}_max")
    range_value = metrics.get(f"{prefix}_range")
    stddev_value = metrics.get(f"{prefix}_stddev")
    if min_value is None or max_value is None or range_value is None or stddev_value is None:
        return None
    suffix = f" {unit}" if unit else ""
    return (
        f"- {label}：{_format_log_number(min_value)} ~ {_format_log_number(max_value)}{suffix}，"
        f"极差 {_format_log_number(range_value)}，标准差 {_format_log_number(stddev_value)}"
    )


def _build_cp_sat_run_log(
    *,
    operation_label: str,
    report: dict[str, Any],
    teacher_count: int,
    subject_count: int,
    wall_seconds: float | None,
) -> str:
    metrics = report.get("metrics") or {}
    status = report.get("status") or "-"
    optimal = bool(report.get("optimal", False))
    message = str(report.get("message") or "-")
    stages = report.get("stages", []) or []

    lines = [
        f"[监考编排][{operation_label}]",
        "本次结果：",
        f"- 总耗时：{_format_log_number(wall_seconds or 0.0, digits=3)}s",
        f"- 求解状态：{status}",
        f"- 已证明全局最优：{'是' if optimal else '否'}",
        f"- 返回说明：{message}",
        f"- 教师数：{teacher_count}",
        f"- 科目数：{subject_count}",
    ]

    count_summary = _format_metric_summary(label="场次数", metrics=metrics, prefix="count")
    current_summary = _format_metric_summary(
        label="本次监考时长",
        metrics=metrics,
        prefix="current_duration",
        unit="分钟",
    )
    overall_summary = _format_metric_summary(
        label="总监考时长",
        metrics=metrics,
        prefix="overall_duration",
        unit="分钟",
    )
    for summary in (count_summary, current_summary, overall_summary):
        if summary:
            lines.append(summary)

    lines.append("")
    lines.append("阶段明细：")
    if not stages:
        lines.append("0. 无阶段数据")
        return "\n".join(lines)

    for index, stage in enumerate(stages, start=1):
        lines.append(f"{index}. {stage.get('name', '-')}")
        lines.append(f"   值：{_format_log_number(stage.get('value'))}")
        lines.append(f"   耗时：{_format_log_number(stage.get('solve_seconds'), digits=3)}s")
        lines.append(f"   状态：{stage.get('status', '-')}")
        lines.append(f"   已证明最优：{'是' if stage.get('proven_optimal') else '否'}")
        stop_reason = stage.get("stop_reason")
        if stop_reason:
            lines.append(f"   停止原因：{stop_reason}")
        idle_seconds = stage.get("idle_after_last_improvement_seconds")
        if idle_seconds is not None:
            lines.append(
                f"   最后改进后空转：{_format_log_number(idle_seconds, digits=3)}s"
            )
        improvement_count = stage.get("improvement_count")
        if improvement_count is not None:
            lines.append(f"   改进次数：{_format_log_number(improvement_count)}")
        best_bound = stage.get("best_bound")
        if best_bound is not None:
            lines.append(f"   best_bound：{_format_log_number(best_bound)}")
        objective_gap = stage.get("objective_gap")
        if objective_gap is not None:
            lines.append(f"   gap：{_format_log_number(objective_gap)}")
        lines.append(
            "   锁定当前值后继续后续阶段："
            + ("是" if stage.get("continued_with_locked_value") else "否")
        )
    return "\n".join(lines)


def _log_cp_sat_run(
    *,
    operation_label: str,
    report: dict[str, Any],
    teacher_count: int,
    subject_count: int,
    wall_seconds: float | None,
) -> None:
    if not logger.isEnabledFor(logging.INFO):
        return
    try:
        logger.info(
            "%s",
            _build_cp_sat_run_log(
                operation_label=operation_label,
                report=report,
                teacher_count=teacher_count,
                subject_count=subject_count,
                wall_seconds=wall_seconds,
            ),
        )
    except Exception:
        logger.debug("Failed to log proctoring CP-SAT summary.", exc_info=True)


def _read_overview_sheet(file_path: str) -> pd.DataFrame | None:
    try:
        return pd.read_excel(file_path, sheet_name="监考总览表")
    except Exception:
        return None


def _detect_overview_room_count(file_path: str) -> int | None:
    df = _read_overview_sheet(file_path)
    if df is None:
        return None
    room_count = len(df.index)
    return room_count if room_count > 0 else None


def _detect_overview_mode(file_path: str) -> str | None:
    df = _read_overview_sheet(file_path)
    if df is None:
        return None
    for column in df.columns:
        col_text = str(column)
        if "监考员1" in col_text or "监考员2" in col_text:
            return "double"
    return "single"


def _format_schedule_result(schedule: Schedule, subjects_data: list) -> dict:
    result = []
    for exam in schedule.exams:
        subj_idx = exam.subject_id - 1
        subj_info = subjects_data[subj_idx] if subj_idx < len(subjects_data) else {}
        rooms_res = []
        original_rooms = subj_info.get("rooms", [])
        room_numbers = sorted({
            _to_int(room_num, 0)
            for room_num in [*exam.rooms, *exam.schedule.keys()]
            if _to_int(room_num, 0) > 0
        })
        for room_num in room_numbers:
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
            "examDate": subj_info.get("exam_date", ""),
            "time": subj_info.get("exam_time", subj_info.get("time", "")),
            "roomCount": len(room_numbers),
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
    subjects_data = _merge_subjects_with_state(params.get("subjects", []) or [], state_subjects)
    schedule_data = params.get("schedule", [])
    config = params.get("config", {})

    teachers = []
    teacher_map = {}
    for td in teachers_data:
        t = _teacher_from_dict(td)
        teachers.append(t)
        teacher_map[t.name] = t

    num_subjects = len(subjects_data)
    default_room_count = _to_int(config.get("roomCount"), 0)
    subject_room_counts = _extract_subject_room_counts(subjects_data, default_room_count)
    if schedule_data:
        for index, schedule_subject in enumerate(schedule_data):
            room_count = len(schedule_subject.get("rooms", []) or [])
            if room_count > 0 and index < len(subject_room_counts):
                subject_room_counts[index] = max(subject_room_counts[index], room_count)
    num_rooms = max(subject_room_counts, default=0)

    mode = config.get("mode", "single")
    schedule = Schedule(teachers, num_subjects, num_rooms, mode)
    _configure_schedule(
        schedule,
        config=config,
        subject_durations=config.get("subjectDurations", []) or _extract_subject_durations(subjects_data),
        subject_room_counts=subject_room_counts,
        lock_imported=bool(config.get("lockImported", False)) or _has_locked_positions(schedule_data),
    )

    schedule.exams = []
    subj_id_map = {s["id"]: i + 1 for i, s in enumerate(subjects_data)}
    for i in range(num_subjects):
        schedule.exams.append(Exam(i + 1, list(range(1, subject_room_counts[i] + 1))))

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
        self._job_lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}

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

    def _trim_jobs_locked(self, keep_last: int = 12) -> None:
        if len(self._jobs) <= keep_last:
            return
        finished_jobs = [
            (job.get("finished_monotonic", 0.0), job_id)
            for job_id, job in self._jobs.items()
            if job.get("status") in {"completed", "failed"}
        ]
        finished_jobs.sort()
        while len(self._jobs) > keep_last and finished_jobs:
            _, job_id = finished_jobs.pop(0)
            self._jobs.pop(job_id, None)

    def _active_job_id_locked(self) -> str | None:
        for job_id, job in self._jobs.items():
            if job.get("status") in {"queued", "running"}:
                return job_id
        return None

    def _append_progress_sample_locked(self, job: dict[str, Any], sample: dict[str, Any] | None) -> None:
        if not sample:
            return
        progress = job["progress"]
        samples = progress.setdefault("progressSamples", [])
        marker = (
            sample.get("stage"),
            sample.get("elapsedSeconds"),
            sample.get("reason"),
            sample.get("objectiveValue"),
            sample.get("bestBound"),
        )
        if samples:
            last = samples[-1]
            last_marker = (
                last.get("stage"),
                last.get("elapsedSeconds"),
                last.get("reason"),
                last.get("objectiveValue"),
                last.get("bestBound"),
            )
            if last_marker == marker:
                return
        samples.append(dict(sample))
        if len(samples) > 200:
            del samples[:-200]

    def _update_job_progress(self, job_id: str, event: dict[str, Any]) -> None:
        now = time.monotonic()
        with self._job_lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            progress = job["progress"]
            event_type = str(event.get("type") or "")
            progress["lastEventType"] = event_type
            progress["lastUpdatedMonotonic"] = now

            if event_type == "solve_started":
                progress["stageCount"] = _to_int(event.get("stage_count"), 0)
                progress["timeLimitSeconds"] = event.get("time_limit_seconds")
                progress["progressIntervalSeconds"] = event.get("progress_interval_seconds")
                progress["noImprovementLimitSeconds"] = event.get("no_improvement_limit_seconds")
                return

            if event_type == "stage_started":
                progress["currentStageName"] = event.get("name")
                progress["currentStageIndex"] = _to_int(event.get("stage_index"), 0)
                progress["stageCount"] = _to_int(event.get("stage_count"), progress.get("stageCount", 0))
                progress["currentStageMaximize"] = bool(event.get("maximize", False))
                job["current_stage_started_monotonic"] = now
                return

            if event_type == "stage_progress":
                progress["currentStageName"] = event.get("name")
                progress["currentStageIndex"] = _to_int(event.get("stage_index"), progress.get("currentStageIndex", 0))
                progress["stageCount"] = _to_int(event.get("stage_count"), progress.get("stageCount", 0))
                progress["currentStageStatus"] = event.get("status")
                progress["currentStageReason"] = event.get("reason")
                progress["currentStageSolveSeconds"] = event.get("solve_seconds")
                progress["solutionCount"] = event.get("solution_count")
                progress["improvementCount"] = event.get("improvement_count")
                progress["firstSolutionSeconds"] = event.get("first_solution_seconds")
                progress["lastSolutionSeconds"] = event.get("last_solution_seconds")
                progress["lastImprovementSeconds"] = event.get("last_improvement_seconds")
                progress["idleAfterLastImprovementSeconds"] = event.get("idle_after_last_improvement_seconds")
                progress["bestObjectiveValue"] = event.get("best_objective_value")
                progress["bestBound"] = event.get("best_bound")
                progress["objectiveGap"] = event.get("objective_gap")
                self._append_progress_sample_locked(job, event.get("latest_sample"))
                return

            if event_type == "stage_finished":
                stages = progress.setdefault("stages", [])
                stage_index = _to_int(event.get("stage_index"), 0)
                stage_payload = {k: v for k, v in event.items() if k != "type"}
                replaced = False
                for idx, stage in enumerate(stages):
                    if _to_int(stage.get("stage_index"), 0) == stage_index:
                        stages[idx] = stage_payload
                        replaced = True
                        break
                if not replaced:
                    stages.append(stage_payload)
                    stages.sort(key=lambda item: _to_int(item.get("stage_index"), 10**9))
                for sample in event.get("progress_samples", []) or []:
                    self._append_progress_sample_locked(job, sample)
                progress["currentStageStatus"] = event.get("status")
                progress["solutionCount"] = event.get("solution_count")
                progress["improvementCount"] = event.get("improvement_count")
                progress["lastImprovementSeconds"] = event.get("last_improvement_seconds")
                progress["idleAfterLastImprovementSeconds"] = event.get("idle_after_last_improvement_seconds")
                progress["bestObjectiveValue"] = event.get("value")
                progress["bestBound"] = event.get("best_bound")
                progress["objectiveGap"] = event.get("objective_gap")

    def _build_job_status_payload(self, job: dict[str, Any]) -> dict[str, Any]:
        now = time.monotonic()
        status = str(job.get("status") or "unknown")
        progress = copy.deepcopy(job.get("progress") or {})
        started_monotonic = job.get("started_monotonic")
        current_stage_started_monotonic = job.get("current_stage_started_monotonic")
        finished_monotonic = job.get("finished_monotonic")

        elapsed_seconds = None
        if started_monotonic is not None:
            end_time = finished_monotonic if finished_monotonic is not None else now
            elapsed_seconds = round(max(0.0, end_time - started_monotonic), 3)

        current_stage_elapsed = progress.get("currentStageSolveSeconds")
        if status == "running" and current_stage_started_monotonic is not None:
            current_stage_elapsed = round(max(0.0, now - current_stage_started_monotonic), 3)
            progress["currentStageSolveSeconds"] = current_stage_elapsed
            last_improvement = progress.get("lastImprovementSeconds")
            if last_improvement is not None:
                progress["idleAfterLastImprovementSeconds"] = round(
                    max(0.0, float(current_stage_elapsed) - float(last_improvement)),
                    3,
                )

        stage_count = max(1, _to_int(progress.get("stageCount"), 0) or 1)
        current_stage_index = _to_int(progress.get("currentStageIndex"), 0)
        completed_stage_count = len(progress.get("stages") or [])
        no_improvement_limit = progress.get("noImprovementLimitSeconds")
        time_limit_seconds = progress.get("timeLimitSeconds")
        within_stage_window = no_improvement_limit or time_limit_seconds or 3
        try:
            within_stage_window = max(1.0, float(within_stage_window))
        except Exception:
            within_stage_window = 3.0
        if status == "completed":
            percent = 100
        elif status == "failed":
            percent = 100
        elif status == "queued":
            percent = 0
        else:
            stage_slot = max(completed_stage_count, current_stage_index - 1)
            current_stage_progress = 0.0
            if current_stage_elapsed is not None:
                current_stage_progress = min(1.0, float(current_stage_elapsed) / within_stage_window)
            percent = min(99, max(1, int(((stage_slot + current_stage_progress) / stage_count) * 100)))

        return {
            "jobId": job.get("id"),
            "operation": job.get("operation"),
            "status": status,
            "message": job.get("message", ""),
            "error": job.get("error"),
            "elapsedSeconds": elapsed_seconds,
            "progressPercent": percent,
            "progress": progress,
            "result": copy.deepcopy(job.get("result")) if status == "completed" else None,
        }

    def _run_background_job(self, job_id: str, operation: str, params: dict) -> None:
        with self._job_lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job["status"] = "running"
            job["started_monotonic"] = time.monotonic()
            job["message"] = "Running CP-SAT solver."

        try:
            result = self._execute_job_operation(
                operation,
                params,
                progress_observer=lambda event: self._update_job_progress(job_id, event),
            )
            with self._job_lock:
                job = self._jobs.get(job_id)
                if job is None:
                    return
                if result.get("error"):
                    job["status"] = "failed"
                    job["error"] = result.get("error")
                    job["message"] = result.get("error", "")
                else:
                    job["status"] = "completed"
                    job["result"] = result
                    job["message"] = (
                        result.get("meta", {}).get("continueMessage")
                        or result.get("optimization", {}).get("earlyStopReason")
                        or "Completed."
                    )
                job["finished_monotonic"] = time.monotonic()
        except Exception as exc:
            with self._job_lock:
                job = self._jobs.get(job_id)
                if job is None:
                    return
                job["status"] = "failed"
                job["error"] = f"{type(exc).__name__}: {str(exc)}"
                job["message"] = job["error"]
                job["trace"] = traceback.format_exc()[-4000:]
                job["finished_monotonic"] = time.monotonic()

    def start_solver_job(self, params: dict) -> Any:
        operation = str(params.get("operation") or "generate").strip().lower()
        if operation not in {"generate", "continue"}:
            raise ValueError(f"Unsupported proctoring job operation: {operation}")

        with self._job_lock:
            active_job_id = self._active_job_id_locked()
            if active_job_id:
                return {
                    "error": f"Another proctoring job is already running: {active_job_id}",
                    "activeJobId": active_job_id,
                }
            job_id = uuid.uuid4().hex
            self._jobs[job_id] = {
                "id": job_id,
                "operation": operation,
                "status": "queued",
                "message": "Queued.",
                "error": None,
                "created_monotonic": time.monotonic(),
                "started_monotonic": None,
                "finished_monotonic": None,
                "current_stage_started_monotonic": None,
                "progress": {
                    "stageCount": 0,
                    "currentStageIndex": 0,
                    "currentStageName": "",
                    "stages": [],
                    "progressSamples": [],
                },
                "result": None,
            }
            self._trim_jobs_locked()

        worker = threading.Thread(
            target=self._run_background_job,
            args=(job_id, operation, copy.deepcopy(params)),
            daemon=True,
        )
        worker.start()
        return {"jobId": job_id, "status": "queued", "operation": operation}

    def get_job_status(self, params: dict) -> Any:
        job_id = str(params.get("jobId") or "").strip()
        if not job_id:
            raise ValueError("jobId is required.")
        with self._job_lock:
            job = self._jobs.get(job_id)
            if job is None:
                return {"jobId": job_id, "status": "missing", "error": "Job not found."}
            return self._build_job_status_payload(job)

    def _execute_job_operation(self, operation: str, params: dict, *, progress_observer=None) -> Any:
        if operation == "generate":
            return self._generate_schedule_impl(params, progress_observer=progress_observer)
        if operation == "continue":
            return self._continue_schedule_impl(params, progress_observer=progress_observer)
        raise ValueError(f"Unsupported proctoring job operation: {operation}")

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
        if "metrics" not in report:
            return {"error": report.get("message", "CP-SAT failed to generate a schedule.")}

        result = _format_schedule_result(schedule, subjects_data)
        optimization, details = _build_cp_sat_optimization_payload(report=report, before_metrics=None)
        result["meta"] = {
            "complete": True,
            "initialUnassigned": 0,
            "continueSuccess": True,
            "continueMessage": report.get("message", ""),
            "solver": "cp_sat",
            "solverStatus": report.get("status"),
            "optimal": bool(report.get("optimal", False)),
        }
        result["optimization"] = optimization
        result["optimizationDetails"] = details

        self._state.proctoring.schedule = result["schedule"]
        self._state.proctoring.teachers = result["teachers"]
        self._repo.save(self._state)
        _log_cp_sat_run(
            operation_label="智能编排",
            report=report,
            teacher_count=len(result["teachers"]),
            subject_count=len(subjects_data),
            wall_seconds=cp_sat_wall_seconds,
        )
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
        subject_room_counts = [len(subj.get("rooms", []) or []) for subj in schedule_data]
        num_rooms = max(subject_room_counts, default=0)

        mode = params.get("config", {}).get("mode", "single")
        schedule = Schedule(teachers, num_subjects, num_rooms, mode)
        schedule.exams = []
        subject_names = []
        exam_dates = []
        exam_times = []

        for idx, subj in enumerate(schedule_data):
            subject_id = idx + 1
            subject_names.append(subj.get("subjectName", f"科目{subject_id}"))
            source_subject = subjects_data[idx] if idx < len(subjects_data) else {}
            exam_dates.append(str(source_subject.get("exam_date") or source_subject.get("examDate") or ""))
            exam_times.append(subj.get("time", ""))
            room_count = subject_room_counts[idx] if idx < len(subject_room_counts) else 0
            exam = Exam(subject_id, list(range(1, room_count + 1)))
            exam.room_locations = {}
            for room_data in subj.get("rooms", []):
                r_id = _to_int(room_data.get("roomNum", room_data.get("id")), 0)
                if r_id <= 0:
                    continue
                exam.room_locations[r_id] = room_data.get("location") or f"绗?{r_id} 鑰冨満"
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
            path,
            schedule=schedule,
            subject_names=subject_names,
            exam_dates=exam_dates,
            exam_times=exam_times,
        )
        return {}

    def import_schedule(self, params: dict) -> Any:
        path = params["path"]
        teachers_data = params.get("teachers", [])
        subjects_data = _merge_subjects_with_state(params.get("subjects", []) or [], self._state.subjects)
        config = dict(params.get("config", {}))
        config["lockImported"] = True
        detected_room_count = _detect_overview_room_count(path)
        if detected_room_count is not None:
            config["roomCount"] = detected_room_count

        teachers = _teachers_from_list(teachers_data)
        num_subjects = len(subjects_data)
        default_room_count = _to_int(config.get("roomCount"), 0)
        subject_room_counts = _extract_subject_room_counts(subjects_data, default_room_count)
        num_rooms = max(subject_room_counts, default=0)
        mode = config.get("mode", "single")
        subject_names = [(s.get("name") or s.get("subjectName") or f"科目{i+1}") for i, s in enumerate(subjects_data)]
        exam_times = [(s.get("exam_time") or s.get("time") or "") for s in subjects_data]
        subject_durations = config.get("subjectDurations", []) or _extract_subject_durations(subjects_data)

        schedule, errors = import_schedule_from_excel(
            file_path=path, teachers=teachers, num_subjects=num_subjects,
            num_rooms=num_rooms, mode=mode, gender_mix=config.get("genderMix", False),
            internal_mix=config.get("internalMix", False), lock_imported=True,
            highlight_imported=True, subject_durations=subject_durations,
            subject_room_counts=subject_room_counts,
            subject_names=subject_names, exam_times=exam_times,
        )

        if errors:
            return {"error": "\n".join(errors)}

        result = _format_schedule_result(schedule, subjects_data)
        self._state.proctoring.schedule = result["schedule"]
        self._state.proctoring.teachers = result["teachers"]
        self._state.proctoring.config = config
        self._repo.save(self._state)
        if detected_room_count is not None:
            result["detectedRoomCount"] = detected_room_count
        return result

    def _continue_schedule_impl(self, params: dict, *, progress_observer=None) -> Any:
        params = dict(params)
        params["subjects"] = _merge_subjects_with_state(params.get("subjects", []) or [], self._state.subjects)
        schedule = _reconstruct_schedule(params, self._state.subjects)
        subjects_data = params.get("subjects", [])
        cp_sat_started = time.perf_counter()
        report = self._run_cp_sat(
            schedule=schedule,
            subjects_data=subjects_data,
            config=self._merge_config(params.get("config", {})),
            fix_existing_assignments=True,
            use_current_solution_as_hint=True,
            default_time_limit_seconds=90.0,
            progress_observer=progress_observer,
        )
        cp_sat_wall_seconds = max(0.0, time.perf_counter() - cp_sat_started)
        if "metrics" not in report:
            return {"error": report.get("message", "CP-SAT failed to complete the imported schedule.")}
        result = _format_schedule_result(schedule, subjects_data)
        optimization, details = _build_cp_sat_optimization_payload(report=report, before_metrics=None)
        result["meta"] = {
            "complete": True,
            "solver": "cp_sat",
            "solverStatus": report.get("status"),
            "optimal": bool(report.get("optimal", False)),
            "continueMessage": report.get("message", ""),
        }
        result["optimization"] = optimization
        result["optimizationDetails"] = details
        self._state.proctoring.schedule = result["schedule"]
        self._state.proctoring.teachers = result["teachers"]
        self._state.proctoring.config = self._merge_config(params.get("config", {}))
        self._repo.save(self._state)
        _log_cp_sat_run(
            operation_label="补全编排",
            report=report,
            teacher_count=len(result["teachers"]),
            subject_count=len(subjects_data),
            wall_seconds=cp_sat_wall_seconds,
        )
        return result

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
        self._state.proctoring.schedule = result["schedule"]
        self._state.proctoring.teachers = result["teachers"]
        self._state.proctoring.config = self._merge_config(params.get("config", {}))
        self._repo.save(self._state)
        return result

    def export_empty_preset(self, params: dict) -> Any:
        path = params["path"]
        subjects_data = params.get("subjects", [])
        default_room_count = _to_int(params.get("roomCount"), 0)
        subject_room_counts = _extract_subject_room_counts(subjects_data, default_room_count)
        num_rooms = max(subject_room_counts, default=0)
        mode = params.get("mode", "single")
        if num_rooms <= 0:
            return {"error": "请先为每个科目设置考场数量，或填写默认考场数量。"}

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
        subjects_data = _merge_subjects_with_state(params.get("subjects", []) or [], self._state.subjects)
        config = dict(params.get("config", {}))
        config["lockImported"] = True
        detected_room_count = _detect_overview_room_count(path)
        if detected_room_count is not None:
            config["roomCount"] = detected_room_count
        detected_mode = _detect_overview_mode(path)
        if detected_mode is not None:
            config["mode"] = detected_mode

        teachers = _teachers_from_list(teachers_data)
        num_subjects = len(subjects_data)
        default_room_count = _to_int(config.get("roomCount"), 0)
        subject_room_counts = _extract_subject_room_counts(subjects_data, default_room_count)
        num_rooms = max(subject_room_counts, default=0)
        mode = config.get("mode", "single")
        subject_names = [s.get("name", f"科目{s['id']}") for s in subjects_data]
        exam_times = [s.get("time", "") for s in subjects_data]
        subject_durations = config.get("subjectDurations", []) or _extract_subject_durations(subjects_data)

        schedule, errors = import_schedule_from_excel(
            file_path=path, teachers=teachers, num_subjects=num_subjects,
            num_rooms=num_rooms, mode=mode, gender_mix=config.get("genderMix", False),
            internal_mix=config.get("internalMix", False), lock_imported=True,
            highlight_imported=True, subject_durations=subject_durations,
            subject_room_counts=subject_room_counts,
            subject_names=subject_names, exam_times=exam_times,
        )

        if errors:
            return {"error": "\n".join(errors)}

        result = _format_schedule_result(schedule, subjects_data)
        self._state.proctoring.schedule = result["schedule"]
        self._state.proctoring.teachers = result["teachers"]
        self._state.proctoring.config = config
        self._repo.save(self._state)
        if detected_room_count is not None:
            result["detectedRoomCount"] = detected_room_count
        if detected_mode is not None:
            result["detectedMode"] = detected_mode
        return result
