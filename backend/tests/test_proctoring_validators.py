from __future__ import annotations

from backend.proctoring.core.entities import Exam, Teacher
from backend.proctoring.core.models import Schedule


def test_check_feasibility_reports_insufficient_capacity() -> None:
    teachers = [
        Teacher("Teacher A", gender="F", is_internal=True, max_sessions=1),
        Teacher("Teacher B", gender="M", is_internal=True, max_sessions=1),
    ]
    schedule = Schedule(teachers, num_subjects=3, num_rooms=1, mode="single")

    feasible, reason = schedule.check_feasibility()

    assert feasible is False
    assert "全局监考名额不足" in reason


def test_get_statistics_keeps_original_teacher_order() -> None:
    teacher_a = Teacher("Teacher A", gender="F", is_internal=True, max_sessions=2)
    teacher_b = Teacher("Teacher B", gender="M", is_internal=True, max_sessions=2)
    schedule = Schedule([teacher_a, teacher_b], num_subjects=1, num_rooms=1, mode="single")
    schedule.original_teachers_order = [teacher_b, teacher_a]

    teacher_a.assign((1, 1), 120)

    assert schedule.get_statistics() == [
        {"name": "Teacher B", "count": 0},
        {"name": "Teacher A", "count": 1},
    ]


def test_is_schedule_complete_respects_double_mode_slot_requirement() -> None:
    teacher_a = Teacher("Teacher A", gender="F", is_internal=True, max_sessions=2)
    teacher_b = Teacher("Teacher B", gender="M", is_internal=False, max_sessions=2)
    schedule = Schedule([teacher_a, teacher_b], num_subjects=1, num_rooms=1, mode="double")

    exam = Exam(1, [1])
    exam.schedule[1] = [teacher_a]
    schedule.exams = [exam]
    assert schedule.is_schedule_complete() is False

    exam.schedule[1] = [teacher_a, teacher_b]
    assert schedule.is_schedule_complete() is True
