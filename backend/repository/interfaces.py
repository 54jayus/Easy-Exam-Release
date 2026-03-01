from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from backend.domain.state import AppState


class IStateRepository(ABC):
    """状态仓储接口"""

    @abstractmethod
    def save(self, state: AppState) -> None:
        """保存应用状态"""
        pass

    @abstractmethod
    def load(self, state: AppState) -> None:
        """加载应用状态"""
        pass
