from __future__ import annotations

import pandas as pd

from backend.printing.core.utils.data_loader import DataLoader
from backend.printing.core.validators.desk_label_validator import check_desk_data_sort


def test_get_headers_returns_first_row_strings(tmp_path) -> None:
    path = tmp_path / "headers.xlsx"
    pd.DataFrame(columns=["考场号", "座位号", "姓名"]).to_excel(path, index=False)

    headers = DataLoader.get_headers(path)

    assert headers == ["考场号", "座位号", "姓名"]


def test_load_data_preserves_string_fields_and_skips_blank_rows(tmp_path) -> None:
    path = tmp_path / "print-data.xlsx"
    pd.DataFrame(
        [
            {
                "考场号": "001",
                "考场": "第一考场",
                "座位号": "01",
                "考生姓名": "张三",
                "考生考号": "240001",
                "班级": 1,
                "学号": 2,
            },
            {
                "考场号": None,
                "考场": None,
                "座位号": None,
                "考生姓名": None,
                "考生考号": None,
                "班级": None,
                "学号": None,
            },
        ]
    ).to_excel(path, index=False)

    result = DataLoader.load_data(
        path,
        {
            "考场号": "考场号",
            "考场": "考场",
            "座位号": "座位号",
            "考生姓名": "考生姓名",
            "考生考号": "考生考号",
            "班级": "班级",
            "学号": "学号",
        },
    )

    assert result == [
        {
            "考场号": "001",
            "考场": "第一考场",
            "座位号": "01",
            "考生姓名": "张三",
            "考生考号": "240001",
            "班级": 1,
            "学号": 2,
        }
    ]


def test_load_exam_bag_data_extracts_positive_counts_only(tmp_path) -> None:
    path = tmp_path / "exam-bag.xlsx"
    pd.DataFrame(
        [
            {"考场": "第一考场", "语文": 30, " 数学 ": " 0 ", "英语": 28},
            {"考场": "第二考场", "语文": "", " 数学 ": 25, "英语": None},
        ]
    ).to_excel(path, index=False)

    result = DataLoader.load_exam_bag_data(path)

    assert result == [
        {"room": "第一考场", "subject": "语文", "count": 30},
        {"room": "第二考场", "subject": "数学", "count": 25},
        {"room": "第一考场", "subject": "英语", "count": 28},
    ]


def test_load_student_info_data_parses_required_and_optional_fields(tmp_path) -> None:
    path = tmp_path / "student-info.xlsx"
    pd.DataFrame(
        [
            {
                "考场号": "001",
                "考场": "第一考场",
                "座位号": "01",
                "考生姓名": "张三",
                "考生考号": "240001",
                "班级": 1,
                "学号": 2,
                "首选": "物理",
                "再选1": "化学",
                "再选2": "",
            }
        ]
    ).to_excel(path, index=False)

    result = DataLoader.load_student_info_data(
        path,
        {
            "考场号": "考场号",
            "考场": "考场",
            "座位号": "座位号",
            "考生姓名": "考生姓名",
            "考生考号": "考生考号",
            "班级": "班级",
            "学号": "学号",
            "首选": "首选",
            "再选1": "再选1",
            "再选2": "再选2",
        },
    )

    assert result == [
        {
            "考场号": "001",
            "考场": "第一考场",
            "座位号": "01",
            "考生姓名": "张三",
            "考生考号": "240001",
            "班级": 1,
            "学号": 2,
            "首选": "物理",
            "再选1": "化学",
            "再选2": "",
        }
    ]


def test_load_student_info_data_accepts_legacy_subject_mapping(tmp_path) -> None:
    path = tmp_path / "legacy-student-info.xlsx"
    pd.DataFrame(
        [{
            "考场号": "001", "考场": "第一考场", "座位号": "01",
            "考生姓名": "张三", "考生考号": "240001", "班级": 1, "学号": 2,
            "首选": "物理", "选科1": "化学", "选科2": "生物",
        }]
    ).to_excel(path, index=False)

    mapping = {field: field for field in ("考场号", "考场", "座位号", "考生姓名", "考生考号", "班级", "学号", "首选", "选科1", "选科2")}
    result = DataLoader.load_student_info_data(path, mapping)

    assert result[0]["再选1"] == "化学"
    assert result[0]["再选2"] == "生物"


def test_check_desk_data_sort_detects_unsorted_string_room_numbers() -> None:
    ok, message = check_desk_data_sort(
        [
            {"考场号": "002", "座位号": "01"},
            {"考场号": "001", "座位号": "01"},
        ]
    )

    assert ok is False
    assert "考场号乱序" in message
