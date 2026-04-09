from __future__ import annotations

from typing import Any


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
