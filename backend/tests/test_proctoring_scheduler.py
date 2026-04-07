from __future__ import annotations

from backend.proctoring.core.entities import Teacher
from backend.proctoring.core.models import Schedule


def test_generate_and_continue_schedule_complete_simple_single_mode() -> None:
    teachers = [
        Teacher("Teacher A", gender="F", is_internal=True, max_sessions=1),
        Teacher("Teacher B", gender="M", is_internal=True, max_sessions=1),
    ]
    schedule = Schedule(teachers, num_subjects=1, num_rooms=1, mode="single")
    schedule.set_constraint("subject_durations", [120])
    schedule.set_constraint("shuffle_teachers", False)

    _exams, unassigned = schedule.generate_schedule()
    success, message = schedule.continue_schedule()

    assert unassigned == 0
    assert success is True
    assert message == "安排完成"
    assert schedule.is_schedule_complete() is True
    assert schedule.exams[0].schedule[1][0] is not None
