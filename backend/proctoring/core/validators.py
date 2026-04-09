#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validation helpers for proctoring scheduling."""


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

    total_room_slots = sum(len(schedule._get_subject_rooms(subject_id)) for subject_id in range(1, schedule.num_subjects + 1))
    required_total = total_room_slots * (2 if mode == "double" else 1)
    if total_capacity < required_total:
        return False, f"全局监考名额不足：需要 {required_total} 人次，只有 {total_capacity} 人次。"

    if mode == "single":
        return True, "可行"

    if not gender_mix and not internal_mix:
        return True, "可行"

    for subject_id in range(1, schedule.num_subjects + 1):
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
            internal_male = sum(1 for teacher in candidates if teacher.is_internal is True and teacher.gender == "M")
            internal_female = sum(1 for teacher in candidates if teacher.is_internal is True and teacher.gender == "F")
            external_male = sum(1 for teacher in candidates if teacher.is_internal is False and teacher.gender == "M")
            external_female = sum(1 for teacher in candidates if teacher.is_internal is False and teacher.gender == "F")
            pair_cap = min(internal_male, external_female) + min(internal_female, external_male)
            required_pairs = len(schedule._get_subject_rooms(subject_id))
            if pair_cap < required_pairs:
                return False, (
                    f"科目{subject_id}在‘性别+本外校’约束下，合法配对最多 {pair_cap} 对，"
                    f"不足以覆盖 {required_pairs} 个考场。"
                )
        elif internal_mix:
            internal_count = sum(1 for teacher in candidates if teacher.is_internal is True)
            external_count = sum(1 for teacher in candidates if teacher.is_internal is False)
            pair_cap = min(internal_count, external_count)
            required_pairs = len(schedule._get_subject_rooms(subject_id))
            if pair_cap < required_pairs:
                return False, (
                    f"科目{subject_id}在‘本外校搭配’约束下，合法配对最多 {pair_cap} 对，"
                    f"不足以覆盖 {required_pairs} 个考场。"
                )
        elif gender_mix:
            male_count = sum(1 for teacher in candidates if teacher.gender == "M")
            female_count = sum(1 for teacher in candidates if teacher.gender == "F")
            pair_cap = min(male_count, female_count)
            required_pairs = len(schedule._get_subject_rooms(subject_id))
            if pair_cap < required_pairs:
                return False, (
                    f"科目{subject_id}在‘性别搭配’约束下，合法配对最多 {pair_cap} 对，"
                    f"不足以覆盖 {required_pairs} 个考场。"
                )

    return True, "可行"


def is_schedule_complete(schedule):
    """Check whether every room has enough assigned teachers for the current mode."""
    required_count = 1 if schedule.mode == "single" else 2
    for exam in schedule.exams:
        for room in exam.rooms:
            teachers = exam.schedule.get(room, [])
            if len([teacher for teacher in teachers if teacher is not None]) < required_count:
                return False
    return True
