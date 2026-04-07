from __future__ import annotations

from backend.proctoring.core.entities import Exam, Teacher
from backend.proctoring.core.models import Schedule


def test_enforce_preset_room_postprocess_moves_teacher_to_preset_room() -> None:
    teacher = Teacher("Teacher A", gender="F", is_internal=True, max_sessions=2)
    teacher.preset_room = 2

    schedule = Schedule([teacher], num_subjects=1, num_rooms=2, mode="single")
    schedule.set_constraint("subject_durations", [120])

    exam = Exam(1, [1, 2])
    exam.schedule[1] = [teacher]
    exam.schedule[2] = [None]
    schedule.exams = [exam]

    teacher.assign((1, 1), 120)

    report = schedule.enforce_preset_room_postprocess()

    assert report == {
        "moves": 1,
        "details": [{"subject": 1, "from_room": 1, "to_room": 2, "teacher": "Teacher A"}],
    }
    assert exam.schedule[1][0] is None
    assert exam.schedule[2][0] is teacher
    assert teacher.assigned_sessions == [(1, 2)]
