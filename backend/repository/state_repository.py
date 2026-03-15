from __future__ import annotations

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

from backend.domain.state import AppState, ProctoringState, RoomsState
from backend.domain.models import PrintingConfig
from backend.repository.interfaces import IStateRepository

logger = logging.getLogger(__name__)


def _json_default(obj):
    if isinstance(obj, set):
        return list(obj)
    return str(obj)


def _serialize_gaokao_results(gaokao_results):
    """将 gaokao_results 转换为可 JSON 序列化的格式"""
    if not gaokao_results:
        return None

    import pandas as pd

    result = {}

    # 序列化 unified DataFrame
    if 'unified' in gaokao_results and gaokao_results['unified'] is not None:
        unified_df = gaokao_results['unified']
        if isinstance(unified_df, pd.DataFrame) and not unified_df.empty:
            result['unified'] = unified_df.fillna("").to_dict('records')
        else:
            result['unified'] = None
    else:
        result['unified'] = None

    # 序列化 electives 字典
    if 'electives' in gaokao_results and gaokao_results['electives']:
        result['electives'] = {}
        for subject, df in gaokao_results['electives'].items():
            if df is not None and isinstance(df, pd.DataFrame) and not df.empty:
                result['electives'][subject] = df.fillna("").to_dict('records')
            else:
                result['electives'][subject] = None
    else:
        result['electives'] = {}

    return result


def _deserialize_gaokao_results(data):
    """将 JSON 数据转换回 gaokao_results 格式"""
    if not data:
        return None

    import pandas as pd

    result = {}

    # 反序列化 unified
    if data.get('unified'):
        result['unified'] = pd.DataFrame(data['unified'])
    else:
        result['unified'] = None

    # 反序列化 electives
    result['electives'] = {}
    if data.get('electives'):
        for subject, records in data['electives'].items():
            if records:
                result['electives'][subject] = pd.DataFrame(records)
            else:
                result['electives'][subject] = None

    return result


class StateRepository(IStateRepository):
    """Handles JSON persistence of AppState with versioning and backup."""

    VERSION = "1.0.0"

    def __init__(self, state_file: str):
        self._path = Path(state_file)
        self._backup_dir = self._path.parent / "backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)

    def load(self, state: AppState) -> None:
        """Load persisted data into *state* in-place. Silently ignores missing file."""
        if not self._path.exists():
            return
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error("Load state failed: %s", e)
            return

        # 检查版本
        version = data.get("version", "0.0.0")
        if version != self.VERSION:
            logger.warning("State version mismatch: %s != %s, attempting migration", version, self.VERSION)
            data = self._migrate(data, version)

        # 加载状态数据
        state_data = data.get("state", data)  # 兼容旧格式
        state.subjects = state_data.get("subjects", [])

        proc = state_data.get("proctoring", {})
        state.proctoring = ProctoringState(
            teachers=proc.get("teachers", []),
            schedule=proc.get("schedule", None),
            config=proc.get("config", {}),
        )

        rooms = state_data.get("rooms", {})
        state.rooms = RoomsState(
            settings_data=rooms.get("settings", []),
            config=rooms.get("config", {}),
            student_path=rooms.get("student_path", ""),
            results=rooms.get("results", []),
            students_preview=rooms.get("students_preview", []),
            gaokao_results=_deserialize_gaokao_results(rooms.get("gaokao_results")),
        )

        printing_data = state_data.get("printing", {})
        state.printing = PrintingConfig(
            source_type=printing_data.get("sourceType", "empty"),
            data_path=printing_data.get("dataPath", ""),
            headers=printing_data.get("headers", []),
            mapping=printing_data.get("mapping", {}),
            data=printing_data.get("data", []),
            total=printing_data.get("total", 0),
            config=printing_data.get("config", {}),
            common_config=printing_data.get("commonConfig", {}),
        )

    def save(self, state: AppState) -> None:
        """Persist *state* to disk with automatic backup."""
        try:
            # 创建备份
            if self._path.exists():
                self._create_backup()

            # 保存新状态（带版本号）
            os.makedirs(self._path.parent, exist_ok=True)
            data = {
                "version": self.VERSION,
                "state": {
                    "subjects": state.subjects,
                    "proctoring": {
                        "teachers": state.proctoring.teachers,
                        "schedule": state.proctoring.schedule,
                        "config": state.proctoring.config,
                    },
                    "rooms": {
                        "settings": state.rooms.settings_data,
                        "config": state.rooms.config,
                        "student_path": state.rooms.student_path,
                        "results": state.rooms.results,
                        "students_preview": state.rooms.students_preview,
                        "gaokao_results": _serialize_gaokao_results(state.rooms.gaokao_results),
                    },
                    "printing": {
                        "sourceType": state.printing.source_type,
                        "dataPath": state.printing.data_path,
                        "headers": state.printing.headers,
                        "mapping": state.printing.mapping,
                        "data": state.printing.data,
                        "total": state.printing.total,
                        "config": state.printing.config,
                        "commonConfig": state.printing.common_config,
                    },
                }
            }
            with open(self._path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=_json_default)
        except Exception as e:
            logger.error("Save state failed: %s", e)

    def _create_backup(self) -> None:
        """创建状态文件备份"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self._backup_dir / f"state_{timestamp}.json"
            shutil.copy2(self._path, backup_file)

            # 只保留最近 10 个备份
            backups = sorted(self._backup_dir.glob("state_*.json"))
            for old_backup in backups[:-10]:
                old_backup.unlink()
        except Exception as e:
            logger.warning("Create backup failed: %s", e)

    def _migrate(self, data: dict, from_version: str) -> dict:
        """迁移旧版本数据"""
        logger.info("Migrating state from version %s to %s", from_version, self.VERSION)

        # 如果是旧格式（没有 version 字段），包装为新格式
        if "version" not in data:
            return {
                "version": self.VERSION,
                "state": data
            }

        # 未来版本迁移逻辑在这里添加
        return data

    def delete(self) -> None:
        """Remove the persisted state file."""
        if self._path.exists():
            try:
                self._path.unlink()
            except Exception:
                pass
