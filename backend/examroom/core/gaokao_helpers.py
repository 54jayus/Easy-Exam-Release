from __future__ import annotations

import secrets

import pandas as pd

from .helpers import get_room_name


def shuffle_students(students_df: pd.DataFrame) -> pd.DataFrame:
    """使用安全随机数打乱学生顺序。"""
    random_state = secrets.randbelow(2**32)
    return students_df.sample(frac=1, random_state=random_state).reset_index(drop=True)


def get_room_list(arrangement) -> list[str]:
    """获取考场号列表，优先使用已配置的考场顺序。"""
    if hasattr(arrangement, "room_setting_df") and arrangement.room_setting_df is not None:
        return [str(row["考场号"]) for _, row in arrangement.room_setting_df.iterrows()]

    if arrangement.room_setting_data is not None and hasattr(arrangement.room_setting_data, "iterrows"):
        return [str(row["考场号"]) for _, row in arrangement.room_setting_data.iterrows()]

    return [str(i) for i in range(1, arrangement.total_rooms + 1)]


def fill_rooms_sequential(arrangement, students_list: pd.DataFrame, start_room_index: int = 0):
    """
    将学生顺序填充到考场。

    返回: (考场分配结果列表, 最后使用的考场索引)
    """
    room_list = get_room_list(arrangement)
    rooms = []
    current_room_index = start_room_index
    current_room_students = []

    for _, student in students_list.iterrows():
        if current_room_students:
            room_num = room_list[current_room_index]
            room_capacity = arrangement.get_room_capacity(room_num)

            if len(current_room_students) >= room_capacity:
                rooms.append({"room_num": room_num, "students": current_room_students})
                current_room_index += 1
                current_room_students = []

        if current_room_index >= len(room_list):
            raise ValueError(f"考场数量不足，至少需要{current_room_index + 1}个考场")

        current_room_students.append(student)

    if current_room_students:
        if current_room_index >= len(room_list):
            raise ValueError(f"考场数量不足，至少需要{current_room_index + 1}个考场")
        room_num = room_list[current_room_index]
        rooms.append({"room_num": room_num, "students": current_room_students})

    return rooms, current_room_index


def extract_subject_from_combination(combination_str, subject_abbr) -> bool:
    """判断选科组合中是否包含指定科目缩写。"""
    return subject_abbr in str(combination_str)


def arrange_unified_exams(arrangement) -> pd.DataFrame:
    """
    编排统考科目（语数英+物理/历史）。

    返回: DataFrame，包含所有学生的统考编排结果。
    """
    physics_students = arrangement.students[arrangement.students[arrangement.subject_column].str.startswith("物")].copy()
    history_students = arrangement.students[arrangement.students[arrangement.subject_column].str.startswith("史")].copy()

    physics_students = shuffle_students(physics_students)
    physics_rooms, last_physics_index = fill_rooms_sequential(arrangement, physics_students, 0)

    history_students = shuffle_students(history_students)
    history_rooms, _ = fill_rooms_sequential(arrangement, history_students, last_physics_index + 1)

    all_rooms = physics_rooms + history_rooms
    result_records = []

    for room in all_rooms:
        room_num = room["room_num"]
        room_name = get_room_name(arrangement, room_num)

        for seat_idx, student in enumerate(room["students"], start=1):
            record = student.to_dict()
            record["考场号"] = room_num
            record["考场"] = room_name
            record["座位号"] = f"{seat_idx:02d}"
            result_records.append(record)

    return pd.DataFrame(result_records)


def arrange_elective_exam(arrangement, subject: str) -> pd.DataFrame:
    """
    编排单个选考科目。

    返回: DataFrame，包含考试与自习学生的编排结果。
    """
    subject_abbr_map = {
        "化学": "化",
        "地理": "地",
        "政治": "政",
        "生物": "生",
    }
    subject_abbr = subject_abbr_map.get(subject, subject[0])

    exam_students = arrangement.students[arrangement.students[arrangement.subject_column].str.contains(subject_abbr)].copy()
    self_study_students = arrangement.students[
        ~arrangement.students[arrangement.subject_column].str.contains(subject_abbr)
    ].copy()

    exam_students = shuffle_students(exam_students)
    exam_rooms, last_exam_index = fill_rooms_sequential(arrangement, exam_students, 0)

    self_study_students = shuffle_students(self_study_students)
    self_study_rooms, _ = fill_rooms_sequential(arrangement, self_study_students, last_exam_index + 1)

    all_rooms = exam_rooms + self_study_rooms
    result_records = []

    for room_idx, room in enumerate(all_rooms):
        room_num = room["room_num"]
        room_name = get_room_name(arrangement, room_num)
        is_exam_room = room_idx < len(exam_rooms)

        for seat_idx, student in enumerate(room["students"], start=1):
            record = student.to_dict()
            record["考场号"] = room_num
            record["考场"] = room_name
            record["座位号"] = f"{seat_idx:02d}"
            record["科目类型"] = subject if is_exam_room else "自习"
            result_records.append(record)

    return pd.DataFrame(result_records)


def arrange_gaokao_mode(arrangement):
    """编排高考模式下的统考与选考结果。"""
    unified_result = arrange_unified_exams(arrangement)

    elective_results = {}
    for subject in ["化学", "地理", "政治", "生物"]:
        elective_results[subject] = arrange_elective_exam(arrangement, subject)

    arrangement.gaokao_results = {
        "unified": unified_result,
        "electives": elective_results,
    }
    arrangement.arranged_students = arrangement._merge_gaokao_results()

    return True, f"高考模式编排完成，共编排{len(arrangement.students)}名学生"
