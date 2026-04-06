from __future__ import annotations

import pandas as pd

from backend.examroom.core.arrangement import ExamArrangement


def test_get_room_capacity_supports_zero_padded_and_int_keys() -> None:
    arrangement = ExamArrangement(
        "students.xlsx",
        max_students_per_room=30,
        room_capacities={"001": 35, 2: 28, "003": 40},
    )

    assert arrangement.get_room_capacity("001") == 35
    assert arrangement.get_room_capacity("1") == 35
    assert arrangement.get_room_capacity("002") == 28
    assert arrangement.get_room_capacity(3) == 40
    assert arrangement.get_room_capacity("999") == 30


def test_validate_subject_column_normalizes_full_names_and_separators() -> None:
    arrangement = ExamArrangement("students.xlsx", arrangement_mode="subject_mode")
    arrangement.students = pd.DataFrame(
        [
            {"班级": "1", "学号": "01", "考号": "240001", "姓名": "张三", "选科": "物理+化学+生物"},
            {"班级": "1", "学号": "02", "考号": "240002", "姓名": "李四", "选科": "历史 地理 政治"},
            {"班级": "1", "学号": "03", "考号": "240003", "姓名": "王五", "选科": "理化生"},
        ]
    )

    ok, message = arrangement.validate_subject_column()

    assert ok is True
    assert message == "选科列校验通过"
    assert arrangement.students["选科"].tolist() == ["物化生", "史地政", "物化生"]


def test_check_required_columns_rejects_non_numeric_class_and_student_no() -> None:
    arrangement = ExamArrangement("students.xlsx", arrangement_mode="normal_mode")
    arrangement.students = pd.DataFrame(
        [{"班级": "高一1班", "学号": "01A", "考号": "240001", "姓名": "张三"}]
    )

    ok, message = arrangement.check_required_columns()

    assert ok is False
    assert "只能填写数字" in message


def test_parse_subject_combination_accepts_compact_and_delimited_forms() -> None:
    arrangement = ExamArrangement("students.xlsx")

    assert arrangement.parse_subject_combination("物化生") == ["物理", "化学", "生物"]
    assert arrangement.parse_subject_combination("历史/地理/政治") == ["历史", "地理", "政治"]


def test_format_subject_time_uses_default_settings_and_handles_invalid_values() -> None:
    arrangement = ExamArrangement("students.xlsx", arrangement_mode="gaokao_mode")

    assert arrangement._format_subject_time("语文") == "6月7日09:00-11:30"
    assert arrangement._format_subject_time("化学", is_self_study=True) == "6月9日08:30-09:45"

    arrangement.gaokao_time_settings = {
        "examTimes": {"语文": {"date": "", "startTime": "09:00", "endTime": "11:30"}},
        "selfStudyTimes": {},
    }
    assert arrangement._format_subject_time("语文") == ""


def test_get_room_name_prefers_room_setting_dataframe() -> None:
    arrangement = ExamArrangement("students.xlsx")
    arrangement.room_setting_df = pd.DataFrame(
        [
            {"考场号": "001", "考场": "第一考场"},
            {"考场号": "002", "考场": "第二考场"},
        ]
    )

    assert arrangement._get_room_name("001") == "第一考场"
    assert arrangement._get_room_name("2") == "第二考场"
    assert arrangement._get_room_name("003") == "第003考场"
