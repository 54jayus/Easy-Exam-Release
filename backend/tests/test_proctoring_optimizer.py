from __future__ import annotations

from backend.proctoring.core.entities import Exam, Teacher
from backend.proctoring.core.models import Schedule


def test_optimize_duration_postprocess_preserves_report_contract_and_reduces_peak_load() -> None:
    teacher_a = Teacher("Teacher A", gender="F", is_internal=True, max_sessions=4)
    teacher_b = Teacher("Teacher B", gender="M", is_internal=True, max_sessions=4)
    teacher_c = Teacher("Teacher C", gender="F", is_internal=True, max_sessions=4)

    schedule = Schedule([teacher_a, teacher_b, teacher_c], num_subjects=3, num_rooms=1, mode="single")
    schedule.set_constraint("subject_durations", [120, 90, 60])

    exam1 = Exam(1, [1])
    exam2 = Exam(2, [1])
    exam3 = Exam(3, [1])
    exam1.schedule[1] = [teacher_a]
    exam2.schedule[1] = [teacher_a]
    exam3.schedule[1] = [teacher_b]
    schedule.exams = [exam1, exam2, exam3]

    teacher_a.assign((1, 1), 120)
    teacher_a.assign((2, 1), 90)
    teacher_b.assign((3, 1), 60)

    report = schedule.optimize_duration_postprocess(max_passes=5, enable_smoothing=False)

    assert report["swap_count"] >= 1
    assert report["before"]["max_overall"] == 210
    assert report["before"]["max_current"] == 210
    assert report["after"]["max_overall"] < report["before"]["max_overall"]
    assert report["after"]["max_current"] <= report["before"]["max_current"]
    assert report["swaps"]
    assert report["swaps"][0]["heavy"] == "Teacher A"
    assert report["swaps"][0]["light"] == "Teacher B"

    assert set(teacher_a.assigned_sessions) == {(2, 1), (3, 1)}
    assert set(teacher_b.assigned_sessions) == {(1, 1)}
