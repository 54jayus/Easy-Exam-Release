from __future__ import annotations

import os
import sys
from typing import Any

from backend.domain.models import PrintingConfig
from backend.domain.state import AppState
from backend.repository.interfaces import IStateRepository
from .update_guard import UpdateGuard


class SystemService:
    def __init__(self, state: AppState, repo: IStateRepository, update_guard: UpdateGuard | None = None):
        self._state = state
        self._repo = repo
        self._update_guard = update_guard

    def reset_data(self, _params: dict) -> Any:
        from backend.domain.state import ProctoringState, RoomsState
        self._state.subjects = []
        self._state.proctoring = ProctoringState()
        self._state.rooms = RoomsState()
        self._state.printing = PrintingConfig()
        self._state.exam_arrangement = None
        self._repo.delete()
        return {"success": True}

    def export_state(self, params: dict) -> Any:
        path = str(params.get("path") or "").strip()
        if not path:
            raise ValueError("缺少导出路径")
        self._repo.export_to(path, self._state)
        return {"success": True}

    def import_state(self, params: dict) -> Any:
        path = str(params.get("path") or "").strip()
        if not path:
            raise ValueError("缺少导入路径")

        imported_state = AppState()
        self._repo.import_from(path, imported_state)

        self._state.subjects = imported_state.subjects
        self._state.proctoring = imported_state.proctoring
        self._state.rooms = imported_state.rooms
        self._state.printing = imported_state.printing
        self._state.exam_arrangement = None

        self._repo.save(self._state)
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

            # Read the manual file
            manual_path = os.path.join(base_dir, "resources", "使用说明书.md")

            if not os.path.exists(manual_path):
                return {"error": f"未找到使用说明书文件: {manual_path}"}
            with open(manual_path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"content": content}
        except Exception as e:
            return {"error": f"读取说明书失败: {str(e)}"}

    def get_update_guard_status(self, _params: dict) -> Any:
        if not self._update_guard:
            return {
                "checked": True,
                "locked": False,
                "currentVersion": "",
                "latestVersion": "",
                "requiredVersion": "",
                "minSupportedVersion": "",
                "mandatory": False,
                "downloadUrl": "",
                "releaseDate": "",
                "notes": [],
                "enabled": False,
                "sourceUrl": "",
                "checkedAt": "",
                "errorMessage": "更新门禁未初始化",
            }
        return self._update_guard.get_status()

    def refresh_update_guard(self, _params: dict) -> Any:
        if not self._update_guard:
            return self.get_update_guard_status({})
        return self._update_guard.refresh()
