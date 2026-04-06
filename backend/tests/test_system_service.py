from __future__ import annotations

import sys

from backend.application.system_service import SystemService
from backend.domain.models import PrintingConfig
from backend.domain.state import AppState


def test_system_reset_data_restores_clean_domain_state(recording_repo) -> None:
    state = AppState()
    state.subjects = [{"name": "语文"}]
    state.proctoring.schedule = {"items": [1]}
    state.rooms.results = [{"姓名": "张三"}]
    state.printing.source_type = "file"
    state.exam_arrangement = object()
    service = SystemService(state, recording_repo)

    result = service.reset_data({})

    assert result == {"success": True}
    assert state.subjects == []
    assert state.proctoring.schedule is None
    assert state.rooms.results == []
    assert isinstance(state.printing, PrintingConfig)
    assert state.printing.source_type == "empty"
    assert state.exam_arrangement is None
    assert recording_repo.delete_calls == 1


def test_system_get_help_manual_reads_from_meipass(monkeypatch, tmp_path, recording_repo) -> None:
    backend_dir = tmp_path / "backend" / "resources"
    backend_dir.mkdir(parents=True)
    manual_path = backend_dir / "使用说明书.md"
    manual_path.write_text("# Manual\n\ncontent", encoding="utf-8")

    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    service = SystemService(AppState(), recording_repo)

    result = service.get_help_manual({})

    assert result == {"content": "# Manual\n\ncontent"}
