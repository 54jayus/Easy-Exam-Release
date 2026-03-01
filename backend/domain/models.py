"""Domain models for ExamFlow system."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Teacher:
    """教师领域模型"""
    name: str
    gender: Optional[str] = None  # 'M' or 'F'
    is_internal: Optional[bool] = None
    max_sessions: Optional[int] = None
    unavailable_subjects: list[str] = field(default_factory=list)
    previous_supervision_duration: int = 0


@dataclass
class ExamSession:
    """考试场次领域模型"""
    subject_id: str
    subject_name: str
    exam_date: str
    exam_time: str
    duration_minutes: int
    room_number: int


@dataclass
class RoomSetting:
    """考场设置领域模型"""
    room_number: int
    capacity: int
    building: str = ""
    floor: str = ""
    room_type: str = "regular"  # regular, special, etc.


@dataclass
class Student:
    """学生领域模型"""
    student_id: str
    name: str
    class_name: str = ""
    subjects: list[str] = field(default_factory=list)


@dataclass
class ArrangementResult:
    """考场编排结果领域模型"""
    room_number: int
    subject_name: str
    students: list[Student]
    exam_date: str
    exam_time: str


@dataclass
class PrintingConfig:
    """打印配置领域模型"""
    source_type: str = "empty"  # empty, file, schedule
    data_path: str = ""
    headers: list[str] = field(default_factory=list)
    mapping: dict[str, str] = field(default_factory=dict)
    data: list[dict] = field(default_factory=list)
    total: int = 0
    config: dict = field(default_factory=dict)
    common_config: dict = field(default_factory=dict)
