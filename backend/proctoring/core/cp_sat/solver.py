from __future__ import annotations

import copy
import threading
import time
from typing import Any, Callable, Sequence

from .assignment import (
    _apply_solver_result,
    _build_consecutive_pairs,
    _build_overlap_pairs,
    _build_teacher_unavailable_map,
    _collect_existing_slot_assignments,
    _set_solution_hints,
    _teacher_can_take_slot,
)
from .common import SubjectContext, _normalize_report_number, _safe_int, cp_model, logger
from .diagnostics import (
    _build_infeasibility_diagnostic_message,
    _build_solution_summary,
    _status_message,
    _status_name,
    _validate_preset_rooms,
)
from .metrics import compute_schedule_metrics
from .objectives import _build_objective_stages
from .progress import _StageProgressTracker


def _add_double_slot_symmetry_breaking(
    model,
    *,
    schedule,
    subject_contexts: Sequence[SubjectContext],
    rooms_by_subject: dict[int, list[int]],
    slot_vars: dict[tuple[int, tuple[int, int, int]], Any],
    candidate_teachers: dict[tuple[int, int, int], list[int]],
    fixed_slots: dict[tuple[int, int, int], int],
) -> None:
    for context in subject_contexts:
        for room in rooms_by_subject[context.subject_id]:
            if not schedule.room_requires_pair_constraints(context.subject_id, room):
                continue
            left_slot = (context.subject_id, room, 0)
            right_slot = (context.subject_id, room, 1)
            if left_slot in fixed_slots or right_slot in fixed_slots:
                continue

            left_terms = [
                (teacher_index + 1) * slot_vars[(teacher_index, left_slot)]
                for teacher_index in candidate_teachers.get(left_slot, [])
                if (teacher_index, left_slot) in slot_vars
            ]
            right_terms = [
                (teacher_index + 1) * slot_vars[(teacher_index, right_slot)]
                for teacher_index in candidate_teachers.get(right_slot, [])
                if (teacher_index, right_slot) in slot_vars
            ]
            if not left_terms or not right_terms:
                continue

            # When the two monitor slots are interchangeable, canonicalize teacher order.
            model.Add(sum(left_terms) <= sum(right_terms))


def solve_schedule_with_cp_sat(
    schedule,
    subject_contexts: Sequence[SubjectContext],
    *,
    fix_existing_assignments: bool = False,
    use_current_solution_as_hint: bool = False,
    time_limit_seconds: float = 90.0,
    num_workers: int = 8,
    room_repeat_preference: str | None = None,
    avoid_consecutive_sessions: bool = False,
    log_search_progress: bool = False,
    progress_interval_seconds: float = 5.0,
    no_improvement_limit_seconds: float | None = None,
    progress_observer: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    if cp_model is None:
        return {
            "status": "ERROR",
            "optimal": False,
            "message": "CP-SAT solver is unavailable. Install the 'ortools' package first.",
        }

    required_slots = 2 if schedule.mode == "double" else 1
    if len(subject_contexts) != int(schedule.num_subjects):
        return {
            "status": "ERROR",
            "optimal": False,
            "message": "Subject context count does not match the schedule subject count.",
        }

    preset_error = _validate_preset_rooms(schedule.teachers, schedule.num_rooms)
    if preset_error:
        return {"status": "INFEASIBLE", "optimal": False, "message": preset_error}

    model = cp_model.CpModel()
    teacher_count = len(schedule.teachers)
    teacher_index_by_name = {teacher.name: index for index, teacher in enumerate(schedule.teachers)}
    rooms_by_subject = {
        context.subject_id: list(schedule._get_subject_rooms(context.subject_id))
        for context in subject_contexts
    }
    all_rooms = sorted({room for rooms in rooms_by_subject.values() for room in rooms})

    fixed_slots, hinted_slots = _collect_existing_slot_assignments(
        schedule,
        teacher_index_by_name=teacher_index_by_name,
        required_slots=required_slots,
        fix_existing_assignments=fix_existing_assignments,
    )

    slots_by_subject: dict[int, list[tuple[int, int, int]]] = {
        context.subject_id: [] for context in subject_contexts
    }
    candidate_teachers: dict[tuple[int, int, int], list[int]] = {}
    slot_vars: dict[tuple[int, tuple[int, int, int]], Any] = {}
    teacher_unavailable = _build_teacher_unavailable_map(schedule.teachers, subject_contexts)

    for context in subject_contexts:
        for room in rooms_by_subject[context.subject_id]:
            active_slot_indexes = schedule.get_active_slot_indexes(context.subject_id, room)
            enforce_double_slot_roles = (
                schedule.mode == "double"
                and schedule.get_constraint("internal_mix", False)
                and len(active_slot_indexes) == 2
            )
            for slot_index in active_slot_indexes:
                slot_key = (context.subject_id, room, slot_index)
                slots_by_subject[context.subject_id].append(slot_key)
                fixed_teacher = fixed_slots.get(slot_key)
                allowed = []

                for teacher_index, teacher in enumerate(schedule.teachers):
                    if not _teacher_can_take_slot(
                        schedule,
                        teacher=teacher,
                        teacher_index=teacher_index,
                        subject_context=context,
                        room=room,
                        slot_index=slot_index,
                        teacher_unavailable=teacher_unavailable,
                        enforce_double_slot_roles=enforce_double_slot_roles,
                    ):
                        continue
                    allowed.append(teacher_index)

                if fixed_teacher is not None and fixed_teacher not in allowed:
                    teacher_name = schedule.teachers[fixed_teacher].name
                    return {
                        "status": "INFEASIBLE",
                        "optimal": False,
                        "message": (
                            f"导入的锁定安排与当前条件冲突：{teacher_name} 无法继续保留在 "
                            f"{context.name} 第 {room} 考场。请检查锁定位置、禁监考科目、预设考场和搭配条件。"
                        ),
                    }

                if not allowed:
                    return {
                        "status": "INFEASIBLE",
                        "optimal": False,
                        "message": (
                            f"{context.name} 第 {room} 考场当前没有可用监考老师。"
                            "请检查老师人数、禁监考科目、最大监考场次、预设考场和搭配条件。"
                        ),
                    }

                candidate_teachers[slot_key] = allowed
                slot_exprs = []
                for teacher_index in allowed:
                    var = model.NewBoolVar(
                        f"x_t{teacher_index}_s{context.subject_id}_r{room}_k{slot_index}"
                    )
                    slot_vars[(teacher_index, slot_key)] = var
                    slot_exprs.append(var)
                    if use_current_solution_as_hint and hinted_slots.get(slot_key) == teacher_index:
                        model.AddHint(var, 1)
                model.Add(sum(slot_exprs) == 1)
                if fixed_teacher is not None:
                    model.Add(slot_vars[(fixed_teacher, slot_key)] == 1)

    if required_slots == 2 and not schedule.get_constraint("internal_mix", False):
        _add_double_slot_symmetry_breaking(
            model,
            schedule=schedule,
            subject_contexts=subject_contexts,
            rooms_by_subject=rooms_by_subject,
            slot_vars=slot_vars,
            candidate_teachers=candidate_teachers,
            fixed_slots=fixed_slots,
        )

    subject_load_vars: dict[tuple[int, int], Any] = {}
    count_vars: list[Any] = []
    current_duration_vars: list[Any] = []
    overall_duration_vars: list[Any] = []
    per_teacher_duration_upper = sum(max(0, context.duration_minutes) for context in subject_contexts)

    for teacher_index, teacher in enumerate(schedule.teachers):
        load_vars_for_teacher = []
        weighted_duration_terms = []

        for context in subject_contexts:
            load_var = model.NewBoolVar(f"load_t{teacher_index}_s{context.subject_id}")
            related_vars = [
                slot_vars[(teacher_index, slot_key)]
                for slot_key in slots_by_subject[context.subject_id]
                if (teacher_index, slot_key) in slot_vars
            ]
            if related_vars:
                model.Add(sum(related_vars) == load_var)
            else:
                model.Add(load_var == 0)
            subject_load_vars[(teacher_index, context.subject_id)] = load_var
            load_vars_for_teacher.append(load_var)
            weighted_duration_terms.append(load_var * max(0, context.duration_minutes))

        max_sessions = _safe_int(getattr(teacher, "max_sessions", 0), default=0)
        count_var = model.NewIntVar(
            0,
            max(0, int(schedule.num_subjects)),
            f"count_t{teacher_index}",
        )
        model.Add(count_var == sum(load_vars_for_teacher))
        model.Add(count_var <= max_sessions)
        count_vars.append(count_var)

        duration_upper_bound = max(0, per_teacher_duration_upper)
        current_duration = model.NewIntVar(0, duration_upper_bound, f"dur_t{teacher_index}")
        model.Add(current_duration == sum(weighted_duration_terms))
        current_duration_vars.append(current_duration)

        previous_duration = _safe_int(
            getattr(teacher, "previous_supervision_duration", 0),
            default=0,
        )
        overall_duration = model.NewIntVar(
            previous_duration,
            previous_duration + duration_upper_bound,
            f"overall_t{teacher_index}",
        )
        model.Add(overall_duration == current_duration + previous_duration)
        overall_duration_vars.append(overall_duration)

    for teacher_index in range(teacher_count):
        for left_subject, right_subject in _build_overlap_pairs(subject_contexts):
            model.Add(
                subject_load_vars[(teacher_index, left_subject)]
                + subject_load_vars[(teacher_index, right_subject)]
                <= 1
            )

    if schedule.mode == "double" and schedule.get_constraint("gender_mix", False):
        for context in subject_contexts:
            for room in rooms_by_subject[context.subject_id]:
                if not schedule.room_requires_pair_constraints(context.subject_id, room):
                    continue
                male_vars = []
                female_vars = []
                for slot_index in schedule.get_active_slot_indexes(context.subject_id, room):
                    slot_key = (context.subject_id, room, slot_index)
                    for teacher_index in candidate_teachers.get(slot_key, []):
                        var = slot_vars[(teacher_index, slot_key)]
                        gender = str(getattr(schedule.teachers[teacher_index], "gender", "") or "").upper()
                        if gender == "M":
                            male_vars.append(var)
                        elif gender == "F":
                            female_vars.append(var)
                model.Add(sum(male_vars) == 1)
                model.Add(sum(female_vars) == 1)

    room_usage_total = None
    if room_repeat_preference:
        room_usage_vars = []
        for teacher_index in range(teacher_count):
            for room in all_rooms:
                used_var = model.NewBoolVar(f"room_used_t{teacher_index}_r{room}")
                related_vars = [
                    slot_vars[(teacher_index, slot_key)]
                    for context in subject_contexts
                    for slot_key in slots_by_subject[context.subject_id]
                    if slot_key[1] == room and (teacher_index, slot_key) in slot_vars
                ]
                if related_vars:
                    for var in related_vars:
                        model.Add(var <= used_var)
                    model.Add(sum(related_vars) >= used_var)
                else:
                    model.Add(used_var == 0)
                room_usage_vars.append(used_var)
        room_usage_total = model.NewIntVar(
            0,
            teacher_count * max(0, len(all_rooms)),
            "room_usage_total",
        )
        model.Add(room_usage_total == sum(room_usage_vars))

    consecutive_total = None
    if avoid_consecutive_sessions:
        consecutive_pairs = _build_consecutive_pairs(subject_contexts)
        if consecutive_pairs:
            pair_vars = []
            for teacher_index in range(teacher_count):
                for left_subject, right_subject in consecutive_pairs:
                    pair_var = model.NewBoolVar(
                        f"consecutive_t{teacher_index}_s{left_subject}_s{right_subject}"
                    )
                    left_load = subject_load_vars[(teacher_index, left_subject)]
                    right_load = subject_load_vars[(teacher_index, right_subject)]
                    model.Add(pair_var <= left_load)
                    model.Add(pair_var <= right_load)
                    model.Add(pair_var >= left_load + right_load - 1)
                    pair_vars.append(pair_var)
            consecutive_total = model.NewIntVar(0, len(pair_vars), "consecutive_total")
            model.Add(consecutive_total == sum(pair_vars))

    total_slots = sum(
        schedule.get_required_assignment_count(context.subject_id, room)
        for context in subject_contexts
        for room in rooms_by_subject[context.subject_id]
    )
    count_deviation_upper = max(1, teacher_count * max(total_slots, int(schedule.num_subjects)))
    count_deviations = []
    for teacher_index, count_var in enumerate(count_vars):
        dev_var = model.NewIntVar(0, count_deviation_upper, f"count_dev_t{teacher_index}")
        model.AddAbsEquality(dev_var, teacher_count * count_var - total_slots)
        count_deviations.append(dev_var)
    total_count_deviation = model.NewIntVar(
        0,
        count_deviation_upper * max(1, teacher_count),
        "total_count_deviation",
    )
    model.Add(total_count_deviation == sum(count_deviations))

    total_current_sum = sum(
        max(0, context.duration_minutes)
        * sum(
            schedule.get_required_assignment_count(context.subject_id, room)
            for room in rooms_by_subject[context.subject_id]
        )
        for context in subject_contexts
    )
    total_overall_sum = sum(
        _safe_int(getattr(teacher, "previous_supervision_duration", 0), default=0)
        for teacher in schedule.teachers
    ) + total_current_sum

    overall_upper_bound = sum(
        _safe_int(getattr(teacher, "previous_supervision_duration", 0), default=0)
        for teacher in schedule.teachers
    ) + total_current_sum
    overall_deviation_upper = max(1, teacher_count * max(overall_upper_bound, total_overall_sum))
    overall_deviations = []
    for teacher_index, overall_var in enumerate(overall_duration_vars):
        dev_var = model.NewIntVar(0, overall_deviation_upper, f"overall_dev_t{teacher_index}")
        model.AddAbsEquality(dev_var, teacher_count * overall_var - total_overall_sum)
        overall_deviations.append(dev_var)
    total_overall_deviation = model.NewIntVar(
        0,
        overall_deviation_upper * max(1, teacher_count),
        "total_overall_deviation",
    )
    model.Add(total_overall_deviation == sum(overall_deviations))

    max_count = model.NewIntVar(0, max(0, int(schedule.num_subjects)), "max_count")
    min_count = model.NewIntVar(0, max(0, int(schedule.num_subjects)), "min_count")
    model.AddMaxEquality(max_count, count_vars)
    model.AddMinEquality(min_count, count_vars)
    count_range = model.NewIntVar(0, max(0, int(schedule.num_subjects)), "count_range")
    model.Add(count_range == max_count - min_count)

    max_overall_duration = model.NewIntVar(0, max(0, overall_upper_bound), "max_overall_duration")
    min_overall_duration = model.NewIntVar(0, max(0, overall_upper_bound), "min_overall_duration")
    model.AddMaxEquality(max_overall_duration, overall_duration_vars)
    model.AddMinEquality(min_overall_duration, overall_duration_vars)

    deadline = time.monotonic() + max(1.0, float(time_limit_seconds))
    stage_reports: list[dict[str, Any]] = []
    final_solver = None
    final_status = None
    optimal = True
    progress_interval_seconds = max(0.0, float(progress_interval_seconds))
    if no_improvement_limit_seconds is not None:
        no_improvement_limit_seconds = max(0.0, float(no_improvement_limit_seconds))
        if no_improvement_limit_seconds <= 0:
            no_improvement_limit_seconds = None

    stages = _build_objective_stages(
        balance_mode=schedule.get_constraint("balance_mode", "duration"),
        max_count=max_count,
        min_count=min_count,
        count_range=count_range,
        total_count_deviation=total_count_deviation,
        max_overall_duration=max_overall_duration,
        min_overall_duration=min_overall_duration,
        total_overall_deviation=total_overall_deviation,
        room_repeat_preference=room_repeat_preference,
        room_usage_total=room_usage_total,
        consecutive_total=consecutive_total,
    )

    if progress_observer is not None:
        try:
            progress_observer(
                {
                    "type": "solve_started",
                    "stage_count": len(stages),
                    "time_limit_seconds": _normalize_report_number(time_limit_seconds),
                    "progress_interval_seconds": _normalize_report_number(progress_interval_seconds),
                    "no_improvement_limit_seconds": _normalize_report_number(no_improvement_limit_seconds),
                }
            )
        except Exception:
            logger.debug("Failed to publish CP-SAT solve start event.", exc_info=True)

    for stage_index, stage in enumerate(stages, start=1):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            optimal = False
            stage_reports.append(
                {"name": stage["name"], "status": "TIMEOUT", "proven_optimal": False}
            )
            break

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = remaining
        solver.parameters.num_search_workers = max(1, int(num_workers))
        solver.parameters.random_seed = 0
        solver.parameters.log_search_progress = bool(log_search_progress)
        tracker = _StageProgressTracker(
            stage_name=stage["name"],
            stage_index=stage_index,
            stage_count=len(stages),
            maximize=stage["maximize"],
            sample_interval_seconds=progress_interval_seconds,
            progress_observer=progress_observer,
        )
        if progress_observer is not None:
            try:
                progress_observer(
                    {
                        "type": "stage_started",
                        "name": stage["name"],
                        "stage_index": stage_index,
                        "stage_count": len(stages),
                        "maximize": bool(stage["maximize"]),
                    }
                )
            except Exception:
                logger.debug("Failed to publish CP-SAT stage start event.", exc_info=True)
        solver.best_bound_callback = (
            lambda bound, current_tracker=tracker: current_tracker.record_best_bound(bound)
        )

        stop_watchdog = threading.Event()
        watchdog_reason: dict[str, Any] = {}
        watchdog_thread = None
        if no_improvement_limit_seconds is not None:
            watchdog_sleep = max(0.2, min(1.0, no_improvement_limit_seconds / 5.0))

            def _watch_no_improvement() -> None:
                while not stop_watchdog.wait(watchdog_sleep):
                    if tracker.solution_count <= 0:
                        continue
                    idle_seconds = tracker.current_progress_snapshot().get(
                        "idle_after_last_improvement_seconds"
                    )
                    if idle_seconds is None:
                        continue
                    if float(idle_seconds) + 1e-9 < float(no_improvement_limit_seconds):
                        continue
                    watchdog_reason["reason"] = "no_improvement_limit"
                    watchdog_reason["idle_seconds"] = _normalize_report_number(idle_seconds)
                    try:
                        solver.StopSearch()
                    except Exception:
                        logger.debug("Failed to stop CP-SAT search from watchdog.", exc_info=True)
                    return

            watchdog_thread = threading.Thread(target=_watch_no_improvement, daemon=True)
            watchdog_thread.start()

        if stage["maximize"]:
            model.Maximize(stage["expr"])
        else:
            model.Minimize(stage["expr"])

        status = solver.Solve(model, tracker)
        stop_watchdog.set()
        if watchdog_thread is not None:
            watchdog_thread.join(timeout=0.2)
        status_name = _status_name(status)
        progress_report = tracker.finalize(solver.BestObjectiveBound())
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            failed_stage_report = {
                "name": stage["name"],
                "status": status_name,
                "proven_optimal": False,
                "continued_with_locked_value": False,
                **progress_report,
            }
            if final_solver is not None and final_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                optimal = False
                stage_reports.append(failed_stage_report)
                break
            return {
                "status": status_name,
                "optimal": False,
                "message": (
                    _build_infeasibility_diagnostic_message(
                        schedule,
                        subject_contexts=subject_contexts,
                        rooms_by_subject=rooms_by_subject,
                        required_slots=required_slots,
                        candidate_teachers=candidate_teachers,
                        fixed_slots=fixed_slots,
                    )
                    if status_name == "INFEASIBLE"
                    else _status_message(status_name)
                ),
                "stages": stage_reports + [failed_stage_report],
            }

        objective_value = _normalize_report_number(solver.ObjectiveValue())
        continued_with_locked_value = (
            status != cp_model.OPTIMAL
            and stage_index < len(stages)
            and deadline - time.monotonic() > 1e-9
        )
        stage_reports.append(
            {
                "name": stage["name"],
                "status": status_name,
                "value": objective_value,
                "proven_optimal": status == cp_model.OPTIMAL,
                "stage_index": stage_index,
                "stage_count": len(stages),
                "stop_reason": watchdog_reason.get("reason"),
                "stop_reason_idle_seconds": watchdog_reason.get("idle_seconds"),
                "continued_with_locked_value": continued_with_locked_value,
                **progress_report,
            }
        )
        stage_preview_schedule = None
        if progress_observer is not None:
            try:
                stage_preview_schedule = copy.deepcopy(schedule)
                _apply_solver_result(
                    stage_preview_schedule,
                    final_solver=solver,
                    slot_vars=slot_vars,
                    subject_contexts=subject_contexts,
                    rooms_by_subject=rooms_by_subject,
                    required_slots=required_slots,
                )
            except Exception:
                logger.debug("Failed to build CP-SAT stage preview.", exc_info=True)
        if progress_observer is not None:
            try:
                event = {
                    "type": "stage_finished",
                    **stage_reports[-1],
                }
                if stage_preview_schedule is not None:
                    event["preview_schedule"] = stage_preview_schedule
                progress_observer(event)
            except Exception:
                logger.debug("Failed to publish CP-SAT stage finish event.", exc_info=True)
        final_solver = solver
        final_status = status

        model.Add(stage["expr"] == objective_value)
        if status != cp_model.OPTIMAL:
            optimal = False
            if continued_with_locked_value:
                _set_solution_hints(model, solver=solver, slot_vars=slot_vars)
                continue
            break
        if stage_index < len(stages) and deadline - time.monotonic() <= 1e-9:
            break
        if stage_index < len(stages):
            _set_solution_hints(model, solver=solver, slot_vars=slot_vars)

    if final_solver is None or final_status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            "status": "UNKNOWN",
            "optimal": False,
            "message": "The CP-SAT solver did not return a usable solution.",
            "stages": stage_reports,
        }

    _apply_solver_result(
        schedule,
        final_solver=final_solver,
        slot_vars=slot_vars,
        subject_contexts=subject_contexts,
        rooms_by_subject=rooms_by_subject,
        required_slots=required_slots,
    )

    summary = _build_solution_summary(
        final_status=final_status,
        optimal=optimal,
        stage_reports=stage_reports,
        no_improvement_limit_seconds=no_improvement_limit_seconds,
    )
    return {
        "status": summary["status"],
        "optimal": summary["optimal"],
        "message": summary["message"],
        "stages": stage_reports,
        "metrics": compute_schedule_metrics(schedule),
    }
