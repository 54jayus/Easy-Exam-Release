from __future__ import annotations

from backend.application.update_guard import UpdateGuard


def test_update_guard_locks_when_current_version_below_min_supported() -> None:
    def fetch_json(_url: str) -> dict:
        return {
            "enabled": True,
            "version": "3.5.0",
            "minSupportedVersion": "3.4.5",
            "mandatory": True,
            "releaseDate": "2026-05-27",
            "notes": ["需要升级"],
            "url": "https://example.com/setup.exe",
        }

    guard = UpdateGuard(current_version="3.4.1", fetch_json=fetch_json)

    status = guard.refresh()

    assert status["checkSucceeded"] is True
    assert status["hasUpdate"] is True
    assert status["mandatoryDetected"] is True
    assert status["requiredVersion"] == "3.4.5"
    assert status["downloadUrl"] == "https://example.com/setup.exe"


def test_update_guard_falls_back_to_latest_version_when_manifest_is_mandatory() -> None:
    def fetch_json(_url: str) -> dict:
        return {
            "enabled": True,
            "version": "3.5.0",
            "mandatory": True,
            "url": "https://example.com/setup.exe",
        }

    guard = UpdateGuard(current_version="3.4.9", fetch_json=fetch_json)

    status = guard.refresh()

    assert status["mandatoryDetected"] is True
    assert status["requiredVersion"] == "3.5.0"
    assert status["minSupportedVersion"] == "3.5.0"


def test_update_guard_skips_lock_when_current_version_missing() -> None:
    guard = UpdateGuard(current_version="", fetch_json=lambda _url: {})

    status = guard.refresh()

    assert status["checkSucceeded"] is False
    assert status["mandatoryDetected"] is False
    assert "版本号" in status["errorMessage"]


def test_update_guard_returns_failed_check_when_feeds_unavailable() -> None:
    guard = UpdateGuard(
        current_version="3.4.1",
        fetch_json=lambda _url: (_ for _ in ()).throw(RuntimeError("network down")),
    )

    status = guard.refresh()

    assert status["checkSucceeded"] is False
    assert status["hasUpdate"] is False
    assert status["mandatoryDetected"] is False
    assert status["currentVersion"] == "3.4.1"
    assert "network down" in status["errorMessage"]
