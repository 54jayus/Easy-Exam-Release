from __future__ import annotations

from datetime import date
import logging
import random
from typing import Any

import pandas as pd

from backend.proctoring.core.cp_sat import SubjectContext
from backend.proctoring.core.entities import (
    EXEMPT_SLOT_ID,
    build_exempt_slot_payload,
)
from backend.proctoring.core.models import Exam, Schedule, Teacher
from backend.subjects.core import _parse_time_range

# Keep the historical logger name so existing log routing stays stable.
logger = logging.getLogger("backend.application.proctoring_service")


def _is_exempt_teacher_payload(value: Any) -> bool:
    return isinstance(value, dict) and bool(value.get("isExempt") or value.get("id") == EXEMPT_SLOT_ID)

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


def _randomize_teacher_order_for_solver(schedule: Schedule) -> None:
    if len(schedule.teachers) <= 1:
        return
    random.SystemRandom().shuffle(schedule.teachers)


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
        "countBalanceHardLimitApplied": report.get("countBalanceHardLimitApplied"),
        "countBalanceConstraintScope": report.get("countBalanceConstraintScope"),
    }
    details = {
        "swaps": [],
        "presetDetails": [],
        "stages": stages,
        "progressSamples": progress_samples,
        "message": message,
        "countBalanceHardLimitApplied": report.get("countBalanceHardLimitApplied"),
        "countBalanceConstraintScope": report.get("countBalanceConstraintScope"),
        "regularTeacherIndexes": report.get("regularTeacherIndexes", []),
        "specialTeacherIndexes": report.get("specialTeacherIndexes", []),
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
            for idx in range(schedule.get_slot_count()):
                if schedule.is_position_exempt(exam.subject_id, room_num, idx):
                    assigned_data.append(build_exempt_slot_payload())
                    continue
                t = assigned[idx] if idx < len(assigned) else None
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
            for slot_index, t_data in enumerate(room_data.get("teachers", [])):
                if _is_exempt_teacher_payload(t_data):
                    assigned_teachers.append(None)
                    schedule.mark_exempt_position(subject_id, r_id, slot_index)
                    continue
                if t_data and t_data.get("name") in teacher_map:
                    t = teacher_map[t_data["name"]]
                    assigned_teachers.append(t)
                    t.assign((subject_id, r_id), schedule._get_subject_duration(subject_id))
                    if isinstance(t_data, dict) and t_data.get("isLocked"):
                        schedule.mark_imported_position(subject_id, r_id, slot_index)
                else:
                    assigned_teachers.append(None)
            if assigned_teachers:
                exam.schedule[r_id] = assigned_teachers

    return schedule


def _build_export_workbook_payload(
    schedule_data: list[dict],
    teachers_data: list[dict],
    subjects_data: list[dict],
    *,
    mode: str,
) -> tuple[Schedule, list[str], list[str], list[str]]:
    teachers = []
    teacher_map = {}
    for teacher_data in teachers_data:
        teacher = _teacher_from_dict(teacher_data)
        teachers.append(teacher)
        teacher_map[teacher.name] = teacher

    num_subjects = len(subjects_data)
    subject_room_counts = [len(subject.get("rooms", []) or []) for subject in schedule_data]
    num_rooms = max(subject_room_counts, default=0)

    schedule = Schedule(teachers, num_subjects, num_rooms, mode)
    schedule.exams = []
    subject_names: list[str] = []
    exam_dates: list[str] = []
    exam_times: list[str] = []

    for index, subject in enumerate(schedule_data):
        subject_id = index + 1
        subject_names.append(str(subject.get("subjectName", f"\u79d1\u76ee{subject_id}")))
        source_subject = subjects_data[index] if index < len(subjects_data) else {}
        exam_dates.append(str(source_subject.get("exam_date") or source_subject.get("examDate") or ""))
        exam_times.append(str(subject.get("time", "")))
        room_count = subject_room_counts[index] if index < len(subject_room_counts) else 0
        exam = Exam(subject_id, list(range(1, room_count + 1)))
        exam.room_locations = {}
        for room_data in subject.get("rooms", []):
            room_id = _to_int(room_data.get("roomNum", room_data.get("id")), 0)
            if room_id <= 0:
                continue
            exam.room_locations[room_id] = room_data.get("location") or f"\u7ed7?{room_id} \u9470\u51a8\u6e80"
            assigned_teachers = []
            for slot_index, teacher_data in enumerate(room_data.get("teachers", [])):
                if _is_exempt_teacher_payload(teacher_data):
                    assigned_teachers.append(None)
                    schedule.mark_exempt_position(subject_id, room_id, slot_index)
                    continue
                if teacher_data and teacher_data.get("name") in teacher_map:
                    teacher = teacher_map[teacher_data["name"]]
                    assigned_teachers.append(teacher)
                    teacher.assign((subject_id, room_id), 0)
                else:
                    assigned_teachers.append(None)
            if assigned_teachers:
                exam.schedule[room_id] = assigned_teachers
        schedule.exams.append(exam)

    return schedule, subject_names, exam_dates, exam_times


def _build_empty_preset_dataframe(
    subjects_data: list[dict],
    default_room_count: int,
    *,
    mode: str,
) -> tuple[pd.DataFrame | None, str | None]:
    subject_room_counts = _extract_subject_room_counts(subjects_data, default_room_count)
    num_rooms = max(subject_room_counts, default=0)
    if num_rooms <= 0:
        return None, "\u8bf7\u5148\u4e3a\u6bcf\u4e2a\u79d1\u76ee\u8bbe\u7f6e\u8003\u573a\u6570\u91cf\uff0c\u6216\u586b\u5199\u9ed8\u8ba4\u8003\u573a\u6570\u91cf\u3002"

    columns = ["\u8003\u573a"]
    subject_names = [subject.get("name", f"\u79d1\u76ee{subject['id']}") for subject in subjects_data]
    exam_times = [subject.get("time", "") for subject in subjects_data]
    for index, name in enumerate(subject_names):
        exam_time = exam_times[index] if index < len(exam_times) else ""
        if mode == "double":
            columns.append(f"{name}-\u76d1\u8003\u54581\n{exam_time}")
            columns.append(f"{name}-\u76d1\u8003\u54582\n{exam_time}")
        else:
            columns.append(f"{name}\n{exam_time}")

    data = []
    for room in range(1, num_rooms + 1):
        row = {"\u8003\u573a": f"\u8003\u573a{room}"}
        for column in columns[1:]:
            row[column] = ""
        data.append(row)

    return pd.DataFrame(data, columns=columns), None


