from __future__ import annotations

import pandas as pd

from backend.domain.models import PrintingConfig
from backend.domain.state import AppState
from backend.repository.in_memory_repository import InMemoryStateRepository


def test_in_memory_repository_round_trip_restores_nested_state() -> None:
    repo = InMemoryStateRepository()
    state = AppState()
    state.subjects = [{"name": "语文"}]
    state.proctoring.teachers = [{"name": "张老师"}]
    state.proctoring.schedule = {"items": [1]}
    state.proctoring.config = {"mode": "double"}
    state.rooms.settings_data = [{"roomNum": "001", "roomName": "第一考场", "capacity": 30}]
    state.rooms.students_preview = [{"姓名": "张三"}]
    state.rooms.student_path = "students.xlsx"
    state.rooms.config = {"mode": "gaokao"}
    state.rooms.results = [{"姓名": "张三", "考场号": "001"}]
    state.rooms.gaokao_results = {
        "unified": pd.DataFrame([{"考号": "240001"}]),
        "electives": {"化学": pd.DataFrame([{"考号": "240001", "科目类型": "化学"}])},
    }
    state.printing = PrintingConfig(source_type="file", data_path="print.xlsx", headers=["姓名"], total=1)

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
    assert loaded.rooms.gaokao_results["unified"].to_dict("records") == [{"考号": "240001"}]
    assert loaded.rooms.gaokao_results["electives"]["化学"].to_dict("records") == [{"考号": "240001", "科目类型": "化学"}]
    assert isinstance(loaded.printing, PrintingConfig)
    assert loaded.printing.source_type == "file"
    assert loaded.printing.data_path == "print.xlsx"
    assert loaded.printing.headers == ["姓名"]
    assert loaded.printing.total == 1
