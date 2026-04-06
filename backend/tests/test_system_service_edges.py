from __future__ import annotations

import sys

from backend.application.system_service import SystemService
from backend.domain.state import AppState


def test_system_get_help_manual_reads_from_source_tree(recording_repo, monkeypatch) -> None:
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    service = SystemService(AppState(), recording_repo)

    result = service.get_help_manual({})

    assert "content" in result
    assert len(result["content"]) > 0


def test_system_get_help_manual_returns_error_when_file_is_missing(tmp_path, recording_repo, monkeypatch) -> None:
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    service = SystemService(AppState(), recording_repo)

    result = service.get_help_manual({})

    assert "error" in result
    assert str(tmp_path / "backend" / "resources") in result["error"]
