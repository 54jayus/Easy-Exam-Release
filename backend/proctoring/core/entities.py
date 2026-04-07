#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Core entity definitions for proctoring scheduling."""


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
