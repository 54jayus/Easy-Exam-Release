#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Balancing helpers for proctoring schedule generation."""


def compute_targets(schedule):
    """
    计算每位教师的目标监考时长(分钟)，用于时长均衡选择时的“公平配额”。
    目标值基于：平均科目时长 × 教师最大监考段数 × 缩放因子（匹配总分钟数）。
    """
    subject_durations = schedule.get_constraint('subject_durations', [])
    if not subject_durations:
        return {t: 0 for t in schedule.teachers}
    avg_duration = sum(subject_durations) / len(subject_durations)
    total_capacity = sum(max(0, t.max_sessions or 0) for t in schedule.teachers)
    mode_factor = 2 if schedule.mode == 'double' else 1
    total_assigned_minutes = sum(subject_durations) * schedule.num_rooms * mode_factor
    alpha = 1.0
    if avg_duration > 0 and total_capacity > 0:
        alpha = total_assigned_minutes / (avg_duration * total_capacity)
    targets = {}
    for teacher in schedule.teachers:
        max_s = max(0, teacher.max_sessions or 0)
        targets[teacher] = avg_duration * max_s * alpha
    return targets


def compute_double_role_counts(schedule):
    counts = {teacher: [0, 0] for teacher in schedule.teachers}
    if schedule.mode != 'double':
        return counts

    for exam in schedule.exams:
        for _room, teachers in (exam.schedule or {}).items():
            if not teachers:
                continue
            if len(teachers) >= 1 and teachers[0] is not None:
                if teachers[0] not in counts:
                    counts[teachers[0]] = [0, 0]
                counts[teachers[0]][0] += 1
            if len(teachers) >= 2 and teachers[1] is not None:
                if teachers[1] not in counts:
                    counts[teachers[1]] = [0, 0]
                counts[teachers[1]][1] += 1

    return counts


def balance_double_role_order(schedule, teacher1, teacher2):
    if schedule.mode != 'double' or schedule.get_constraint('internal_mix', False):
        return [teacher1, teacher2]

    counts = compute_double_role_counts(schedule)
    a0, a1 = counts.get(teacher1, [0, 0])
    b0, b1 = counts.get(teacher2, [0, 0])

    score_keep = abs((a0 + 1) - a1) + abs(b0 - (b1 + 1))
    score_swap = abs(a0 - (a1 + 1)) + abs((b0 + 1) - b1)

    if score_swap < score_keep:
        return [teacher2, teacher1]
    if score_swap > score_keep:
        return [teacher1, teacher2]

    d1 = a0 - a1
    d2 = b0 - b1
    if d1 > d2:
        return [teacher2, teacher1]
    if d1 < d2:
        return [teacher1, teacher2]

    if (a0 + a1 + b0 + b1) % 2 == 0:
        return [teacher2, teacher1]
    return [teacher1, teacher2]


def rebalance_double_roles_postprocess(schedule, max_passes=3, max_candidates=40):
    if (
        schedule.mode != 'double'
        or schedule.get_constraint('internal_mix', False)
        or schedule.get_constraint('gender_mix', False)
    ):
        return {"swaps": 0, "moves": 0}

    def is_fixed(exam, room, idx, teacher):
        if teacher is None:
            return True
        if getattr(teacher, 'preset_room', None) is not None:
            return True
        if schedule.is_position_imported(exam.subject_id, room, idx):
            return True
        return False

    def replace_assigned_room(teacher, subject_id, old_room, new_room):
        if teacher is None:
            return
        try:
            old_key = (int(subject_id), int(old_room))
            new_key = (int(subject_id), int(new_room))
        except Exception:
            old_key = (subject_id, old_room)
            new_key = (subject_id, new_room)

        try:
            sessions = teacher.assigned_sessions
        except Exception:
            return

        for i, session in enumerate(list(sessions)):
            if session == old_key:
                sessions[i] = new_key
                return
        if new_key not in sessions:
            sessions.append(new_key)

    swaps = 0
    moves = 0

    for _ in range(max(1, int(max_passes))):
        changed = False
        counts = compute_double_role_counts(schedule)

        for exam in schedule.exams:
            sched = exam.schedule or {}

            for room, teachers in sched.items():
                if not teachers or len(teachers) < 2:
                    continue
                t0 = teachers[0]
                t1 = teachers[1]
                if t0 is None or t1 is None or t0 == t1:
                    continue
                if is_fixed(exam, room, 0, t0) or is_fixed(exam, room, 1, t1):
                    continue

                a0, a1 = counts.get(t0, [0, 0])
                b0, b1 = counts.get(t1, [0, 0])
                before = abs(a0 - a1) + abs(b0 - b1)
                after = abs((a0 - 1) - (a1 + 1)) + abs((b0 + 1) - (b1 - 1))

                if after < before:
                    teachers[0], teachers[1] = t1, t0
                    counts[t0] = [a0 - 1, a1 + 1]
                    counts[t1] = [b0 + 1, b1 - 1]
                    swaps += 1
                    changed = True

            pos0 = []
            pos1 = []
            for room, teachers in sched.items():
                if not teachers or len(teachers) < 2:
                    continue
                t0 = teachers[0]
                t1 = teachers[1]

                if t0 is not None and not is_fixed(exam, room, 0, t0):
                    c0, c1 = counts.get(t0, [0, 0])
                    diff = c0 - c1
                    if diff > 0:
                        pos0.append((diff, room, t0))

                if t1 is not None and not is_fixed(exam, room, 1, t1):
                    c0, c1 = counts.get(t1, [0, 0])
                    diff = c0 - c1
                    if diff < 0:
                        pos1.append((diff, room, t1))

            if pos0 and pos1:
                pos0.sort(key=lambda x: -x[0])
                pos1.sort(key=lambda x: x[0])
                pos0 = pos0[: max(1, int(max_candidates))]
                pos1 = pos1[: max(1, int(max_candidates))]

                for _d0, r0, ta in pos0:
                    t_list0 = sched.get(r0)
                    if not t_list0 or len(t_list0) < 2:
                        continue
                    other0 = t_list0[1]
                    if other0 is None:
                        continue

                    for _d1, r1, tb in pos1:
                        if r0 == r1:
                            continue
                        if ta == tb:
                            continue

                        t_list1 = sched.get(r1)
                        if not t_list1 or len(t_list1) < 2:
                            continue
                        other1 = t_list1[0]
                        if other1 is None:
                            continue

                        if other0 == tb or other1 == ta:
                            continue

                        a0, a1 = counts.get(ta, [0, 0])
                        b0, b1 = counts.get(tb, [0, 0])
                        before = abs(a0 - a1) + abs(b0 - b1)
                        after = abs((a0 - 1) - (a1 + 1)) + abs((b0 + 1) - (b1 - 1))

                        if after < before:
                            t_list0[0] = tb
                            t_list1[1] = ta
                            counts[ta] = [a0 - 1, a1 + 1]
                            counts[tb] = [b0 + 1, b1 - 1]
                            replace_assigned_room(ta, exam.subject_id, r0, r1)
                            replace_assigned_room(tb, exam.subject_id, r1, r0)
                            moves += 1
                            changed = True
                            break

                    if changed:
                        break

        if not changed:
            break

    return {"swaps": swaps, "moves": moves}
