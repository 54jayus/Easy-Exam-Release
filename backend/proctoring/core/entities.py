#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Core entity definitions for proctoring scheduling."""

from __future__ import annotations

EXEMPT_SLOT_ID = "__EXEMPT__"
EXEMPT_SLOT_NAME = "无需编排"
EXEMPT_SLOT_MARKER = "#无需编排"


def is_exempt_slot_value(value: object) -> bool:
    return str(value or "").strip() == EXEMPT_SLOT_MARKER


def build_exempt_slot_payload() -> dict[str, object]:
    return {
        "id": EXEMPT_SLOT_ID,
        "name": EXEMPT_SLOT_NAME,
        "isExempt": True,
    }


class Teacher:
    """Teacher entity."""

    def __init__(
        self,
        name,
        gender=None,
        is_internal=None,
        max_sessions=None,
        unavailable_subjects=None,
        previous_supervision_duration=0,
    ):
        self.name = name
        self.gender = gender
        self.is_internal = is_internal
        self.max_sessions = max_sessions
        self.unavailable_subjects = unavailable_subjects or []
        self.assigned_sessions = []
        self.supervision_duration = 0
        self.previous_supervision_duration = previous_supervision_duration or 0
        # Preset room number. ``None`` means no preset room is configured.
        self.preset_room = None

    def can_supervise(self, subject_id):
        return subject_id not in self.unavailable_subjects

    def is_available(self):
        return len(self.assigned_sessions) < self.max_sessions

    def assign(self, session, duration=0):
        if self.is_available():
            self.assigned_sessions.append(session)
            self.supervision_duration += duration
            return True
        return False

    def unassign(self, session, duration=0):
        if session in self.assigned_sessions:
            self.assigned_sessions.remove(session)
            self.supervision_duration = max(0, self.supervision_duration - duration)
            return True
        return False

    def assigned_count(self):
        return len(self.assigned_sessions)

    def is_assigned_to_subject(self, subject_id):
        for session in self.assigned_sessions:
            if session[0] == subject_id:
                return True
        return False


class Exam:
    """Exam entity."""

    def __init__(self, subject_id, rooms):
        self.subject_id = subject_id
        self.rooms = rooms
        self.schedule = {}
