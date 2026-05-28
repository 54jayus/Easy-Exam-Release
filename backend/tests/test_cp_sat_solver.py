from __future__ import annotations

from backend.proctoring.core import cp_sat
from backend.proctoring.core.entities import Exam, Teacher
from backend.proctoring.core.models import Schedule


def _make_context(
    subject_id: int,
    name: str,
    exam_date: str,
    start_hour: int,
    end_hour: int,
) -> cp_sat.SubjectContext:
    return cp_sat.SubjectContext(
        subject_id=subject_id,
        name=name,
        exam_date=exam_date,
        exam_time=f"{start_hour:02d}:00-{end_hour:02d}:00",
        duration_minutes=(end_hour - start_hour) * 60,
        start_minute=start_hour * 60,
        end_minute=end_hour * 60,
        sort_key=(1, start_hour * 60),
    )


def test_build_consecutive_pairs_links_each_session_to_same_day_next_session() -> None:
    subject_contexts = [
        cp_sat.SubjectContext(
            subject_id=1,
            name="Subject A",
            exam_date="2026-06-01",
            exam_time="09:00-10:00",
            duration_minutes=60,
            start_minute=9 * 60,
            end_minute=10 * 60,
            sort_key=(1, 9 * 60),
        ),
        cp_sat.SubjectContext(
            subject_id=2,
            name="Subject B",
            exam_date="2026-06-01",
            exam_time="10:30-11:30",
            duration_minutes=60,
            start_minute=10 * 60 + 30,
            end_minute=11 * 60 + 30,
            sort_key=(1, 10 * 60 + 30),
        ),
        cp_sat.SubjectContext(
            subject_id=3,
            name="Subject C",
            exam_date="2026-06-01",
            exam_time="14:00-15:00",
            duration_minutes=60,
            start_minute=14 * 60,
            end_minute=15 * 60,
            sort_key=(1, 14 * 60),
        ),
    ]

    pairs = cp_sat._build_consecutive_pairs(subject_contexts)

    assert pairs == [(1, 2), (2, 3)]


def test_build_consecutive_pairs_uses_next_non_overlapping_block() -> None:
    subject_contexts = [
        cp_sat.SubjectContext(
            subject_id=1,
            name="Subject A",
            exam_date="2026-06-01",
            exam_time="09:00-10:00",
            duration_minutes=60,
            start_minute=9 * 60,
            end_minute=10 * 60,
            sort_key=(1, 9 * 60),
        ),
        cp_sat.SubjectContext(
            subject_id=2,
            name="Subject B",
            exam_date="2026-06-01",
            exam_time="09:00-10:00",
            duration_minutes=60,
            start_minute=9 * 60,
            end_minute=10 * 60,
            sort_key=(1, 9 * 60),
        ),
        cp_sat.SubjectContext(
            subject_id=3,
            name="Subject C",
            exam_date="2026-06-01",
            exam_time="10:30-11:30",
            duration_minutes=60,
            start_minute=10 * 60 + 30,
            end_minute=11 * 60 + 30,
            sort_key=(1, 10 * 60 + 30),
        ),
    ]

    pairs = cp_sat._build_consecutive_pairs(subject_contexts)

    assert pairs == [(1, 3), (2, 3)]


def test_build_solution_summary_reports_optimal_only_when_all_stages_are_proven() -> None:
    summary = cp_sat._build_solution_summary(
        final_status=cp_sat.cp_model.OPTIMAL,
        optimal=True,
        stage_reports=[
            {
                "name": "minimize_max_overall_duration",
                "continued_with_locked_value": False,
            }
        ],
        no_improvement_limit_seconds=5,
    )

    assert summary == {
        "status": "OPTIMAL",
        "optimal": True,
        "message": "Solved to proven global optimality.",
    }


def test_build_solution_summary_keeps_feasible_status_after_continued_partial_stage() -> None:
    summary = cp_sat._build_solution_summary(
        final_status=cp_sat.cp_model.OPTIMAL,
        optimal=False,
        stage_reports=[
            {
                "name": "minimize_max_overall_duration",
                "continued_with_locked_value": True,
                "stop_reason": "no_improvement_limit",
                "stop_reason_idle_seconds": 5.2,
            }
        ],
        no_improvement_limit_seconds=5,
    )

    assert summary["status"] == "FEASIBLE"
    assert summary["optimal"] is False
    assert "continued optimizing later tie-breakers" in summary["message"]


def test_build_infeasibility_diagnostic_message_reports_total_capacity_shortfall() -> None:
    teachers = [Teacher("Teacher A", max_sessions=1)]
    schedule = Schedule(teachers, num_subjects=2, num_rooms=1, mode="single")
    subject_contexts = [
        _make_context(1, "Subject A", "2026-06-01", 9, 10),
        _make_context(2, "Subject B", "2026-06-01", 14, 15),
    ]

    message = cp_sat._build_infeasibility_diagnostic_message(
        schedule,
        subject_contexts=subject_contexts,
        rooms_by_subject={1: [1], 2: [1]},
        required_slots=1,
        candidate_teachers={
            (1, 1, 0): [0],
            (2, 1, 0): [0],
        },
        fixed_slots={},
    )

    assert "2" in message
    assert "1" in message


def test_build_infeasibility_diagnostic_message_reports_overlap_capacity_shortfall() -> None:
    teachers = [
        Teacher("Teacher A", max_sessions=2),
        Teacher("Teacher B", max_sessions=2),
        Teacher("Teacher C", max_sessions=1),
    ]
    schedule = Schedule(teachers, num_subjects=3, num_rooms=2, mode="single")
    subject_contexts = [
        _make_context(1, "Subject A", "2026-06-01", 9, 10),
        _make_context(2, "Subject B", "2026-06-01", 9, 10),
        _make_context(3, "Subject C", "2026-06-01", 14, 15),
    ]

    message = cp_sat._build_infeasibility_diagnostic_message(
        schedule,
        subject_contexts=subject_contexts,
        rooms_by_subject={1: [1, 2], 2: [1], 3: [1]},
        required_slots=1,
        candidate_teachers={
            (1, 1, 0): [0],
            (1, 2, 0): [0],
            (2, 1, 0): [1],
            (3, 1, 0): [0, 1, 2],
        },
        fixed_slots={},
    )

    assert "2026-06-01 09:00-10:00" in message
    assert "Subject A" in message
    assert "Subject B" in message


def test_diagnose_locked_assignment_conflicts_reports_overlapping_locked_teacher() -> None:
    teachers = [Teacher("Teacher A", max_sessions=2)]
    schedule = Schedule(teachers, num_subjects=2, num_rooms=1, mode="single")
    subject_contexts = [
        _make_context(1, "Subject A", "2026-06-01", 9, 11),
        _make_context(2, "Subject B", "2026-06-01", 10, 12),
    ]

    message = cp_sat._diagnose_locked_assignment_conflicts(
        schedule,
        fixed_slots={
            (1, 1, 0): 0,
            (2, 1, 0): 0,
        },
        subject_contexts=subject_contexts,
    )

    assert message is not None
    assert "Teacher A" in message


def test_solve_schedule_with_cp_sat_keeps_fixed_double_slot_order_when_symmetry_breaking_is_enabled() -> None:
    teachers = [
        Teacher("Teacher A", gender="M", is_internal=True, max_sessions=1),
        Teacher("Teacher B", gender="F", is_internal=False, max_sessions=1),
    ]
    schedule = Schedule(teachers, num_subjects=1, num_rooms=1, mode="double")
    schedule.set_constraint("subject_durations", [60])
    schedule.set_constraint("subject_room_counts", [1])

    exam = Exam(1, [1])
    exam.schedule[1] = [teachers[1], None]
    schedule.exams = [exam]
    schedule.mark_imported_position(1, 1, 0)

    report = cp_sat.solve_schedule_with_cp_sat(
        schedule,
        [_make_context(1, "Subject A", "2026-06-01", 9, 10)],
        fix_existing_assignments=True,
        use_current_solution_as_hint=True,
        time_limit_seconds=5,
        num_workers=1,
    )

    assert report["status"] in {"OPTIMAL", "FEASIBLE"}
    assigned = schedule.exams[0].schedule[1]
    assert assigned[0].name == "Teacher B"
    assert assigned[1].name == "Teacher A"


def test_solve_schedule_with_cp_sat_supports_negative_previous_durations() -> None:
    teachers = [
        Teacher("Teacher A", max_sessions=1, previous_supervision_duration=-120),
        Teacher("Teacher B", max_sessions=1, previous_supervision_duration=0),
    ]
    schedule = Schedule(teachers, num_subjects=1, num_rooms=1, mode="single")
    schedule.set_constraint("subject_durations", [60])
    schedule.set_constraint("subject_room_counts", [1])

    report = cp_sat.solve_schedule_with_cp_sat(
        schedule,
        [_make_context(1, "Subject A", "2026-06-01", 9, 10)],
        time_limit_seconds=5,
        num_workers=1,
    )

    assert report["status"] in {"OPTIMAL", "FEASIBLE"}
    assert report["metrics"]["overall_duration_min"] == -60
    assert report["metrics"]["overall_duration_max"] == 0
    assert schedule.exams[0].schedule[1][0].name == "Teacher A"


def test_solve_schedule_with_cp_sat_allows_two_female_teachers_when_gender_mix_enabled() -> None:
    teachers = [
        Teacher("Teacher A", gender="F", is_internal=True, max_sessions=1),
        Teacher("Teacher B", gender="F", is_internal=False, max_sessions=1),
    ]
    schedule = Schedule(teachers, num_subjects=1, num_rooms=1, mode="double")
    schedule.set_constraint("gender_mix", True)
    schedule.set_constraint("subject_durations", [60])
    schedule.set_constraint("subject_room_counts", [1])

    report = cp_sat.solve_schedule_with_cp_sat(
        schedule,
        [_make_context(1, "Subject A", "2026-06-01", 9, 10)],
        time_limit_seconds=5,
        num_workers=1,
    )

    assert report["status"] in {"OPTIMAL", "FEASIBLE"}
    assigned = schedule.exams[0].schedule[1]
    assert {teacher.name for teacher in assigned} == {"Teacher A", "Teacher B"}
