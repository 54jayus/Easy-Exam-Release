from __future__ import annotations

from copy import deepcopy
from datetime import date
from types import SimpleNamespace

import pandas as pd

from backend.application.rooms_service import (
    RoomsService,
    _build_exam_arrangement,
    _normalize_subject_priority_order,
)
from backend.domain.state import AppState
from backend.examroom.core.gaokao_defaults import GAOKAO_TIME_DEFAULTS


def test_normalize_subject_priority_order_filters_deduplicates_and_completes() -> None:
    order = _normalize_subject_priority_order(["地理", "化学", "地理", "无效", "政治"])

    assert order == ["地理", "化学", "政治", "生物"]


def test_build_exam_arrangement_maps_mode_and_room_metadata() -> None:
    settings = [
        {"roomNum": "001", "roomName": "第一考场", "capacity": 35},
        {"roomNum": "002", "roomName": "第二考场", "capacity": 28},
    ]
    custom_times = deepcopy(GAOKAO_TIME_DEFAULTS)
    custom_times["examTimes"]["语文"]["date"] = "2026-06-07"
    config = {
        "mode": "gaokao",
        "seatsPerRoom": 36,
        "totalRooms": 12,
        "subjectPriorityOrder": ["地理", "化学"],
        "gaokaoTimeSettings": custom_times,
    }

    arrangement = _build_exam_arrangement(settings, config, "students.xlsx")

    assert arrangement.file_path == "students.xlsx"
    assert arrangement.arrangement_mode == "gaokao_mode"
    assert arrangement.max_students_per_room == 36
    assert arrangement.total_rooms == 12
    assert arrangement.room_capacities == {"001": 35, "002": 28}
    assert arrangement.subject_priority_order == ["地理", "化学", "生物", "政治"]
    assert arrangement.gaokao_time_settings == custom_times
    assert arrangement.room_setting_df.to_dict("records") == [
        {"考场号": "001", "考场": "第一考场"},
        {"考场号": "002", "考场": "第二考场"},
    ]


def test_set_gaokao_time_settings_validates_input_and_persists_state(recording_repo) -> None:
    state = AppState()
    state.exam_arrangement = SimpleNamespace()
    service = RoomsService(state, recording_repo)

    missing = service.set_gaokao_time_settings({})
    wrong_type = service.set_gaokao_time_settings({"settings": []})
    missing_fields = service.set_gaokao_time_settings({"settings": {"examTimes": {}}})

    assert missing == {"error": "缺少 settings 参数"}
    assert wrong_type == {"error": "settings 必须是字典类型"}
    assert missing_fields == {"error": "settings 缺少必要字段"}
    assert recording_repo.save_calls == 0

    settings = deepcopy(GAOKAO_TIME_DEFAULTS)
    settings["selfStudyTimes"]["化学"]["startTime"] = "08:40"

    result = service.set_gaokao_time_settings({"settings": settings})

    assert result == {}
    assert state.rooms.config["gaokaoTimeSettings"] == settings
    assert state.exam_arrangement.gaokao_time_settings == settings
    assert recording_repo.save_calls == 1


def test_set_gaokao_time_settings_rejects_duplicate_subject_names(recording_repo) -> None:
    state = AppState()
    service = RoomsService(state, recording_repo)

    settings = deepcopy(GAOKAO_TIME_DEFAULTS)
    settings["examTimes"]["语文"]["subjectName"] = "语文"
    settings["examTimes"]["数学"]["subjectName"] = "语文"

    result = service.set_gaokao_time_settings({"settings": settings})

    assert result == {"error": "科目名称不能重复：语文"}
    assert recording_repo.save_calls == 0


def test_get_gaokao_time_settings_normalizes_legacy_config(recording_repo) -> None:
    state = AppState()
    state.rooms.config = {
        "gaokaoTimeSettings": {
            "examTimes": {
                "语文": {"date": "2026-06-07", "startTime": "09:00", "endTime": "11:30"},
            },
            "selfStudyTimes": {},
        }
    }
    service = RoomsService(state, recording_repo)

    result = service.get_gaokao_time_settings({})

    assert result["settings"]["examTimes"]["语文"]["subjectName"] == "语文"
    assert result["settings"]["examTimes"]["语文"]["date"] == "2026-06-07"
    assert result["settings"]["examTimes"]["数学"]["date"] == date.today().isoformat()


def test_get_state_fills_missing_room_config_from_settings(recording_repo) -> None:
    state = AppState()
    state.rooms.settings_data = [
        {"roomNum": "001", "roomName": "第一考场", "capacity": 30},
        {"roomNum": "002", "roomName": "第二考场", "capacity": 35},
    ]
    service = RoomsService(state, recording_repo)

    result = service.get_state({})

    assert result["settings"] == state.rooms.settings_data
    assert result["config"]["totalRooms"] == 2
    assert result["config"]["seatsPerRoom"] == 30
    assert result["config"]["subjectPriorityOrder"] == ["化学", "生物", "政治", "地理"]
    assert result["config"]["seatLayout"]["defaultLayout"]["layoutName"] == "7行×6列"


def test_get_seat_layout_migrates_legacy_printing_desk_config(recording_repo) -> None:
    state = AppState()
    state.printing.config = {"desk": {"layoutName": "5行×6列", "layoutRows": 5, "layoutCols": 6, "layoutPattern": "Z型横排", "startPos": "right"}}
    service = RoomsService(state, recording_repo)

    result = service.get_seat_layout({})

    assert result["seatLayout"]["defaultLayout"]["layoutName"] == "5行×6列"
    assert result["seatLayout"]["defaultLayout"]["layoutPattern"] == "Z型横排"


def test_import_results_subject_mode_enriches_subject_columns(tmp_path, recording_repo) -> None:
    state = AppState()
    state.rooms.config = {"mode": "normal"}
    state.rooms.student_path = "students.xlsx"
    service = RoomsService(state, recording_repo)

    path = tmp_path / "subject-results.xlsx"
    pd.DataFrame(
        [
            {
                "班级": "1",
                "学号": "01",
                "考号": "240001",
                "姓名": "张三",
                "考场号": "001",
                "座位号": "01",
                "选科": "物化生",
            },
            {
                "班级": "1",
                "学号": "02",
                "考号": "240002",
                "姓名": "李四",
                "考场号": "001",
                "座位号": "02",
                "选科": "史地政",
            },
        ]
    ).to_excel(path, index=False)

    result = service.import_results({"path": str(path)})

    assert result["message"] == "导入成功，共 2 人"
    assert state.rooms.config["mode"] == "3+1+2"
    assert state.rooms.results[0]["考场"] == "第001考场"
    assert state.rooms.results[0]["首选"] == "物理"
    assert state.rooms.results[0]["选科1"] == "化学"
    assert state.rooms.results[0]["选科2"] == "生物"
    assert "物化生" in state.rooms.results[0]["考场选科组合"]
    assert "史地政" in state.rooms.results[0]["考场选科组合"]
    assert recording_repo.save_calls == 1


def test_import_results_rejects_duplicate_room_and_seat_pairs(tmp_path, recording_repo) -> None:
    state = AppState()
    service = RoomsService(state, recording_repo)

    path = tmp_path / "duplicate-room-seat.xlsx"
    pd.DataFrame(
        [
            {"班级": "1", "学号": "01", "考号": "240001", "姓名": "张三", "考场号": "001", "座位号": "01"},
            {"班级": "1", "学号": "02", "考号": "240002", "姓名": "李四", "考场号": "001", "座位号": "01"},
        ]
    ).to_excel(path, index=False)

    result = service.import_results({"path": str(path)})

    assert result["error"] == "导入失败：存在重复的考场号+座位号: 001-01, 001-01（请确保同一考场内座位号不重复）"
    assert recording_repo.save_calls == 0


def test_import_results_gaokao_reconstructs_gaokao_state(tmp_path, recording_repo) -> None:
    state = AppState()
    state.rooms.config = {"mode": "normal"}
    state.rooms.student_path = "gaokao.xlsx"
    service = RoomsService(state, recording_repo)

    path = tmp_path / "gaokao-results.xlsx"
    pd.DataFrame(
        [
            {
                "班级": "1",
                "学号": "01",
                "考号": "240001",
                "姓名": "张三",
                "选科": "物化生",
                "语文考场号": "001",
                "语文考场": "第一考场",
                "语文座位号": "01",
                "化学科目": "化学",
                "化学考场号": "005",
                "化学考场": "第五考场",
                "化学座位号": "12",
                "地理科目": "自习",
                "地理考场号": "015",
                "地理考场": "第十五考场",
                "地理座位号": "08",
            }
        ]
    ).to_excel(path, index=False)

    result = service.import_results({"path": str(path)})

    assert result["message"] == "导入成功（高考模式），共 1 人"
    assert state.rooms.config["mode"] == "gaokao"
    assert state.rooms.gaokao_results is not None
    assert state.rooms.gaokao_results["unified"].to_dict("records") == [
        {
            "班级": "1",
            "学号": "01",
            "姓名": "张三",
            "考号": "240001",
            "选科": "物化生",
            "考场号": "001",
            "考场": "第一考场",
            "座位号": "01",
        }
    ]
    assert state.rooms.gaokao_results["electives"]["化学"].to_dict("records") == [
        {
            "班级": "1",
            "学号": "01",
            "姓名": "张三",
            "考号": "240001",
            "选科": "物化生",
            "考场号": "005",
            "考场": "第五考场",
            "座位号": "12",
            "科目类型": "化学",
        }
    ]
    assert state.rooms.gaokao_results["electives"]["地理"].to_dict("records") == [
        {
            "班级": "1",
            "学号": "01",
            "姓名": "张三",
            "考号": "240001",
            "选科": "物化生",
            "考场号": "015",
            "考场": "第十五考场",
            "座位号": "08",
            "科目类型": "自习",
        }
    ]
    assert recording_repo.save_calls == 1


def test_import_results_prefers_known_result_sheet_name(tmp_path, recording_repo) -> None:
    state = AppState()
    state.rooms.config = {"mode": "normal"}
    state.rooms.student_path = "students.xlsx"
    service = RoomsService(state, recording_repo)

    path = tmp_path / "multi-sheet-results.xlsx"
    with pd.ExcelWriter(path) as writer:
        pd.DataFrame([{"说明": "ignore"}]).to_excel(writer, sheet_name="说明", index=False)
        pd.DataFrame(
            [
                {
                    "班级": "1",
                    "学号": "01",
                    "考号": "240001",
                    "姓名": "张三",
                    "考场号": "001",
                    "座位号": "01",
                }
            ]
        ).to_excel(writer, sheet_name="学生编排结果", index=False)

    result = service.import_results({"path": str(path)})

    assert result["message"] == "导入成功，共 1 人"
    assert state.rooms.results[0]["考场号"] == "001"
    assert recording_repo.save_calls == 1
