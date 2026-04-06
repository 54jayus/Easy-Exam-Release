from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from backend.application.rooms_service import RoomsService
from backend.domain.state import AppState


def test_arrange_returns_load_error_after_persisting_input_state(monkeypatch, recording_repo) -> None:
    state = AppState()
    service = RoomsService(state, recording_repo)
    fake_arrangement = SimpleNamespace(
        arranged_students=None,
        arrangement_mode="normal_mode",
        gaokao_results=None,
        load_data=lambda: (False, "文件不存在"),
    )

    monkeypatch.setattr("backend.application.rooms_service._build_exam_arrangement", lambda *args, **kwargs: fake_arrangement)

    result = service.arrange(
        {
            "studentPath": "students.xlsx",
            "settings": [{"roomNum": "001", "roomName": "第一考场", "capacity": 30}],
            "config": {"mode": "normal"},
        }
    )

    assert result == {"error": "文件不存在"}
    assert state.rooms.student_path == "students.xlsx"
    assert state.rooms.config["gaokaoTimeSettings"]["examTimes"]["语文"]["date"] == "2024-06-07"
    assert recording_repo.save_calls == 1


def test_arrange_persists_results_and_gaokao_state(monkeypatch, recording_repo) -> None:
    state = AppState()
    arranged_students = pd.DataFrame([{"姓名": "张三", "考场号": "001"}])
    fake_arrangement = SimpleNamespace(
        arranged_students=arranged_students,
        arrangement_mode="gaokao_mode",
        gaokao_results={"unified": pd.DataFrame([{"考号": "240001"}]), "electives": {}},
        load_data=lambda: (True, "loaded"),
        arrange_exam_rooms=lambda: (True, "编排完成"),
    )
    service = RoomsService(state, recording_repo)

    monkeypatch.setattr("backend.application.rooms_service._build_exam_arrangement", lambda *args, **kwargs: fake_arrangement)

    result = service.arrange(
        {
            "studentPath": "students.xlsx",
            "settings": [{"roomNum": "001", "roomName": "第一考场", "capacity": 30}],
            "config": {"mode": "gaokao"},
        }
    )

    assert result == {"results": [{"姓名": "张三", "考场号": "001"}], "message": "编排完成"}
    assert state.exam_arrangement is fake_arrangement
    assert state.rooms.results == [{"姓名": "张三", "考场号": "001"}]
    assert state.rooms.gaokao_results is fake_arrangement.gaokao_results
    assert recording_repo.save_calls == 2
