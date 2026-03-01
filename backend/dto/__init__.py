"""Data Transfer Objects for RPC communication."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class SubjectDTO:
    """科目数据传输对象"""
    name: str
    exam_date: str
    exam_time: str
    remark: str = ""
    duration_minutes: int = 0
    id: Optional[str] = None  # Frontend-assigned ID


@dataclass
class TeacherDTO:
    """教师数据传输对象"""
    name: str
    gender: Optional[str] = None
    is_internal: Optional[bool] = None
    max_sessions: Optional[int] = None
    unavailable_subjects: list[str] = field(default_factory=list)
    previous_supervision_duration: int = 0


@dataclass
class RoomSettingDTO:
    """考场设置数据传输对象"""
    room_number: int
    capacity: int
    building: str = ""
    floor: str = ""
    room_type: str = "regular"


@dataclass
class StudentDTO:
    """学生数据传输对象"""
    student_id: str
    name: str
    class_name: str = ""
    subjects: list[str] = field(default_factory=list)


@dataclass
class ArrangementResultDTO:
    """考场编排结果数据传输对象"""
    room_number: int
    subject_name: str
    students: list[dict]  # Keep as dict for backward compatibility
    exam_date: str
    exam_time: str


@dataclass
class ProctoringScheduleDTO:
    """监考编排结果数据传输对象"""
    exams: list[dict]  # Keep as dict for backward compatibility
    teachers: list[dict]
    statistics: dict = field(default_factory=dict)


@dataclass
class PrintingStateDTO:
    """打印状态数据传输对象"""
    source_type: str = "empty"
    data_path: str = ""
    headers: list[str] = field(default_factory=list)
    mapping: dict[str, str] = field(default_factory=dict)
    data: list[dict] = field(default_factory=list)
    total: int = 0
    config: dict = field(default_factory=dict)
    common_config: dict = field(default_factory=dict)
    total_count: Optional[int] = None
