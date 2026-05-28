from __future__ import annotations

from backend.proctoring.core.entities import Exam, Teacher
from backend.proctoring.core.models import Schedule


def _build_double_schedule(*teachers: Teacher) -> Schedule:
    schedule = Schedule(list(teachers), num_subjects=1, num_rooms=2, mode="double")
    schedule.set_constraint("gender_mix", True)
    schedule.set_constraint("subject_durations", [120])
    exam = Exam(1, [1, 2])
    schedule.exams = [exam]
    return schedule


def test_swap_teachers_allows_female_female_pair_when_gender_mix_enabled() -> None:
    male_teacher = Teacher("Teacher A", gender="M", is_internal=True, max_sessions=1)
    female_teacher_1 = Teacher("Teacher B", gender="F", is_internal=True, max_sessions=1)
    female_teacher_2 = Teacher("Teacher C", gender="F", is_internal=False, max_sessions=1)
    female_teacher_3 = Teacher("Teacher D", gender="F", is_internal=False, max_sessions=1)
    schedule = _build_double_schedule(
        male_teacher,
        female_teacher_1,
        female_teacher_2,
        female_teacher_3,
    )
    exam = schedule.exams[0]
    exam.schedule[1] = [male_teacher, female_teacher_1]
    exam.schedule[2] = [female_teacher_2, female_teacher_3]
    male_teacher.assign((1, 1), 120)
    female_teacher_1.assign((1, 1), 120)
    female_teacher_2.assign((1, 2), 120)
    female_teacher_3.assign((1, 2), 120)

    ok, message = schedule.swap_teachers((1, 1, 0), (1, 2, 0))

    assert ok is True
    assert message == "交换成功"
    assert exam.schedule[1][0].name == "Teacher C"
    assert exam.schedule[1][1].name == "Teacher B"
    assert exam.schedule[2][0].name == "Teacher A"
    assert exam.schedule[2][1].name == "Teacher D"


def test_swap_teachers_still_rejects_two_male_pair_when_gender_mix_enabled() -> None:
    male_teacher_1 = Teacher("Teacher A", gender="M", is_internal=True, max_sessions=1)
    female_teacher_1 = Teacher("Teacher B", gender="F", is_internal=True, max_sessions=1)
    male_teacher_2 = Teacher("Teacher C", gender="M", is_internal=False, max_sessions=1)
    female_teacher_2 = Teacher("Teacher D", gender="F", is_internal=False, max_sessions=1)
    schedule = _build_double_schedule(
        male_teacher_1,
        female_teacher_1,
        male_teacher_2,
        female_teacher_2,
    )
    exam = schedule.exams[0]
    exam.schedule[1] = [male_teacher_1, female_teacher_1]
    exam.schedule[2] = [male_teacher_2, female_teacher_2]
    male_teacher_1.assign((1, 1), 120)
    female_teacher_1.assign((1, 1), 120)
    male_teacher_2.assign((1, 2), 120)
    female_teacher_2.assign((1, 2), 120)

    ok, message = schedule.swap_teachers((1, 1, 1), (1, 2, 0))

    assert ok is False
    assert "性别不匹配" in message
