from __future__ import annotations

import os
import sys
from typing import Any

from backend.domain.state import AppState
from backend.repository.interfaces import IStateRepository


class SystemService:
    def __init__(self, state: AppState, repo: IStateRepository):
        self._state = state
        self._repo = repo

    def reset_data(self, _params: dict) -> Any:
        from backend.domain.state import ProctoringState, RoomsState
        self._state.subjects = []
        self._state.proctoring = ProctoringState()
        self._state.rooms = RoomsState()
        self._state.printing = {
            "sourceType": "empty", "dataPath": "", "headers": [],
            "mapping": {}, "data": [], "total": 0,
        }
        self._state.exam_arrangement = None
        self._repo.delete()
        return {"success": True}

    def get_help_manual(self, _params: dict) -> Any:
        try:
            if hasattr(sys, "_MEIPASS"):
                base_dir = os.path.join(sys._MEIPASS, "backend")
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))
                # Walk up to backend/
                while base_dir and not os.path.basename(base_dir) == "backend":
                    parent = os.path.dirname(base_dir)
                    if parent == base_dir:
                        break
                    base_dir = parent

            manual_path = os.path.join(base_dir, "resources", "使用说明书.md")
            if not os.path.exists(manual_path):
                return {"error": f"未找到使用说明书文件: {manual_path}"}
            with open(manual_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"content": content}
        except Exception as e:
            return {"error": f"读取说明书失败: {str(e)}"}
