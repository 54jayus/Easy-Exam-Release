"""Tests for the avoid-rooms (回避考场) feature."""
from __future__ import annotations

from backend.proctoring.core.cp_sat.assignment import _teacher_can_take_slot
from backend.proctoring.core.cp_sat.common import SubjectContext
from backend.proctoring.core.cp_sat.diagnostics import _validate_preset_rooms
from backend.proctoring.core.entities import Exam, Teacher
from backend.proctoring.core.models import Schedule


# ---------------------------------------------------------------------------
# _teacher_can_take_slot
# ---------------------------------------------------------------------------

def _make_subject_context(subject_id: int = 1) -> SubjectContext:
    return SubjectContext(
        subject_id=subject_id,
        name=f"科目{subject_id}",
        exam_date="2025-06-01",
        exam_time="09:00-11:00",
        duration_minutes=120,
        start_minute=540,
        end_minute=660,
        sort_key=subject_id,
    )


def test_teacher_can_take_slot_rejects_avoided_room() -> None:
    """Teacher should NOT be assigned to a room in their avoid_rooms list."""
    teacher = Teacher("T1", gender="M", is_internal=True, max_sessions=5)
    teacher.avoid_rooms = [3, 5]
    schedule = Schedule([teacher], num_subjects=1, num_rooms=5, mode="single")

    ctx = _make_subject_context()
    # Room 3 is avoided -> should be rejected
    assert _teacher_can_take_slot(
        schedule,
        teacher=teacher,
        teacher_index=0,
        subject_context=ctx,
        room=3,
        slot_index=0,
        teacher_unavailable={},
        enforce_double_slot_roles=False,
    ) is False


def test_teacher_can_take_slot_allows_non_avoided_room() -> None:
    """Teacher CAN be assigned to a room NOT in their avoid_rooms list."""
    teacher = Teacher("T1", gender="M", is_internal=True, max_sessions=5)
    teacher.avoid_rooms = [3, 5]
    schedule = Schedule([teacher], num_subjects=1, num_rooms=5, mode="single")

    ctx = _make_subject_context()
    # Room 1 is not avoided -> should be allowed
    assert _teacher_can_take_slot(
        schedule,
        teacher=teacher,
        teacher_index=0,
        subject_context=ctx,
        room=1,
        slot_index=0,
        teacher_unavailable={},
        enforce_double_slot_roles=False,
    ) is True


def test_teacher_can_take_slot_allows_when_avoid_rooms_empty() -> None:
    """Teacher with empty avoid_rooms can be assigned to any room."""
    teacher = Teacher("T1", gender="M", is_internal=True, max_sessions=5)
    teacher.avoid_rooms = []
    schedule = Schedule([teacher], num_subjects=1, num_rooms=5, mode="single")

    ctx = _make_subject_context()
    for room in range(1, 6):
        assert _teacher_can_take_slot(
            schedule,
            teacher=teacher,
            teacher_index=0,
            subject_context=ctx,
            room=room,
            slot_index=0,
            teacher_unavailable={},
            enforce_double_slot_roles=False,
        ) is True


def test_preset_room_takes_precedence_over_avoid_rooms() -> None:
    """If preset_room is set, teacher is locked to that room regardless of avoid_rooms.

    The validation layer should have already removed conflicts, but even if
    avoid_rooms contains the preset room, the preset_room check fires first
    and rejects other rooms, while the avoided room is never reached because
    the teacher is only eligible for the preset room.
    """
    teacher = Teacher("T1", gender="M", is_internal=True, max_sessions=5)
    teacher.preset_room = 2
    teacher.avoid_rooms = [2, 3]  # conflict that validation should catch
    schedule = Schedule([teacher], num_subjects=1, num_rooms=5, mode="single")

    ctx = _make_subject_context()
    # Room 1: rejected because preset_room=2 != 1
    assert _teacher_can_take_slot(
        schedule, teacher=teacher, teacher_index=0, subject_context=ctx,
        room=1, slot_index=0, teacher_unavailable={}, enforce_double_slot_roles=False,
    ) is False
    # Room 2: allowed by preset (avoid check would reject, but preset is checked first)
    # Actually in our code, preset is checked FIRST, then avoid. So room 2 passes preset
    # but is then blocked by avoid. This is fine -- validation should prevent this case.
    # We test the actual code behavior here:
    result = _teacher_can_take_slot(
        schedule, teacher=teacher, teacher_index=0, subject_context=ctx,
        room=2, slot_index=0, teacher_unavailable={}, enforce_double_slot_roles=False,
    )
    # With both preset_room=2 and avoid_rooms=[2,3], room 2 passes preset check
    # but fails avoid check -> False. The validation layer prevents this in practice.
    assert result is False


# ---------------------------------------------------------------------------
# swap_teachers
# ---------------------------------------------------------------------------

def test_swap_blocked_by_avoid_room() -> None:
    """Manual swap should be blocked when target room is in teacher's avoid_rooms."""
    teacher1 = Teacher("T1", gender="M", is_internal=True, max_sessions=2)
    teacher1.avoid_rooms = [2]
    teacher2 = Teacher("T2", gender="F", is_internal=False, max_sessions=2)

    schedule = Schedule([teacher1, teacher2], num_subjects=1, num_rooms=2, mode="single")
    schedule.set_constraint("subject_durations", [120])
    exam = Exam(1, [1, 2])
    exam.schedule = {1: [teacher1], 2: [teacher2]}
    schedule.exams = [exam]
    teacher1.assign((1, 1), 120)
    teacher2.assign((1, 2), 120)

    # Swap T1 (room 1) with T2 (room 2) -- T1 avoids room 2 -> should fail
    ok, message = schedule.swap_teachers((1, 1, 0), (1, 2, 0))
    assert ok is False
    assert "回避考场" in message
    assert "2" in message


def test_swap_allowed_when_no_avoid_conflict() -> None:
    """Manual swap should succeed when no avoid_rooms conflict."""
    teacher1 = Teacher("T1", gender="M", is_internal=True, max_sessions=2)
    teacher1.avoid_rooms = [3]  # avoids room 3, not room 2
    teacher2 = Teacher("T2", gender="F", is_internal=False, max_sessions=2)

    schedule = Schedule([teacher1, teacher2], num_subjects=1, num_rooms=3, mode="single")
    schedule.set_constraint("subject_durations", [120])
    exam = Exam(1, [1, 2, 3])
    exam.schedule = {1: [teacher1], 2: [teacher2], 3: [None]}
    schedule.exams = [exam]
    teacher1.assign((1, 1), 120)
    teacher2.assign((1, 2), 120)

    # Swap T1 (room 1) with T2 (room 2) -- T1 avoids room 3, not 2 -> should succeed
    ok, message = schedule.swap_teachers((1, 1, 0), (1, 2, 0))
    assert ok is True
    assert message == "交换成功"


# ---------------------------------------------------------------------------
# _validate_preset_rooms  (diagnostics)
# ---------------------------------------------------------------------------

def test_validate_preset_rooms_reports_avoid_room_out_of_range() -> None:
    """Validation should catch avoid_rooms values exceeding room_count."""
    teacher = Teacher("T1", max_sessions=5)
    teacher.avoid_rooms = [10]
    error = _validate_preset_rooms([teacher], room_count=5)
    assert error is not None
    assert "回避" in error
    assert "10" in error


def test_validate_preset_rooms_reports_preset_conflicts_with_avoid() -> None:
    """Validation should catch preset_room appearing in avoid_rooms."""
    teacher = Teacher("T1", max_sessions=5)
    teacher.preset_room = 3
    teacher.avoid_rooms = [3, 5]
    error = _validate_preset_rooms([teacher], room_count=5)
    assert error is not None
    assert "冲突" in error


def test_validate_preset_rooms_passes_valid_avoid_rooms() -> None:
    """Validation should pass when avoid_rooms are valid and no conflicts."""
    teacher = Teacher("T1", max_sessions=5)
    teacher.preset_room = 1
    teacher.avoid_rooms = [3, 5]
    error = _validate_preset_rooms([teacher], room_count=5)
    assert error is None


# ---------------------------------------------------------------------------
# data_import  (Excel parsing)
# ---------------------------------------------------------------------------

def test_data_import_parses_avoid_rooms_from_excel(tmp_path) -> None:
    """import_teachers_from_excel should parse the 回避考场 column."""
    import pandas as pd
    from backend.proctoring.core.data_import import DataImporter

    df = pd.DataFrame([
        {"姓名": "张三", "性别": "男", "是否本校": "是", "最大监考段数": 3,
         "不监考科目": "", "历次监考时长": 0, "预设监考考场": "", "回避考场": "2,4"},
        {"姓名": "李四", "性别": "女", "是否本校": "否", "最大监考段数": 2,
         "不监考科目": "", "历次监考时长": 0, "预设监考考场": "", "回避考场": ""},
        {"姓名": "王五", "性别": "男", "是否本校": "是", "最大监考段数": 4,
         "不监考科目": "", "历次监考时长": 0, "预设监考考场": "", "回避考场": "考场3"},
    ])
    file_path = str(tmp_path / "teachers.xlsx")
    df.to_excel(file_path, index=False)

    teachers = DataImporter.import_teachers_from_excel(file_path)
    assert len(teachers) == 3
    assert teachers[0].avoid_rooms == [2, 4]
    assert teachers[1].avoid_rooms == []
    assert teachers[2].avoid_rooms == [3]


def test_data_import_validate_catches_preset_avoid_conflict(tmp_path) -> None:
    """validate_teachers should warn when preset_room is in avoid_rooms."""
    import pandas as pd
    from backend.proctoring.core.data_import import DataImporter

    df = pd.DataFrame([
        {"姓名": "张三", "性别": "男", "是否本校": "是", "最大监考段数": 3,
         "不监考科目": "", "历次监考时长": 0, "预设监考考场": "3", "回避考场": "2,3"},
    ])
    file_path = str(tmp_path / "teachers.xlsx")
    df.to_excel(file_path, index=False)

    teachers = DataImporter.import_teachers_from_excel(file_path)
    errors, warnings = DataImporter.validate_teachers(
        teachers, mode="single", num_rooms=5, subject_count=3,
        subject_names=["语文", "数学", "英语"], source_file_path=file_path,
    )
    # Should have a warning about the conflict
    conflict_warnings = [w for w in warnings if "冲突" in w or "回避" in w]
    assert len(conflict_warnings) > 0
    # After validation, preset_room=3 should be removed from avoid_rooms
    assert 3 not in teachers[0].avoid_rooms


def test_data_import_validate_catches_avoid_room_out_of_range(tmp_path) -> None:
    """validate_teachers should warn when avoid_rooms contains out-of-range values."""
    import pandas as pd
    from backend.proctoring.core.data_import import DataImporter

    df = pd.DataFrame([
        {"姓名": "张三", "性别": "男", "是否本校": "是", "最大监考段数": 3,
         "不监考科目": "", "历次监考时长": 0, "预设监考考场": "", "回避考场": "1,99"},
    ])
    file_path = str(tmp_path / "teachers.xlsx")
    df.to_excel(file_path, index=False)

    teachers = DataImporter.import_teachers_from_excel(file_path)
    errors, warnings = DataImporter.validate_teachers(
        teachers, mode="single", num_rooms=5, subject_count=3,
        subject_names=["语文", "数学", "英语"], source_file_path=file_path,
    )
    # Should have a warning about out-of-range
    out_of_range_warnings = [w for w in warnings if "越界" in w]
    assert len(out_of_range_warnings) > 0
    # 99 should be removed, 1 should remain
    assert teachers[0].avoid_rooms == [1]


# ---------------------------------------------------------------------------
# Integration: CP-SAT solver respects avoid_rooms end-to-end
# ---------------------------------------------------------------------------

def test_cp_sat_solver_respects_avoid_rooms() -> None:
    """Full integration test: run CP-SAT solver and verify avoid_rooms is honored."""
    from backend.proctoring.core.cp_sat import solve_schedule_with_cp_sat
    from backend.proctoring.core.cp_sat.common import SubjectContext

    # 3 teachers, 1 subject, 3 rooms
    # T1 avoids room 3, T2 avoids room 1, T3 has no restrictions
    t1 = Teacher("T1", gender="M", is_internal=True, max_sessions=3)
    t1.avoid_rooms = [3]
    t2 = Teacher("T2", gender="F", is_internal=False, max_sessions=3)
    t2.avoid_rooms = [1]
    t3 = Teacher("T3", gender="M", is_internal=True, max_sessions=3)

    schedule = Schedule([t1, t2, t3], num_subjects=1, num_rooms=3, mode="single")
    schedule.set_constraint("subject_durations", [120])
    schedule.set_constraint("subject_room_counts", [3])
    schedule.set_constraint("balance_mode", "duration")

    subject_contexts = [
        SubjectContext(
            subject_id=1, name="语文", exam_date="2025-06-01",
            exam_time="09:00-11:00", duration_minutes=120,
            start_minute=540, end_minute=660, sort_key=1,
        ),
    ]

    result = solve_schedule_with_cp_sat(
        schedule=schedule,
        subject_contexts=subject_contexts,
        fix_existing_assignments=False,
        use_current_solution_as_hint=False,
        time_limit_seconds=10,
    )

    assert result["status"] in ("OPTIMAL", "FEASIBLE"), f"Solver failed: {result}"

    # Verify avoid_rooms constraints
    for exam in schedule.exams:
        for room_num, teachers_in_room in exam.schedule.items():
            for t in teachers_in_room:
                if t is None:
                    continue
                avoid = getattr(t, "avoid_rooms", []) or []
                assert room_num not in avoid, (
                    f"{t.name} was assigned to room {room_num} but avoids it! "
                    f"(avoid_rooms={avoid})"
                )
