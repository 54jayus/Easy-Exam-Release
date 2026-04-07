#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post-processing helpers for proctoring scheduling."""


def enforce_preset_room_postprocess(schedule):
    """Move teachers toward their preset room when a safe same-subject swap exists."""
    moves = 0
    details = []
    required_slots = 2 if schedule.mode == "double" else 1

    for exam in schedule.exams:
        subject_id = exam.subject_id
        for room in exam.rooms:
            if room not in exam.schedule:
                exam.schedule[room] = []
            while len(exam.schedule[room]) < required_slots:
                exam.schedule[room].append(None)

        for room in exam.rooms:
            teachers = exam.schedule.get(room, [])
            while len(teachers) < required_slots:
                teachers.append(None)
            for idx, teacher in enumerate(list(teachers)):
                if not teacher:
                    continue
                try:
                    preset = teacher.preset_room
                except Exception:
                    preset = None
                if preset is None or preset == room:
                    continue

                target_room = int(preset)
                if target_room not in exam.schedule:
                    exam.schedule[target_room] = []
                while len(exam.schedule[target_room]) < required_slots:
                    exam.schedule[target_room].append(None)

                if schedule.get_constraint("lock_imported"):
                    try:
                        if schedule.is_position_imported(subject_id, room, idx):
                            continue
                    except Exception:
                        pass

                dest_indices = [0] if schedule.mode == "single" else [0, 1]
                for dest_idx in dest_indices:
                    if schedule.get_constraint("lock_imported"):
                        try:
                            if schedule.is_position_imported(subject_id, target_room, dest_idx):
                                continue
                        except Exception:
                            pass

                    dest_teacher = None
                    try:
                        dest_teacher = exam.schedule[target_room][dest_idx]
                    except Exception:
                        dest_teacher = None

                    if dest_teacher and getattr(dest_teacher, "preset_room", None) is not None:
                        try:
                            dest_preset = int(dest_teacher.preset_room)
                        except Exception:
                            dest_preset = None
                        if dest_preset is not None and dest_preset == int(target_room):
                            continue

                    ok, _msg = schedule.swap_teachers(
                        (subject_id, room, idx),
                        (subject_id, target_room, dest_idx),
                    )
                    if ok:
                        moves += 1
                        details.append({
                            "subject": subject_id,
                            "from_room": room,
                            "to_room": target_room,
                            "teacher": getattr(teacher, "name", ""),
                        })
                        break

    return {"moves": moves, "details": details}
