from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from backend.domain.models import PrintingConfig


@dataclass
class ProctoringState:
    """监考状态 - 保持向后兼容，使用 dict 存储"""
    teachers: list[dict] = field(default_factory=list)
    schedule: Optional[dict] = None  # 监考编排结果
    config: dict = field(default_factory=dict)


@dataclass
class RoomsState:
    """考场状态 - 保持向后兼容，使用 dict 存储"""
    settings_data: list[dict] = field(default_factory=list)
    students_preview: list[dict] = field(default_factory=list)
    student_path: str = ""
    config: dict = field(default_factory=dict)
    results: list[dict] = field(default_factory=list)
    gaokao_results: Optional[dict] = None  # 高考模式结果（包含 unified 和 electives）


@dataclass
class AppState:
    """应用状态 - 使用领域模型"""
    subjects: list[dict] = field(default_factory=list)  # 保持 dict 以兼容现有代码
    proctoring: ProctoringState = field(default_factory=ProctoringState)
    rooms: RoomsState = field(default_factory=RoomsState)
    printing: PrintingConfig = field(default_factory=PrintingConfig)
    # exam_arrangement is a live object, not persisted directly
    exam_arrangement: Any = field(default=None, repr=False)
