from __future__ import annotations

import itertools
import secrets
from functools import lru_cache

import pandas as pd


def _is_physics_subject(subject: str) -> bool:
    text = str(subject or "").strip()
    return text.startswith("物") or text.startswith("理")


def _is_history_subject(subject: str) -> bool:
    text = str(subject or "").strip()
    return text.startswith("史")


def _get_subject_category(subject: str) -> str:
    if _is_physics_subject(subject):
        return "physics"
    if _is_history_subject(subject):
        return "history"
    return "history"


def _get_room_specs(arrangement):
    if arrangement.room_setting_data:
        room_numbers = sorted(
            arrangement.room_setting_data.keys(),
            key=lambda value: int(value) if str(value).isdigit() else float("inf"),
        )
        arrangement.total_rooms = len(room_numbers)
    else:
        room_numbers = [i + 1 for i in range(arrangement.total_rooms)]

    return [{"room_num": room_num, "capacity": arrangement.get_room_capacity(room_num)} for room_num in room_numbers]


def _get_subject_priority_map(arrangement) -> dict[str, int]:
    default_order = ["化学", "生物", "政治", "地理"]
    configured = getattr(arrangement, "subject_priority_order", None)
    if not isinstance(configured, list):
        configured = list(default_order)

    normalized = []
    for subject in configured:
        text = str(subject or "").strip()
        if text and text not in normalized:
            normalized.append(text)
    for subject in default_order:
        if subject not in normalized:
            normalized.append(subject)
    return {subject: index for index, subject in enumerate(normalized)}


def _subject_sort_key(arrangement, subject: str, subject_counts: dict[str, int]):
    parsed = arrangement.parse_subject_combination(subject)
    priority_map = _get_subject_priority_map(arrangement)
    secondary_key = tuple(sorted(priority_map.get(name, len(priority_map)) for name in parsed[1:]))
    return (-subject_counts.get(subject, 0), secondary_key, subject)


def _sort_subject_keys(arrangement, subject_counts: dict[str, int]) -> list[str]:
    return sorted(subject_counts, key=lambda subject: _subject_sort_key(arrangement, subject, subject_counts))


def _build_student_groups(arrangement):
    subject_counts = arrangement.students[arrangement.subject_column].value_counts().to_dict()
    ordered_subjects = _sort_subject_keys(arrangement, subject_counts)
    student_groups = {}

    for subject in ordered_subjects:
        mask = arrangement.students[arrangement.subject_column] == subject
        subject_students = arrangement.students[mask]
        if len(subject_students) > 1:
            random_state = secrets.randbelow(2**32)
            subject_students = subject_students.sample(frac=1, random_state=random_state)
        student_groups[subject] = subject_students.to_dict("records")

    return student_groups


def initialize_rooms(arrangement):
    return [{"room_num": spec["room_num"], "students": [], "subjects": set()} for spec in _get_room_specs(arrangement)]


def group_and_sort_subjects(arrangement):
    subject_counts = arrangement.students[arrangement.subject_column].value_counts().to_dict()
    physics_subjects = {
        subject: count for subject, count in subject_counts.items() if _is_physics_subject(str(subject))
    }
    history_subjects = {
        subject: count for subject, count in subject_counts.items() if _is_history_subject(str(subject))
    }

    ordered_physics = _sort_subject_keys(arrangement, physics_subjects)
    ordered_history = _sort_subject_keys(arrangement, history_subjects)
    return (
        {subject: physics_subjects[subject] for subject in ordered_physics},
        {subject: history_subjects[subject] for subject in ordered_history},
    )


def assign_large_groups(arrangement, rooms, physics_subjects, history_subjects):
    ordered_subjects = list(physics_subjects.items()) + list(history_subjects.items())
    remaining_students = []
    current_room_index = 0

    for subject, count in ordered_subjects:
        if count <= arrangement.SMALL_GROUP_THRESHOLD:
            mask = arrangement.students[arrangement.subject_column] == subject
            remaining_students.extend(arrangement.students[mask].to_dict("records"))
            continue

        mask = arrangement.students[arrangement.subject_column] == subject
        subject_students = arrangement.students[mask]

        if len(subject_students) > 1:
            random_state = secrets.randbelow(2**32)
            subject_students = subject_students.sample(frac=1, random_state=random_state)

        subject_students_list = subject_students.to_dict("records")
        current_subject_idx = 0
        total_subject_count = len(subject_students_list)

        while current_room_index < len(rooms):
            current_room = rooms[current_room_index]
            room_capacity = arrangement.get_room_capacity(current_room["room_num"])
            remaining_count = total_subject_count - current_subject_idx

            if remaining_count < room_capacity:
                break

            end_idx = current_subject_idx + room_capacity
            current_room["students"] = subject_students_list[current_subject_idx:end_idx]
            current_room["subjects"].add(subject)
            current_subject_idx = end_idx
            current_room_index += 1

        if current_subject_idx < total_subject_count:
            remaining_students.extend(subject_students_list[current_subject_idx:])

    return current_room_index, remaining_students


def sort_students_by_subject_count(arrangement, students_list):
    if not students_list:
        return students_list

    students_df = pd.DataFrame(students_list)
    subject_counts = students_df[arrangement.subject_column].value_counts().to_dict()
    students_df["_sort_key"] = students_df[arrangement.subject_column].map(subject_counts)
    sorted_df = students_df.sort_values("_sort_key", ascending=False).drop("_sort_key", axis=1)
    return sorted_df.to_dict("records")


def get_room_category(arrangement, room, physics_students, history_students):
    if room["students"]:
        first_subject = room["students"][0].get(arrangement.subject_column, "")
        return _get_subject_category(str(first_subject))

    return "physics" if len(physics_students) >= len(history_students) else "history"


def assign_remaining_students(arrangement, rooms, remaining_students, current_room_index):
    if not remaining_students:
        return

    remaining_df = pd.DataFrame(remaining_students)
    physics_mask = remaining_df[arrangement.subject_column].fillna("").astype(str).map(_is_physics_subject)
    history_mask = remaining_df[arrangement.subject_column].fillna("").astype(str).map(_is_history_subject)

    physics_students = remaining_df[physics_mask].to_dict("records")
    history_students = remaining_df[history_mask | ~(physics_mask | history_mask)].to_dict("records")

    physics_students = sort_students_by_subject_count(arrangement, physics_students)
    history_students = sort_students_by_subject_count(arrangement, history_students)

    while current_room_index < len(rooms) and (physics_students or history_students):
        current_room = rooms[current_room_index]
        room_capacity = arrangement.get_room_capacity(current_room["room_num"])
        available_seats = room_capacity - len(current_room["students"])

        if available_seats <= 0:
            current_room_index += 1
            continue

        room_category = get_room_category(arrangement, current_room, physics_students, history_students)
        source_students = physics_students if room_category == "physics" else history_students

        fill_count = min(available_seats, len(source_students))
        if fill_count > 0:
            batch = source_students[:fill_count]
            current_room["students"].extend(batch)
            for student in batch:
                current_room["subjects"].add(student[arrangement.subject_column])

            if room_category == "physics":
                physics_students = physics_students[fill_count:]
            else:
                history_students = history_students[fill_count:]

        current_room_index += 1


def _count_room_mixed(room) -> int:
    return 1 if len(room["subjects"]) > 1 else 0


def _get_room_available_seats(arrangement, room) -> int:
    room_capacity = arrangement.get_room_capacity(room["room_num"])
    return max(0, room_capacity - len(room["students"]))


def _build_room_subject_groups(arrangement, room):
    grouped = {}
    for student in room["students"]:
        subject = str(student.get(arrangement.subject_column, "")).strip()
        grouped.setdefault(subject, []).append(student)
    return grouped


def _room_accepts_subject_without_new_mix(arrangement, room, subject: str) -> bool:
    if not room["students"]:
        return True
    if subject in room["subjects"]:
        return True
    if len(room["subjects"]) > 1:
        first_subject = room["students"][0].get(arrangement.subject_column, "")
        return _get_subject_category(subject) == _get_subject_category(first_subject)
    return False


def _allocate_students_to_target_rooms(arrangement, rooms, source_room, subject: str, students_to_move):
    remaining = list(students_to_move)
    candidate_rooms = []

    for room in rooms:
        if room is source_room:
            continue

        available_seats = _get_room_available_seats(arrangement, room)
        if available_seats <= 0:
            continue
        if not _room_accepts_subject_without_new_mix(arrangement, room, subject):
            continue

        if not room["students"]:
            priority = 2
        elif subject in room["subjects"]:
            priority = 0
        else:
            priority = 1
        candidate_rooms.append((priority, -available_seats, room))

    candidate_rooms.sort(key=lambda item: (item[0], item[1]))
    assignments = []

    for _, _, room in candidate_rooms:
        if not remaining:
            break
        move_count = min(_get_room_available_seats(arrangement, room), len(remaining))
        if move_count <= 0:
            continue
        batch = remaining[:move_count]
        remaining = remaining[move_count:]
        assignments.append((room, batch))

    if remaining:
        return None
    return assignments


def reduce_mixed_rooms(arrangement, rooms):
    changed = True

    while changed:
        changed = False
        mixed_rooms = [room for room in rooms if len(room["subjects"]) > 1]

        for source_room in mixed_rooms:
            source_groups = _build_room_subject_groups(arrangement, source_room)
            current_mixed_count = sum(_count_room_mixed(room) for room in rooms)

            ordered_subjects = sorted(source_groups.items(), key=lambda item: len(item[1]))
            for subject, students_to_move in ordered_subjects:
                assignments = _allocate_students_to_target_rooms(arrangement, rooms, source_room, subject, students_to_move)
                if not assignments:
                    continue

                for room, batch in assignments:
                    room["students"].extend(batch)
                    room["subjects"].update(str(student.get(arrangement.subject_column, "")).strip() for student in batch)

                moved_ids = {id(student) for student in students_to_move}
                source_room["students"] = [student for student in source_room["students"] if id(student) not in moved_ids]
                source_room["subjects"] = {
                    str(student.get(arrangement.subject_column, "")).strip()
                    for student in source_room["students"]
                    if str(student.get(arrangement.subject_column, "")).strip()
                }

                next_mixed_count = sum(_count_room_mixed(room) for room in rooms)
                if next_mixed_count < current_mixed_count:
                    changed = True
                    break

                for room, batch in assignments:
                    moved_ids_batch = {id(student) for student in batch}
                    room["students"] = [student for student in room["students"] if id(student) not in moved_ids_batch]
                    room["subjects"] = {
                        str(student.get(arrangement.subject_column, "")).strip()
                        for student in room["students"]
                        if str(student.get(arrangement.subject_column, "")).strip()
                    }

                source_room["students"].extend(students_to_move)
                source_room["subjects"] = {
                    str(student.get(arrangement.subject_column, "")).strip()
                    for student in source_room["students"]
                    if str(student.get(arrangement.subject_column, "")).strip()
                }

            if changed:
                break


def _score_room_plans(room_plans) -> tuple[int, int, int, int]:
    mixed_rooms = 0
    extra_groups = 0
    empty_seats = 0

    for room_plan in room_plans:
        active_subjects = [subject for subject, count in room_plan["assignments"].items() if count > 0]
        if len(active_subjects) > 1:
            mixed_rooms += 1
            extra_groups += len(active_subjects) - 1
        empty_seats += room_plan["capacity"] - sum(room_plan["assignments"].values())

    return mixed_rooms, extra_groups, empty_seats, len(room_plans)


def _is_mixed_plan(room_plan) -> bool:
    return sum(1 for count in room_plan["assignments"].values() if count > 0) > 1


def _order_room_plans_by_subject(arrangement, room_plans, subject_counts):
    subject_order = _sort_subject_keys(arrangement, subject_counts)
    subject_rank = {subject: index for index, subject in enumerate(subject_order)}
    pure_plans = [plan for plan in room_plans if not _is_mixed_plan(plan)]
    mixed_plans = [plan for plan in room_plans if _is_mixed_plan(plan)]

    pure_plans.sort(
        key=lambda plan: (
            subject_rank.get(next(iter(plan["assignments"])), len(subject_rank)),
            -sum(plan["assignments"].values()),
        )
    )
    return pure_plans, mixed_plans


def _generate_room_allocation_candidates(subject_order, subject_counts, capacity):
    active_subjects = [subject for subject in subject_order if subject_counts.get(subject, 0) > 0]
    allocations = {}

    for length in range(1, len(active_subjects) + 1):
        for permutation in itertools.permutations(active_subjects, length):
            remaining_capacity = capacity
            allocation = {}

            for subject in permutation:
                if remaining_capacity <= 0:
                    break
                available = subject_counts.get(subject, 0)
                if available <= 0:
                    continue
                take = min(available, remaining_capacity)
                if take <= 0:
                    continue
                allocation[subject] = take
                remaining_capacity -= take

            if not allocation:
                continue

            key = tuple(allocation.get(subject, 0) for subject in subject_order)
            allocations[key] = allocation

    def sort_key(key):
        active_count = sum(1 for value in key if value > 0)
        return (
            1 if active_count > 1 else 0,
            active_count,
            -sum(key),
            tuple(-value for value in key),
        )

    return [allocations[key] for key in sorted(allocations, key=sort_key)]


def _search_tail_room_plans(arrangement, subject_counts, capacities, reserve_after_students):
    if not subject_counts:
        return [], (0, 0, 0, 0)

    subject_order = tuple(_sort_subject_keys(arrangement, subject_counts))
    capacity_list = tuple(capacities)
    suffix_capacity = [0] * (len(capacity_list) + 1)
    for index in range(len(capacity_list) - 1, -1, -1):
        suffix_capacity[index] = suffix_capacity[index + 1] + capacity_list[index]

    initial_counts = tuple(subject_counts.get(subject, 0) for subject in subject_order)

    @lru_cache(maxsize=None)
    def dfs(room_index, counts_tuple):
        remaining_students = sum(counts_tuple)
        if remaining_students == 0:
            if suffix_capacity[room_index] < reserve_after_students:
                return None
            return (0, 0, 0, 0), ()
        if room_index >= len(capacity_list):
            return None
        if suffix_capacity[room_index] < remaining_students + reserve_after_students:
            return None

        current_capacity = capacity_list[room_index]
        current_counts = {
            subject_order[index]: count for index, count in enumerate(counts_tuple) if count > 0
        }
        best_result = None

        for allocation in _generate_room_allocation_candidates(subject_order, current_counts, current_capacity):
            next_counts = list(counts_tuple)
            used_seats = 0
            active_subjects = 0

            for subject_index, subject in enumerate(subject_order):
                take = allocation.get(subject, 0)
                if take <= 0:
                    continue
                next_counts[subject_index] -= take
                used_seats += take
                active_subjects += 1

            child_result = dfs(room_index + 1, tuple(next_counts))
            if child_result is None:
                continue

            child_score, child_plans = child_result
            score = (
                child_score[0] + (1 if active_subjects > 1 else 0),
                child_score[1] + max(0, active_subjects - 1),
                child_score[2] + (current_capacity - used_seats),
                child_score[3] + 1,
            )
            plan = (
                {
                    "capacity": current_capacity,
                    "assignments": {subject: count for subject, count in allocation.items() if count > 0},
                },
            ) + child_plans

            if best_result is None or score < best_result[0]:
                best_result = (score, plan)

        return best_result

    result = dfs(0, initial_counts)
    if result is None:
        return None

    score, plans = result
    return list(plans), score


def _plan_category_rooms(arrangement, subject_counts, capacities, reserve_after_students):
    subject_counts = {subject: count for subject, count in subject_counts.items() if count > 0}
    if not subject_counts:
        return [], (0, 0, 0, 0)
    if sum(capacities) < sum(subject_counts.values()) + reserve_after_students:
        return None

    plans = []
    current_counts = dict(subject_counts)
    ordered_subjects = _sort_subject_keys(arrangement, subject_counts)
    room_index = 0

    while current_counts and room_index < len(capacities):
        remaining_students = sum(current_counts.values())
        if sum(capacities[room_index:]) < remaining_students + reserve_after_students:
            return None

        current_capacity = capacities[room_index]
        fillable_subjects = [
            subject for subject in ordered_subjects if current_counts.get(subject, 0) >= current_capacity
        ]

        if not fillable_subjects:
            tail_result = _search_tail_room_plans(
                arrangement,
                current_counts,
                capacities[room_index:],
                reserve_after_students,
            )
            if tail_result is None:
                return None

            tail_plans, _ = tail_result
            plans.extend(tail_plans)
            return plans, _score_room_plans(plans)

        subject = fillable_subjects[0]
        plans.append({"capacity": current_capacity, "assignments": {subject: current_capacity}})
        current_counts[subject] -= current_capacity
        if current_counts[subject] <= 0:
            del current_counts[subject]
        room_index += 1

    if current_counts:
        return None

    return plans, _score_room_plans(plans)


def _materialize_room_plan(room_spec, room_plan, student_groups, arrangement):
    room = {"room_num": room_spec["room_num"], "students": [], "subjects": set()}

    for subject, count in room_plan["assignments"].items():
        students = student_groups.get(subject, [])
        if len(students) < count:
            raise ValueError(f"选科 {subject} 的学生数量不足，无法完成考场落位")

        room["students"].extend(students[:count])
        del students[:count]
        if count > 0:
            room["subjects"].add(subject)

    return room


def _plan_subject_mode_rooms(arrangement):
    room_specs = _get_room_specs(arrangement)
    student_groups = _build_student_groups(arrangement)
    all_subject_counts = {subject: len(students) for subject, students in student_groups.items()}

    physics_counts = {
        subject: count for subject, count in all_subject_counts.items() if _is_physics_subject(subject)
    }
    history_counts = {
        subject: count for subject, count in all_subject_counts.items() if _is_history_subject(subject)
    }

    history_total = sum(history_counts.values())
    capacities = [spec["capacity"] for spec in room_specs]

    physics_result = _plan_category_rooms(arrangement, physics_counts, capacities, history_total)
    if physics_result is None:
        return None, "考场数量不足，无法在物理类和历史类连续的前提下完成编排"
    physics_plans, _ = physics_result

    history_room_specs = room_specs[len(physics_plans) :]
    history_capacities = [spec["capacity"] for spec in history_room_specs]
    history_result = _plan_category_rooms(arrangement, history_counts, history_capacities, 0)
    if history_result is None:
        return None, "考场数量不足，无法完成历史类考场编排"
    history_plans, _ = history_result

    physics_pure_plans, physics_mixed_plans = _order_room_plans_by_subject(arrangement, physics_plans, physics_counts)
    history_pure_plans, history_mixed_plans = _order_room_plans_by_subject(arrangement, history_plans, history_counts)

    ordered_room_plans = (
        physics_pure_plans
        + history_pure_plans
        + physics_mixed_plans
        + history_mixed_plans
    )

    rooms = []
    for room_spec, room_plan in zip(room_specs, ordered_room_plans):
        rooms.append(_materialize_room_plan(room_spec, room_plan, student_groups, arrangement))

    leftover_students = {
        subject: len(students) for subject, students in student_groups.items() if students
    }
    if leftover_students:
        return None, f"仍有学生未分配到考场: {leftover_students}"

    return rooms, ""


def generate_results(arrangement, rooms):
    arranged_results = []

    for room in rooms:
        if not room["students"]:
            continue

        room_subjects_str = ", ".join(sorted(room["subjects"]))
        for seat_num, student in enumerate(room["students"], 1):
            student_info = student.copy()
            student_info.update(
                {
                    "考场号": room["room_num"],
                    "座位号": f"{seat_num:02d}",
                    "考场选科组合": room_subjects_str,
                }
            )
            arranged_results.append(student_info)

    if not arranged_results:
        return False, "编排失败，没有学生被分配到考场"

    arrangement.arranged_students = pd.DataFrame(arranged_results)
    arrangement._apply_room_names()

    parsed_subjects = arrangement.arranged_students[arrangement.subject_column].apply(arrangement.parse_subject_combination)
    arrangement.arranged_students[["首选", "再选1", "再选2"]] = pd.DataFrame(
        parsed_subjects.tolist(),
        index=arrangement.arranged_students.index,
    )

    return True, f"考场编排完成，共编排{len(arranged_results)}名学生"


def arrange_subject_mode(arrangement):
    rooms, error = _plan_subject_mode_rooms(arrangement)
    if rooms is None:
        return False, error
    return generate_results(arrangement, rooms)
