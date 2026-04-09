from __future__ import annotations

from typing import Any, Sequence

from backend.proctoring.core.entities import Exam

from .common import SubjectContext, _safe_int


def _apply_solver_result(
    schedule,
    *,
    final_solver,
    slot_vars: dict[tuple[int, tuple[int, int, int]], Any],
    subject_contexts: Sequence[SubjectContext],
    rooms_by_subject: dict[int, list[int]],
    required_slots: int,
) -> None:
    teacher_map = {index: teacher for index, teacher in enumerate(schedule.teachers)}
    for teacher in schedule.teachers:
        teacher.assigned_sessions = []
        teacher.supervision_duration = 0

    exams = []
    exam_by_subject: dict[int, Exam] = {}
    for context in subject_contexts:
        exam = Exam(context.subject_id, list(rooms_by_subject.get(context.subject_id, [])))
        for room in exam.rooms:
            exam.schedule[room] = [None] * required_slots
        exams.append(exam)
        exam_by_subject[context.subject_id] = exam

    for (teacher_index, slot_key), var in slot_vars.items():
        if final_solver.Value(var) != 1:
            continue
        subject_id, room, slot_index = slot_key
        teacher = teacher_map[teacher_index]
        exam = exam_by_subject[subject_id]
        exam.schedule[room][slot_index] = teacher
        duration = next(
            (context.duration_minutes for context in subject_contexts if context.subject_id == subject_id),
            0,
        )
        teacher.assign((subject_id, room), duration)

    schedule.exams = exams

def _set_solution_hints(
    model,
    *,
    solver,
    slot_vars: dict[tuple[int, tuple[int, int, int]], Any],
) -> None:
    if not hasattr(model, "ClearHints"):
        return
    model.ClearHints()
    for var in slot_vars.values():
        model.AddHint(var, solver.Value(var))

def _collect_existing_slot_assignments(
    schedule,
    *,
    teacher_index_by_name: dict[str, int],
    required_slots: int,
    fix_existing_assignments: bool,
) -> tuple[dict[tuple[int, int, int], int], dict[tuple[int, int, int], int]]:
    fixed_slots: dict[tuple[int, int, int], int] = {}
    hinted_slots: dict[tuple[int, int, int], int] = {}

    for exam in schedule.exams or []:
        room_numbers = set()
        room_numbers.update(int(room) for room in getattr(exam, "rooms", []) or [])
        room_numbers.update(int(room) for room in (exam.schedule or {}).keys())
        for room in sorted(room_numbers):
            teachers = list((exam.schedule or {}).get(room, []))
            while len(teachers) < required_slots:
                teachers.append(None)
            for slot_index in range(required_slots):
                teacher = teachers[slot_index] if slot_index < len(teachers) else None
                if teacher is None:
                    continue
                teacher_index = teacher_index_by_name.get(teacher.name)
                if teacher_index is None:
                    continue
                slot_key = (int(exam.subject_id), int(room), int(slot_index))
                hinted_slots[slot_key] = teacher_index
                if fix_existing_assignments or schedule.is_position_imported(*slot_key):
                    fixed_slots[slot_key] = teacher_index
    return fixed_slots, hinted_slots

def _teacher_can_take_slot(
    schedule,
    *,
    teacher,
    teacher_index: int,
    subject_context: SubjectContext,
    room: int,
    slot_index: int,
    teacher_unavailable: dict[int, set[int]],
) -> bool:
    if _safe_int(getattr(teacher, "max_sessions", 0), default=0) <= 0:
        return False

    preset_room = _safe_int(getattr(teacher, "preset_room", None), default=0)
    if preset_room > 0 and preset_room != room:
        return False

    if subject_context.subject_id in teacher_unavailable.get(teacher_index, set()):
        return False

    if schedule.mode == "double" and schedule.get_constraint("internal_mix", False):
        is_internal = getattr(teacher, "is_internal", None)
        if slot_index == 0 and is_internal is not True:
            return False
        if slot_index == 1 and is_internal is not False:
            return False

    return True

def _build_teacher_unavailable_map(
    teachers: Sequence[Any],
    subject_contexts: Sequence[SubjectContext],
) -> dict[int, set[int]]:
    subject_name_to_id = {context.name: context.subject_id for context in subject_contexts if context.name}
    unavailable: dict[int, set[int]] = {}
    for teacher_index, teacher in enumerate(teachers):
        blocked_subjects: set[int] = set()
        for raw_value in getattr(teacher, "unavailable_subjects", []) or []:
            if isinstance(raw_value, int):
                blocked_subjects.add(raw_value)
                continue
            text = str(raw_value).strip()
            if not text:
                continue
            numeric = _safe_int(text, default=0)
            if numeric > 0:
                blocked_subjects.add(numeric)
                continue
            normalized = text.replace("科目", "").strip()
            if normalized in subject_name_to_id:
                blocked_subjects.add(subject_name_to_id[normalized])
        unavailable[teacher_index] = blocked_subjects
    return unavailable

def _build_overlap_pairs(subject_contexts: Sequence[SubjectContext]) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    sorted_subjects = sorted(subject_contexts, key=lambda context: context.sort_key)
    for left_index, left in enumerate(sorted_subjects):
        for right in sorted_subjects[left_index + 1 :]:
            if left.exam_date != right.exam_date:
                continue
            if left.end_minute <= right.start_minute or right.end_minute <= left.start_minute:
                continue
            pairs.append((left.subject_id, right.subject_id))
    return pairs

def _build_consecutive_pairs(
    subject_contexts: Sequence[SubjectContext],
    *,
    gap_minutes: int,
) -> list[tuple[int, int]]:
    del gap_minutes
    pairs: list[tuple[int, int]] = []
    contexts_by_day: dict[str, list[SubjectContext]] = {}
    for context in subject_contexts:
        contexts_by_day.setdefault(context.exam_date, []).append(context)

    for same_day_contexts in contexts_by_day.values():
        sorted_subjects = sorted(
            same_day_contexts,
            key=lambda context: (
                context.start_minute,
                context.end_minute,
                context.subject_id,
            ),
        )
        blocks: list[dict[str, Any]] = []
        for context in sorted_subjects:
            if (
                blocks
                and blocks[-1]["start"] == context.start_minute
                and blocks[-1]["end"] == context.end_minute
            ):
                blocks[-1]["subject_ids"].append(context.subject_id)
                continue
            blocks.append(
                {
                    "start": context.start_minute,
                    "end": context.end_minute,
                    "subject_ids": [context.subject_id],
                }
            )

        for index, current_block in enumerate(blocks):
            next_block = next(
                (
                    candidate
                    for candidate in blocks[index + 1 :]
                    if int(candidate["start"]) >= int(current_block["end"])
                ),
                None,
            )
            if next_block is None:
                continue
            for left_subject_id in current_block["subject_ids"]:
                for right_subject_id in next_block["subject_ids"]:
                    pairs.append((int(left_subject_id), int(right_subject_id)))
    return pairs
