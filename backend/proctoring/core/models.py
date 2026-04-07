#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Data model module: defines core data structures for scheduling.

import random
import logging

from backend.proctoring.core.balance import (
    balance_double_role_order,
    compute_double_role_counts,
    compute_targets,
    rebalance_double_roles_postprocess,
)
from backend.proctoring.core.entities import Exam, Teacher
from backend.proctoring.core.optimizer import optimize_duration_postprocess as run_duration_optimizer
from backend.proctoring.core.postprocess import enforce_preset_room_postprocess
from backend.proctoring.core.scheduler import continue_schedule as run_continue_schedule
from backend.proctoring.core.scheduler import generate_schedule as run_generate_schedule
from backend.proctoring.core.selectors import select_teacher, select_teachers_pair
from backend.proctoring.core.statistics import get_statistics
from backend.proctoring.core.swap import find_teacher_index, swap_teachers
from backend.proctoring.core.validators import check_feasibility, is_schedule_complete

logger = logging.getLogger(__name__)


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
        return compute_targets(self)

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
        return compute_double_role_counts(self)

    def _balance_double_role_order(self, t1, t2):
        return balance_double_role_order(self, t1, t2)

    def rebalance_double_roles_postprocess(self, max_passes=3, max_candidates=40):
        return rebalance_double_roles_postprocess(self, max_passes=max_passes, max_candidates=max_candidates)

    def generate_schedule(self):
        return run_generate_schedule(self)

    def continue_schedule(self):
        return run_continue_schedule(self)
    def _select_teacher(self, subject_id, room=None):
        return select_teacher(self, subject_id, room=room)

    def _select_teachers_pair(self, subject_id, existing_teachers, room=None):
        return select_teachers_pair(self, subject_id, existing_teachers, room=room)

    def swap_assignments(self, session1, session2):
        """
        交换两个场次的监考安排
        """
        # TODO: 实现监考安排交换逻辑
        pass

    def swap_teachers(self, session1_info, session2_info):
        return swap_teachers(self, session1_info, session2_info)

    def _find_teacher_index(self, subject_id, room, teacher):
        return find_teacher_index(self, subject_id, room, teacher)

    def optimize_duration_postprocess(self, max_passes=5, enable_smoothing=True, smoothing_passes=20):
        return run_duration_optimizer(
            self,
            max_passes=max_passes,
            enable_smoothing=enable_smoothing,
            smoothing_passes=smoothing_passes,
        )

    def enforce_preset_room_postprocess(self):
        return enforce_preset_room_postprocess(self)

    def check_feasibility(self):
        return check_feasibility(self)

    def get_statistics(self):
        return get_statistics(self)

    def is_schedule_complete(self):
        return is_schedule_complete(self)
