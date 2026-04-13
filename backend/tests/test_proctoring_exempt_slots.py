from __future__ import annotations

import pandas as pd

from backend.application.proctoring_service import ProctoringService
from backend.domain.state import AppState
from backend.proctoring.core.entities import Exam
from backend.proctoring.core.models import Schedule


def test_import_preset_marks_single_exempt_slot(recording_repo, tmp_path) -> None:
    workbook = tmp_path / "preset-single-exempt.xlsx"
    pd.DataFrame(
        {
            "考场": ["考场1"],
            "语文\n09:00": ["#无需编排"],
        }
    ).to_excel(workbook, sheet_name="监考总览表", index=False)

    service = ProctoringService(AppState(), recording_repo)
    result = service.import_preset(
        {
            "path": str(workbook),
            "teachers": [
                {"name": "张老师", "gender": "M", "isInternal": True, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "语文", "time": "09:00", "durationMinutes": 120}],
            "config": {"roomCount": 1, "mode": "single", "balanceMode": "duration"},
        }
    )

    assert result["schedule"][0]["rooms"][0]["teachers"] == [
        {"id": "__EXEMPT__", "name": "无需编排", "isExempt": True},
    ]


def test_import_preset_marks_partial_double_exempt_slot(recording_repo, tmp_path) -> None:
    workbook = tmp_path / "preset-double-exempt.xlsx"
    pd.DataFrame(
        {
            "考场": ["考场1"],
            "语文-监考员1\n09:00": ["#无需编排"],
            "语文-监考员2\n09:00": ["李老师"],
        }
    ).to_excel(workbook, sheet_name="监考总览表", index=False)

    service = ProctoringService(AppState(), recording_repo)
    result = service.import_preset(
        {
            "path": str(workbook),
            "teachers": [
                {"name": "李老师", "gender": "F", "isInternal": False, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "语文", "time": "09:00", "durationMinutes": 120}],
            "config": {"roomCount": 1, "mode": "double", "balanceMode": "duration"},
        }
    )

    teachers = result["schedule"][0]["rooms"][0]["teachers"]
    assert teachers[0] == {"id": "__EXEMPT__", "name": "无需编排", "isExempt": True}
    assert teachers[1]["name"] == "李老师"


def test_continue_schedule_keeps_exempt_slots_and_relaxes_internal_mix_for_remaining_slot(recording_repo) -> None:
    state = AppState()
    state.subjects = [
        {
            "name": "语文",
            "exam_date": "2026-06-01",
            "exam_time": "09:00-11:00",
            "duration_minutes": 120,
        }
    ]
    service = ProctoringService(state, recording_repo)

    result = service.continue_schedule(
        {
            "teachers": [
                {"name": "校内老师", "gender": "M", "isInternal": True, "maxSessions": 1},
            ],
            "subjects": [{"id": "1", "name": "语文"}],
            "schedule": [
                {
                    "subjectId": "1",
                    "subjectName": "语文",
                    "rooms": [
                        {
                            "id": 1,
                            "roomNum": 1,
                            "teachers": [
                                {"id": "__EXEMPT__", "name": "无需编排", "isExempt": True},
                                None,
                            ],
                        },
                    ],
                }
            ],
            "config": {
                "roomCount": 1,
                "mode": "double",
                "balanceMode": "duration",
                "internalMix": True,
                "lockImported": True,
            },
        }
    )

    room_teachers = result["schedule"][0]["rooms"][0]["teachers"]
    assert room_teachers[0] == {"id": "__EXEMPT__", "name": "无需编排", "isExempt": True}
    assert room_teachers[1]["name"] == "校内老师"


def test_schedule_is_complete_when_slot_is_exempt() -> None:
    schedule = Schedule([], num_subjects=1, num_rooms=1, mode="single")
    exam = Exam(1, [1])
    exam.schedule[1] = [None]
    schedule.exams = [exam]
    schedule.mark_exempt_position(1, 1, 0)

    assert schedule.is_schedule_complete() is True


def test_export_schedule_writes_exempt_marker(recording_repo, tmp_path) -> None:
    service = ProctoringService(AppState(), recording_repo)
    path = tmp_path / "schedule-exempt.xlsx"

    service.export(
        {
            "path": str(path),
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 2},
            ],
            "subjects": [
                {"id": "1", "name": "语文", "exam_date": "2026-06-07", "time": "09:00-11:00", "roomCount": 1},
            ],
            "schedule": [
                {
                    "subjectId": "1",
                    "subjectName": "语文",
                    "time": "09:00-11:00",
                    "rooms": [
                        {
                            "id": 1,
                            "roomNum": 1,
                            "location": "第一考场",
                            "teachers": [{"id": "__EXEMPT__", "name": "无需编排", "isExempt": True}],
                        },
                    ],
                },
            ],
            "config": {"mode": "single"},
        }
    )

    overview = pd.read_excel(path, sheet_name="监考总览表").fillna("")
    assert overview.iloc[0, 1] == "#无需编排"
