#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Data model module: defines core data structures for scheduling.

from backend.proctoring.core.entities import Exam, Teacher
from backend.proctoring.core.statistics import get_statistics
from backend.proctoring.core.swap import find_teacher_index, swap_teachers
from backend.proctoring.core.validators import check_feasibility, is_schedule_complete


class Schedule:
    """
    监考安排类
    """

    def __init__(self, teachers, num_subjects, num_rooms, mode="single"):
        self.teachers = teachers
        self.original_teachers_order = list(teachers)
        self.num_subjects = num_subjects
        self.num_rooms = num_rooms
        self.mode = mode
        self.exams = []
        self.constraints = {}
        self.imported_positions = set()
        self.exempt_positions = set()

    def set_constraint(self, key, value):
        self.constraints[key] = value

    def get_constraint(self, key, default=False):
        return self.constraints.get(key, default)

    def mark_imported_position(self, subject_id, room, index):
        self.imported_positions.add((subject_id, room, index))

    def is_position_imported(self, subject_id, room, index):
        return (subject_id, room, index) in self.imported_positions

    def mark_exempt_position(self, subject_id, room, index):
        self.exempt_positions.add((subject_id, room, index))

    def clear_exempt_position(self, subject_id, room, index):
        self.exempt_positions.discard((subject_id, room, index))

    def is_position_exempt(self, subject_id, room, index):
        return (subject_id, room, index) in self.exempt_positions

    def get_slot_count(self):
        return 2 if self.mode == "double" else 1

    def get_slot_indexes(self, subject_id, room):
        del subject_id, room
        return list(range(self.get_slot_count()))

    def get_active_slot_indexes(self, subject_id, room):
        return [
            slot_index
            for slot_index in self.get_slot_indexes(subject_id, room)
            if not self.is_position_exempt(subject_id, room, slot_index)
        ]

    def get_exempt_slot_count(self, subject_id, room):
        return sum(
            1
            for slot_index in self.get_slot_indexes(subject_id, room)
            if self.is_position_exempt(subject_id, room, slot_index)
        )

    def get_required_assignment_count(self, subject_id, room):
        return len(self.get_active_slot_indexes(subject_id, room))

    def room_requires_pair_constraints(self, subject_id, room):
        return self.mode == "double" and len(self.get_active_slot_indexes(subject_id, room)) == 2

    def _get_subject_duration(self, subject_id):
        subject_durations = self.get_constraint("subject_durations", [])
        return subject_durations[subject_id - 1] if (subject_id - 1) < len(subject_durations) else 0

    def _get_subject_room_count(self, subject_id):
        subject_room_counts = self.get_constraint("subject_room_counts", [])
        if (subject_id - 1) < len(subject_room_counts):
            return max(0, int(subject_room_counts[subject_id - 1] or 0))
        return max(0, int(self.num_rooms or 0))

    def _get_subject_rooms(self, subject_id):
        for exam in self.exams or []:
            if int(getattr(exam, "subject_id", 0)) == int(subject_id):
                rooms = [int(room) for room in (getattr(exam, "rooms", []) or []) if int(room) > 0]
                if rooms:
                    return rooms
        room_count = self._get_subject_room_count(subject_id)
        return list(range(1, room_count + 1))

    def is_valid_pair(self, teacher1, teacher2):
        if self.get_constraint("gender_mix"):
            if not teacher1.gender or not teacher2.gender:
                return False
            if str(teacher1.gender).upper() == "M" and str(teacher2.gender).upper() == "M":
                return False

        if self.get_constraint("internal_mix"):
            if teacher1.is_internal is None or teacher2.is_internal is None:
                return False
            if teacher1.is_internal == teacher2.is_internal:
                return False

        return True

    def swap_assignments(self, session1, session2):
        pass

    def swap_teachers(self, session1_info, session2_info):
        return swap_teachers(self, session1_info, session2_info)

    def _find_teacher_index(self, subject_id, room, teacher):
        return find_teacher_index(self, subject_id, room, teacher)

    def check_feasibility(self):
        return check_feasibility(self)

    def get_statistics(self):
        return get_statistics(self)

    def is_schedule_complete(self):
        return is_schedule_complete(self)
