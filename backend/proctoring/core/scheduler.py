#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scheduling helpers for proctoring scheduling."""

from backend.proctoring.core.entities import Exam


def generate_schedule(schedule):
    """
    生成监考安排（在现有安排基础上继续安排）
    """
    progress_cb = schedule.get_constraint("progress_callback", None)
    done_steps = 0
    total_steps = max(1, schedule.num_subjects) + max(1, len(schedule.teachers)) + (schedule.num_subjects * schedule.num_rooms) + 2
    if callable(progress_cb):
        try:
            progress_cb("开始生成监考安排：初始化与排序", 0)
        except Exception:
            pass

    schedule.exams = []
    for subject_id in range(1, schedule.num_subjects + 1):
        exam = Exam(subject_id, list(range(1, schedule.num_rooms + 1)))
        schedule.exams.append(exam)
        done_steps += 1
        if callable(progress_cb):
            try:
                progress_cb(f"初始化科目 {subject_id}/{schedule.num_subjects}", int(100 * done_steps / total_steps))
            except Exception:
                pass

    for teacher in schedule.teachers:
        teacher.assigned_sessions = []
        teacher.supervision_duration = 0
        done_steps += 1
        if callable(progress_cb):
            try:
                progress_cb("重置教师分配状态", int(100 * done_steps / total_steps))
            except Exception:
                pass

    schedule._shuffle_teachers_inplace()

    subject_durations = schedule.get_constraint("subject_durations", [])
    if subject_durations:
        schedule.exams.sort(
            key=lambda exam: subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0,
            reverse=True,
        )
    done_steps += 1
    if callable(progress_cb):
        try:
            progress_cb("按科目时长降序排序（LPT）", int(100 * done_steps / total_steps))
        except Exception:
            pass

    for exam in schedule.exams:
        for room in exam.rooms:
            if room in exam.schedule and exam.schedule[room]:
                teachers = exam.schedule[room]
                for teacher in teachers:
                    if teacher:
                        duration = subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0
                        teacher.assign((exam.subject_id, room), duration)
                        if callable(progress_cb):
                            try:
                                progress_cb(f"恢复导入安排：科目{exam.subject_id} 考场{room}", int(100 * done_steps / total_steps))
                            except Exception:
                                pass

    unassigned_count = 0

    for exam in schedule.exams:
        for room in exam.rooms:
            if room in exam.schedule and len(exam.schedule[room]) > 0:
                if schedule.mode == "double" and len(exam.schedule[room]) >= 2:
                    continue
                if schedule.mode == "single":
                    continue

            if schedule.mode == "single":
                if room in exam.schedule and len(exam.schedule[room]) > 0:
                    continue

                teacher = schedule._select_teacher(exam.subject_id, room)
                if teacher:
                    exam.schedule[room] = [teacher]
                    duration = subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0
                    teacher.assign((exam.subject_id, room), duration)
                    done_steps += 1
                    if callable(progress_cb):
                        try:
                            progress_cb(f"分配监考：科目{exam.subject_id} 考场{room}", int(100 * done_steps / total_steps))
                        except Exception:
                            pass
                else:
                    unassigned_count += 1
                    done_steps += 1
                    if callable(progress_cb):
                        try:
                            progress_cb(f"分配失败：科目{exam.subject_id} 考场{room}", int(100 * done_steps / total_steps))
                        except Exception:
                            pass
            else:
                if room in exam.schedule and len(exam.schedule[room]) >= 2:
                    continue

                teachers = schedule._select_teachers_pair(exam.subject_id, exam.schedule.get(room, []), room)
                if teachers:
                    exam.schedule[room] = teachers
                    duration = subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0
                    for teacher in teachers:
                        if teacher:
                            teacher.assign((exam.subject_id, room), duration)
                    done_steps += 1
                    if callable(progress_cb):
                        try:
                            progress_cb(f"分配监考（双）：科目{exam.subject_id} 考场{room}", int(100 * done_steps / total_steps))
                        except Exception:
                            pass
                else:
                    unassigned_count += 1
                    done_steps += 1
                    if callable(progress_cb):
                        try:
                            progress_cb(f"分配失败（双）：科目{exam.subject_id} 考场{room}", int(100 * done_steps / total_steps))
                        except Exception:
                            pass

    if callable(progress_cb):
        try:
            progress_cb(f"生成完成，未分配考场数={unassigned_count}", 100)
        except Exception:
            pass

    try:
        schedule.rebalance_double_roles_postprocess()
    except Exception:
        pass

    return schedule.exams, unassigned_count


def continue_schedule(schedule):
    """
    继续为未安排的考场分配监考教师
    Returns:
        (bool, str): (是否完全安排成功, 未完成原因)
    """
    if not schedule.exams:
        return False, "没有考试安排信息"

    schedule._shuffle_teachers_inplace()

    subject_durations = schedule.get_constraint("subject_durations", [])
    if subject_durations:
        try:
            schedule.exams.sort(
                key=lambda exam: subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0,
                reverse=True,
            )
        except Exception:
            pass

    progress_cb = schedule.get_constraint("progress_callback", None)
    total_missing = 0
    for exam in schedule.exams:
        for room in exam.rooms:
            if room not in exam.schedule:
                total_missing += 2 if schedule.mode == "double" else 1
            elif schedule.mode == "double":
                teachers = exam.schedule[room]
                if len(teachers) < 2 or None in teachers:
                    total_missing += 2 - sum(1 for teacher in teachers if teacher is not None)
    total_missing = max(1, total_missing)
    completed = 0

    if callable(progress_cb):
        try:
            progress_cb("开始补全未安排考场", 0)
        except Exception:
            pass

    for exam in schedule.exams:
        for room in exam.rooms:
            if room not in exam.schedule:
                if schedule.mode == "single":
                    teacher = schedule._select_teacher(exam.subject_id, room)
                    if teacher:
                        exam.schedule[room] = [teacher]
                        duration = subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0
                        teacher.assign((exam.subject_id, room), duration)
                        completed += 1
                        if callable(progress_cb):
                            try:
                                progress_cb(f"补全：科目{exam.subject_id} 考场{room}", int(100 * completed / total_missing))
                            except Exception:
                                pass
                    else:
                        if callable(progress_cb):
                            try:
                                progress_cb(f"补全失败：科目{exam.subject_id} 考场{room}", int(100 * completed / total_missing))
                            except Exception:
                                pass
                        return False, f"科目{exam.subject_id}考场{room}找不到合适的监考教师"
                else:
                    teachers = schedule._select_teachers_pair(exam.subject_id, [])
                    if teachers:
                        exam.schedule[room] = teachers
                        duration = subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0
                        for teacher in teachers:
                            if teacher:
                                teacher.assign((exam.subject_id, room), duration)
                        completed += 2
                        if callable(progress_cb):
                            try:
                                progress_cb(f"补全（双）：科目{exam.subject_id} 考场{room}", int(100 * completed / total_missing))
                            except Exception:
                                pass
                    else:
                        if callable(progress_cb):
                            try:
                                progress_cb(f"补全失败（双）：科目{exam.subject_id} 考场{room}", int(100 * completed / total_missing))
                            except Exception:
                                pass
                        return False, f"科目{exam.subject_id}考场{room}找不到合适的监考教师对"

            elif schedule.mode == "double":
                teachers = exam.schedule[room]
                if len(teachers) < 2 or None in teachers:
                    while len(teachers) < 2:
                        teachers.append(None)

                    missing_indices = [index for index, teacher in enumerate(teachers) if teacher is None]
                    duration = subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0

                    if len(missing_indices) == 2:
                        pair = schedule._select_teachers_pair(exam.subject_id, [], room)
                        if pair:
                            exam.schedule[room] = pair
                            for teacher in pair:
                                if teacher:
                                    teacher.assign((exam.subject_id, room), duration)
                            completed += 2
                            if callable(progress_cb):
                                try:
                                    progress_cb(f"补全双缺：科目{exam.subject_id} 考场{room}", int(100 * completed / total_missing))
                                except Exception:
                                    pass
                        else:
                            if callable(progress_cb):
                                try:
                                    progress_cb(f"补全双缺失败：科目{exam.subject_id} 考场{room}", int(100 * completed / total_missing))
                                except Exception:
                                    pass
                            return False, f"科目{exam.subject_id}考场{room}找不到合适的监考教师对"
                    elif len(missing_indices) == 1:
                        missing_idx = missing_indices[0]
                        other_idx = 1 - missing_idx
                        existing_teacher = teachers[other_idx]

                        if existing_teacher is None:
                            pair = schedule._select_teachers_pair(exam.subject_id, [], room)
                            if pair:
                                exam.schedule[room] = pair
                                for teacher in pair:
                                    if teacher:
                                        teacher.assign((exam.subject_id, room), duration)
                                completed += 2
                                if callable(progress_cb):
                                    try:
                                        progress_cb(f"补全双（回退）：科目{exam.subject_id} 考场{room}", int(100 * completed / total_missing))
                                    except Exception:
                                        pass
                            else:
                                if callable(progress_cb):
                                    try:
                                        progress_cb(f"补全双（回退）失败：科目{exam.subject_id} 考场{room}", int(100 * completed / total_missing))
                                    except Exception:
                                        pass
                                return False, f"科目{exam.subject_id}考场{room}找不到合适的监考教师对"
                        else:
                            pair = schedule._select_teachers_pair(exam.subject_id, [existing_teacher], room)
                            if pair:
                                partner = pair[0] if pair[0] != existing_teacher else pair[1]
                                teachers[missing_idx] = partner
                                exam.schedule[room] = teachers
                                if partner:
                                    partner.assign((exam.subject_id, room), duration)
                                completed += 1
                                if callable(progress_cb):
                                    try:
                                        progress_cb(f"补全单缺：科目{exam.subject_id} 考场{room}", int(100 * completed / total_missing))
                                    except Exception:
                                        pass
                            else:
                                if callable(progress_cb):
                                    try:
                                        progress_cb(f"补全单缺失败：科目{exam.subject_id} 考场{room}", int(100 * completed / total_missing))
                                    except Exception:
                                        pass
                                return False, f"科目{exam.subject_id}考场{room}找不到合适的第二位监考教师"

    if callable(progress_cb):
        try:
            progress_cb("补全完成", 100)
        except Exception:
            pass

    try:
        schedule.rebalance_double_roles_postprocess()
    except Exception:
        pass

    return True, "安排完成"
