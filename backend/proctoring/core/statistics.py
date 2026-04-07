#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Statistics helpers for proctoring scheduling."""


def get_statistics(schedule):
    """Return teacher supervision counts in original teacher order."""
    stats = []
    teachers_to_iterate = getattr(schedule, "original_teachers_order", schedule.teachers)
    for teacher in teachers_to_iterate:
        stats.append({
            "name": teacher.name,
            "count": teacher.assigned_count(),
        })
    return stats
