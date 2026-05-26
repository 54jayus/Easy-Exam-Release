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

    @abstractmethod
    def delete(self) -> None:
        """删除持久化状态"""
        pass

    @abstractmethod
    def export_to(self, path: str, state: AppState) -> None:
        """导出当前状态到指定文件"""
        pass

    @abstractmethod
    def import_from(self, path: str, state: AppState) -> None:
        """从指定文件导入状态"""
        pass
