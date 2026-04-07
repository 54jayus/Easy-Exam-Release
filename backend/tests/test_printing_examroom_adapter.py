from __future__ import annotations

from copy import deepcopy
from types import SimpleNamespace

import pandas as pd

from backend.examroom.core.arrangement import ExamArrangement
from backend.examroom.core.gaokao_defaults import GAOKAO_TIME_DEFAULTS
from backend.printing.core.adapters.examroom_adapter import (
    load_examroom_data_for_corner,
    load_examroom_data_for_exam_bag,
    load_examroom_data_for_ticket,
)


def _build_gaokao_arrangement() -> ExamArrangement:
    arrangement = ExamArrangement("students.xlsx", total_rooms=2, arrangement_mode="gaokao_mode")
    arrangement.subject_column = "选科"
    arrangement.room_setting_df = pd.DataFrame(
        [
            {"考场号": "001", "考场": "第一考场"},
            {"考场号": "002", "考场": "第二考场"},
        ]
    )
    arrangement.gaokao_time_settings = deepcopy(GAOKAO_TIME_DEFAULTS)
    arrangement.gaokao_results = {
        "unified": pd.DataFrame(
            [
                {"班级": "1", "学号": "01", "姓名": "张三", "考号": "240001", "选科": "物化生", "考场号": "001", "考场": "第一考场", "座位号": "01"},
                {"班级": "1", "学号": "02", "姓名": "李四", "考号": "240002", "选科": "史地政", "考场号": "001", "考场": "第一考场", "座位号": "02"},
            ]
        ),
        "electives": {
            "化学": pd.DataFrame(
                [
                    {"班级": "1", "学号": "01", "姓名": "张三", "考号": "240001", "考场号": "005", "考场": "第五考场", "座位号": "12", "科目类型": "化学"},
                    {"班级": "1", "学号": "02", "姓名": "李四", "考号": "240002", "考场号": "015", "考场": "第十五考场", "座位号": "08", "科目类型": "自习"},
                ]
            ),
            "地理": pd.DataFrame(
                [
                    {"班级": "1", "学号": "01", "姓名": "张三", "考号": "240001", "考场号": "025", "考场": "第二十五考场", "座位号": "18", "科目类型": "自习"},
                    {"班级": "1", "学号": "02", "姓名": "李四", "考号": "240002", "考场号": "006", "考场": "第六考场", "座位号": "06", "科目类型": "地理"},
                ]
            ),
            "政治": pd.DataFrame(
                [
                    {"班级": "1", "学号": "01", "姓名": "张三", "考号": "240001", "考场号": "035", "考场": "第三十五考场", "座位号": "28", "科目类型": "自习"},
                    {"班级": "1", "学号": "02", "姓名": "李四", "考号": "240002", "考场号": "007", "考场": "第七考场", "座位号": "09", "科目类型": "政治"},
                ]
            ),
            "生物": pd.DataFrame(
                [
                    {"班级": "1", "学号": "01", "姓名": "张三", "考号": "240001", "考场号": "008", "考场": "第八考场", "座位号": "03", "科目类型": "生物"},
                    {"班级": "1", "学号": "02", "姓名": "李四", "考号": "240002", "考场号": "045", "考场": "第四十五考场", "座位号": "11", "科目类型": "自习"},
                ]
            ),
        },
    }
    return arrangement


def test_load_examroom_data_for_corner_formats_regular_arrangement() -> None:
    df = pd.DataFrame(
        [
            {"班级": "高一(1)班", "学号": "02", "考号": "240001", "姓名": "张三", "考场": "第一考场", "考场号": "001", "座位号": "05"}
        ]
    )

    result = load_examroom_data_for_corner(df)

    assert result == [
        {
            "考生姓名": "张三",
            "考生考号": "240001",
            "考生班级学号": "1班02号",
            "班级": "1",
            "学号": "02",
            "考场": "第一考场",
            "考场号": "001",
            "座位号": "05",
        }
    ]


def test_load_examroom_data_for_ticket_returns_gaokao_subject_schedule() -> None:
    arrangement = _build_gaokao_arrangement()

    result = load_examroom_data_for_ticket(arrangement)

    assert len(result) == 2
    first_student = result[0]
    assert first_student["考生姓名"] == "张三"
    assert first_student["班级"] == "1"
    assert len(first_student["科目数据"]) == 8
    assert first_student["科目数据"][0] == {
        "科目": "语文",
        "考场": "第一考场",
        "考场号": "001",
        "座位号": "01",
        "时间": "6月7日 09:00-11:30",
    }
    assert first_student["科目数据"][2]["科目"] == "物理"
    assert first_student["科目数据"][4]["科目"] == "化学"
    assert first_student["科目数据"][5]["科目"] == "自习"
    assert first_student["科目数据"][5]["考场号"] == "025"


def test_load_examroom_data_for_exam_bag_counts_only_actual_exam_subjects() -> None:
    arrangement = _build_gaokao_arrangement()

    result = load_examroom_data_for_exam_bag(arrangement)

    assert {"room": "第一考场", "subject": "语文", "count": 2} in result
    assert {"room": "第一考场", "subject": "物理", "count": 1} in result
    assert {"room": "第一考场", "subject": "历史", "count": 1} in result
    assert {"room": "第005考场", "subject": "化学", "count": 1} in result
    assert {"room": "第006考场", "subject": "地理", "count": 1} in result
    assert {"room": "第007考场", "subject": "政治", "count": 1} in result
    assert {"room": "第008考场", "subject": "生物", "count": 1} in result
    assert not any(item["room"] == "第015考场" for item in result)
def test_load_examroom_data_for_exam_bag_supports_regular_arrangement() -> None:
    arrangement = SimpleNamespace(
        arrangement_mode="normal_mode",
        arranged_students=pd.DataFrame(
            [
                {"姓名": "张三", "考场号": "001", "考场": "第一考场"},
                {"姓名": "李四", "考场号": "001", "考场": "第一考场"},
                {"姓名": "王五", "考场号": "002", "考场": "第二考场"},
            ]
        ),
        _get_room_list=lambda: ["001", "002"],
        _get_room_name=lambda room: {"001": "第一考场", "002": "第二考场"}[str(room)],
    )

    result = load_examroom_data_for_exam_bag(arrangement, [{"name": "语文"}, {"name": "数学"}])

    assert result == [
        {"room": "第一考场", "subject": "语文", "count": 2},
        {"room": "第一考场", "subject": "数学", "count": 2},
        {"room": "第二考场", "subject": "语文", "count": 1},
        {"room": "第二考场", "subject": "数学", "count": 1},
    ]


def test_load_examroom_data_for_exam_bag_supports_subject_mode_counts() -> None:
    arrangement = SimpleNamespace(
        arrangement_mode="subject_mode",
        arranged_students=pd.DataFrame(
            [
                {"姓名": "张三", "考场号": "001", "考场": "第一考场", "首选": "物理", "选科1": "化学", "选科2": "生物"},
                {"姓名": "李四", "考场号": "001", "考场": "第一考场", "首选": "历史", "选科1": "政治", "选科2": "地理"},
                {"姓名": "王五", "考场号": "001", "考场": "第一考场", "首选": "物理", "选科1": "政治", "选科2": "地理"},
            ]
        ),
        _get_room_list=lambda: ["001"],
        _get_room_name=lambda room: "第一考场",
    )

    result = load_examroom_data_for_exam_bag(
        arrangement,
        [{"name": "语文"}, {"name": "物理"}, {"name": "历史"}, {"name": "化学"}, {"name": "政治"}],
    )

    assert result == [
        {"room": "第一考场", "subject": "语文", "count": 3},
        {"room": "第一考场", "subject": "物理", "count": 2},
        {"room": "第一考场", "subject": "历史", "count": 1},
        {"room": "第一考场", "subject": "化学", "count": 1},
        {"room": "第一考场", "subject": "政治", "count": 2},
    ]
