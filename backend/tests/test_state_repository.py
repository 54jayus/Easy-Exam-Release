from __future__ import annotations

import json

import pandas as pd

from backend.domain.state import AppState
from backend.repository.state_repository import StateRepository


def test_state_repository_round_trip_preserves_nested_state(tmp_path) -> None:
    repo = StateRepository(str(tmp_path / "state.json"))
    state = AppState()
    state.subjects = [{"id": "1", "name": "语文"}]
    state.proctoring.teachers = [{"name": "张老师"}]
    state.proctoring.schedule = {"items": [{"subjectId": "1"}]}
    state.proctoring.config = {"mode": "double"}
    state.rooms.settings_data = [{"roomNum": "001", "roomName": "第一考场", "capacity": 30}]
    state.rooms.students_preview = [{"姓名": "张三"}]
    state.rooms.student_path = "students.xlsx"
    state.rooms.config = {"mode": "gaokao"}
    state.rooms.results = [{"姓名": "张三", "考场号": "001"}]
    state.rooms.gaokao_results = {
        "unified": pd.DataFrame([{"姓名": "张三", "语文考场号": "001"}]),
        "electives": {
            "化学": pd.DataFrame([{"姓名": "张三", "化学考场号": "005"}]),
            "政治": None,
        },
    }
    state.printing.source_type = "file"
    state.printing.data_path = "print.xlsx"
    state.printing.headers = ["姓名"]
    state.printing.mapping = {"name": "姓名"}
    state.printing.data = [{"姓名": "张三"}]
    state.printing.total = 1
    state.printing.config = {"paperSize": "A4"}
    state.printing.common_config = {"schoolName": "第一中学"}

    repo.save(state)

    loaded = AppState()
    repo.load(loaded)

    assert loaded.subjects == state.subjects
    assert loaded.proctoring.teachers == state.proctoring.teachers
    assert loaded.proctoring.schedule == state.proctoring.schedule
    assert loaded.proctoring.config == state.proctoring.config
    assert loaded.rooms.settings_data == state.rooms.settings_data
    assert loaded.rooms.students_preview == state.rooms.students_preview
    assert loaded.rooms.student_path == "students.xlsx"
    assert loaded.rooms.config == {"mode": "gaokao"}
    assert loaded.rooms.results == state.rooms.results
    assert loaded.rooms.gaokao_results["unified"].to_dict("records") == [{"姓名": "张三", "语文考场号": "001"}]
    assert loaded.rooms.gaokao_results["electives"]["化学"].to_dict("records") == [{"姓名": "张三", "化学考场号": "005"}]
    assert loaded.rooms.gaokao_results["electives"]["政治"] is None
    assert loaded.printing.source_type == "file"
    assert loaded.printing.data_path == "print.xlsx"
    assert loaded.printing.headers == ["姓名"]
    assert loaded.printing.mapping == {"name": "姓名"}
    assert loaded.printing.data == [{"姓名": "张三"}]
    assert loaded.printing.total == 1
    assert loaded.printing.config == {"paperSize": "A4"}
    assert loaded.printing.common_config == {"schoolName": "第一中学"}


def test_state_repository_creates_backup_on_second_save(tmp_path) -> None:
    repo = StateRepository(str(tmp_path / "state.json"))
    state = AppState()

    repo.save(state)
    state.subjects = [{"id": "1"}]
    repo.save(state)

    backups = list((tmp_path / "backups").glob("state_*.json"))
    assert len(backups) == 1


def test_state_repository_loads_legacy_unversioned_state(tmp_path) -> None:
    state_file = tmp_path / "state.json"
    legacy_state = {
        "subjects": [{"id": "1", "name": "语文"}],
        "proctoring": {"teachers": [{"name": "张老师"}], "schedule": None, "config": {"mode": "single"}},
        "rooms": {
            "settings": [{"roomNum": "001", "roomName": "第一考场", "capacity": 30}],
            "config": {"mode": "normal"},
            "student_path": "legacy.xlsx",
            "results": [{"姓名": "张三"}],
            "students_preview": [{"姓名": "张三"}],
            "gaokao_results": {
                "unified": [{"姓名": "张三", "语文考场号": "001"}],
                "electives": {"化学": [{"姓名": "张三", "化学考场号": "005"}]},
            },
        },
        "printing": {"sourceType": "empty"},
    }
    state_file.write_text(json.dumps(legacy_state, ensure_ascii=False), encoding="utf-8")

    loaded = AppState()
    StateRepository(str(state_file)).load(loaded)

    assert loaded.subjects == [{"id": "1", "name": "语文"}]
    assert loaded.rooms.student_path == "legacy.xlsx"
    assert loaded.rooms.gaokao_results["unified"].to_dict("records") == [{"姓名": "张三", "语文考场号": "001"}]
    assert loaded.rooms.gaokao_results["electives"]["化学"].to_dict("records") == [{"姓名": "张三", "化学考场号": "005"}]
