from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

from backend.repository.interfaces import IStateRepository
from backend.repository.state_repository import StateRepository, deserialize_state, serialize_state

if TYPE_CHECKING:
    from backend.domain.state import AppState


class InMemoryStateRepository(IStateRepository):
    """内存状态仓储（用于测试）"""

    def __init__(self):
        self._data = None

    def save(self, state: AppState) -> None:
        """保存状态到内存"""
        self._data = {
            "version": StateRepository.VERSION,
            "state": deepcopy(serialize_state(state)),
        }

    def load(self, state: AppState) -> None:
        """从内存加载状态"""
        if self._data:
            deserialize_state(deepcopy(self._data.get("state", {})), state)

    def delete(self) -> None:
        self._data = None

    def export_to(self, path: str, state: AppState) -> None:
        raise NotImplementedError("InMemoryStateRepository 不支持导出到文件")

    def import_from(self, path: str, state: AppState) -> None:
        raise NotImplementedError("InMemoryStateRepository 不支持从文件导入")
