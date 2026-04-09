from __future__ import annotations

import logging
import math
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Sequence

try:
    from ortools.sat.python import cp_model
except Exception:  # pragma: no cover - handled at runtime
    cp_model = None

from backend.proctoring.core.entities import Exam


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SubjectContext:
    subject_id: int
    name: str
    exam_date: str
    exam_time: str
    duration_minutes: int
    start_minute: int
    end_minute: int
    sort_key: tuple[int, int]


def _normalize_report_number(value: float | int | None) -> int | float | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except Exception:
        return value
    rounded = round(numeric)
    if abs(numeric - rounded) < 1e-9:
        return int(rounded)
    return round(numeric, 6)


_CallbackBase = cp_model.CpSolverSolutionCallback if cp_model is not None else object


class _StageProgressTracker(_CallbackBase):
    def __init__(
        self,
        *,
        stage_name: str,
        stage_index: int,
        stage_count: int,
        maximize: bool,
        sample_interval_seconds: float,
        progress_observer: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        if cp_model is not None:
            super().__init__()
        self.stage_name = stage_name
        self.stage_index = stage_index
        self.stage_count = stage_count
        self.maximize = bool(maximize)
        self.sample_interval_seconds = max(0.0, float(sample_interval_seconds))
        self.progress_observer = progress_observer
        self.samples: list[dict[str, Any]] = []
        self.solution_count = 0
        self.improvement_count = 0
        self.first_solution_seconds: float | None = None
        self.last_solution_seconds: float | None = None
        self.last_improvement_seconds: float | None = None
        self.last_objective_value: float | None = None
        self.best_bound_value: float | None = None
        self._stage_start_monotonic = time.monotonic()
        self._next_sample_seconds = (
            self.sample_interval_seconds if self.sample_interval_seconds > 0 else None
        )

    def _elapsed_since_stage_start(self) -> float:
        return max(0.0, time.monotonic() - self._stage_start_monotonic)

    def _is_improvement(self, objective_value: float) -> bool:
        if self.last_objective_value is None:
            return True
        if self.maximize:
            return objective_value > self.last_objective_value + 1e-9
        return objective_value < self.last_objective_value - 1e-9

    def _current_gap(self) -> float | None:
        if self.last_objective_value is None or self.best_bound_value is None:
            return None
        if self.maximize:
            gap = self.best_bound_value - self.last_objective_value
        else:
            gap = self.last_objective_value - self.best_bound_value
        return max(0.0, float(gap))

    def _append_sample(self, elapsed_seconds: float, reason: str) -> None:
        if self.last_objective_value is None:
            return
        sample = {
            "stage": self.stage_name,
            "elapsedSeconds": round(max(0.0, float(elapsed_seconds)), 3),
            "objectiveValue": _normalize_report_number(self.last_objective_value),
            "bestBound": _normalize_report_number(self.best_bound_value),
            "objectiveGap": _normalize_report_number(self._current_gap()),
            "reason": reason,
        }
        if self.samples and self.samples[-1] == sample:
            return
        self.samples.append(sample)
        self._notify_progress(status="RUNNING", reason=reason)

    def _emit_interval_samples(self, elapsed_seconds: float) -> None:
        if self._next_sample_seconds is None:
            return
        current = max(0.0, float(elapsed_seconds))
        while self._next_sample_seconds <= current + 1e-9:
            self._append_sample(self._next_sample_seconds, "interval")
            self._next_sample_seconds += self.sample_interval_seconds

    def OnSolutionCallback(self) -> None:
        elapsed_seconds = self._elapsed_since_stage_start()
        objective_value = float(self.ObjectiveValue())
        best_bound = float(self.BestObjectiveBound())
        self.solution_count += 1
        if self.first_solution_seconds is None:
            self.first_solution_seconds = elapsed_seconds
        self.last_solution_seconds = elapsed_seconds
        improved = self._is_improvement(objective_value)
        self.last_objective_value = objective_value
        self.best_bound_value = best_bound
        self._emit_interval_samples(elapsed_seconds)
        if improved:
            self.improvement_count += 1
            self.last_improvement_seconds = elapsed_seconds
            self._append_sample(elapsed_seconds, "improvement")

    def record_best_bound(self, best_bound: float) -> None:
        self.best_bound_value = float(best_bound)
        self._emit_interval_samples(self._elapsed_since_stage_start())

    def current_progress_snapshot(
        self,
        *,
        status: str = "RUNNING",
        reason: str | None = None,
    ) -> dict[str, Any]:
        elapsed_seconds = self._elapsed_since_stage_start()
        idle_after_last_improvement = None
        if self.last_improvement_seconds is not None:
            idle_after_last_improvement = max(0.0, elapsed_seconds - self.last_improvement_seconds)
        latest_sample = self.samples[-1] if self.samples else None
        snapshot = {
            "type": "stage_progress",
            "name": self.stage_name,
            "stage_index": self.stage_index,
            "stage_count": self.stage_count,
            "status": status,
            "reason": reason,
            "solve_seconds": round(elapsed_seconds, 3),
            "solution_count": self.solution_count,
            "improvement_count": self.improvement_count,
            "first_solution_seconds": _normalize_report_number(self.first_solution_seconds),
            "last_solution_seconds": _normalize_report_number(self.last_solution_seconds),
            "last_improvement_seconds": _normalize_report_number(self.last_improvement_seconds),
            "idle_after_last_improvement_seconds": _normalize_report_number(idle_after_last_improvement),
            "best_objective_value": _normalize_report_number(self.last_objective_value),
            "best_bound": _normalize_report_number(self.best_bound_value),
            "objective_gap": _normalize_report_number(self._current_gap()),
            "latest_sample": latest_sample,
        }
        return snapshot

    def _notify_progress(self, *, status: str = "RUNNING", reason: str | None = None) -> None:
        if self.progress_observer is None:
            return
        try:
            self.progress_observer(self.current_progress_snapshot(status=status, reason=reason))
        except Exception:
            logger.debug("Failed to publish CP-SAT stage progress.", exc_info=True)

    def finalize(
        self,
        best_bound: float | None = None,
    ) -> dict[str, Any]:
        elapsed_seconds = self._elapsed_since_stage_start()
        if best_bound is not None:
            self.best_bound_value = float(best_bound)
        self._emit_interval_samples(elapsed_seconds)
        self._append_sample(elapsed_seconds, "final")
        idle_after_last_improvement = None
        if self.last_improvement_seconds is not None:
            idle_after_last_improvement = max(0.0, elapsed_seconds - self.last_improvement_seconds)
        return {
            "solve_seconds": round(elapsed_seconds, 3),
            "solution_count": self.solution_count,
            "improvement_count": self.improvement_count,
            "first_solution_seconds": _normalize_report_number(self.first_solution_seconds),
            "last_solution_seconds": _normalize_report_number(self.last_solution_seconds),
            "last_improvement_seconds": _normalize_report_number(self.last_improvement_seconds),
            "idle_after_last_improvement_seconds": _normalize_report_number(idle_after_last_improvement),
            "best_bound": _normalize_report_number(self.best_bound_value),
            "objective_gap": _normalize_report_number(self._current_gap()),
            "progress_samples": self.samples,
        }


def compute_schedule_metrics(schedule) -> dict[str, Any]:
    teachers = getattr(schedule, "original_teachers_order", schedule.teachers)
    counts = [teacher.assigned_count() for teacher in teachers]
    current = [int(teacher.supervision_duration or 0) for teacher in teachers]
    overall = [
        int(teacher.supervision_duration or 0) + int(teacher.previous_supervision_duration or 0)
        for teacher in teachers
    ]

    def _variance(values: Sequence[int]) -> float:
        if not values:
            return 0.0
        mean = sum(values) / len(values)
        return sum((value - mean) ** 2 for value in values) / len(values)

    def _summary(values: Sequence[int], prefix: str) -> dict[str, Any]:
        if not values:
            return {
                f"{prefix}_max": 0,
                f"{prefix}_min": 0,
                f"{prefix}_range": 0,
                f"{prefix}_variance": 0.0,
                f"{prefix}_stddev": 0.0,
            }
        variance = _variance(values)
        return {
            f"{prefix}_max": max(values),
            f"{prefix}_min": min(values),
            f"{prefix}_range": max(values) - min(values),
            f"{prefix}_variance": variance,
            f"{prefix}_stddev": math.sqrt(variance),
        }

    metrics = {}
    metrics.update(_summary(counts, "count"))
    metrics.update(_summary(current, "current_duration"))
    metrics.update(_summary(overall, "overall_duration"))
    metrics["teacher_count"] = len(teachers)
    metrics["total_assignments"] = sum(counts)
    metrics["total_current_duration"] = sum(current)
    metrics["total_overall_duration"] = sum(overall)

    # Keep legacy keys for the existing optimization drawer.
    metrics["max_current"] = metrics["current_duration_max"]
    metrics["max_overall"] = metrics["overall_duration_max"]
    metrics["var_current"] = metrics["current_duration_variance"]
    metrics["var_overall"] = metrics["overall_duration_variance"]
    return metrics


def _normalize_balance_mode(balance_mode: Any) -> str:
    normalized = str(balance_mode or "duration").strip().lower()
    if normalized in {"session", "sessions", "count", "counts"}:
        return "session"
    if normalized in {"duration", "durations", "time", "times"}:
        return "duration"
    return "duration"


def _build_objective_stages(
    *,
    balance_mode: Any,
    max_count: Any,
    min_count: Any,
    count_range: Any,
    total_count_deviation: Any,
    max_overall_duration: Any,
    min_overall_duration: Any,
    total_overall_deviation: Any,
    room_repeat_preference: str | None,
    room_usage_total: Any | None,
    consecutive_total: Any | None,
) -> list[dict[str, Any]]:
    session_stages = [
        {"name": "minimize_max_count", "expr": max_count, "maximize": False},
        {"name": "maximize_min_count", "expr": min_count, "maximize": True},
        {"name": "minimize_count_deviation", "expr": total_count_deviation, "maximize": False},
    ]
    session_follow_up_stages = [
        {"name": "minimize_max_overall_duration", "expr": max_overall_duration, "maximize": False},
        {"name": "maximize_min_overall_duration", "expr": min_overall_duration, "maximize": True},
        {"name": "minimize_overall_duration_deviation", "expr": total_overall_deviation, "maximize": False},
    ]
    duration_stages = [
        {"name": "minimize_max_overall_duration", "expr": max_overall_duration, "maximize": False},
        {"name": "minimize_count_range", "expr": count_range, "maximize": False},
        {"name": "maximize_min_overall_duration", "expr": min_overall_duration, "maximize": True},
        {"name": "minimize_overall_duration_deviation", "expr": total_overall_deviation, "maximize": False},
        {"name": "minimize_max_count", "expr": max_count, "maximize": False},
        {"name": "minimize_count_deviation", "expr": total_count_deviation, "maximize": False},
    ]

    stages: list[dict[str, Any]]
    if _normalize_balance_mode(balance_mode) == "session":
        stages = [*session_stages, *session_follow_up_stages]
    else:
        stages = duration_stages

    normalized_room_preference = (room_repeat_preference or "").strip().lower()
    if room_usage_total is not None:
        if normalized_room_preference in {"high", "same", "prefer_same", "fixed"}:
            stages.append(
                {"name": "minimize_distinct_rooms", "expr": room_usage_total, "maximize": False}
            )
        elif normalized_room_preference in {"low", "different", "prefer_different"}:
            stages.append(
                {"name": "maximize_distinct_rooms", "expr": room_usage_total, "maximize": True}
            )

    if consecutive_total is not None:
        stages.append(
            {"name": "minimize_consecutive_sessions", "expr": consecutive_total, "maximize": False}
        )

    return stages


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
    consecutive_gap_minutes: int = 0,
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
            for slot_index in range(required_slots):
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
                male_vars = []
                female_vars = []
                for slot_index in range(required_slots):
                    slot_key = (context.subject_id, room, slot_index)
                    for teacher_index in candidate_teachers[slot_key]:
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
        consecutive_pairs = _build_consecutive_pairs(
            subject_contexts,
            gap_minutes=max(0, consecutive_gap_minutes),
        )
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

    total_slots = (
        sum(len(rooms_by_subject[context.subject_id]) for context in subject_contexts) * required_slots
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

    total_current_sum = (
        sum(
            max(0, context.duration_minutes) * len(rooms_by_subject[context.subject_id])
            for context in subject_contexts
        )
        * required_slots
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
                "continued_with_locked_value": False,
                **progress_report,
            }
        )
        if progress_observer is not None:
            try:
                progress_observer(
                    {
                        "type": "stage_finished",
                        **stage_reports[-1],
                    }
                )
            except Exception:
                logger.debug("Failed to publish CP-SAT stage finish event.", exc_info=True)
        final_solver = solver
        final_status = status

        model.Add(stage["expr"] == objective_value)
        if status != cp_model.OPTIMAL:
            optimal = False
            if stage_index < len(stages) and deadline - time.monotonic() > 1e-9:
                _set_solution_hints(model, solver=solver, slot_vars=slot_vars)
                stage_reports[-1]["continued_with_locked_value"] = True
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


def _apply_solver_result(
    schedule,
    *,
    final_solver,
    slot_vars: dict[tuple[int, tuple[int, int, int]], Any],
    subject_contexts: Sequence[SubjectContext],
    rooms_by_subject: dict[int, list[int]],
    required_slots: int,
) -> None:
    teacher_map = {index: teacher for index, teacher in enumerate(schedule.teachers)}
    for teacher in schedule.teachers:
        teacher.assigned_sessions = []
        teacher.supervision_duration = 0

    exams = []
    exam_by_subject: dict[int, Exam] = {}
    for context in subject_contexts:
        exam = Exam(context.subject_id, list(rooms_by_subject.get(context.subject_id, [])))
        for room in exam.rooms:
            exam.schedule[room] = [None] * required_slots
        exams.append(exam)
        exam_by_subject[context.subject_id] = exam

    for (teacher_index, slot_key), var in slot_vars.items():
        if final_solver.Value(var) != 1:
            continue
        subject_id, room, slot_index = slot_key
        teacher = teacher_map[teacher_index]
        exam = exam_by_subject[subject_id]
        exam.schedule[room][slot_index] = teacher
        duration = next(
            (context.duration_minutes for context in subject_contexts if context.subject_id == subject_id),
            0,
        )
        teacher.assign((subject_id, room), duration)

    schedule.exams = exams


def _set_solution_hints(
    model,
    *,
    solver,
    slot_vars: dict[tuple[int, tuple[int, int, int]], Any],
) -> None:
    if not hasattr(model, "ClearHints"):
        return
    model.ClearHints()
    for var in slot_vars.values():
        model.AddHint(var, solver.Value(var))


def _collect_existing_slot_assignments(
    schedule,
    *,
    teacher_index_by_name: dict[str, int],
    required_slots: int,
    fix_existing_assignments: bool,
) -> tuple[dict[tuple[int, int, int], int], dict[tuple[int, int, int], int]]:
    fixed_slots: dict[tuple[int, int, int], int] = {}
    hinted_slots: dict[tuple[int, int, int], int] = {}

    for exam in schedule.exams or []:
        room_numbers = set()
        room_numbers.update(int(room) for room in getattr(exam, "rooms", []) or [])
        room_numbers.update(int(room) for room in (exam.schedule or {}).keys())
        for room in sorted(room_numbers):
            teachers = list((exam.schedule or {}).get(room, []))
            while len(teachers) < required_slots:
                teachers.append(None)
            for slot_index in range(required_slots):
                teacher = teachers[slot_index] if slot_index < len(teachers) else None
                if teacher is None:
                    continue
                teacher_index = teacher_index_by_name.get(teacher.name)
                if teacher_index is None:
                    continue
                slot_key = (int(exam.subject_id), int(room), int(slot_index))
                hinted_slots[slot_key] = teacher_index
                if fix_existing_assignments or schedule.is_position_imported(*slot_key):
                    fixed_slots[slot_key] = teacher_index
    return fixed_slots, hinted_slots


def _teacher_can_take_slot(
    schedule,
    *,
    teacher,
    teacher_index: int,
    subject_context: SubjectContext,
    room: int,
    slot_index: int,
    teacher_unavailable: dict[int, set[int]],
) -> bool:
    if _safe_int(getattr(teacher, "max_sessions", 0), default=0) <= 0:
        return False

    preset_room = _safe_int(getattr(teacher, "preset_room", None), default=0)
    if preset_room > 0 and preset_room != room:
        return False

    if subject_context.subject_id in teacher_unavailable.get(teacher_index, set()):
        return False

    if schedule.mode == "double" and schedule.get_constraint("internal_mix", False):
        is_internal = getattr(teacher, "is_internal", None)
        if slot_index == 0 and is_internal is not True:
            return False
        if slot_index == 1 and is_internal is not False:
            return False

    return True


def _build_teacher_unavailable_map(
    teachers: Sequence[Any],
    subject_contexts: Sequence[SubjectContext],
) -> dict[int, set[int]]:
    subject_name_to_id = {context.name: context.subject_id for context in subject_contexts if context.name}
    unavailable: dict[int, set[int]] = {}
    for teacher_index, teacher in enumerate(teachers):
        blocked_subjects: set[int] = set()
        for raw_value in getattr(teacher, "unavailable_subjects", []) or []:
            if isinstance(raw_value, int):
                blocked_subjects.add(raw_value)
                continue
            text = str(raw_value).strip()
            if not text:
                continue
            numeric = _safe_int(text, default=0)
            if numeric > 0:
                blocked_subjects.add(numeric)
                continue
            normalized = text.replace("科目", "").strip()
            if normalized in subject_name_to_id:
                blocked_subjects.add(subject_name_to_id[normalized])
        unavailable[teacher_index] = blocked_subjects
    return unavailable


def _build_overlap_pairs(subject_contexts: Sequence[SubjectContext]) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    sorted_subjects = sorted(subject_contexts, key=lambda context: context.sort_key)
    for left_index, left in enumerate(sorted_subjects):
        for right in sorted_subjects[left_index + 1 :]:
            if left.exam_date != right.exam_date:
                continue
            if left.end_minute <= right.start_minute or right.end_minute <= left.start_minute:
                continue
            pairs.append((left.subject_id, right.subject_id))
    return pairs


def _build_consecutive_pairs(
    subject_contexts: Sequence[SubjectContext],
    *,
    gap_minutes: int,
) -> list[tuple[int, int]]:
    del gap_minutes
    pairs: list[tuple[int, int]] = []
    contexts_by_day: dict[str, list[SubjectContext]] = {}
    for context in subject_contexts:
        contexts_by_day.setdefault(context.exam_date, []).append(context)

    for same_day_contexts in contexts_by_day.values():
        sorted_subjects = sorted(
            same_day_contexts,
            key=lambda context: (
                context.start_minute,
                context.end_minute,
                context.subject_id,
            ),
        )
        blocks: list[dict[str, Any]] = []
        for context in sorted_subjects:
            if (
                blocks
                and blocks[-1]["start"] == context.start_minute
                and blocks[-1]["end"] == context.end_minute
            ):
                blocks[-1]["subject_ids"].append(context.subject_id)
                continue
            blocks.append(
                {
                    "start": context.start_minute,
                    "end": context.end_minute,
                    "subject_ids": [context.subject_id],
                }
            )

        for index, current_block in enumerate(blocks):
            next_block = next(
                (
                    candidate
                    for candidate in blocks[index + 1 :]
                    if int(candidate["start"]) >= int(current_block["end"])
                ),
                None,
            )
            if next_block is None:
                continue
            for left_subject_id in current_block["subject_ids"]:
                for right_subject_id in next_block["subject_ids"]:
                    pairs.append((int(left_subject_id), int(right_subject_id)))
    return pairs


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
        len(rooms_by_subject.get(context.subject_id, [])) * required_slots
        for context in subject_contexts
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
            len(rooms_by_subject.get(subject_id, [])) * required_slots
            for subject_id in active_subject_ids
        )
        available_teacher_count = len(segment_teacher_indexes)
        if available_teacher_count < required_positions:
            return (
                f"{_format_segment_label(segment)} 时段共需要 {required_positions} 个监考岗位，"
                f"但当前最多只能安排 {available_teacher_count} 位老师。涉及科目：{subject_names}。"
                "请增加该时段可用老师，或放宽禁监考科目、最大监考场次、预设考场等限制。"
            )

        room_demand = sum(len(rooms_by_subject.get(subject_id, [])) for subject_id in active_subject_ids)
        if schedule.mode == "double" and schedule.get_constraint("gender_mix", False):
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


def _safe_int(value: Any, *, default: int = 0) -> int:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        return int(float(str(value).strip()))
    except Exception:
        return default


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
