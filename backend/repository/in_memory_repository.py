from __future__ import annotations

from dataclasses import asdict
from typing import TYPE_CHECKING

from backend.domain.models import PrintingConfig
from backend.repository.interfaces import IStateRepository

if TYPE_CHECKING:
    from backend.domain.state import AppState


class InMemoryStateRepository(IStateRepository):
    """内存状态仓储（用于测试）"""

    def __init__(self):
        self._data = None

    def save(self, state: AppState) -> None:
        """保存状态到内存"""
        self._data = asdict(state)

    def load(self, state: AppState) -> None:
        """从内存加载状态"""
        if self._data:
            # 从字典恢复状态
            if "subjects" in self._data:
                state.subjects = self._data["subjects"]
            if "proctoring" in self._data:
                from backend.domain.state import ProctoringState
                proctoring_data = self._data["proctoring"]
                state.proctoring.teachers = proctoring_data.get("teachers", [])
                state.proctoring.schedule = proctoring_data.get("schedule", [])
                state.proctoring.config = proctoring_data.get("config", {})
            if "rooms" in self._data:
                from backend.domain.state import RoomsState
                rooms_data = self._data["rooms"]
                state.rooms.settings_data = rooms_data.get("settings_data", [])
                state.rooms.students_preview = rooms_data.get("students_preview", [])
                state.rooms.student_path = rooms_data.get("student_path", "")
                state.rooms.config = rooms_data.get("config", {})
                state.rooms.results = rooms_data.get("results", [])
                state.rooms.gaokao_results = rooms_data.get("gaokao_results", None)
            if "printing" in self._data:
                printing_data = self._data["printing"] or {}
                state.printing = PrintingConfig(
                    source_type=printing_data.get("source_type", "empty"),
                    data_path=printing_data.get("data_path", ""),
                    headers=printing_data.get("headers", []),
                    mapping=printing_data.get("mapping", {}),
                    data=printing_data.get("data", []),
                    total=printing_data.get("total", 0),
                    config=printing_data.get("config", {}),
                    common_config=printing_data.get("common_config", {}),
                )
