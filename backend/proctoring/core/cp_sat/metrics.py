from __future__ import annotations

import math
from typing import Any, Sequence


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
