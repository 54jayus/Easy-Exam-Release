from __future__ import annotations

from backend.application.subjects_service import SubjectsService
from backend.domain.state import AppState
from backend.subjects.core import Subject, SubjectImportResult


def test_subjects_list_rebuilds_sequential_ids(recording_repo) -> None:
    state = AppState()
    state.subjects = [
        {"name": "语文", "exam_date": "2026-06-07", "exam_time": "09:00-11:30", "room_count": 12},
        {"name": "数学", "exam_date": "2026-06-07", "exam_time": "15:00-17:00", "room_count": 10},
    ]
    service = SubjectsService(state, recording_repo)

    result = service.list({})

    assert result == {
        "subjects": [
            {"id": "1", "name": "语文", "exam_date": "2026-06-07", "exam_time": "09:00-11:30", "room_count": 12},
            {"id": "2", "name": "数学", "exam_date": "2026-06-07", "exam_time": "15:00-17:00", "room_count": 10},
        ]
    }


def test_subjects_update_resets_proctoring_schedule_when_present(recording_repo) -> None:
    state = AppState()
    state.proctoring.schedule = {"items": [1]}
    service = SubjectsService(state, recording_repo)

    result = service.update(
        {
            "subjects": [
                {"name": "英语", "exam_date": "2026-06-08", "exam_time": "09:00-11:00", "room_count": 8}
            ]
        }
    )

    assert state.subjects == [
        {
            "name": "英语",
            "exam_date": "2026-06-08",
            "exam_time": "09:00-11:00",
            "remark": "",
            "duration_minutes": 0,
            "room_count": 8,
        }
    ]
    assert state.proctoring.schedule is None
    assert result == {"proctoringReset": True}
    assert recording_repo.save_calls == 1


def test_subjects_validate_allows_overlapping_exam_times(recording_repo) -> None:
    service = SubjectsService(AppState(), recording_repo)

    result = service.validate(
        {
            "subjects": [
                {"name": "语文", "exam_date": "2026-06-07", "exam_time": "09:00-11:30", "room_count": 12},
                {"name": "数学", "exam_date": "2026-06-07", "exam_time": "10:00-12:00", "room_count": 10},
            ]
        }
    )

    assert result["errors"] == []


def test_subjects_import_from_excel_updates_state(monkeypatch, recording_repo) -> None:
    state = AppState()
    state.proctoring.schedule = {"items": [1]}
    service = SubjectsService(state, recording_repo)

    monkeypatch.setattr(
        "backend.application.subjects_service.import_subjects_from_excel",
        lambda path: SubjectImportResult(
            subjects=[
                Subject(name="语文", exam_date="2026-06-07", exam_time="09:00-11:30", duration_minutes=150, room_count=12),
                Subject(name="数学", exam_date="2026-06-07", exam_time="15:00-17:00", duration_minutes=120, room_count=10),
            ],
            errors=[],
        ),
    )

    result = service.import_from_excel({"path": "subjects.xlsx"})

    assert result["errors"] == []
    assert result["proctoringReset"] is True
    assert [item["id"] for item in result["subjects"]] == ["1", "2"]
    assert state.subjects[0]["name"] == "语文"
    assert state.subjects[0]["room_count"] == 12
    assert recording_repo.save_calls == 1
