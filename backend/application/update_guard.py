from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.request import Request, urlopen

from backend.domain.errors import DomainError, ErrorCode

logger = logging.getLogger(__name__)

UPDATE_FEED_URLS = (
    "https://54jayus.github.io/Easy-Exam-Release/update/win/latest.json",
    "https://raw.githubusercontent.com/54jayus/Easy-Exam-Release/main/update/win/latest.json",
)


def compare_versions(left: str, right: str) -> int:
    left_parts = [int(part or 0) for part in str(left or "").split(".")]
    right_parts = [int(part or 0) for part in str(right or "").split(".")]
    max_length = max(len(left_parts), len(right_parts))

    for index in range(max_length):
        left_value = left_parts[index] if index < len(left_parts) else 0
        right_value = right_parts[index] if index < len(right_parts) else 0
        if left_value > right_value:
            return 1
        if left_value < right_value:
            return -1
    return 0


class ForceUpdateRequiredError(DomainError):
    def __init__(self, status: dict[str, Any]):
        details = {
            "currentVersion": status.get("currentVersion") or "",
            "latestVersion": status.get("latestVersion") or "",
            "requiredVersion": status.get("requiredVersion") or "",
            "minSupportedVersion": status.get("minSupportedVersion") or "",
            "downloadUrl": status.get("downloadUrl") or "",
            "releaseDate": status.get("releaseDate") or "",
            "notes": status.get("notes") or [],
            "checkedAt": status.get("checkedAt") or "",
            "sourceUrl": status.get("sourceUrl") or "",
        }
        super().__init__(
            ErrorCode.FORCE_UPDATE_REQUIRED,
            "当前版本过低，必须升级后才能继续使用软件。",
            details,
        )


class UpdateGuard:
    def __init__(
        self,
        current_version: str | None = None,
        fetch_json: Callable[[str], dict[str, Any]] | None = None,
    ) -> None:
        self._current_version = str(
            current_version or os.environ.get("EASY_EXAM_APP_VERSION") or ""
        ).strip()
        self._fetch_json = fetch_json or self._default_fetch_json
        self._status = self._build_default_status()

    def _build_default_status(self) -> dict[str, Any]:
        return {
            "checked": False,
            "locked": False,
            "currentVersion": self._current_version,
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
            "errorMessage": "",
        }

    def get_status(self) -> dict[str, Any]:
        return dict(self._status)

    def refresh(self) -> dict[str, Any]:
        if not self._current_version:
            self._status = {
                **self._build_default_status(),
                "checked": True,
                "errorMessage": "后端未收到当前软件版本号，已跳过强制更新门禁。",
            }
            return self.get_status()

        last_error: Exception | None = None
        for feed_url in UPDATE_FEED_URLS:
            try:
                payload = self._fetch_json(feed_url)
                status = self._build_status_from_manifest(payload, feed_url)
                self._status = status
                return self.get_status()
            except Exception as error:  # noqa: BLE001
                last_error = error if isinstance(error, Exception) else Exception(str(error))
                logger.warning("更新门禁检查失败，将尝试下一个地址：%s", feed_url, exc_info=error)

        if self._status.get("locked"):
            self._status = {
                **self._status,
                "checked": True,
                "errorMessage": str(last_error) if last_error else "更新门禁检查失败",
            }
            return self.get_status()

        self._status = {
            **self._build_default_status(),
            "checked": True,
            "currentVersion": self._current_version,
            "errorMessage": str(last_error) if last_error else "更新门禁检查失败",
        }
        return self.get_status()

    def ensure_allowed(self, method: str, allowed_methods: set[str]) -> None:
        if method in allowed_methods:
            return
        if self._status.get("locked"):
            raise ForceUpdateRequiredError(self._status)

    def _build_status_from_manifest(self, payload: dict[str, Any], source_url: str) -> dict[str, Any]:
        latest_version = str(payload.get("version") or "").strip()
        mandatory = payload.get("mandatory") is True
        min_supported_version = str(payload.get("minSupportedVersion") or "").strip()
        if not min_supported_version and mandatory:
            min_supported_version = latest_version

        release_date = str(payload.get("releaseDate") or "").strip()
        notes = (
            [str(item).strip() for item in payload.get("notes", []) if str(item).strip()]
            if isinstance(payload.get("notes"), list)
            else []
        )
        download_url = str(payload.get("url") or "").strip()
        enabled = payload.get("enabled") is True
        required_version = min_supported_version or latest_version
        locked = (
            enabled
            and bool(required_version)
            and compare_versions(self._current_version, required_version) < 0
        )

        return {
            "checked": True,
            "locked": locked,
            "currentVersion": self._current_version,
            "latestVersion": latest_version,
            "requiredVersion": required_version,
            "minSupportedVersion": min_supported_version,
            "mandatory": mandatory,
            "downloadUrl": download_url,
            "releaseDate": release_date,
            "notes": notes,
            "enabled": enabled,
            "sourceUrl": source_url,
            "checkedAt": datetime.now(timezone.utc).isoformat(),
            "errorMessage": "",
        }

    @staticmethod
    def _default_fetch_json(url: str) -> dict[str, Any]:
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "Cache-Control": "no-cache",
                "User-Agent": "Easy-Exam-UpdateGuard/1.0",
            },
        )
        with urlopen(request, timeout=4) as response:  # noqa: S310
            raw = response.read().decode("utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("更新清单格式无效")
        return data
