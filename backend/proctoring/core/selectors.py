#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teacher selection helpers for proctoring scheduling."""

from backend.proctoring.core.balance import balance_double_role_order, compute_targets


def select_teacher(schedule, subject_id, room=None):
    """
    选择单个教师（单教师监考模式）
    """
    available_teachers = [
        teacher for teacher in schedule.teachers
        if teacher.can_supervise(subject_id)
        and teacher.is_available()
        and not teacher.is_assigned_to_subject(subject_id)
        and (teacher.preset_room is None or (room is not None and teacher.preset_room == room))
    ]

    if not available_teachers:
        return None

    balance_mode = schedule.get_constraint('balance_mode', 'session')
    if balance_mode == 'session':
        min_count = min(teacher.assigned_count() for teacher in available_teachers)
        candidates = [teacher for teacher in available_teachers if teacher.assigned_count() == min_count]
        candidates.sort(key=lambda teacher: (teacher.supervision_duration, teacher.assigned_count()))
        return candidates[0]

    targets = compute_targets(schedule)

    def deficit_ratio(teacher):
        target = max(targets.get(teacher, 0), 1e-9)
        current_total = (teacher.supervision_duration or 0) + (teacher.previous_supervision_duration or 0)
        deficit = max(target - current_total, 0.0)
        return deficit / target

    available_teachers.sort(
        key=lambda teacher: (
            -deficit_ratio(teacher),
            (teacher.supervision_duration or 0) + (teacher.previous_supervision_duration or 0),
            teacher.assigned_count(),
        )
    )
    return available_teachers[0]


def select_teachers_pair(schedule, subject_id, existing_teachers, room=None):
    """
    选择教师对（双教师监考模式）
    支持在现有安排基础上继续安排
    """
    def has_quota(teacher):
        try:
            capacity = int(teacher.max_sessions) if teacher.max_sessions is not None else 0
        except Exception:
            capacity = 0
        return capacity > len(teacher.assigned_sessions)

    available_teachers = [
        teacher for teacher in schedule.teachers
        if teacher.can_supervise(subject_id)
        and has_quota(teacher)
        and not teacher.is_assigned_to_subject(subject_id)
        and (teacher.preset_room is None or (room is not None and teacher.preset_room == room))
    ]

    balance_mode = schedule.get_constraint('balance_mode', 'session')

    if len(existing_teachers) == 1 and existing_teachers[0]:
        existing_teacher = existing_teachers[0]
        if existing_teacher and existing_teacher.preset_room is not None and room is not None and existing_teacher.preset_room != room:
            return None

        valid_teachers = [
            teacher for teacher in available_teachers
            if teacher != existing_teacher and schedule.is_valid_pair(existing_teacher, teacher)
        ]

        if not valid_teachers:
            return None

        if balance_mode == 'session':
            valid_teachers.sort(key=lambda teacher: teacher.assigned_count())
        else:
            targets = compute_targets(schedule)

            def deficit_ratio(teacher):
                target = max(targets.get(teacher, 0), 1e-9)
                current_total = (teacher.supervision_duration or 0) + (teacher.previous_supervision_duration or 0)
                deficit = max(target - current_total, 0.0)
                return deficit / target

            valid_teachers.sort(
                key=lambda teacher: (
                    -deficit_ratio(teacher),
                    (teacher.supervision_duration or 0) + (teacher.previous_supervision_duration or 0),
                    teacher.assigned_count(),
                )
            )

        teacher = valid_teachers[0]

        if schedule.get_constraint('internal_mix'):
            if existing_teacher.is_internal is True and teacher.is_internal is False:
                return [existing_teacher, teacher]
            if existing_teacher.is_internal is False and teacher.is_internal is True:
                return [teacher, existing_teacher]
        else:
            return [existing_teacher, teacher]

    gender_mix = schedule.get_constraint('gender_mix', False)
    internal_mix = schedule.get_constraint('internal_mix', False)
    targets = compute_targets(schedule) if balance_mode == 'duration' else None

    def deficit_ratio(teacher):
        if targets is None:
            return 0.0
        target = max(targets.get(teacher, 0), 1e-9)
        current_total = (teacher.supervision_duration or 0) + (teacher.previous_supervision_duration or 0)
        deficit = max(target - current_total, 0.0)
        return deficit / target

    def pair_cost(teacher1, teacher2):
        if balance_mode == 'session':
            return (teacher1.assigned_count() + teacher2.assigned_count(),)
        deficit = -(deficit_ratio(teacher1) + deficit_ratio(teacher2))
        total_minutes = (
            (teacher1.supervision_duration or 0) + (teacher1.previous_supervision_duration or 0) +
            (teacher2.supervision_duration or 0) + (teacher2.previous_supervision_duration or 0)
        )
        return (deficit, total_minutes)

    if internal_mix and gender_mix:
        group_a_left = [teacher for teacher in available_teachers if teacher.is_internal is True and teacher.gender == 'M']
        group_a_right = [teacher for teacher in available_teachers if teacher.is_internal is False and teacher.gender == 'F']
        group_b_left = [teacher for teacher in available_teachers if teacher.is_internal is True and teacher.gender == 'F']
        group_b_right = [teacher for teacher in available_teachers if teacher.is_internal is False and teacher.gender == 'M']

        candidates = []
        for left, right in ((group_a_left, group_a_right), (group_b_left, group_b_right)):
            for teacher1 in left:
                for teacher2 in right:
                    if not schedule.is_valid_pair(teacher1, teacher2):
                        continue
                    candidates.append((pair_cost(teacher1, teacher2), teacher1, teacher2))

        if candidates:
            candidates.sort(key=lambda candidate: candidate[0])
            _, teacher1, teacher2 = candidates[0]
            return [teacher1, teacher2]
        return None

    if internal_mix:
        internals = [teacher for teacher in available_teachers if teacher.is_internal is True]
        externals = [teacher for teacher in available_teachers if teacher.is_internal is False]
        candidates = []
        for teacher1 in internals:
            for teacher2 in externals:
                if not schedule.is_valid_pair(teacher1, teacher2):
                    continue
                candidates.append((pair_cost(teacher1, teacher2), teacher1, teacher2))
        if candidates:
            candidates.sort(key=lambda candidate: candidate[0])
            _, teacher1, teacher2 = candidates[0]
            return [teacher1, teacher2]
        return None

    if gender_mix:
        males = [teacher for teacher in available_teachers if teacher.gender == 'M']
        females = [teacher for teacher in available_teachers if teacher.gender == 'F']
        candidates = []
        for teacher1 in males:
            for teacher2 in females:
                if not schedule.is_valid_pair(teacher1, teacher2):
                    continue
                candidates.append((pair_cost(teacher1, teacher2), teacher1, teacher2))
        if candidates:
            candidates.sort(key=lambda candidate: candidate[0])
            _, teacher1, teacher2 = candidates[0]
            return balance_double_role_order(schedule, teacher1, teacher2)
        return None

    candidates = []
    for i in range(len(available_teachers)):
        for j in range(i + 1, len(available_teachers)):
            teacher1 = available_teachers[i]
            teacher2 = available_teachers[j]
            if not schedule.is_valid_pair(teacher1, teacher2):
                continue
            candidates.append((pair_cost(teacher1, teacher2), teacher1, teacher2))
    if candidates:
        candidates.sort(key=lambda candidate: candidate[0])
        _, teacher1, teacher2 = candidates[0]
        return balance_double_role_order(schedule, teacher1, teacher2)
    return None
