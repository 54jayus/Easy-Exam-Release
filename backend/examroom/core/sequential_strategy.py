from __future__ import annotations

import random

import pandas as pd


def arrange_sequential(arrangement, shuffle: bool):
    """顺序/随机编排的共同实现。"""
    if arrangement.room_setting_data:
        room_numbers = sorted(
            arrangement.room_setting_data.keys(),
            key=lambda value: int(value) if str(value).isdigit() else float("inf"),
        )
        rooms = [{"room_num": room_num, "students": []} for room_num in room_numbers]
        arrangement.total_rooms = len(rooms)
    else:
        rooms = [{"room_num": i + 1, "students": []} for i in range(arrangement.total_rooms)]

    students_list = arrangement.students.to_dict("records")
    if shuffle:
        random.shuffle(students_list)

    current_room_index = 0
    for student in students_list:
        current_room = rooms[current_room_index]
        room_capacity = arrangement.get_room_capacity(current_room["room_num"])

        if len(current_room["students"]) >= room_capacity:
            current_room_index += 1
            if current_room_index >= arrangement.total_rooms:
                return False, f"考场数量不足，无法容纳所有学生。需要至少 {current_room_index + 1} 个考场"

            current_room = rooms[current_room_index]

        current_room["students"].append(student)

    arranged_results = []
    for room in rooms:
        if not room["students"]:
            continue

        for seat_num, student in enumerate(room["students"], 1):
            student_info = student.copy()
            student_info.update({"考场号": room["room_num"], "座位号": f"{seat_num:02d}"})

            if arrangement.room_setting_data and room["room_num"] in arrangement.room_setting_data:
                student_info["考场"] = arrangement.room_setting_data[room["room_num"]]
            else:
                student_info["考场"] = f"第{room['room_num']}考场"

            arranged_results.append(student_info)

    mode_label = "随机" if shuffle else "顺序"
    if not arranged_results:
        return False, "编排失败，没有学生被分配到考场"

    arrangement.arranged_students = pd.DataFrame(arranged_results)
    arrangement._apply_room_names()
    return True, f"{mode_label}编排完成，共编排{len(arranged_results)}名学生"
