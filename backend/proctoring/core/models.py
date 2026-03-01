#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Data model module: defines core data structures for scheduling.

import random
import logging

logger = logging.getLogger(__name__)

class Teacher:
    """
    教师类
    """
    def __init__(self, name, gender=None, is_internal=None, max_sessions=None, unavailable_subjects=None, previous_supervision_duration=0):
        self.name = name                    # 姓名
        self.gender = gender                # 性别 ('M'/'F')
        self.is_internal = is_internal      # 是否本校 (True/False)
        self.max_sessions = max_sessions    # 最大监考段数
        self.unavailable_subjects = unavailable_subjects or []  # 不监考科目列表
        self.assigned_sessions = []         # 已分配的监考场次
        self.supervision_duration = 0       # 本次监考时长(分钟)
        self.previous_supervision_duration = previous_supervision_duration or 0  # 历次监考时长(分钟)
        # 预设监考考场（整数房间号；None表示无预设）。用于初次安排硬过滤与最终修复。
        self.preset_room = None

    def can_supervise(self, subject_id):
        """
        检查教师是否可以监考指定科目
        """
        return subject_id not in self.unavailable_subjects

    def is_available(self):
        """
        检查教师是否还有监考名额
        """
        return len(self.assigned_sessions) < self.max_sessions

    def assign(self, session, duration=0):
        """
        为教师分配监考场次
        :param session: 监考场次信息
        :param duration: 监考时长(分钟)
        """
        if self.is_available():
            self.assigned_sessions.append(session)
            self.supervision_duration += duration
            return True
        return False

    def unassign(self, session, duration=0):
        """
        取消教师的监考场次分配
        :param session: 监考场次信息
        :param duration: 要减少的监考时长(分钟)
        """
        if session in self.assigned_sessions:
            self.assigned_sessions.remove(session)
            self.supervision_duration = max(0, self.supervision_duration - duration)
            return True
        return False

    def assigned_count(self):
        """
        获取教师已分配的监考次数
        """
        return len(self.assigned_sessions)

    # 添加新方法：检查教师是否已在指定科目监考
    def is_assigned_to_subject(self, subject_id):
        """
        检查教师是否已在指定科目监考
        """
        for session in self.assigned_sessions:
            if session[0] == subject_id:
                return True
        return False


class Exam:
    """
    考试类
    """
    def __init__(self, subject_id, rooms):
        self.subject_id = subject_id        # 科目编号
        self.rooms = rooms                  # 考场列表
        self.schedule = {}                  # 监考安排 {考场号: [监考教师列表]}


class Schedule:
    """
    监考安排类
    """
    def __init__(self, teachers, num_subjects, num_rooms, mode="single"):
        self.teachers = teachers            # 教师列表
        self.original_teachers_order = list(teachers)  # 保存教师原始顺序
        self.num_subjects = num_subjects    # 科目数
        self.num_rooms = num_rooms          # 考场数
        self.mode = mode                    # 监考模式 ("single"/"double")
        self.exams = []                     # 考试安排列表
        self.constraints = {}               # 约束条件
        self.imported_positions = set()     # 导入的固定位置标记: (subject_id, room, index)

    def set_constraint(self, key, value):
        """
        设置约束条件
        """
        self.constraints[key] = value

    def get_constraint(self, key, default=False):
        """
        获取约束条件
        """
        return self.constraints.get(key, default)

    def mark_imported_position(self, subject_id, room, index):
        """标记指定科目-考场-位置为导入安排位置。"""
        self.imported_positions.add((subject_id, room, index))

    def is_position_imported(self, subject_id, room, index):
        """检查指定科目-考场-位置是否为导入安排位置。"""
        return (subject_id, room, index) in self.imported_positions

    def _get_subject_duration(self, subject_id):
        """获取指定科目的考试时长(分钟)，无则返回0。"""
        subject_durations = self.get_constraint('subject_durations', [])
        return subject_durations[subject_id - 1] if (subject_id - 1) < len(subject_durations) else 0

    def _shuffle_teachers_inplace(self):
        # 如果你未来想临时关闭随机（例如调试复现），可以在构建 Schedule 后设置：schedule.set_constraint('shuffle_teachers', False)；默认不设置就是开启随机。
        if not self.get_constraint('shuffle_teachers', True):
            return
        try:
            random.shuffle(self.teachers)
        except Exception:
            pass

    def _compute_targets(self):
        """
        计算每位教师的目标监考时长(分钟)，用于时长均衡选择时的“公平配额”。
        目标值基于：平均科目时长 × 教师最大监考段数 × 缩放因子（匹配总分钟数）。
        """
        subject_durations = self.get_constraint('subject_durations', [])
        if not subject_durations:
            return {t: 0 for t in self.teachers}
        avg_duration = sum(subject_durations) / len(subject_durations)
        total_capacity = sum(max(0, t.max_sessions or 0) for t in self.teachers)
        mode_factor = 2 if self.mode == 'double' else 1
        total_assigned_minutes = sum(subject_durations) * self.num_rooms * mode_factor
        # 避免除零
        alpha = 1.0
        if avg_duration > 0 and total_capacity > 0:
            alpha = total_assigned_minutes / (avg_duration * total_capacity)
        targets = {}
        for t in self.teachers:
            max_s = max(0, t.max_sessions or 0)
            targets[t] = avg_duration * max_s * alpha
        return targets

    def is_valid_pair(self, teacher1, teacher2):
        """
        检查两个教师是否满足搭配要求（双教师模式）
        """
        # 检查性别搭配要求
        if self.get_constraint('gender_mix'):
            if not teacher1.gender or not teacher2.gender:
                return False
            if teacher1.gender == teacher2.gender:
                return False

        # 检查本外校搭配要求
        if self.get_constraint('internal_mix'):
            if teacher1.is_internal is None or teacher2.is_internal is None:
                return False
            if teacher1.is_internal == teacher2.is_internal:
                return False

        return True

    def _compute_double_role_counts(self):
        counts = {t: [0, 0] for t in self.teachers}
        if self.mode != 'double':
            return counts

        for exam in self.exams:
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

    def _balance_double_role_order(self, t1, t2):
        if self.mode != 'double' or self.get_constraint('internal_mix', False):
            return [t1, t2]

        counts = self._compute_double_role_counts()
        a0, a1 = counts.get(t1, [0, 0])
        b0, b1 = counts.get(t2, [0, 0])

        score_keep = abs((a0 + 1) - a1) + abs(b0 - (b1 + 1))
        score_swap = abs(a0 - (a1 + 1)) + abs((b0 + 1) - b1)

        if score_swap < score_keep:
            return [t2, t1]
        if score_swap > score_keep:
            return [t1, t2]

        d1 = a0 - a1
        d2 = b0 - b1
        if d1 > d2:
            return [t2, t1]
        if d1 < d2:
            return [t1, t2]

        if (a0 + a1 + b0 + b1) % 2 == 0:
            return [t2, t1]
        return [t1, t2]

    def rebalance_double_roles_postprocess(self, max_passes=3, max_candidates=40):
        if (
            self.mode != 'double'
            or self.get_constraint('internal_mix', False)
            or self.get_constraint('gender_mix', False)
        ):
            return {"swaps": 0, "moves": 0}

        def is_fixed(exam, room, idx, teacher):
            if teacher is None:
                return True
            if getattr(teacher, 'preset_room', None) is not None:
                return True
            if self.is_position_imported(exam.subject_id, room, idx):
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

            for i, s in enumerate(list(sessions)):
                if s == old_key:
                    sessions[i] = new_key
                    return
            if new_key not in sessions:
                sessions.append(new_key)

        swaps = 0
        moves = 0

        for _ in range(max(1, int(max_passes))):
            changed = False
            counts = self._compute_double_role_counts()

            for exam in self.exams:
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
                        d = c0 - c1
                        if d > 0:
                            pos0.append((d, room, t0))

                    if t1 is not None and not is_fixed(exam, room, 1, t1):
                        c0, c1 = counts.get(t1, [0, 0])
                        d = c0 - c1
                        if d < 0:
                            pos1.append((d, room, t1))

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

    def generate_schedule(self):
        """
        生成监考安排（在现有安排基础上继续安排）
        """
        # 进度回调：由UI层通过约束注入，保持与实际步骤同步
        progress_cb = self.get_constraint('progress_callback', None)
        log_swaps = bool(self.get_constraint('log_optimization_swaps', False))
        done_steps = 0
        total_steps = max(1, self.num_subjects) + max(1, len(self.teachers)) + (self.num_subjects * self.num_rooms) + 2
        if callable(progress_cb):
            try:
                progress_cb("开始生成监考安排：初始化与排序", 0)
            except Exception:
                pass
        # 初始化考试安排
        self.exams = []
        for subject_id in range(1, self.num_subjects + 1):
            exam = Exam(subject_id, list(range(1, self.num_rooms + 1)))
            self.exams.append(exam)
            done_steps += 1
            if callable(progress_cb):
                try:
                    progress_cb(f"初始化科目 {subject_id}/{self.num_subjects}", int(100 * done_steps / total_steps))
                except Exception:
                    pass

        # 清空教师已分配的场次和监考时长（每次生成新安排时需要清空）
        for teacher in self.teachers:
            teacher.assigned_sessions = []
            teacher.supervision_duration = 0
            done_steps += 1
            if callable(progress_cb):
                try:
                    progress_cb("重置教师分配状态", int(100 * done_steps / total_steps))
                except Exception:
                    pass

        self._shuffle_teachers_inplace()

        # 按考试时长降序进行LPT排序，以改善时长均衡
        subject_durations = self.get_constraint('subject_durations', [])
        if subject_durations:
            self.exams.sort(
                key=lambda e: subject_durations[e.subject_id - 1] if (e.subject_id - 1) < len(subject_durations) else 0,
                reverse=True
            )
        done_steps += 1
        if callable(progress_cb):
            try:
                progress_cb("按科目时长降序排序（LPT）", int(100 * done_steps / total_steps))
            except Exception:
                pass

        # 重新根据现有安排分配教师场次
        for exam in self.exams:
            for room in exam.rooms:
                if room in exam.schedule and exam.schedule[room]:
                    teachers = exam.schedule[room]
                    for teacher in teachers:
                        if teacher:  # 只有当教师存在时才分配
                            # 获取科目时长
                            subject_durations = self.get_constraint('subject_durations', [])
                            duration = subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0
                            teacher.assign((exam.subject_id, room), duration)
                            if callable(progress_cb):
                                try:
                                    progress_cb(f"恢复导入安排：科目{exam.subject_id} 考场{room}", int(100 * done_steps / total_steps))
                                except Exception:
                                    pass

        # 记录未能安排的考场数量
        unassigned_count = 0
        
        # 按科目顺序进行监考安排
        for exam in self.exams:
            for room in exam.rooms:
                # 检查是否已经安排过监考
                if room in exam.schedule and len(exam.schedule[room]) > 0:
                    # 如果是双教师模式，检查是否已经安排了两名教师
                    if self.mode == "double" and len(exam.schedule[room]) >= 2:
                        # 已经完整安排，跳过
                        continue
                    elif self.mode == "single":
                        # 单教师模式已经安排，跳过
                        continue
                
                if self.mode == "single":
                    # 单教师监考模式
                    # 如果已经安排了教师，跳过
                    if room in exam.schedule and len(exam.schedule[room]) > 0:
                        continue
                    
                    # 初次安排采用硬过滤：若教师有preset_room，必须与当前room匹配
                    teacher = self._select_teacher(exam.subject_id, room)
                    if teacher:
                        exam.schedule[room] = [teacher]
                        # 获取科目时长
                        subject_durations = self.get_constraint('subject_durations', [])
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
                    # 双教师监考模式
                    # 检查是否已经安排了两名教师
                    if room in exam.schedule and len(exam.schedule[room]) >= 2:
                        continue
                    
                    # 传入room以便在选择时对preset_room进行硬过滤
                    teachers = self._select_teachers_pair(exam.subject_id, exam.schedule.get(room, []), room)
                    if teachers:
                        exam.schedule[room] = teachers
                        # 获取科目时长
                        subject_durations = self.get_constraint('subject_durations', [])
                        duration = subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0
                        for teacher in teachers:
                            if teacher:  # 只有当教师存在时才分配
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

        # 返回安排结果和未安排数量（完成进度）
        if callable(progress_cb):
            try:
                progress_cb(f"生成完成，未分配考场数={unassigned_count}", 100)
            except Exception:
                pass

        try:
            self.rebalance_double_roles_postprocess()
        except Exception:
            pass

        return self.exams, unassigned_count

    def continue_schedule(self):
        """
        继续为未安排的考场分配监考教师
        Returns:
            (bool, str): (是否完全安排成功, 未完成原因)
        """
        if not self.exams:
            return False, "没有考试安排信息"

        self._shuffle_teachers_inplace()

        # 在补全前按科目时长降序（LPT）排序科目，优先填重段，提升均衡起点
        subject_durations = self.get_constraint('subject_durations', [])
        if subject_durations:
            try:
                self.exams.sort(
                    key=lambda e: subject_durations[e.subject_id - 1] if (e.subject_id - 1) < len(subject_durations) else 0,
                    reverse=True
                )
            except Exception:
                # 如果时长信息异常，保持原有顺序
                pass
        # 进度回调：统计缺口并按步骤更新
        progress_cb = self.get_constraint('progress_callback', None)
        total_missing = 0
        for exam in self.exams:
            for room in exam.rooms:
                if room not in exam.schedule:
                    total_missing += (2 if self.mode == "double" else 1)
                elif self.mode == "double":
                    teachers = exam.schedule[room]
                    if len(teachers) < 2 or None in teachers:
                        # 缺一个位置
                        total_missing += (2 - sum(1 for t in teachers if t is not None))
        total_missing = max(1, total_missing)
        completed = 0
        if callable(progress_cb):
            try:
                progress_cb("开始补全未安排考场", 0)
            except Exception:
                pass
            
        # 统计并处理未安排的考场
        for exam in self.exams:
            for room in exam.rooms:
                if room not in exam.schedule:
                    # 未安排的考场
                    if self.mode == "single":
                        teacher = self._select_teacher(exam.subject_id, room)
                        if teacher:
                            exam.schedule[room] = [teacher]
                            # 获取科目时长
                            subject_durations = self.get_constraint('subject_durations', [])
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
                        teachers = self._select_teachers_pair(exam.subject_id, [])
                        if teachers:
                            exam.schedule[room] = teachers
                            # 获取科目时长
                            subject_durations = self.get_constraint('subject_durations', [])
                            duration = subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0
                            for t in teachers:
                                if t:
                                    t.assign((exam.subject_id, room), duration)
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
                
                elif self.mode == "double":
                    # 检查双教师模式下是否需要补充第二个教师
                    teachers = exam.schedule[room]
                    # 保持已有教师位置不变：仅填充空位，不重排
                    if len(teachers) < 2 or None in teachers:
                        # 统一将教师列表扩展到两个位置
                        while len(teachers) < 2:
                            teachers.append(None)

                        # 找到空位索引
                        missing_indices = [i for i, t in enumerate(teachers) if t is None]

                        # 获取科目时长
                        subject_durations = self.get_constraint('subject_durations', [])
                        duration = subject_durations[exam.subject_id - 1] if (exam.subject_id - 1) < len(subject_durations) else 0

                        if len(missing_indices) == 2:
                            # 两个位置都为空，选择一对教师并直接放入
                            pair = self._select_teachers_pair(exam.subject_id, [], room)
                            if pair:
                                exam.schedule[room] = pair
                                for t in pair:
                                    if t:
                                        t.assign((exam.subject_id, room), duration)
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
                            # 仅有一个空位，选择与现有教师匹配的另一位，并保持现有教师原位置不动
                            missing_idx = missing_indices[0]
                            other_idx = 1 - missing_idx
                            existing_teacher = teachers[other_idx]

                            # 如果另一位置也为None（理论上不会到这里），回退到选择一对
                            if existing_teacher is None:
                                pair = self._select_teachers_pair(exam.subject_id, [], room)
                                if pair:
                                    exam.schedule[room] = pair
                                    for t in pair:
                                        if t:
                                            t.assign((exam.subject_id, room), duration)
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
                                pair = self._select_teachers_pair(exam.subject_id, [existing_teacher], room)
                                if pair:
                                    # 从返回的配对中提取新教师（非existing_teacher）
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
            self.rebalance_double_roles_postprocess()
        except Exception:
            pass

        return True, "安排完成"
    def _select_teacher(self, subject_id, room=None):
        """
        选择单个教师（单教师监考模式）
        """
        # 筛选可用教师（增加对同一科目不能重复监考的检查）
        available_teachers = [
            t for t in self.teachers 
            if t.can_supervise(subject_id)
            and t.is_available()
            and not t.is_assigned_to_subject(subject_id)
            and (t.preset_room is None or (room is not None and t.preset_room == room))
        ]

        if not available_teachers:
            return None

        # 根据均衡模式选择教师
        balance_mode = self.get_constraint('balance_mode', 'session')
        if balance_mode == 'session':
            # 按已分配次数排序，优先选择次数较少的教师
            min_count = min(t.assigned_count() for t in available_teachers)
            candidates = [t for t in available_teachers if t.assigned_count() == min_count]
            # 去除随机性：在并列候选中按当前时长与已分配次数稳定排序
            candidates.sort(key=lambda t: (t.supervision_duration, t.assigned_count()))
            return candidates[0]
        else:  # duration
            # 使用“目标缺口优先”策略：优先选择当前与目标差距最大的教师，避免两极化
            # 缺口 = max(目标 - 当前时长, 0)，并用目标归一化保证不同最大段数的教师公平比较
            targets = self._compute_targets()
            def deficit_ratio(t):
                target = max(targets.get(t, 0), 1e-9)
                current_total = (t.supervision_duration or 0) + (t.previous_supervision_duration or 0)
                deficit = max(target - current_total, 0.0)
                return deficit / target
            # 选择缺口占比最大的教师；并在并列时优先当前总时长更少、已分配次数更少者
            available_teachers.sort(key=lambda t: (-deficit_ratio(t), (t.supervision_duration or 0) + (t.previous_supervision_duration or 0), t.assigned_count()))
            return available_teachers[0]

    def _select_teachers_pair(self, subject_id, existing_teachers, room=None):
        """
        选择教师对（双教师监考模式）
        支持在现有安排基础上继续安排
        """
        # 筛选可用教师（对同一科目不能重复监考，且名额>已分配）
        def has_quota(t):
            try:
                cap = int(t.max_sessions) if t.max_sessions is not None else 0
            except Exception:
                cap = 0
            return cap > len(t.assigned_sessions)

        available_teachers = [
            t for t in self.teachers
            if t.can_supervise(subject_id)
            and has_quota(t)
            and not t.is_assigned_to_subject(subject_id)
            and (t.preset_room is None or (room is not None and t.preset_room == room))
        ]

        # 获取均衡模式
        balance_mode = self.get_constraint('balance_mode', 'session')

        # 如果已经有一个教师，只需要再选一个
        if len(existing_teachers) == 1 and existing_teachers[0]:
            existing_teacher = existing_teachers[0]
            # 若现有教师有预设房间且不匹配当前房间，则无法在该房间补充另一位
            if existing_teacher and existing_teacher.preset_room is not None and room is not None and existing_teacher.preset_room != room:
                return None
            # 查找与现有教师搭配的教师
            valid_teachers = [
                teacher for teacher in available_teachers
                if teacher != existing_teacher and self.is_valid_pair(existing_teacher, teacher)
            ]

            if not valid_teachers:
                return None

            # 根据均衡模式排序
            if balance_mode == 'session':
                # 按已分配次数排序
                valid_teachers.sort(key=lambda t: t.assigned_count())
            else:  # duration
                # 使用“目标缺口优先”策略：优先缺口大的教师，减少两极化
                targets = self._compute_targets()
                def deficit_ratio(t):
                    target = max(targets.get(t, 0), 1e-9)
                    current_total = (t.supervision_duration or 0) + (t.previous_supervision_duration or 0)
                    deficit = max(target - current_total, 0.0)
                    return deficit / target
                valid_teachers.sort(key=lambda t: (-deficit_ratio(t), (t.supervision_duration or 0) + (t.previous_supervision_duration or 0), t.assigned_count()))

            # 选择排序后的第一个教师
            teacher = valid_teachers[0]

            # 如果启用了本外校搭配约束，需要确保监考员1是本校，监考员2是外校
            if self.get_constraint('internal_mix'):
                if existing_teacher.is_internal is True and teacher.is_internal is False:
                    return [existing_teacher, teacher]
                elif existing_teacher.is_internal is False and teacher.is_internal is True:
                    return [teacher, existing_teacher]
            else:
                return [existing_teacher, teacher]

        # 选择两个满足搭配要求的教师：分组剪枝 + 目标缓存 + 在线选择
        gender_mix = self.get_constraint('gender_mix', False)
        internal_mix = self.get_constraint('internal_mix', False)

        # 预先计算目标时长（duration模式仅计算一次）
        targets = self._compute_targets() if balance_mode == 'duration' else None

        def deficit_ratio(t):
            if targets is None:
                return 0.0
            target = max(targets.get(t, 0), 1e-9)
            current_total = (t.supervision_duration or 0) + (t.previous_supervision_duration or 0)
            deficit = max(target - current_total, 0.0)
            return deficit / target

        def pair_cost(t1, t2):
            if balance_mode == 'session':
                return (t1.assigned_count() + t2.assigned_count(),)
            # duration：优先缺口占比和更大（取负便于最小化），并兼顾当前总时长更低
            dr = -(deficit_ratio(t1) + deficit_ratio(t2))
            total_minutes = ((t1.supervision_duration or 0) + (t1.previous_supervision_duration or 0) +
                             (t2.supervision_duration or 0) + (t2.previous_supervision_duration or 0))
            return (dr, total_minutes)

        # 构建分组，减少无效组合
        if internal_mix and gender_mix:
            group_A_left = [t for t in available_teachers if t.is_internal is True and t.gender == 'M']
            group_A_right = [t for t in available_teachers if t.is_internal is False and t.gender == 'F']
            group_B_left = [t for t in available_teachers if t.is_internal is True and t.gender == 'F']
            group_B_right = [t for t in available_teachers if t.is_internal is False and t.gender == 'M']

            candidates = []
            for left, right in ((group_A_left, group_A_right), (group_B_left, group_B_right)):
                for t1 in left:
                    for t2 in right:
                        if not self.is_valid_pair(t1, t2):
                            continue
                        candidates.append((pair_cost(t1, t2), t1, t2))

            if candidates:
                candidates.sort(key=lambda c: c[0])
                _, t1, t2 = candidates[0]
                return [t1, t2]
            return None

        elif internal_mix:
            internals = [t for t in available_teachers if t.is_internal is True]
            externals = [t for t in available_teachers if t.is_internal is False]
            candidates = []
            for t1 in internals:
                for t2 in externals:
                    if not self.is_valid_pair(t1, t2):
                        continue
                    # 保证监考员1为本校、2为外校
                    candidates.append((pair_cost(t1, t2), t1, t2))
            if candidates:
                candidates.sort(key=lambda c: c[0])
                _, t1, t2 = candidates[0]
                return [t1, t2]
            return None

        elif gender_mix:
            males = [t for t in available_teachers if t.gender == 'M']
            females = [t for t in available_teachers if t.gender == 'F']
            candidates = []
            for t1 in males:
                for t2 in females:
                    if not self.is_valid_pair(t1, t2):
                        continue
                    candidates.append((pair_cost(t1, t2), t1, t2))
            if candidates:
                candidates.sort(key=lambda c: c[0])
                _, t1, t2 = candidates[0]
                return self._balance_double_role_order(t1, t2)
            return None

        # 无约束：保持原有完整性，选择最优组合但仍覆盖所有可能对
        candidates = []
        for i in range(len(available_teachers)):
            for j in range(i + 1, len(available_teachers)):
                t1 = available_teachers[i]
                t2 = available_teachers[j]
                if not self.is_valid_pair(t1, t2):
                    continue
                candidates.append((pair_cost(t1, t2), t1, t2))
        if candidates:
            candidates.sort(key=lambda c: c[0])
            _, t1, t2 = candidates[0]
            return self._balance_double_role_order(t1, t2)
        return None

    def swap_assignments(self, session1, session2):
        """
        交换两个场次的监考安排
        """
        # TODO: 实现监考安排交换逻辑
        pass

    def swap_teachers(self, session1_info, session2_info):
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
        
        # 查找对应的考试场次
        exam1 = None
        exam2 = None
        for exam in self.exams:
            if exam.subject_id == subject1:
                exam1 = exam
            if exam.subject_id == subject2:
                exam2 = exam
                
        if not exam1 or not exam2:
            return False, "无法找到对应的考试场次"
            
        # 检查考场是否已安排监考
        if room1 not in exam1.schedule or room2 not in exam2.schedule:
            return False, "指定考场未安排监考教师"
            
        # 获取教师对象
        teachers1 = exam1.schedule[room1]
        teachers2 = exam2.schedule[room2]
        
        # 确保教师列表长度为2，不足的用None填充
        while len(teachers1) < 2:
            teachers1.append(None)
        while len(teachers2) < 2:
            teachers2.append(None)
        
        if len(teachers1) <= teacher_index1 or len(teachers2) <= teacher_index2:
            return False, "监考教师信息不完整"
            
        # 保存原始教师
        original_teacher1 = teachers1[teacher_index1]
        original_teacher2 = teachers2[teacher_index2]

        # 尊重预设房间的交换约束（默认开启，可通过约束关闭）
        respect_preset = bool(self.get_constraint('respect_preset_on_swap', True))
        if respect_preset:
            # 教师1：若有预设房间，禁止交换到非预设房间
            if original_teacher1 and getattr(original_teacher1, 'preset_room', None) is not None:
                try:
                    pr1 = int(original_teacher1.preset_room)
                except Exception:
                    pr1 = None
                if pr1 is not None and int(room2) != pr1:
                    return False, f"教师 {original_teacher1.name} 预设房间为 {pr1}，不能交换到考场 {room2}"
            # 教师2：若有预设房间，禁止交换到非预设房间
            if original_teacher2 and getattr(original_teacher2, 'preset_room', None) is not None:
                try:
                    pr2 = int(original_teacher2.preset_room)
                except Exception:
                    pr2 = None
                if pr2 is not None and int(room1) != pr2:
                    return False, f"教师 {original_teacher2.name} 预设房间为 {pr2}，不能交换到考场 {room1}"

        # 额外校验：双教师模式下禁止同一教师同时占据监考员1和监考员2（同科目同考场的两个位置）
        if self.mode == "double":
            other_idx1 = 1 - teacher_index1
            other_idx2 = 1 - teacher_index2
            # 若将 original_teacher1 放入 exam2 的 room2 的 teacher_index2，检查另一位置是否已是同一教师
            if original_teacher1 is not None:
                other_teacher_in_room2 = teachers2[other_idx2] if len(teachers2) > other_idx2 else None
                if other_teacher_in_room2 is not None and other_teacher_in_room2 == original_teacher1 and (subject1 != subject2 or room1 != room2 or teacher_index1 != other_idx2):
                    return False, f"教师 {original_teacher1.name} 已在科目{subject2}考场{room2}担任另一位置，禁止同场重复担任监考员1和2"
            # 若将 original_teacher2 放入 exam1 的 room1 的 teacher_index1，检查另一位置是否已是同一教师
            if original_teacher2 is not None:
                other_teacher_in_room1 = teachers1[other_idx1] if len(teachers1) > other_idx1 else None
                if other_teacher_in_room1 is not None and other_teacher_in_room1 == original_teacher2 and (subject1 != subject2 or room1 != room2 or teacher_index2 != other_idx1):
                    return False, f"教师 {original_teacher2.name} 已在科目{subject1}考场{room1}担任另一位置，禁止同场重复担任监考员1和2"
        
        # 检查教师是否可以监考交换后的科目
        if subject1 != subject2:  # 只有在科目不同的情况下才需要检查
            # 检查教师1是否可以监考科目2
            if original_teacher1 and not original_teacher1.can_supervise(subject2):
                return False, f"教师 {original_teacher1.name} 无法监考科目 {subject2}"
            
            # 检查教师2是否可以监考科目1
            if original_teacher2 and not original_teacher2.can_supervise(subject1):
                return False, f"教师 {original_teacher2.name} 无法监考科目 {subject1}"
                
            # 检查教师是否已经在目标科目监考（避免同一科目重复监考）
            if original_teacher1 and original_teacher1.is_assigned_to_subject(subject2):
                # 如果教师1已经在科目2监考，但不是在当前要交换的房间，则不允许
                already_assigned = False
                for session in original_teacher1.assigned_sessions:
                    if session[0] == subject2 and session[1] != room2:
                        already_assigned = True
                        break
                if already_assigned:
                    return False, f"教师 {original_teacher1.name} 已经在科目 {subject2} 中监考其他考场"
                        
            if original_teacher2 and original_teacher2.is_assigned_to_subject(subject1):
                # 如果教师2已经在科目1监考，但不是在当前要交换的房间，则不允许
                already_assigned = False
                for session in original_teacher2.assigned_sessions:
                    if session[0] == subject1 and session[1] != room1:
                        already_assigned = True
                        break
                if already_assigned:
                    return False, f"教师 {original_teacher2.name} 已经在科目 {subject1} 中监考其他考场"
        else:
            # 如果是同一科目，则只需要检查不监考科目限制
            if original_teacher1 and not original_teacher1.can_supervise(subject2):
                return False, f"教师 {original_teacher1.name} 无法监考科目 {subject2}"
                
            if original_teacher2 and not original_teacher2.can_supervise(subject1):
                return False, f"教师 {original_teacher2.name} 无法监考科目 {subject1}"
            
        # 检查教师名额是否足够
        if subject1 != subject2:
            # 对于不同科目间的交换，需要检查教师是否已经在目标科目监考
            # 如果教师1已经在目标科目监考其他场次，则不允许交换
            if original_teacher1:
                for session in original_teacher1.assigned_sessions:
                    if session[0] == subject2 and session[1] != room2:
                        return False, f"教师 {original_teacher1.name} 已经在科目 {subject2} 中监考其他考场"
            
            # 如果教师2已经在目标科目监考其他场次，则不允许交换
            if original_teacher2:
                for session in original_teacher2.assigned_sessions:
                    if session[0] == subject1 and session[1] != room1:
                        return False, f"教师 {original_teacher2.name} 已经在科目 {subject1} 中监考其他考场"
            
        # 如果是双教师模式，需要检查交换是否违反搭配约束
        if self.mode == "double":
            # 获取同一考场的另一位教师
            other_teacher1 = teachers1[1 - teacher_index1] if len(teachers1) > 1 else None
            other_teacher2 = teachers2[1 - teacher_index2] if len(teachers2) > 1 else None
            
            # 检查交换后是否违反性别搭配约束
            if self.get_constraint('gender_mix'):
                # 检查教师1与对方考场另一位教师的性别搭配
                if other_teacher2 and original_teacher1 and \
                   other_teacher2.gender and original_teacher1.gender and \
                   other_teacher2.gender == original_teacher1.gender:
                    return False, f"教师 {original_teacher1.name} 与考场{room2}的另一位教师性别不匹配"
                
                # 检查教师2与对方考场另一位教师的性别搭配
                if other_teacher1 and original_teacher2 and \
                   other_teacher1.gender and original_teacher2.gender and \
                   other_teacher1.gender == original_teacher2.gender:
                    return False, f"教师 {original_teacher2.name} 与考场{room1}的另一位教师性别不匹配"
            
            # 检查交换后是否违反本外校搭配约束
            if self.get_constraint('internal_mix'):
                # 检查教师1与对方考场另一位教师的本外校搭配
                if other_teacher2 and original_teacher1 and \
                   other_teacher2.is_internal is not None and original_teacher1.is_internal is not None and \
                   other_teacher2.is_internal == original_teacher1.is_internal:
                    return False, f"教师 {original_teacher1.name} 与考场{room2}的另一位教师本外校属性不匹配"
                
                # 检查教师2与对方考场另一位教师的本外校搭配
                if other_teacher1 and original_teacher2 and \
                   other_teacher1.is_internal is not None and original_teacher2.is_internal is not None and \
                   other_teacher1.is_internal == original_teacher2.is_internal:
                    return False, f"教师 {original_teacher2.name} 与考场{room1}的另一位教师本外校属性不匹配"
                
                # 检查本外校顺序约束（监考员1必须是本校，监考员2必须是外校）
                # 如果交换的是监考员1的位置
                if teacher_index1 == 0 and original_teacher1 and original_teacher1.is_internal is False:
                    # 原来的监考员1是外校，但应该为本校
                    return False, f"教师 {original_teacher1.name} 是外校教师，不能作为监考员1"
                
                if teacher_index1 == 1 and original_teacher1 and original_teacher1.is_internal is True:
                    # 原来的监考员2是本校，但应该为外校
                    return False, f"教师 {original_teacher1.name} 是本校教师，不能作为监考员2"
                
                # 如果交换的是监考员2的位置
                if teacher_index2 == 0 and original_teacher2 and original_teacher2.is_internal is False:
                    # 原来的监考员1是外校，但应该为本校
                    return False, f"教师 {original_teacher2.name} 是外校教师，不能作为监考员1"
                
                if teacher_index2 == 1 and original_teacher2 and original_teacher2.is_internal is True:
                    # 原来的监考员2是本校，但应该为外校
                    return False, f"教师 {original_teacher2.name} 是本校教师，不能作为监考员2"
        
        # 执行交换
        # 先从原科目中取消分配
        if original_teacher1:
            # 获取原科目时长
            subject_durations = self.get_constraint('subject_durations', [])
            duration1 = subject_durations[subject1 - 1] if (subject1 - 1) < len(subject_durations) else 0
            original_teacher1.unassign((subject1, room1), duration1)
        if original_teacher2:
            # 获取原科目时长
            subject_durations = self.get_constraint('subject_durations', [])
            duration2 = subject_durations[subject2 - 1] if (subject2 - 1) < len(subject_durations) else 0
            original_teacher2.unassign((subject2, room2), duration2)
        
        # 更新监考安排
        exam1.schedule[room1][teacher_index1] = original_teacher2
        exam2.schedule[room2][teacher_index2] = original_teacher1
        
        # 分配到新科目
        if original_teacher1:
            # 获取科目时长
            subject_durations = self.get_constraint('subject_durations', [])
            duration = subject_durations[subject2 - 1] if (subject2 - 1) < len(subject_durations) else 0
            original_teacher1.assign((subject2, room2), duration)
        if original_teacher2:
            # 获取科目时长
              subject_durations = self.get_constraint('subject_durations', [])
              duration = subject_durations[subject1 - 1] if (subject1 - 1) < len(subject_durations) else 0
              original_teacher2.assign((subject1, room1), duration)
        
        return True, "交换成功"

    def _find_teacher_index(self, subject_id, room, teacher):
        """
        查找指定教师在某科目某考场的索引位置（单/双教师模式）
        返回: 0/1 或 None
        """
        exam = next((e for e in self.exams if e.subject_id == subject_id), None)
        if not exam:
            return None
        teachers = exam.schedule.get(room, [])
        # 单教师模式：索引通常为0；双教师模式：可能为0或1
        for idx, t in enumerate(teachers):
            if t == teacher:
                return idx
        return None

    def optimize_duration_postprocess(self, max_passes=5, enable_smoothing=True, smoothing_passes=20):
        """
        后处理均衡（两阶段）
        - 第一阶段：重载优先（压低峰值：先总时长，再本次时长）
        - 第二阶段：轻载平滑（在不提升峰值前提下降低方差）

        Returns:
            dict: 优化报告，包含交换次数、前后最大总时长/本次时长、交换记录
        """
        progress_cb = self.get_constraint('progress_callback', None)
        log_swaps = bool(self.get_constraint('log_optimization_swaps', False))
        def variance(values):
            if not values:
                return 0.0
            mean = sum(values) / len(values)
            return sum((v - mean) ** 2 for v in values) / len(values)
        def current_minutes(t):
            return (t.supervision_duration or 0)
        def overall_minutes(t):
            return (t.supervision_duration or 0) + (t.previous_supervision_duration or 0)

        def snapshot_metrics():
            cur = [current_minutes(t) for t in self.teachers]
            ov = [overall_minutes(t) for t in self.teachers]
            return {
                'max_current': max(cur) if cur else 0,
                'max_overall': max(ov) if ov else 0,
                'var_current': variance(cur),
                'var_overall': variance(ov),
            }

        report = {
            'swaps': [],
            'before': snapshot_metrics(),
        }
        total_steps = max_passes + (smoothing_passes if enable_smoothing else 0)
        if callable(progress_cb):
            try:
                progress_cb(f"计划轮次 {total_steps}", 0)
            except Exception:
                pass
        # 初始基线日志输出（中文）
        try:
            if log_swaps:
                logger.info(
                    f"[二次均衡] 初始指标：最大总时长={report['before']['max_overall']}, "
                    f"最大本次时长={report['before']['max_current']}, "
                    f"总时长方差={report['before']['var_overall']:.4f}, "
                    f"本次时长方差={report['before']['var_current']:.4f}"
                )
        except Exception:
            pass

        # 第一阶段：重载优先（steepest descent）
        patience = int(self.get_constraint('early_stop_patience', 5))
        no_improve_count = 0
        last_swap_sig = None  # 回滚保护：避免立即反向交换
        pass_idx = 0
        for _ in range(max_passes):
            pass_idx += 1
            teachers_desc = sorted(self.teachers, key=lambda t: overall_minutes(t), reverse=True)
            teachers_asc = sorted(self.teachers, key=lambda t: overall_minutes(t))
            before = snapshot_metrics()
            variance_weight = float(self.get_constraint('variance_weight', 1.5))
            if callable(progress_cb):
                try:
                    progress_cb("均衡优化中：", int(100 * (pass_idx-1) / max_passes) if total_steps == max_passes else int(100 * (pass_idx-1) / total_steps))
                except Exception:
                    pass

            candidates = []  # 收集所有满足约束的候选交换
            for heavy in teachers_desc:
                heavy_overall = overall_minutes(heavy)
                heavy_current = current_minutes(heavy)
                if not heavy.assigned_sessions:
                    continue
                for (sub1, room1) in list(heavy.assigned_sessions):
                    idx1 = self._find_teacher_index(sub1, room1, heavy)
                    if idx1 is None:
                        continue
                    if self.get_constraint('lock_imported') and self.is_position_imported(sub1, room1, idx1):
                        continue
                    d1 = self._get_subject_duration(sub1)

                    for light in teachers_asc:
                        if light is heavy:
                            continue
                        if not light.assigned_sessions:
                            continue
                        light_overall = overall_minutes(light)
                        if light_overall >= heavy_overall:
                            continue
                        for (sub2, room2) in list(light.assigned_sessions):
                            idx2 = self._find_teacher_index(sub2, room2, light)
                            if idx2 is None:
                                continue
                            if self.get_constraint('lock_imported') and self.is_position_imported(sub2, room2, idx2):
                                continue
                            d2 = self._get_subject_duration(sub2)
                            if d2 >= d1:
                                continue

                            # 预估交换后的两人总时长
                            heavy_overall_after = heavy_overall - d1 + d2
                            light_overall_after = light_overall - d2 + d1

                            # 计算交换后的全局最大总时长/本次时长
                            others_overall = [overall_minutes(t) for t in self.teachers if t not in (heavy, light)]
                            after_max_overall = max([heavy_overall_after, light_overall_after] + others_overall) if others_overall else max(heavy_overall_after, light_overall_after)

                            heavy_current_after = heavy_current - d1 + d2
                            light_current = current_minutes(light)
                            light_current_after = light_current - d2 + d1
                            others_current = [current_minutes(t) for t in self.teachers if t not in (heavy, light)]
                            after_max_current = max([heavy_current_after, light_current_after] + others_current) if others_current else max(heavy_current_after, light_current_after)

                            # 硬约束：不允许提升“本次时长最大值”
                            if after_max_current > before['max_current']:
                                continue
                            # 接受条件：降低总最大值，或总最大值不变且本次最大值不升
                            if not (after_max_overall < before['max_overall'] or (after_max_overall == before['max_overall'] and after_max_current <= before['max_current'])):
                                continue

                            # 计算交换后的方差，用作次级排序依据
                            cur_after = [heavy_current_after, light_current_after] + [current_minutes(t) for t in self.teachers if t not in (heavy, light)]
                            ov_after = [heavy_overall_after, light_overall_after] + [overall_minutes(t) for t in self.teachers if t not in (heavy, light)]
                            var_cur_after = variance(cur_after)
                            var_ov_after = variance(ov_after)
                            var_score = var_ov_after + variance_weight * var_cur_after

                            candidates.append({
                                'score': (after_max_overall, after_max_current, var_score),
                                'swap': ((sub1, room1, idx1), (sub2, room2, idx2)),
                                'from': {'subject': sub1, 'room': room1, 'duration': d1},
                                'to': {'subject': sub2, 'room': room2, 'duration': d2},
                                'heavy': heavy.name,
                                'light': light.name,
                            })

            # 选择“最佳改进”并尝试执行
            if not candidates:
                if callable(progress_cb):
                    try:
                        progress_cb(f"第 {pass_idx} 轮：无可行候选，提前结束", int(100 * (max_passes if total_steps == max_passes else pass_idx) / total_steps))
                    except Exception:
                        pass
                break

            candidates.sort(key=lambda c: c['score'])
            applied = False
            for cand in candidates:
                # 避免与上一轮刚执行的交换反向重复（防回滚抖动）
                try:
                    if last_swap_sig and set(cand['swap']) == set(last_swap_sig):
                        continue
                except Exception:
                    pass
                (s1, s2) = cand['swap']
                ok, msg = self.swap_teachers(s1, s2)
                if ok:
                    # 每次交换后，记录并输出当前指标
                    post = snapshot_metrics()
                    # 严格改进：最大总时长下降，或在最大总时长不变时最大本次时长下降
                    improved_strict = (post['max_overall'] < before['max_overall']) or (
                        post['max_overall'] == before['max_overall'] and post['max_current'] < before['max_current']
                    )
                    # 方差改进（不计入耐心值）
                    eps = float(self.get_constraint('variance_improve_epsilon', 0.5))
                    improved_variance = (post['var_overall'] < before['var_overall'] - eps) or (
                        post['var_current'] < before['var_current'] - eps
                    )
                    improved = improved_strict or improved_variance
                    try:
                        if log_swaps:
                            logger.info(
                                f"[二次均衡] 交换{len(report['swaps']) + 1}：最大总时长={post['max_overall']}, "
                                f"最大本次时长={post['max_current']}, "
                                f"总时长方差={post['var_overall']:.4f}, "
                                f"本次时长方差={post['var_current']:.4f}; "
                                f"重载教师={cand['heavy']} 的科目{cand['from']['subject']}考场{cand['from']['room']}({cand['from']['duration']}分钟) ? "
                                f"轻载教师={cand['light']} 的科目{cand['to']['subject']}考场{cand['to']['room']}({cand['to']['duration']}分钟)"
                            )
                    except Exception:
                        pass
                    report['swaps'].append({
                        'index': len(report['swaps']) + 1,
                        'heavy': cand['heavy'],
                        'light': cand['light'],
                        'from': cand['from'],
                        'to': cand['to'],
                        'note': 'steepest: 优先 max_overall↓；其次 max_current↓；再次 variance↓（不提升本次峰值）',
                        'max_overall': post['max_overall'],
                        'max_current': post['max_current'],
                        'var_overall': post['var_overall'],
                        'var_current': post['var_current'],
                        'improved': improved,
                    })
                    # 更新无改进计数与回滚签名
                    if improved:
                        no_improve_count = 0
                    else:
                        no_improve_count += 1
                    last_swap_sig = (s1, s2)
                    applied = True
                    break
            if not applied:
                if callable(progress_cb):
                    try:
                        progress_cb(f"第 {pass_idx} 轮：未应用交换，提前结束", int(100 * (max_passes if total_steps == max_passes else pass_idx) / total_steps))
                    except Exception:
                        pass
                break
            # 提前终止：连续若干次交换无改进（峰值与方差均无下降），判定为均衡瓶颈
            if no_improve_count >= patience:
                reason = f"连续{no_improve_count}次交换未降低最大总时长或最大本次时长，且方差也未改善（判定为当前算法均衡瓶颈）"
                prev = report.get('early_stop_reason')
                report['early_stop_reason'] = f"{prev}; {reason}" if prev else reason
                try:
                    if log_swaps:
                        logger.info(f"[二次均衡] 提前结束：{reason}")
                except Exception:
                    pass
                break

        # 第二阶段：轻载平滑（不提升峰值，优先降低方差）
        if enable_smoothing and smoothing_passes > 0:
            variance_weight = float(self.get_constraint('variance_weight', 1.5))
            eps = float(self.get_constraint('variance_improve_epsilon', 0.5))
            smooth_patience = int(self.get_constraint('smoothing_patience', 5))
            no_var_improve_count = 0
            # 阶段开始提示
            try:
                if log_swaps:
                    logger.info(f"[方差平滑] 阶段开始：预计轮次={smoothing_passes}，遵循不提升峰值约束")
            except Exception:
                pass
            for sp in range(smoothing_passes):
                # 进度（总步数 = 第一阶段 + 第二阶段）
                if callable(progress_cb):
                    try:
                        progress_cb("均衡优化中：", int(100 * (max_passes + sp) / total_steps))
                    except Exception:
                        pass
                baseline = snapshot_metrics()
                base_score = baseline['var_overall'] + variance_weight * baseline['var_current']

                candidates = []
                teachers_asc = sorted(self.teachers, key=lambda t: overall_minutes(t))
                for light in teachers_asc:
                    if not light.assigned_sessions:
                        continue
                    light_overall = overall_minutes(light)
                    light_current = current_minutes(light)
                    for (sub2, room2) in list(light.assigned_sessions):
                        idx2 = self._find_teacher_index(sub2, room2, light)
                        if idx2 is None:
                            continue
                        if self.get_constraint('lock_imported') and self.is_position_imported(sub2, room2, idx2):
                            continue
                        d2 = self._get_subject_duration(sub2)

                        for mid in self.teachers:
                            if mid is light:
                                continue
                            if not mid.assigned_sessions:
                                continue
                            mid_overall = overall_minutes(mid)
                            if mid_overall <= light_overall:
                                continue
                            mid_current = current_minutes(mid)
                            for (sub1, room1) in list(mid.assigned_sessions):
                                idx1 = self._find_teacher_index(sub1, room1, mid)
                                if idx1 is None:
                                    continue
                                if self.get_constraint('lock_imported') and self.is_position_imported(sub1, room1, idx1):
                                    continue
                                d1 = self._get_subject_duration(sub1)
                                if d1 <= d2:
                                    continue

                                # 交换后的个人与全局指标
                                mid_overall_after = mid_overall - d1 + d2
                                light_overall_after = light_overall - d2 + d1
                                mid_current_after = mid_current - d1 + d2
                                light_current_after = light_current - d2 + d1
                                others_overall = [overall_minutes(t) for t in self.teachers if t not in (mid, light)]
                                after_max_overall = max([mid_overall_after, light_overall_after] + others_overall) if others_overall else max(mid_overall_after, light_overall_after)
                                others_current = [current_minutes(t) for t in self.teachers if t not in (mid, light)]
                                after_max_current = max([mid_current_after, light_current_after] + others_current) if others_current else max(mid_current_after, light_current_after)

                                # 硬约束：不提升峰值（相对于平滑阶段进入时的基线）
                                if after_max_overall > baseline['max_overall']:
                                    continue
                                if after_max_current > baseline['max_current']:
                                    continue

                                cur_after = [mid_current_after, light_current_after] + [current_minutes(t) for t in self.teachers if t not in (mid, light)]
                                ov_after = [mid_overall_after, light_overall_after] + [overall_minutes(t) for t in self.teachers if t not in (mid, light)]
                                var_cur_after = variance(cur_after)
                                var_ov_after = variance(ov_after)
                                var_score = var_ov_after + variance_weight * var_cur_after
                                if var_score >= base_score - eps:
                                    continue

                                candidates.append({
                                    'score': var_score,
                                    'swap': ((sub1, room1, idx1), (sub2, room2, idx2)),
                                    'from': {'subject': sub1, 'room': room1, 'duration': d1},
                                    'to': {'subject': sub2, 'room': room2, 'duration': d2},
                                    'heavy': mid.name,
                                    'light': light.name,
                                })

                if not candidates:
                    reason = "轻载平滑阶段：无可行候选，提前结束"
                    prev = report.get('early_stop_reason')
                    report['early_stop_reason'] = f"{prev}; {reason}" if prev else reason
                    try:
                        if log_swaps:
                            logger.info(f"[方差平滑] 提前结束：{reason}")
                    except Exception:
                        pass
                    break

                candidates.sort(key=lambda c: c['score'])
                applied = False
                for cand in candidates:
                    (s1, s2) = cand['swap']
                    ok, msg = self.swap_teachers(s1, s2)
                    if ok:
                        post = snapshot_metrics()
                        try:
                            if log_swaps:
                                logger.info(
                                    f"[方差平滑] 交换{len(report['swaps']) + 1}：最大总时长={post['max_overall']}, "
                                    f"最大本次时长={post['max_current']}, "
                                    f"总时长方差={post['var_overall']:.4f}, "
                                    f"本次时长方差={post['var_current']:.4f}; "
                                    f"重载教师={cand['heavy']} 的科目{cand['from']['subject']}考场{cand['from']['room']}({cand['from']['duration']}分钟) ? "
                                    f"轻载教师={cand['light']} 的科目{cand['to']['subject']}考场{cand['to']['room']}({cand['to']['duration']}分钟)"
                                )
                        except Exception:
                            pass
                        report['swaps'].append({
                            'index': len(report['swaps']) + 1,
                            'heavy': cand['heavy'],
                            'light': cand['light'],
                            'from': cand['from'],
                            'to': cand['to'],
                            'note': 'smoothing: 方差平滑（不提升峰值）',
                            'max_overall': post['max_overall'],
                            'max_current': post['max_current'],
                            'var_overall': post['var_overall'],
                            'var_current': post['var_current'],
                            'improved': True,
                        })
                        applied = True
                        no_var_improve_count = 0
                        break
                if not applied:
                    no_var_improve_count += 1
                    if no_var_improve_count >= smooth_patience:
                        reason = f"轻载平滑阶段：连续{no_var_improve_count}次未找到方差改善，提前结束"
                        prev = report.get('early_stop_reason')
                        report['early_stop_reason'] = f"{prev}; {reason}" if prev else reason
                        try:
                            if log_swaps:
                                logger.info(f"[方差平滑] 提前结束：{reason}")
                        except Exception:
                            pass
                        break

        report['after'] = snapshot_metrics()
        if callable(progress_cb):
            try:
                progress_cb("优化完成", 100)
            except Exception:
                pass
        report['swap_count'] = len(report['swaps'])
        return report

    # 已移除：房间稳定性优化

    def enforce_preset_room_postprocess(self):
        """
        预设房间后处理修复：将已分配但未在预设房间的教师，尽量移动到其预设房间（同科目）。
        - 仅在教师有 `preset_room` 且当前房间与预设不一致时尝试修复。
        - 尊重锁定的导入位置（lock_imported），不对被标记的索引做调整。
        - 双教师模式下，尝试两个索引位置，遵循性别/本外校约束（由 swap_teachers 内部检查）。

        Returns:
            dict: { 'moves': <应用次数>, 'details': [ {subject, from_room, to_room, teacher} ... ] }
        """
        moves = 0
        details = []
        # 所需位置数
        required_slots = 2 if self.mode == 'double' else 1

        for exam in self.exams:
            subject_id = exam.subject_id
            # 确保所有房间的schedule结构存在并填充到所需长度
            for room in exam.rooms:
                if room not in exam.schedule:
                    exam.schedule[room] = []
                while len(exam.schedule[room]) < required_slots:
                    exam.schedule[room].append(None)

            # 遍历每个房间的每个教师，查找需修复的预设
            for room in exam.rooms:
                teachers = exam.schedule.get(room, [])
                # 填充到所需长度以避免索引错误
                while len(teachers) < required_slots:
                    teachers.append(None)
                for idx, t in enumerate(list(teachers)):
                    if not t:
                        continue
                    try:
                        preset = t.preset_room
                    except Exception:
                        preset = None
                    if preset is None:
                        continue
                    if preset == room:
                        continue

                    target_room = int(preset)
                    # 目标房间结构准备
                    if target_room not in exam.schedule:
                        exam.schedule[target_room] = []
                    while len(exam.schedule[target_room]) < required_slots:
                        exam.schedule[target_room].append(None)

                    # 若导入位置锁定，源或目的位置锁定则跳过
                    if self.get_constraint('lock_imported'):
                        try:
                            if self.is_position_imported(subject_id, room, idx):
                                continue
                        except Exception:
                            pass

                    # 选择目的索引（单监考仅0，双监考尝试0/1）
                    dest_indices = [0] if self.mode == 'single' else [0, 1]
                    applied = False
                    for dest_idx in dest_indices:
                        if self.get_constraint('lock_imported'):
                            try:
                                if self.is_position_imported(subject_id, target_room, dest_idx):
                                    continue
                            except Exception:
                                pass
                        # 若目标位置已有教师，且该教师的预设就是目标房间，则不要把他换走
                        dest_teacher = None
                        try:
                            dest_teacher = exam.schedule[target_room][dest_idx]
                        except Exception:
                            dest_teacher = None
                        if dest_teacher and getattr(dest_teacher, 'preset_room', None) is not None:
                            try:
                                dest_pr = int(dest_teacher.preset_room)
                            except Exception:
                                dest_pr = None
                            if dest_pr is not None and dest_pr == int(target_room):
                                continue
                        ok, msg = self.swap_teachers((subject_id, room, idx), (subject_id, target_room, dest_idx))
                        if ok:
                            moves += 1
                            details.append({
                                'subject': subject_id,
                                'from_room': room,
                                'to_room': target_room,
                                'teacher': getattr(t, 'name', '')
                            })
                            applied = True
                            break
                    # 若两个索引均无法应用，则保留原状
        return { 'moves': moves, 'details': details }

    def check_feasibility(self):
        """
        预判当前参数下是否存在可行安排（不做具体分配）。
        返回: (feasible: bool, reason: str)
        - 全局容量：检查教师总可用名额是否覆盖所需人次（单=1倍，双=2倍）。
        - 科目维度（仅双监考且启用约束时）：按性别/本外校约束计算每科目的合法配对上限，若不足以覆盖考场数则判定不可行。
        注：该预判是必要条件检查，不会误判“不可行”为“可行”。
        """
        mode = self.mode
        gender_mix = self.get_constraint('gender_mix', False)
        internal_mix = self.get_constraint('internal_mix', False)

        # 全局容量检查：总名额 >= 需求人次
        total_capacity = 0
        for t in self.teachers:
            try:
                cap = int(t.max_sessions) if t.max_sessions is not None else 0
            except Exception:
                cap = 0
            total_capacity += max(0, cap)

        required_total = self.num_subjects * self.num_rooms * (2 if mode == 'double' else 1)
        if total_capacity < required_total:
            return False, f"全局监考名额不足：需要 {required_total} 人次，只有 {total_capacity} 人次。"

        # 单监考不需要进一步的配对约束检查
        if mode == 'single':
            return True, "可行"

        # 双监考下，如未启用性别/本外约束，则不做科目配对上限判断（交由算法处理）
        if not gender_mix and not internal_mix:
            return True, "可行"

        # 科目维度的配对上限检查（必要条件）
        for subject_id in range(1, self.num_subjects + 1):
            # 仅统计对该科目“可监考且至少有1个名额”的教师
            candidates = []
            for t in self.teachers:
                try:
                    cap = int(t.max_sessions) if t.max_sessions is not None else 0
                except Exception:
                    cap = 0
                if cap > 0 and t.can_supervise(subject_id):
                    candidates.append(t)

            if not candidates:
                return False, f"科目{subject_id}没有任何可用教师。"

            if internal_mix and gender_mix:
                im = sum(1 for t in candidates if t.is_internal is True and t.gender == 'M')
                if_ = sum(1 for t in candidates if t.is_internal is True and t.gender == 'F')
                em = sum(1 for t in candidates if t.is_internal is False and t.gender == 'M')
                ef = sum(1 for t in candidates if t.is_internal is False and t.gender == 'F')
                pair_cap = min(im, ef) + min(if_, em)
                if pair_cap < self.num_rooms:
                    return False, (
                        f"科目{subject_id}在‘性别+本外校’约束下，合法配对最多 {pair_cap} 对，"
                        f"不足以覆盖 {self.num_rooms} 个考场。"
                    )
            elif internal_mix:
                internal_count = sum(1 for t in candidates if t.is_internal is True)
                external_count = sum(1 for t in candidates if t.is_internal is False)
                pair_cap = min(internal_count, external_count)
                if pair_cap < self.num_rooms:
                    return False, (
                        f"科目{subject_id}在‘本外校搭配’约束下，合法配对最多 {pair_cap} 对，"
                        f"不足以覆盖 {self.num_rooms} 个考场。"
                    )
            elif gender_mix:
                male_count = sum(1 for t in candidates if t.gender == 'M')
                female_count = sum(1 for t in candidates if t.gender == 'F')
                pair_cap = min(male_count, female_count)
                if pair_cap < self.num_rooms:
                    return False, (
                        f"科目{subject_id}在‘性别搭配’约束下，合法配对最多 {pair_cap} 对，"
                        f"不足以覆盖 {self.num_rooms} 个考场。"
                    )

        return True, "可行"

    def get_statistics(self):
        """
        获取监考统计信息
        """
        stats = []
        # 使用原始顺序生成统计信息，避免因shuffle导致导出顺序错乱
        teachers_to_iterate = getattr(self, 'original_teachers_order', self.teachers)
        for teacher in teachers_to_iterate:
            stats.append({
                'name': teacher.name,
                'count': teacher.assigned_count()
            })
        return stats

    def is_schedule_complete(self):
        """
        检查当前的监考安排是否完整
        对于单教师模式，检查每个考场是否至少有1位教师
        对于双教师模式，检查每个考场是否至少有2位教师
        如果所有考场都满足要求，则返回 True，否则返回 False
        """
        # 遍历所有考试和考场
        for exam in self.exams:
            for room in exam.rooms:
                # 获取当前考场的监考教师列表
                teachers = exam.schedule.get(room, [])
                
                # 根据监考模式检查教师数量
                if self.mode == "single":
                    # 单教师模式：至少需要1位教师
                    if len([t for t in teachers if t is not None]) < 1:
                        return False
                else:
                    # 双教师模式：至少需要2位教师
                    if len([t for t in teachers if t is not None]) < 2:
                        return False
        
        # 所有考场都满足要求
        return True
