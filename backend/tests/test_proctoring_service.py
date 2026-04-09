from __future__ import annotations

import pandas as pd
import time

from backend.application.proctoring_service import (
    ProctoringService,
    _build_cp_sat_run_log,
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
    assert teacher.unavailable_subjects == [1, 2]
    assert teacher.previous_supervision_duration == 90
    assert teacher.preset_room == 301
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


def test_build_cp_sat_run_log_includes_result_and_stage_details() -> None:
    log_text = _build_cp_sat_run_log(
        operation_label="智能编排",
        report={
            "status": "FEASIBLE",
            "optimal": False,
            "message": "Locked the best known value for stage minimize_overall_duration_deviation.",
            "metrics": {
                "count_min": 2,
                "count_max": 3,
                "count_range": 1,
                "count_stddev": 0.4899,
                "current_duration_min": 220,
                "current_duration_max": 295,
                "current_duration_range": 75,
                "current_duration_stddev": 27.6405,
                "overall_duration_min": 255,
                "overall_duration_max": 320,
                "overall_duration_range": 65,
                "overall_duration_stddev": 25.671,
            },
            "stages": [
                {
                    "name": "minimize_overall_duration_deviation",
                    "value": 9160,
                    "solve_seconds": 3.687,
                    "status": "FEASIBLE",
                    "proven_optimal": False,
                    "stop_reason": "no_improvement_limit",
                    "idle_after_last_improvement_seconds": 3.578,
                    "improvement_count": 1,
                    "best_bound": 8860,
                    "objective_gap": 300,
                    "continued_with_locked_value": True,
                }
            ],
        },
        teacher_count=20,
        subject_count=6,
        wall_seconds=4.364,
    )

    assert "本次结果：" in log_text
    assert "阶段明细：" in log_text
    assert "总耗时：4.364s" in log_text
    assert "总监考时长：255 ~ 320 分钟" in log_text
    assert "1. minimize_overall_duration_deviation" in log_text
    assert "停止原因：no_improvement_limit" in log_text


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
    assert result["detectedMode"] == "single"
    assert len(rooms) == 2
    assert rooms[0]["teachers"][0]["name"] == "张老师"
    assert rooms[1]["teachers"][0]["name"] == "李老师"
    assert service.get_state({})["config"]["roomCount"] == 2
    assert service.get_state({})["config"]["mode"] == "single"


def test_import_preset_auto_detects_double_mode_from_excel(recording_repo, tmp_path) -> None:
    workbook = tmp_path / "preset-double.xlsx"
    pd.DataFrame(
        {
            "考场": ["考场1"],
            "语文-监考员1\n09:00": ["张老师"],
            "语文-监考员2\n09:00": ["李老师"],
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
            "config": {"roomCount": 1, "mode": "single", "balanceMode": "duration"},
        }
    )

    rooms = result["schedule"][0]["rooms"]
    assert result["detectedMode"] == "double"
    assert len(rooms) == 1
    assert [teacher["name"] for teacher in rooms[0]["teachers"]] == ["张老师", "李老师"]
    assert service.get_state({})["config"]["mode"] == "double"


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


def test_generate_schedule_cp_sat_respects_real_time_overlap(recording_repo) -> None:
    state = AppState()
    state.subjects = [
        {
            "name": "Subject A",
            "exam_date": "2026-06-01",
            "exam_time": "09:00-11:00",
            "duration_minutes": 120,
        },
        {
            "name": "Subject B",
            "exam_date": "2026-06-01",
            "exam_time": "10:00-12:00",
            "duration_minutes": 120,
        },
    ]
    service = ProctoringService(state, recording_repo)

    result = service.generate_schedule(
        {
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 2},
                {"name": "Teacher B", "gender": "F", "isInternal": False, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "Subject A"}, {"id": "2", "name": "Subject B"}],
            "config": {"roomCount": 1, "mode": "single", "balanceMode": "duration"},
        }
    )

    teacher_name_a = result["schedule"][0]["rooms"][0]["teachers"][0]["name"]
    teacher_name_b = result["schedule"][1]["rooms"][0]["teachers"][0]["name"]
    assert teacher_name_a != teacher_name_b
    assert result["meta"]["solver"] == "cp_sat"


def test_continue_schedule_cp_sat_preserves_locked_assignments(recording_repo) -> None:
    state = AppState()
    state.subjects = [
        {
            "name": "Subject A",
            "exam_date": "2026-06-01",
            "exam_time": "09:00-11:00",
            "duration_minutes": 120,
        }
    ]
    service = ProctoringService(state, recording_repo)

    result = service.continue_schedule(
        {
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 1},
                {"name": "Teacher B", "gender": "F", "isInternal": False, "maxSessions": 1},
            ],
            "subjects": [{"id": "1", "name": "Subject A"}],
            "schedule": [
                {
                    "subjectId": "1",
                    "subjectName": "Subject A",
                    "rooms": [
                        {"id": 1, "roomNum": 1, "teachers": [{"name": "Teacher A", "isLocked": True}]},
                    ],
                }
            ],
            "config": {"roomCount": 2, "mode": "single", "balanceMode": "duration", "lockImported": True},
        }
    )

    rooms = result["schedule"][0]["rooms"]
    assert rooms[0]["teachers"][0]["name"] == "Teacher A"
    assert rooms[0]["teachers"][0]["isLocked"] is True
    assert rooms[1]["teachers"][0]["name"] == "Teacher B"


def test_generate_schedule_cp_sat_reports_stage_progress(recording_repo) -> None:
    state = AppState()
    state.subjects = [
        {
            "name": "Subject A",
            "exam_date": "2026-06-01",
            "exam_time": "09:00-10:00",
            "duration_minutes": 60,
        },
        {
            "name": "Subject B",
            "exam_date": "2026-06-02",
            "exam_time": "09:00-10:00",
            "duration_minutes": 60,
        },
    ]
    service = ProctoringService(state, recording_repo)

    result = service.generate_schedule(
        {
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 2},
                {"name": "Teacher B", "gender": "F", "isInternal": False, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "Subject A"}, {"id": "2", "name": "Subject B"}],
            "config": {
                "roomCount": 1,
                "mode": "single",
                "balanceMode": "duration",
                "cpSatProgressIntervalSeconds": 0.1,
            },
        }
    )

    details = result["optimizationDetails"]
    assert details["stages"]
    first_stage = details["stages"][0]
    assert "solve_seconds" in first_stage
    assert "improvement_count" in first_stage
    assert "progress_samples" in first_stage
    assert isinstance(details["progressSamples"], list)


def test_generate_schedule_cp_sat_uses_duration_first_objectives(recording_repo) -> None:
    state = AppState()
    state.subjects = [
        {
            "name": "Subject A",
            "exam_date": "2026-06-01",
            "exam_time": "09:00-10:00",
            "duration_minutes": 60,
        },
        {
            "name": "Subject B",
            "exam_date": "2026-06-02",
            "exam_time": "09:00-11:00",
            "duration_minutes": 120,
        },
    ]
    service = ProctoringService(state, recording_repo)

    result = service.generate_schedule(
        {
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 2},
                {"name": "Teacher B", "gender": "F", "isInternal": False, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "Subject A"}, {"id": "2", "name": "Subject B"}],
            "config": {
                "roomCount": 1,
                "mode": "single",
                "balanceMode": "duration",
                "cpSatProgressIntervalSeconds": 0.1,
            },
        }
    )

    stage_names = [stage["name"] for stage in result["optimizationDetails"]["stages"][:4]]
    assert stage_names == [
        "minimize_max_overall_duration",
        "minimize_count_range",
        "maximize_min_overall_duration",
        "minimize_overall_duration_deviation",
    ]


def test_generate_schedule_cp_sat_uses_session_first_objectives(recording_repo) -> None:
    state = AppState()
    state.subjects = [
        {
            "name": "Subject A",
            "exam_date": "2026-06-01",
            "exam_time": "09:00-10:00",
            "duration_minutes": 60,
        },
        {
            "name": "Subject B",
            "exam_date": "2026-06-02",
            "exam_time": "09:00-11:00",
            "duration_minutes": 120,
        },
    ]
    service = ProctoringService(state, recording_repo)

    result = service.generate_schedule(
        {
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 2},
                {"name": "Teacher B", "gender": "F", "isInternal": False, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "Subject A"}, {"id": "2", "name": "Subject B"}],
            "config": {
                "roomCount": 1,
                "mode": "single",
                "balanceMode": "session",
                "cpSatProgressIntervalSeconds": 0.1,
            },
        }
    )

    stage_names = [stage["name"] for stage in result["optimizationDetails"]["stages"][:3]]
    assert stage_names == [
        "minimize_max_count",
        "maximize_min_count",
        "minimize_count_deviation",
    ]


def test_start_solver_job_returns_pollable_status_and_result(recording_repo) -> None:
    state = AppState()
    state.subjects = [
        {
            "name": "Subject A",
            "exam_date": "2026-06-01",
            "exam_time": "09:00-10:00",
            "duration_minutes": 60,
        },
        {
            "name": "Subject B",
            "exam_date": "2026-06-02",
            "exam_time": "09:00-10:00",
            "duration_minutes": 60,
        },
    ]
    service = ProctoringService(state, recording_repo)

    started = service.start_solver_job(
        {
            "operation": "generate",
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 2},
                {"name": "Teacher B", "gender": "F", "isInternal": False, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "Subject A"}, {"id": "2", "name": "Subject B"}],
            "config": {
                "roomCount": 1,
                "mode": "single",
                "balanceMode": "duration",
                "cpSatProgressIntervalSeconds": 0.1,
                "cpSatNoImprovementSeconds": 5,
            },
        }
    )

    assert started["jobId"]
    deadline = time.monotonic() + 5.0
    status = None
    while time.monotonic() < deadline:
        status = service.get_job_status({"jobId": started["jobId"]})
        if status["status"] == "completed":
            break
        if status["status"] == "failed":
            raise AssertionError(status["error"])
        time.sleep(0.05)

    assert status is not None
    assert status["status"] == "completed"
    assert status["result"]["schedule"]
    assert "progress" in status


def test_generate_schedule_cp_sat_uses_subject_specific_room_counts(recording_repo) -> None:
    state = AppState()
    state.subjects = [
        {
            "name": "语文",
            "exam_date": "2026-06-01",
            "exam_time": "09:00-10:00",
            "duration_minutes": 60,
            "room_count": 2,
        },
        {
            "name": "数学",
            "exam_date": "2026-06-01",
            "exam_time": "10:30-11:30",
            "duration_minutes": 60,
            "room_count": 1,
        },
    ]
    service = ProctoringService(state, recording_repo)

    result = service.generate_schedule(
        {
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 2},
                {"name": "Teacher B", "gender": "F", "isInternal": False, "maxSessions": 2},
                {"name": "Teacher C", "gender": "F", "isInternal": True, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "语文", "roomCount": 2}, {"id": "2", "name": "数学", "roomCount": 1}],
            "config": {"roomCount": 0, "mode": "single", "balanceMode": "duration"},
        }
    )

    assert len(result["schedule"][0]["rooms"]) == 2
    assert len(result["schedule"][1]["rooms"]) == 1
    assert result["schedule"][0]["roomCount"] == 2
    assert result["schedule"][1]["roomCount"] == 1


def test_export_schedule_workbook_includes_time_overview_sheet(recording_repo, tmp_path) -> None:
    service = ProctoringService(AppState(), recording_repo)
    path = tmp_path / "schedule.xlsx"

    service.export(
        {
            "path": str(path),
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 2},
                {"name": "Teacher B", "gender": "F", "isInternal": False, "maxSessions": 2},
            ],
            "subjects": [
                {"id": "1", "name": "语文", "exam_date": "2026-06-07", "time": "09:00-11:00", "roomCount": 2},
                {"id": "2", "name": "数学", "exam_date": "2026-06-07", "time": "10:00-12:00", "roomCount": 1},
            ],
            "schedule": [
                {
                    "subjectId": "1",
                    "subjectName": "语文",
                    "time": "09:00-11:00",
                    "rooms": [
                        {"id": 1, "roomNum": 1, "location": "第一考场", "teachers": [{"name": "Teacher A"}]},
                        {"id": 2, "roomNum": 2, "location": "第二考场", "teachers": [{"name": "Teacher B"}]},
                    ],
                },
                {
                    "subjectId": "2",
                    "subjectName": "数学",
                    "time": "10:00-12:00",
                    "rooms": [
                        {"id": 1, "roomNum": 1, "location": "第一考场", "teachers": [{"name": "Teacher B"}]},
                    ],
                },
            ],
            "config": {"mode": "single"},
        }
    )

    workbook = pd.ExcelFile(path)
    assert "监考总览表" in workbook.sheet_names
    assert "按时段总览" in workbook.sheet_names

    time_overview = pd.read_excel(path, sheet_name="按时段总览").fillna("")
    assert time_overview.to_dict("records") == [
        {"日期": "2026-06-07", "时间": "09:00-11:00", "科目": "语文", "考场编号": 1, "考场": "第一考场", "监考教师": "Teacher A"},
        {"日期": "2026-06-07", "时间": "09:00-11:00", "科目": "语文", "考场编号": 2, "考场": "第二考场", "监考教师": "Teacher B"},
        {"日期": "2026-06-07", "时间": "10:00-12:00", "科目": "数学", "考场编号": 1, "考场": "第一考场", "监考教师": "Teacher B"},
    ]
