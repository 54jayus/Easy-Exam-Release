from __future__ import annotations

import pandas as pd
import time

import backend.application.proctoring_service as proctoring_service_module
from backend.application.proctoring_service import (
    ProctoringService,
    _build_cp_sat_run_log,
    _build_count_balance_attempt_limits,
    _classify_count_balance_teacher_indexes,
    _extract_subject_durations,
    _has_locked_positions,
    _sort_subjects,
    _teacher_from_dict,
)
from backend.domain.state import AppState
from backend.proctoring.core.entities import Exam
from backend.proctoring.core.models import Schedule
from backend.proctoring.teacher_import import import_teachers_with_validation


def _successful_cp_sat_report() -> dict:
    return {
        "status": "OPTIMAL",
        "optimal": True,
        "message": "ok",
        "metrics": {
            "count_min": 0,
            "count_max": 1,
            "count_range": 1,
            "count_stddev": 0.5,
            "current_duration_min": 0,
            "current_duration_max": 60,
            "current_duration_range": 60,
            "current_duration_stddev": 30,
            "overall_duration_min": 0,
            "overall_duration_max": 60,
            "overall_duration_range": 60,
            "overall_duration_stddev": 30,
        },
        "stages": [],
    }


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


def test_classify_count_balance_teacher_indexes_uses_max_sessions_as_boundary() -> None:
    teachers = [
        _teacher_from_dict({"name": "A", "maxSessions": 8}),
        _teacher_from_dict({"name": "B", "maxSessions": 8}),
        _teacher_from_dict({"name": "C", "maxSessions": 5}),
    ]

    regular_indexes, special_indexes, max_cap = _classify_count_balance_teacher_indexes(teachers)

    assert regular_indexes == [0, 1]
    assert special_indexes == [2]
    assert max_cap == 8


def test_build_count_balance_attempt_limits_uses_progressive_fallback() -> None:
    assert _build_count_balance_attempt_limits([0, 1]) == [1, 2, None]
    assert _build_count_balance_attempt_limits([0]) == [None]


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


def test_import_teachers_allows_negative_previous_supervision_duration(tmp_path) -> None:
    workbook = tmp_path / "teachers.xlsx"
    pd.DataFrame(
        {
            "姓名": ["张老师", "李老师"],
            "性别": ["男", "女"],
            "是否本校": ["是", "是"],
            "最大监考段数": [1, 1],
            "不监考科目": ["", ""],
            "历次监考时长": [-120, 30],
        }
    ).to_excel(workbook, index=False)

    teachers, errors, warnings = import_teachers_with_validation(
        str(workbook),
        mode="single",
        gender_mix=False,
        internal_mix=False,
        subject_count=1,
        subject_names=["语文"],
        num_rooms=1,
    )

    assert errors == []
    assert warnings == []
    assert [teacher.previous_supervision_duration for teacher in teachers] == [-120, 30]


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


def test_generate_schedule_randomizes_teacher_order_for_solver_but_preserves_output_order(
    recording_repo, monkeypatch
) -> None:
    state = AppState()
    state.subjects = [
        {
            "name": "Subject A",
            "exam_date": "2026-06-01",
            "exam_time": "09:00-10:00",
            "duration_minutes": 60,
        }
    ]
    service = ProctoringService(state, recording_repo)
    solver_teacher_orders: list[list[str]] = []

    def fake_randomize(schedule: Schedule) -> None:
        schedule.teachers.reverse()

    def fake_solver(schedule_arg, subject_contexts, **kwargs):
        del subject_contexts, kwargs
        solver_teacher_orders.append([teacher.name for teacher in schedule_arg.teachers])
        return _successful_cp_sat_report()

    monkeypatch.setattr(proctoring_service_module, "_randomize_teacher_order_for_solver", fake_randomize)
    monkeypatch.setattr(proctoring_service_module, "solve_schedule_with_cp_sat", fake_solver)

    result = service.generate_schedule(
        {
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 1},
                {"name": "Teacher B", "gender": "F", "isInternal": False, "maxSessions": 1},
                {"name": "Teacher C", "gender": "F", "isInternal": True, "maxSessions": 1},
            ],
            "subjects": [{"id": "1", "name": "Subject A"}],
            "config": {"roomCount": 1, "mode": "single", "balanceMode": "duration"},
        }
    )

    assert solver_teacher_orders == [["Teacher C", "Teacher B", "Teacher A"]]
    assert [teacher["name"] for teacher in result["teachers"]] == [
        "Teacher A",
        "Teacher B",
        "Teacher C",
    ]


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


def test_continue_schedule_randomizes_teacher_order_for_solver(recording_repo, monkeypatch) -> None:
    state = AppState()
    state.subjects = [
        {
            "name": "Subject A",
            "exam_date": "2026-06-01",
            "exam_time": "09:00-10:00",
            "duration_minutes": 60,
        }
    ]
    service = ProctoringService(state, recording_repo)
    solver_teacher_orders: list[list[str]] = []

    def fake_randomize(schedule: Schedule) -> None:
        schedule.teachers.reverse()

    def fake_solver(schedule_arg, subject_contexts, **kwargs):
        del subject_contexts, kwargs
        solver_teacher_orders.append([teacher.name for teacher in schedule_arg.teachers])
        return _successful_cp_sat_report()

    monkeypatch.setattr(proctoring_service_module, "_randomize_teacher_order_for_solver", fake_randomize)
    monkeypatch.setattr(proctoring_service_module, "solve_schedule_with_cp_sat", fake_solver)

    result = service.continue_schedule(
        {
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 2},
                {"name": "Teacher B", "gender": "F", "isInternal": False, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "Subject A"}],
            "schedule": [],
            "config": {"roomCount": 1, "mode": "single", "balanceMode": "duration"},
        }
    )

    assert solver_teacher_orders == [["Teacher B", "Teacher A"]]
    assert [teacher["name"] for teacher in result["teachers"]] == ["Teacher A", "Teacher B"]


def test_generate_schedule_short_circuits_capacity_infeasibility_before_solver(
    recording_repo, monkeypatch
) -> None:
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
            "exam_date": "2026-06-01",
            "exam_time": "14:00-15:00",
            "duration_minutes": 60,
        },
    ]
    service = ProctoringService(state, recording_repo)

    def should_not_run_solver(*args, **kwargs):
        raise AssertionError("solver should not run when fast feasibility precheck fails")

    monkeypatch.setattr(proctoring_service_module, "solve_schedule_with_cp_sat", should_not_run_solver)

    result = service.generate_schedule(
        {
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 1},
            ],
            "subjects": [{"id": "1", "name": "Subject A"}, {"id": "2", "name": "Subject B"}],
            "config": {"roomCount": 1, "mode": "single", "balanceMode": "duration"},
        }
    )

    assert "error" in result
    assert "不足" in result["error"]


def test_continue_schedule_short_circuits_locked_conflict_before_solver(
    recording_repo, monkeypatch
) -> None:
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

    def should_not_run_solver(*args, **kwargs):
        raise AssertionError("solver should not run when locked assignments already conflict")

    monkeypatch.setattr(proctoring_service_module, "solve_schedule_with_cp_sat", should_not_run_solver)

    result = service.continue_schedule(
        {
            "teachers": [
                {"name": "Teacher A", "gender": "M", "isInternal": True, "maxSessions": 2},
                {"name": "Teacher B", "gender": "F", "isInternal": False, "maxSessions": 2},
            ],
            "subjects": [{"id": "1", "name": "Subject A"}, {"id": "2", "name": "Subject B"}],
            "schedule": [
                {
                    "subjectId": "1",
                    "subjectName": "Subject A",
                    "rooms": [
                        {"id": 1, "roomNum": 1, "teachers": [{"name": "Teacher A", "isLocked": True}]},
                    ],
                },
                {
                    "subjectId": "2",
                    "subjectName": "Subject B",
                    "rooms": [
                        {"id": 1, "roomNum": 1, "teachers": [{"name": "Teacher A", "isLocked": True}]},
                    ],
                },
            ],
            "config": {
                "roomCount": 1,
                "mode": "single",
                "balanceMode": "duration",
                "lockImported": True,
            },
        }
    )

    assert "error" in result
    assert "Teacher A" in result["error"]


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


def test_run_cp_sat_formats_stage_preview_result(recording_repo, monkeypatch) -> None:
    service = ProctoringService(AppState(), recording_repo)

    schedule = Schedule([_teacher_from_dict({"name": "张老师", "maxSessions": 1})], 1, 1, mode="single")
    schedule.set_constraint("subject_durations", [60])
    schedule.set_constraint("subject_room_counts", [1])

    preview_teacher = _teacher_from_dict({"name": "张老师", "maxSessions": 1})
    preview_teacher.assign((1, 1), 60)
    preview_schedule = Schedule([preview_teacher], 1, 1, mode="single")
    preview_schedule.set_constraint("subject_durations", [60])
    preview_schedule.set_constraint("subject_room_counts", [1])
    preview_exam = Exam(1, [1])
    preview_exam.schedule[1] = [preview_teacher]
    preview_schedule.exams = [preview_exam]

    captured_events: list[dict] = []

    def fake_solver(schedule_arg, subject_contexts, **kwargs):
        assert schedule_arg is schedule
        assert len(subject_contexts) == 1
        kwargs["progress_observer"](
            {
                "type": "stage_finished",
                "name": "minimize_max_count",
                "stage_index": 1,
                "stage_count": 2,
                "status": "FEASIBLE",
                "proven_optimal": False,
                "preview_schedule": preview_schedule,
            }
        )
        return {
            "status": "FEASIBLE",
            "optimal": False,
            "message": "preview ready",
            "metrics": {},
            "stages": [],
        }

    monkeypatch.setattr(proctoring_service_module, "solve_schedule_with_cp_sat", fake_solver)

    result = service._run_cp_sat(
        schedule=schedule,
        subjects_data=[
            {
                "id": "1",
                "name": "语文",
                "exam_time": "09:00-10:00",
                "durationMinutes": 60,
                "rooms": [{"id": 1, "location": "第一考场"}],
            }
        ],
        config={"roomCount": 1, "mode": "single", "balanceMode": "duration"},
        fix_existing_assignments=False,
        use_current_solution_as_hint=False,
        default_time_limit_seconds=90.0,
        progress_observer=captured_events.append,
    )

    assert result["status"] == "FEASIBLE"
    assert len(captured_events) == 1
    preview_event = captured_events[0]
    assert "preview_schedule" not in preview_event
    assert preview_event["preview_result"]["meta"]["complete"] is False
    assert preview_event["preview_result"]["meta"]["isPreview"] is True
    assert preview_event["preview_result"]["meta"]["stageIndex"] == 1
    assert preview_event["preview_result"]["schedule"][0]["rooms"][0]["teachers"][0]["name"] == "张老师"


def test_run_cp_sat_retries_count_balance_limit_with_progressive_fallback(recording_repo, monkeypatch) -> None:
    service = ProctoringService(AppState(), recording_repo)

    schedule = Schedule(
        [
            _teacher_from_dict({"name": "A", "maxSessions": 2}),
            _teacher_from_dict({"name": "B", "maxSessions": 2}),
            _teacher_from_dict({"name": "C", "maxSessions": 1}),
        ],
        1,
        1,
        mode="single",
    )
    schedule.set_constraint("subject_durations", [60])
    schedule.set_constraint("subject_room_counts", [1])

    attempted_limits: list[int | None] = []

    def fake_solver(schedule_arg, subject_contexts, **kwargs):
        del schedule_arg, subject_contexts
        attempted_limits.append(kwargs.get("count_balance_limit"))
        if kwargs.get("count_balance_limit") == 1:
            return {"status": "INFEASIBLE", "optimal": False, "message": "no", "stages": []}
        return {
            **_successful_cp_sat_report(),
            "status": "FEASIBLE",
            "optimal": False,
            "message": "fallback ok",
        }

    monkeypatch.setattr(proctoring_service_module, "solve_schedule_with_cp_sat", fake_solver)

    result = service._run_cp_sat(
        schedule=schedule,
        subjects_data=[
            {
                "id": "1",
                "name": "语文",
                "exam_time": "09:00-10:00",
                "durationMinutes": 60,
            }
        ],
        config={"roomCount": 1, "mode": "single", "balanceMode": "duration"},
        fix_existing_assignments=False,
        use_current_solution_as_hint=False,
        default_time_limit_seconds=90.0,
    )

    assert attempted_limits == [1, 2]
    assert result["countBalanceHardLimitApplied"] == 2
    assert result["countBalanceConstraintScope"] == "regular_teachers"
    assert result["regularTeacherIndexes"] == [0, 1]
    assert result["specialTeacherIndexes"] == [2]


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
        "maximize_min_overall_duration",
        "minimize_overall_duration_deviation",
        "minimize_count_range",
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


def test_generate_schedule_cp_sat_uses_regular_teacher_count_objectives_when_special_teachers_exist(
    recording_repo,
) -> None:
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
                {"name": "Teacher C", "gender": "F", "isInternal": True, "maxSessions": 1},
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

    stage_names = [stage["name"] for stage in result["optimizationDetails"]["stages"][:6]]
    assert stage_names[:4] == [
        "minimize_max_overall_duration",
        "maximize_min_overall_duration",
        "minimize_overall_duration_deviation",
        "minimize_regular_count_range",
    ]
    assert "minimize_regular_count_deviation" in stage_names
    assert result["meta"]["countBalanceHardLimitApplied"] == 1
    assert result["meta"]["countBalanceConstraintScope"] == "regular_teachers"


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
