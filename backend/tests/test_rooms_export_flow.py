from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pandas as pd

from backend.application.rooms_service import RoomsService
from backend.domain.state import AppState
from backend.examroom.core.gaokao_defaults import GAOKAO_TIME_DEFAULTS


def test_rooms_export_requires_existing_arrangement(recording_repo) -> None:
    service = RoomsService(AppState(), recording_repo)

    result = service.export({"path": "out.xlsx"})

    assert result == {"error": "请先进行编排"}


def test_rooms_export_calls_gaokao_export_and_applies_time_settings(recording_repo) -> None:
    state = AppState()
    state.rooms.config = {"gaokaoTimeSettings": deepcopy(GAOKAO_TIME_DEFAULTS)}
    state.rooms.config["gaokaoTimeSettings"]["examTimes"]["语文"]["date"] = "2026-06-07"

    calls: list[str] = []

    class FakeArrangement:
        arrangement_mode = "gaokao_mode"
        arranged_students = pd.DataFrame([{"姓名": "张三"}])

        def save_gaokao_results(self, path: str):
            calls.append(path)
            return True, "ok"

    state.exam_arrangement = FakeArrangement()
    service = RoomsService(state, recording_repo)

    result = service.export({"path": "gaokao.xlsx"})

    assert result == {}
    assert calls == ["gaokao.xlsx"]
    assert state.exam_arrangement.gaokao_time_settings["examTimes"]["语文"]["date"] == "2026-06-07"


def test_rooms_export_promotes_subject_mode_before_normal_export(recording_repo) -> None:
    state = AppState()
    state.rooms.config = {"subjectPriorityOrder": ["地理", "化学"]}

    calls: list[str] = []

    class FakeArrangement:
        arrangement_mode = "normal_mode"
        arranged_students = pd.DataFrame([{"姓名": "张三", "选科": "物化生"}])

        def save_results(self, path: str):
            calls.append(path)
            return True, "ok"

    state.exam_arrangement = FakeArrangement()
    service = RoomsService(state, recording_repo)

    result = service.export({"path": "subject.xlsx"})

    assert result == {}
    assert calls == ["subject.xlsx"]
    assert state.exam_arrangement.arrangement_mode == "subject_mode"
    assert state.exam_arrangement.subject_priority_order == ["地理", "化学", "生物", "政治"]


def test_rooms_export_returns_save_error(recording_repo) -> None:
    state = AppState()
    state.exam_arrangement = SimpleNamespace(
        arrangement_mode="normal_mode",
        arranged_students=pd.DataFrame([{"姓名": "张三"}]),
        save_results=lambda path: (False, "写入失败"),
    )
    service = RoomsService(state, recording_repo)

    result = service.export({"path": "broken.xlsx"})

    assert result == {"error": "写入失败"}
