#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation helpers for proctoring scheduling."""


def _gender_pair_capacity(male_count: int, female_count: int) -> int:
    return min(max(0, female_count), max(0, male_count + female_count) // 2)


def _gender_internal_pair_capacity(
    internal_male: int,
    internal_female: int,
    external_male: int,
    external_female: int,
) -> int:
    max_pairs = 0
    max_internal_male_pairs = min(max(0, internal_male), max(0, external_female))
    for internal_male_pairs in range(max_internal_male_pairs + 1):
        remaining_external_female = max(0, external_female - internal_male_pairs)
        remaining_external_pool = max(0, external_male) + remaining_external_female
        pair_count = internal_male_pairs + min(max(0, internal_female), remaining_external_pool)
        max_pairs = max(max_pairs, pair_count)
    return max_pairs


def check_feasibility(schedule):
    """Check whether the current configuration has a feasible assignment space."""
    mode = schedule.mode
    gender_mix = schedule.get_constraint("gender_mix", False)
    internal_mix = schedule.get_constraint("internal_mix", False)

    total_capacity = 0
    for teacher in schedule.teachers:
        try:
            cap = int(teacher.max_sessions) if teacher.max_sessions is not None else 0
        except Exception:
            cap = 0
        total_capacity += max(0, cap)

    required_total = sum(
        schedule.get_required_assignment_count(subject_id, room)
        for subject_id in range(1, schedule.num_subjects + 1)
        for room in schedule._get_subject_rooms(subject_id)
    )
    if total_capacity < required_total:
        return (
            False,
            f"全局监考名额不足：需要 {required_total} 人次，只有 {total_capacity} 人次。",
        )

    if mode == "single":
        return True, "可行"

    if not gender_mix and not internal_mix:
        return True, "可行"

    for subject_id in range(1, schedule.num_subjects + 1):
        required_pairs = sum(
            1
            for room in schedule._get_subject_rooms(subject_id)
            if schedule.room_requires_pair_constraints(subject_id, room)
        )
        if required_pairs <= 0:
            continue

        candidates = []
        for teacher in schedule.teachers:
            try:
                cap = int(teacher.max_sessions) if teacher.max_sessions is not None else 0
            except Exception:
                cap = 0
            if cap > 0 and teacher.can_supervise(subject_id):
                candidates.append(teacher)

        if not candidates:
            return False, f"科目{subject_id}没有任何可用教师。"

        if internal_mix and gender_mix:
            internal_male = sum(
                1 for teacher in candidates if teacher.is_internal is True and teacher.gender == "M"
            )
            internal_female = sum(
                1 for teacher in candidates if teacher.is_internal is True and teacher.gender == "F"
            )
            external_male = sum(
                1 for teacher in candidates if teacher.is_internal is False and teacher.gender == "M"
            )
            external_female = sum(
                1 for teacher in candidates if teacher.is_internal is False and teacher.gender == "F"
            )
            pair_cap = _gender_internal_pair_capacity(
                internal_male,
                internal_female,
                external_male,
                external_female,
            )
            if pair_cap < required_pairs:
                return (
                    False,
                    (
                        f"科目{subject_id}在“性别+本外校”约束下，合法配对最多 {pair_cap} 对，"
                        f"不足以覆盖 {required_pairs} 个考场。"
                    ),
                )
        elif internal_mix:
            internal_count = sum(1 for teacher in candidates if teacher.is_internal is True)
            external_count = sum(1 for teacher in candidates if teacher.is_internal is False)
            pair_cap = min(internal_count, external_count)
            if pair_cap < required_pairs:
                return (
                    False,
                    (
                        f"科目{subject_id}在“本外校搭配”约束下，合法配对最多 {pair_cap} 对，"
                        f"不足以覆盖 {required_pairs} 个考场。"
                    ),
                )
        elif gender_mix:
            male_count = sum(1 for teacher in candidates if teacher.gender == "M")
            female_count = sum(1 for teacher in candidates if teacher.gender == "F")
            pair_cap = _gender_pair_capacity(male_count, female_count)
            if pair_cap < required_pairs:
                return (
                    False,
                    (
                        f"科目{subject_id}在“性别搭配”约束下，合法配对最多 {pair_cap} 对，"
                        f"不足以覆盖 {required_pairs} 个考场。"
                    ),
                )

    return True, "可行"


def is_schedule_complete(schedule):
    """Check whether every room has enough assigned teachers or exempt slots."""
    for exam in schedule.exams:
        for room in exam.rooms:
            teachers = exam.schedule.get(room, [])
            assigned_count = len([teacher for teacher in teachers if teacher is not None])
            exempt_count = schedule.get_exempt_slot_count(exam.subject_id, room)
            if assigned_count + exempt_count < schedule.get_slot_count():
                return False
    return True
