from __future__ import annotations

import secrets

import pandas as pd


def initialize_rooms(arrangement):
    """初始化选科编排使用的考场列表。"""
    if arrangement.room_setting_data:
        room_numbers = sorted(
            arrangement.room_setting_data.keys(),
            key=lambda value: int(value) if str(value).isdigit() else float("inf"),
        )
        arrangement.total_rooms = len(room_numbers)
        return [{"room_num": num, "students": [], "subjects": set()} for num in room_numbers]

    return [{"room_num": i + 1, "students": [], "subjects": set()} for i in range(arrangement.total_rooms)]


def group_and_sort_subjects(arrangement):
    """按物理/历史分组并按人数降序排序。"""
    subject_counts = arrangement.students[arrangement.subject_column].value_counts()

    physics_subjects = {
        subject: count
        for subject, count in subject_counts.items()
        if "物" in subject or "理" in subject
    }
    history_subjects = {
        subject: count
        for subject, count in subject_counts.items()
        if "史" in subject
    }

    physics_subjects = dict(sorted(physics_subjects.items(), key=lambda item: item[1], reverse=True))
    history_subjects = dict(sorted(history_subjects.items(), key=lambda item: item[1], reverse=True))
    return physics_subjects, history_subjects


def assign_large_groups(arrangement, rooms, physics_subjects, history_subjects):
    """优先分配大组学生，返回当前房间索引和剩余学生。"""
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
    """按选科人数降序排列学生。"""
    if not students_list:
        return students_list

    students_df = pd.DataFrame(students_list)
    subject_counts = students_df[arrangement.subject_column].value_counts().to_dict()
    students_df["_sort_key"] = students_df[arrangement.subject_column].map(subject_counts)
    sorted_df = students_df.sort_values("_sort_key", ascending=False).drop("_sort_key", axis=1)
    return sorted_df.to_dict("records")


def get_room_category(arrangement, room, physics_students, history_students):
    """确定房间应优先填充物理类还是历史类学生。"""
    if room["students"]:
        first_subject = room["students"][0].get(arrangement.subject_column, "")
        subject = str(first_subject).strip()
        return "physics" if subject.startswith("物") or subject.startswith("理") else "history"

    return "physics" if len(physics_students) >= len(history_students) else "history"


def assign_remaining_students(arrangement, rooms, remaining_students, current_room_index):
    """分配剩余学生到考场。"""
    if not remaining_students:
        return

    remaining_df = pd.DataFrame(remaining_students)
    physics_mask = remaining_df[arrangement.subject_column].str.contains("物", na=False) | remaining_df[
        arrangement.subject_column
    ].str.contains("理", na=False)
    history_mask = remaining_df[arrangement.subject_column].str.contains("史", na=False)

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


def generate_results(arrangement, rooms):
    """生成选科编排的最终结果。"""
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
    arrangement.arranged_students[["首选", "选科1", "选科2"]] = pd.DataFrame(
        parsed_subjects.tolist(),
        index=arrangement.arranged_students.index,
    )

    return True, f"考场编排完成，共编排{len(arranged_results)}名学生"


def arrange_subject_mode(arrangement):
    """选科编排主流程。"""
    rooms = initialize_rooms(arrangement)
    physics_subjects, history_subjects = group_and_sort_subjects(arrangement)
    current_room_index, remaining_students = assign_large_groups(arrangement, rooms, physics_subjects, history_subjects)
    assign_remaining_students(arrangement, rooms, remaining_students, current_room_index)
    return generate_results(arrangement, rooms)
