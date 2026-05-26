from __future__ import annotations

import sys

from backend.application.system_service import SystemService
from backend.domain.models import PrintingConfig
from backend.domain.state import AppState
from backend.repository.state_repository import StateRepository


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


def test_system_export_state_writes_backup_file(tmp_path) -> None:
    repo = StateRepository(str(tmp_path / "state.json"))
    state = AppState()
    state.subjects = [{"name": "高一语文"}]
    service = SystemService(state, repo)

    export_path = tmp_path / "grade1.examstate"
    result = service.export_state({"path": str(export_path)})

    assert result == {"success": True}
    assert export_path.exists() is True


def test_system_import_state_replaces_runtime_state_and_persists(tmp_path) -> None:
    repo = StateRepository(str(tmp_path / "state.json"))
    source_state = AppState()
    source_state.subjects = [{"name": "高一语文"}]
    source_state.proctoring.teachers = [{"name": "王老师"}]
    source_state.rooms.results = [{"姓名": "张三", "考场号": "001"}]
    source_state.printing.source_type = "schedule"
    export_path = tmp_path / "grade1.examstate"
    repo.export_to(str(export_path), source_state)

    current_state = AppState()
    current_state.subjects = [{"name": "高二数学"}]
    current_state.exam_arrangement = object()
    service = SystemService(current_state, repo)

    result = service.import_state({"path": str(export_path)})

    reloaded = AppState()
    repo.load(reloaded)

    assert result == {"success": True}
    assert current_state.subjects == [{"name": "高一语文"}]
    assert current_state.proctoring.teachers == [{"name": "王老师"}]
    assert current_state.rooms.results == [{"姓名": "张三", "考场号": "001"}]
    assert current_state.printing.source_type == "schedule"
    assert current_state.exam_arrangement is None
    assert reloaded.subjects == [{"name": "高一语文"}]


def test_system_import_state_failure_does_not_mutate_current_state(tmp_path) -> None:
    repo = StateRepository(str(tmp_path / "state.json"))
    bad_file = tmp_path / "bad.examstate"
    bad_file.write_text("{invalid", encoding="utf-8")
    state = AppState()
    state.subjects = [{"name": "保留方案"}]
    service = SystemService(state, repo)

    try:
        service.import_state({"path": str(bad_file)})
    except Exception:
        pass

    assert state.subjects == [{"name": "保留方案"}]
