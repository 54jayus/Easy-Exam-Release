from __future__ import annotations

import pandas as pd

from backend.application.proctoring_service import (
    ProctoringService,
    _extract_subject_durations,
    _has_locked_positions,
    _sort_subjects,
    _teacher_from_dict,
)
from backend.domain.state import AppState


def test_teacher_from_dict_keeps_optional_fields() -> None:
    teacher = _teacher_from_dict(
        {
            "name": "张老师",
            "gender": "F",
            "isInternal": True,
            "maxSessions": 4,
            "unavailableSubjects": ["1", "2"],
            "previousSupervisionDuration": 90,
            "presetRoom": "301",
            "supervisionDuration": 45,
        }
    )

    assert teacher.name == "张老师"
    assert teacher.gender == "F"
    assert teacher.is_internal is True
    assert teacher.max_sessions == 4
    assert teacher.unavailable_subjects == ["1", "2"]
    assert teacher.previous_supervision_duration == 90
    assert teacher.preset_room == "301"
    assert teacher.supervision_duration == 45


def test_sort_subjects_uses_numeric_ids_when_all_present() -> None:
    subjects = [
        {"id": "10", "name": "英语"},
        {"id": "2", "name": "数学"},
        {"id": "01", "name": "语文"},
    ]

    sorted_subjects = _sort_subjects(subjects)

    assert [subject["id"] for subject in sorted_subjects] == ["01", "2", "10"]


def test_sort_subjects_keeps_original_order_when_ids_are_incomplete() -> None:
    subjects = [
        {"id": "2", "name": "数学"},
        {"id": "", "name": "语文"},
        {"name": "英语"},
    ]

    assert _sort_subjects(subjects) == subjects


def test_has_locked_positions_detects_nested_locked_teacher() -> None:
    unlocked = [{"rooms": [{"teachers": [{"name": "张老师"}]}]}]
    locked = [{"rooms": [{"teachers": [{"name": "李老师", "isLocked": True}]}]}]

    assert _has_locked_positions(unlocked) is False
    assert _has_locked_positions(locked) is True


def test_extract_subject_durations_supports_multiple_field_names() -> None:
    durations = _extract_subject_durations(
        [
            {"durationMinutes": "120"},
            {"duration_minutes": 90},
            {"duration": "45"},
            {"duration_minutes": "bad"},
        ]
    )

    assert durations == [120, 90, 45, 0]


def test_import_preset_uses_detected_room_count_from_excel(recording_repo, tmp_path) -> None:
    workbook = tmp_path / "preset.xlsx"
    pd.DataFrame(
        {
            "考场": ["考场1", "考场2"],
            "语文\n09:00": ["张老师", "李老师"],
        }
    ).to_excel(workbook, sheet_name="监考总览表", index=False)

    service = ProctoringService(AppState(), recording_repo)
    result = service.import_preset(
        {
            "path": str(workbook),
            "teachers": [
                {"name": "张老师", "gender": "M", "isInternal": True, "maxSessions": 2},
                {"name": "李老师", "gender": "F", "isInternal": False, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "语文", "time": "09:00", "durationMinutes": 120}],
            "config": {"roomCount": 0, "mode": "single", "balanceMode": "duration"},
        }
    )

    rooms = result["schedule"][0]["rooms"]
    assert result["detectedRoomCount"] == 2
    assert len(rooms) == 2
    assert rooms[0]["teachers"][0]["name"] == "张老师"
    assert rooms[1]["teachers"][0]["name"] == "李老师"
    assert service.get_state({})["config"]["roomCount"] == 2


def test_continue_schedule_rebuilds_rooms_from_config_when_schedule_is_empty(recording_repo) -> None:
    state = AppState()
    service = ProctoringService(state, recording_repo)

    result = service.continue_schedule(
        {
            "teachers": [
                {"name": "张老师", "gender": "M", "isInternal": True, "maxSessions": 2},
                {"name": "李老师", "gender": "F", "isInternal": False, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "语文", "time": "09:00", "durationMinutes": 120}],
            "schedule": [],
            "config": {"roomCount": 2, "mode": "single", "balanceMode": "duration"},
        }
    )

    rooms = result["schedule"][0]["rooms"]
    assert len(rooms) == 2
    assert all(len(room["teachers"]) == 1 for room in rooms)
