from __future__ import annotations

from typing import Any, Sequence

from .common import SubjectContext, _normalize_report_number, _safe_int, cp_model


def _format_clock(minute: int) -> str:
    normalized = max(0, int(minute))
    return f"{normalized // 60:02d}:{normalized % 60:02d}"


def _format_subject_names(
    subject_ids: Sequence[int],
    subject_context_by_id: dict[int, SubjectContext],
    *,
    limit: int = 4,
) -> str:
    names = [
        subject_context_by_id.get(int(subject_id), SubjectContext(
            subject_id=int(subject_id),
            name=f"科目{int(subject_id)}",
            exam_date="",
            exam_time="",
            duration_minutes=0,
            start_minute=0,
            end_minute=0,
            sort_key=(0, 0),
        )).name
        for subject_id in subject_ids
    ]
    if len(names) <= limit:
        return "、".join(names)
    return "、".join(names[:limit]) + f" 等 {len(names)} 科"


def _format_segment_label(segment: dict[str, Any]) -> str:
    time_text = f"{_format_clock(segment['start_minute'])}-{_format_clock(segment['end_minute'])}"
    exam_date = str(segment.get("exam_date") or "").strip()
    if not exam_date or exam_date.startswith("__subject_"):
        return time_text
    return f"{exam_date} {time_text}"


def _build_overlap_segments(subject_contexts: Sequence[SubjectContext]) -> list[dict[str, Any]]:
    contexts_by_day: dict[str, list[SubjectContext]] = {}
    for context in subject_contexts:
        contexts_by_day.setdefault(context.exam_date, []).append(context)

    segments: list[dict[str, Any]] = []
    for exam_date, same_day_contexts in contexts_by_day.items():
        boundaries = sorted(
            {
                int(context.start_minute)
                for context in same_day_contexts
            }
            | {
                int(context.end_minute)
                for context in same_day_contexts
            }
        )
        for left_minute, right_minute in zip(boundaries, boundaries[1:]):
            if int(right_minute) <= int(left_minute):
                continue
            active_subject_ids = sorted(
                context.subject_id
                for context in same_day_contexts
                if int(context.start_minute) < int(right_minute)
                and int(context.end_minute) > int(left_minute)
            )
            if not active_subject_ids:
                continue
            if (
                segments
                and segments[-1]["exam_date"] == exam_date
                and int(segments[-1]["end_minute"]) == int(left_minute)
                and segments[-1]["subject_ids"] == active_subject_ids
            ):
                segments[-1]["end_minute"] = int(right_minute)
                continue
            segments.append(
                {
                    "exam_date": exam_date,
                    "start_minute": int(left_minute),
                    "end_minute": int(right_minute),
                    "subject_ids": active_subject_ids,
                }
            )
    return segments


def _build_subject_teacher_map(
    candidate_teachers: dict[tuple[int, int, int], list[int]],
) -> dict[int, set[int]]:
    subject_teacher_map: dict[int, set[int]] = {}
    for slot_key, teacher_indexes in candidate_teachers.items():
        subject_id = int(slot_key[0])
        subject_teacher_map.setdefault(subject_id, set()).update(int(index) for index in teacher_indexes)
    return subject_teacher_map


def _diagnose_locked_assignment_conflicts(
    schedule,
    *,
    fixed_slots: dict[tuple[int, int, int], int],
    subject_contexts: Sequence[SubjectContext],
) -> str | None:
    if not fixed_slots:
        return None

    subject_context_by_id = {context.subject_id: context for context in subject_contexts}
    teacher_slots: dict[int, list[tuple[int, int, int]]] = {}
    for slot_key, teacher_index in fixed_slots.items():
        teacher_slots.setdefault(int(teacher_index), []).append(slot_key)

    for teacher_index, slots in teacher_slots.items():
        teacher = schedule.teachers[teacher_index]
        subject_ids = [int(slot_key[0]) for slot_key in slots]
        repeated_subject_ids = sorted(
            {
                subject_id
                for subject_id in set(subject_ids)
                if subject_ids.count(subject_id) > 1
            }
        )
        if repeated_subject_ids:
            return (
                f"导入的锁定安排存在冲突：{teacher.name} 被锁定到同一科目的多个考场，"
                f"涉及 { _format_subject_names(repeated_subject_ids, subject_context_by_id) }。"
                "同一位老师不能在同一科目监考多个考场，请检查已锁定位置。"
            )

        unique_subject_ids = sorted(set(subject_ids))
        max_sessions = max(0, _safe_int(getattr(teacher, "max_sessions", 0), default=0))
        if max_sessions > 0 and len(unique_subject_ids) > max_sessions:
            return (
                f"导入的锁定安排存在冲突：{teacher.name} 已被锁定 {len(unique_subject_ids)} 场，"
                f"但最大监考场次只有 {max_sessions}。请检查已锁定位置或调整最大监考场次。"
            )

        for left_index, left_subject_id in enumerate(unique_subject_ids):
            left_context = subject_context_by_id.get(left_subject_id)
            if left_context is None:
                continue
            for right_subject_id in unique_subject_ids[left_index + 1 :]:
                right_context = subject_context_by_id.get(right_subject_id)
                if right_context is None:
                    continue
                if left_context.exam_date != right_context.exam_date:
                    continue
                if (
                    int(left_context.end_minute) <= int(right_context.start_minute)
                    or int(right_context.end_minute) <= int(left_context.start_minute)
                ):
                    continue
                return (
                    f"导入的锁定安排存在冲突：{teacher.name} 同时被锁定在 "
                    f"{left_context.name} 和 {right_context.name}，两场考试时间重叠，无法同时监考。"
                )
    return None


def _build_infeasibility_diagnostic_message(
    schedule,
    *,
    subject_contexts: Sequence[SubjectContext],
    rooms_by_subject: dict[int, list[int]],
    required_slots: int,
    candidate_teachers: dict[tuple[int, int, int], list[int]],
    fixed_slots: dict[tuple[int, int, int], int],
) -> str:
    subject_context_by_id = {context.subject_id: context for context in subject_contexts}
    locked_conflict = _diagnose_locked_assignment_conflicts(
        schedule,
        fixed_slots=fixed_slots,
        subject_contexts=subject_contexts,
    )
    if locked_conflict:
        return locked_conflict

    subject_teacher_map = _build_subject_teacher_map(candidate_teachers)
    total_required_slots = sum(
        schedule.get_required_assignment_count(context.subject_id, room)
        for context in subject_contexts
        for room in rooms_by_subject.get(context.subject_id, [])
    )
    total_capacity = 0
    for teacher_index, teacher in enumerate(schedule.teachers):
        max_sessions = max(0, _safe_int(getattr(teacher, "max_sessions", 0), default=0))
        if max_sessions <= 0:
            continue
        eligible_subject_count = len(
            {
                context.subject_id
                for context in subject_contexts
                if teacher_index in subject_teacher_map.get(context.subject_id, set())
            }
        )
        total_capacity += min(max_sessions, eligible_subject_count)

    if total_capacity < total_required_slots:
        return (
            f"当前监考需求共需要 {total_required_slots} 个监考岗位，但按老师最大监考场次和可监考科目估算，"
            f"最多只能覆盖 {total_capacity} 个岗位。请增加老师，或放宽禁监考科目、最大监考场次、预设考场等限制。"
        )

    for segment in _build_overlap_segments(subject_contexts):
        active_subject_ids = [int(subject_id) for subject_id in segment["subject_ids"]]
        subject_names = _format_subject_names(active_subject_ids, subject_context_by_id)
        segment_teacher_indexes = sorted(
            {
                teacher_index
                for subject_id in active_subject_ids
                for teacher_index in subject_teacher_map.get(subject_id, set())
            }
        )
        required_positions = sum(
            schedule.get_required_assignment_count(subject_id, room)
            for subject_id in active_subject_ids
            for room in rooms_by_subject.get(subject_id, [])
        )
        available_teacher_count = len(segment_teacher_indexes)
        if available_teacher_count < required_positions:
            return (
                f"{_format_segment_label(segment)} 时段共需要 {required_positions} 个监考岗位，"
                f"但当前最多只能安排 {available_teacher_count} 位老师。涉及科目：{subject_names}。"
                "请增加该时段可用老师，或放宽禁监考科目、最大监考场次、预设考场等限制。"
            )

        room_demand = sum(
            1
            for subject_id in active_subject_ids
            for room in rooms_by_subject.get(subject_id, [])
            if schedule.room_requires_pair_constraints(subject_id, room)
        )
        if schedule.mode == "double" and schedule.get_constraint("gender_mix", False):
            if room_demand <= 0:
                continue
            male_count = sum(
                1
                for teacher_index in segment_teacher_indexes
                if str(getattr(schedule.teachers[teacher_index], "gender", "") or "").upper() == "M"
            )
            female_count = sum(
                1
                for teacher_index in segment_teacher_indexes
                if str(getattr(schedule.teachers[teacher_index], "gender", "") or "").upper() == "F"
            )
            if male_count < room_demand or female_count < room_demand:
                return (
                    f"已开启男女搭配。{_format_segment_label(segment)} 时段共需要 {room_demand} 名男老师和 "
                    f"{room_demand} 名女老师，但当前可用男老师 {male_count} 名、女老师 {female_count} 名。"
                    f"涉及科目：{subject_names}。请补充老师，或关闭男女搭配。"
                )

        if schedule.mode == "double" and schedule.get_constraint("internal_mix", False):
            if room_demand <= 0:
                continue
            internal_count = sum(
                1
                for teacher_index in segment_teacher_indexes
                if getattr(schedule.teachers[teacher_index], "is_internal", None) is True
            )
            external_count = sum(
                1
                for teacher_index in segment_teacher_indexes
                if getattr(schedule.teachers[teacher_index], "is_internal", None) is False
            )
            if internal_count < room_demand or external_count < room_demand:
                return (
                    f"已开启本外校搭配。{_format_segment_label(segment)} 时段共需要 {room_demand} 名本校老师和 "
                    f"{room_demand} 名外校老师，但当前可用本校老师 {internal_count} 名、外校老师 {external_count} 名。"
                    f"涉及科目：{subject_names}。请补充老师，或关闭本外校搭配。"
                )

    return (
        "未找到满足当前条件的监考安排。请优先检查老师总人数、考试重叠时段的可用老师、"
        "禁监考科目、最大监考场次、预设考场和已锁定安排。"
    )


def _validate_preset_rooms(teachers: Sequence[Any], room_count: int) -> str | None:
    preset_map: dict[int, str] = {}
    for teacher in teachers:
        preset_room = _safe_int(getattr(teacher, "preset_room", None), default=0)
        if preset_room <= 0:
            continue
        if preset_room > int(room_count):
            return (
                f"预设考场设置无效：{teacher.name} 预设为第 {preset_room} 考场，"
                f"但当前最多只有 {room_count} 个考场。请检查预设考场或考场数量。"
            )
        if preset_room in preset_map:
            return (
                f"预设考场设置冲突：{teacher.name} 和 {preset_map[preset_room]} 都被预设到第 {preset_room} 考场。"
                "同一个考场只能预设给一位老师，请检查预设考场。"
            )
        preset_map[preset_room] = teacher.name
    return None

def _status_name(status: int) -> str:
    if cp_model is None:
        return "ERROR"
    mapping = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN",
    }
    return mapping.get(status, f"STATUS_{status}")

def _status_message(status_name: str) -> str:
    if status_name == "INFEASIBLE":
        return (
            "未找到满足当前条件的监考安排。请优先检查老师人数、考试重叠时段的可用老师、"
            "禁监考科目、最大监考场次、预设考场和已锁定安排。"
        )
    if status_name == "MODEL_INVALID":
        return "当前监考编排设置无效，请检查参数后重试。"
    return "当前未能生成可用的监考安排，请稍后重试。"

def _build_solution_summary(
    *,
    final_status: int,
    optimal: bool,
    stage_reports: Sequence[dict[str, Any]],
    no_improvement_limit_seconds: float | None,
) -> dict[str, Any]:
    overall_optimal = bool(optimal and cp_model is not None and final_status == cp_model.OPTIMAL)
    if overall_optimal:
        return {
            "status": "OPTIMAL",
            "optimal": True,
            "message": "Solved to proven global optimality.",
        }

    continued_stage = next(
        (stage for stage in reversed(stage_reports) if stage.get("continued_with_locked_value")),
        None,
    )
    if continued_stage is not None:
        idle_seconds = continued_stage.get("stop_reason_idle_seconds")
        idle_text = (
            f"{idle_seconds} seconds"
            if idle_seconds is not None
            else f"{_normalize_report_number(no_improvement_limit_seconds)} seconds"
        )
        if continued_stage.get("stop_reason") == "no_improvement_limit":
            message = (
                f"Locked the best known value for stage {continued_stage.get('name')} after "
                f"{idle_text} without improvement and continued optimizing later tie-breakers. "
                "Global optimality was not proven."
            )
        else:
            message = (
                f"Locked the best known value for stage {continued_stage.get('name')} and "
                "continued optimizing later tie-breakers. Global optimality was not proven."
            )
        return {"status": "FEASIBLE", "optimal": False, "message": message}

    last_stage = stage_reports[-1] if stage_reports else {}
    if last_stage.get("stop_reason") == "no_improvement_limit":
        idle_seconds = last_stage.get("stop_reason_idle_seconds")
        idle_text = (
            f"{idle_seconds} seconds"
            if idle_seconds is not None
            else f"{_normalize_report_number(no_improvement_limit_seconds)} seconds"
        )
        message = f"Stopped early after {idle_text} without finding a better solution."
    else:
        message = "Found a feasible schedule, but global optimality was not proven within the time limit."
    return {"status": "FEASIBLE", "optimal": False, "message": message}
