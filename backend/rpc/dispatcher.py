from __future__ import annotations

from typing import Any, Callable


class RpcDispatcher:
    """RPC 调度器，管理方法注册和调度"""

    def __init__(self):
        self._handlers: dict[str, Callable[[dict], Any]] = {}

    def register(self, method: str, handler: Callable[[dict], Any]) -> None:
        """注册 RPC 方法处理器"""
        self._handlers[method] = handler

    def dispatch(self, method: str, params: dict) -> Any:
        """调度 RPC 方法调用"""
        if method not in self._handlers:
            raise ValueError(f"Unknown method: {method}")
        return self._handlers[method](params)

    def has_method(self, method: str) -> bool:
        """检查方法是否已注册"""
        return method in self._handlers

    def list_methods(self) -> list[str]:
        """列出所有已注册的方法"""
        return list(self._handlers.keys())
