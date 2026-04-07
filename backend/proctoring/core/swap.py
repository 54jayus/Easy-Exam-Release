#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Swap helpers for proctoring scheduling."""


def find_teacher_index(schedule, subject_id, room, teacher):
    """
    查找指定教师在某科目某考场的索引位置（单/双教师模式）
    返回: 0/1 或 None
    """
    exam = next((exam for exam in schedule.exams if exam.subject_id == subject_id), None)
    if not exam:
        return None
    teachers = exam.schedule.get(room, [])
    for idx, current in enumerate(teachers):
        if current == teacher:
            return idx
    return None


def swap_teachers(schedule, session1_info, session2_info):
    """
    交换两个监考教师

    Args:
        session1_info: (subject_id, room, teacher_index) 第一个场次信息
        session2_info: (subject_id, room, teacher_index) 第二个场次信息

    Returns:
        (bool, str): (是否成功, 错误信息)
    """
    subject1, room1, teacher_index1 = session1_info
    subject2, room2, teacher_index2 = session2_info

    exam1 = None
    exam2 = None
    for exam in schedule.exams:
        if exam.subject_id == subject1:
            exam1 = exam
        if exam.subject_id == subject2:
            exam2 = exam

    if not exam1 or not exam2:
        return False, "无法找到对应的考试场次"

    if room1 not in exam1.schedule or room2 not in exam2.schedule:
        return False, "指定考场未安排监考教师"

    teachers1 = exam1.schedule[room1]
    teachers2 = exam2.schedule[room2]

    while len(teachers1) < 2:
        teachers1.append(None)
    while len(teachers2) < 2:
        teachers2.append(None)

    if len(teachers1) <= teacher_index1 or len(teachers2) <= teacher_index2:
        return False, "监考教师信息不完整"

    original_teacher1 = teachers1[teacher_index1]
    original_teacher2 = teachers2[teacher_index2]

    respect_preset = bool(schedule.get_constraint('respect_preset_on_swap', True))
    if respect_preset:
        if original_teacher1 and getattr(original_teacher1, 'preset_room', None) is not None:
            try:
                preset_room1 = int(original_teacher1.preset_room)
            except Exception:
                preset_room1 = None
            if preset_room1 is not None and int(room2) != preset_room1:
                return False, f"教师 {original_teacher1.name} 预设房间为 {preset_room1}，不能交换到考场 {room2}"
        if original_teacher2 and getattr(original_teacher2, 'preset_room', None) is not None:
            try:
                preset_room2 = int(original_teacher2.preset_room)
            except Exception:
                preset_room2 = None
            if preset_room2 is not None and int(room1) != preset_room2:
                return False, f"教师 {original_teacher2.name} 预设房间为 {preset_room2}，不能交换到考场 {room1}"

    if schedule.mode == "double":
        other_idx1 = 1 - teacher_index1
        other_idx2 = 1 - teacher_index2
        if original_teacher1 is not None:
            other_teacher_in_room2 = teachers2[other_idx2] if len(teachers2) > other_idx2 else None
            if other_teacher_in_room2 is not None and other_teacher_in_room2 == original_teacher1 and (subject1 != subject2 or room1 != room2 or teacher_index1 != other_idx2):
                return False, f"教师 {original_teacher1.name} 已在科目{subject2}考场{room2}担任另一位置，禁止同场重复担任监考员1和2"
        if original_teacher2 is not None:
            other_teacher_in_room1 = teachers1[other_idx1] if len(teachers1) > other_idx1 else None
            if other_teacher_in_room1 is not None and other_teacher_in_room1 == original_teacher2 and (subject1 != subject2 or room1 != room2 or teacher_index2 != other_idx1):
                return False, f"教师 {original_teacher2.name} 已在科目{subject1}考场{room1}担任另一位置，禁止同场重复担任监考员1和2"

    if subject1 != subject2:
        if original_teacher1 and not original_teacher1.can_supervise(subject2):
            return False, f"教师 {original_teacher1.name} 无法监考科目 {subject2}"
        if original_teacher2 and not original_teacher2.can_supervise(subject1):
            return False, f"教师 {original_teacher2.name} 无法监考科目 {subject1}"

        if original_teacher1 and original_teacher1.is_assigned_to_subject(subject2):
            already_assigned = False
            for session in original_teacher1.assigned_sessions:
                if session[0] == subject2 and session[1] != room2:
                    already_assigned = True
                    break
            if already_assigned:
                return False, f"教师 {original_teacher1.name} 已经在科目 {subject2} 中监考其他考场"

        if original_teacher2 and original_teacher2.is_assigned_to_subject(subject1):
            already_assigned = False
            for session in original_teacher2.assigned_sessions:
                if session[0] == subject1 and session[1] != room1:
                    already_assigned = True
                    break
            if already_assigned:
                return False, f"教师 {original_teacher2.name} 已经在科目 {subject1} 中监考其他考场"
    else:
        if original_teacher1 and not original_teacher1.can_supervise(subject2):
            return False, f"教师 {original_teacher1.name} 无法监考科目 {subject2}"
        if original_teacher2 and not original_teacher2.can_supervise(subject1):
            return False, f"教师 {original_teacher2.name} 无法监考科目 {subject1}"

    if subject1 != subject2:
        if original_teacher1:
            for session in original_teacher1.assigned_sessions:
                if session[0] == subject2 and session[1] != room2:
                    return False, f"教师 {original_teacher1.name} 已经在科目 {subject2} 中监考其他考场"
        if original_teacher2:
            for session in original_teacher2.assigned_sessions:
                if session[0] == subject1 and session[1] != room1:
                    return False, f"教师 {original_teacher2.name} 已经在科目 {subject1} 中监考其他考场"

    if schedule.mode == "double":
        other_teacher1 = teachers1[1 - teacher_index1] if len(teachers1) > 1 else None
        other_teacher2 = teachers2[1 - teacher_index2] if len(teachers2) > 1 else None

        if schedule.get_constraint('gender_mix'):
            if other_teacher2 and original_teacher1 and other_teacher2.gender and original_teacher1.gender and other_teacher2.gender == original_teacher1.gender:
                return False, f"教师 {original_teacher1.name} 与考场{room2}的另一位教师性别不匹配"
            if other_teacher1 and original_teacher2 and other_teacher1.gender and original_teacher2.gender and other_teacher1.gender == original_teacher2.gender:
                return False, f"教师 {original_teacher2.name} 与考场{room1}的另一位教师性别不匹配"

        if schedule.get_constraint('internal_mix'):
            if other_teacher2 and original_teacher1 and other_teacher2.is_internal is not None and original_teacher1.is_internal is not None and other_teacher2.is_internal == original_teacher1.is_internal:
                return False, f"教师 {original_teacher1.name} 与考场{room2}的另一位教师本外校属性不匹配"
            if other_teacher1 and original_teacher2 and other_teacher1.is_internal is not None and original_teacher2.is_internal is not None and other_teacher1.is_internal == original_teacher2.is_internal:
                return False, f"教师 {original_teacher2.name} 与考场{room1}的另一位教师本外校属性不匹配"
            if teacher_index1 == 0 and original_teacher1 and original_teacher1.is_internal is False:
                return False, f"教师 {original_teacher1.name} 是外校教师，不能作为监考员1"
            if teacher_index1 == 1 and original_teacher1 and original_teacher1.is_internal is True:
                return False, f"教师 {original_teacher1.name} 是本校教师，不能作为监考员2"
            if teacher_index2 == 0 and original_teacher2 and original_teacher2.is_internal is False:
                return False, f"教师 {original_teacher2.name} 是外校教师，不能作为监考员1"
            if teacher_index2 == 1 and original_teacher2 and original_teacher2.is_internal is True:
                return False, f"教师 {original_teacher2.name} 是本校教师，不能作为监考员2"

    if original_teacher1:
        subject_durations = schedule.get_constraint('subject_durations', [])
        duration1 = subject_durations[subject1 - 1] if (subject1 - 1) < len(subject_durations) else 0
        original_teacher1.unassign((subject1, room1), duration1)
    if original_teacher2:
        subject_durations = schedule.get_constraint('subject_durations', [])
        duration2 = subject_durations[subject2 - 1] if (subject2 - 1) < len(subject_durations) else 0
        original_teacher2.unassign((subject2, room2), duration2)

    exam1.schedule[room1][teacher_index1] = original_teacher2
    exam2.schedule[room2][teacher_index2] = original_teacher1

    if original_teacher1:
        subject_durations = schedule.get_constraint('subject_durations', [])
        duration = subject_durations[subject2 - 1] if (subject2 - 1) < len(subject_durations) else 0
        original_teacher1.assign((subject2, room2), duration)
    if original_teacher2:
        subject_durations = schedule.get_constraint('subject_durations', [])
        duration = subject_durations[subject1 - 1] if (subject1 - 1) < len(subject_durations) else 0
        original_teacher2.assign((subject1, room1), duration)

    return True, "交换成功"
