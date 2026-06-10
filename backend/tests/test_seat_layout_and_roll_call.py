from __future__ import annotations

from types import SimpleNamespace

import openpyxl
import pandas as pd
import pytest

from backend.printing.core.adapters.roll_call import build_roll_call_groups
from backend.printing.core.config import RollCallConfig
from backend.printing.core.generators.excel.roll_call import RollCallGenerator
from backend.printing.core.generators.pdf.roll_call_pdf import RollCallPDFGenerator
from backend.printing.core.seat_layout import (
    get_seat_mapping,
    layout_capacity,
    layout_for_room,
    mirror_layout_start_pos,
    normalize_seat_layout,
)


@pytest.mark.parametrize(
    ("pattern", "expected"),
    [
        ("Z型横排", {1: (0, 0), 2: (0, 1), 3: (1, 0), 4: (1, 1)}),
        ("S型横排", {1: (0, 0), 2: (0, 1), 3: (1, 1), 4: (1, 0)}),
        ("Z型竖排", {1: (0, 0), 2: (1, 0), 3: (0, 1), 4: (1, 1)}),
        ("S型竖排", {1: (0, 0), 2: (1, 0), 3: (1, 1), 4: (0, 1)}),
    ],
)
def test_seat_mapping_supports_all_patterns(pattern, expected) -> None:
    layout = {"layoutRows": 2, "layoutCols": 2, "layoutPattern": pattern, "startPos": "right"}
    assert get_seat_mapping(layout) == expected


def test_seat_mapping_honors_left_start_and_custom_columns() -> None:
    layout = {
        "layoutRows": 3,
        "layoutCols": 2,
        "layoutPattern": "Z型竖排",
        "startPos": "left",
        "customColCounts": [2, 3],
    }

    assert get_seat_mapping(layout) == {1: (0, 1), 2: (1, 1), 3: (2, 1), 4: (0, 0), 5: (1, 0)}
    assert layout_capacity(layout) == 5


def test_room_override_falls_back_to_default() -> None:
    config = normalize_seat_layout({
        "defaultLayout": {"layoutRows": 5, "layoutCols": 6},
        "roomOverrides": {"002": {"layoutRows": 7, "layoutCols": 6}},
    })

    assert layout_for_room(config, "001")["layoutRows"] == 5
    assert layout_for_room(config, "002")["layoutRows"] == 7


def test_mirror_layout_start_pos_flips_view() -> None:
    layout = {"layoutRows": 2, "layoutCols": 2, "layoutPattern": "Z型横排", "startPos": "left"}

    mirrored = mirror_layout_start_pos(layout, True)

    assert mirrored["startPos"] == "right"
    assert get_seat_mapping(mirrored)[1] == (0, 0)


def test_roll_call_regular_builds_one_group_per_subject_and_room() -> None:
    arrangement = SimpleNamespace(
        arrangement_mode="normal_mode",
        arranged_students=pd.DataFrame([
            {"姓名": "张三", "考号": "1", "班级": "1", "考场": "一考场", "考场号": "001", "座位号": "1"},
            {"姓名": "李四", "考号": "2", "班级": "1", "考场": "二考场", "考场号": "002", "座位号": "1"},
        ]),
    )
    seat_layout = {"defaultLayout": {"layoutRows": 5, "layoutCols": 6}, "roomOverrides": {}}

    groups = build_roll_call_groups(arrangement, [{"name": "语文"}, {"name": "数学"}], seat_layout)

    assert [(item["subject"], item["roomNo"]) for item in groups] == [
        ("语文", "001"), ("语文", "002"), ("数学", "001"), ("数学", "002")
    ]


def test_roll_call_subject_mode_filters_electives() -> None:
    arrangement = SimpleNamespace(
        arrangement_mode="subject_mode",
        arranged_students=pd.DataFrame([
            {"姓名": "张三", "考号": "1", "考场": "一考场", "考场号": "001", "座位号": "1", "首选": "物理", "选科1": "化学", "选科2": "生物"},
            {"姓名": "李四", "考号": "2", "考场": "一考场", "考场号": "001", "座位号": "2", "首选": "历史", "选科1": "政治", "选科2": "地理"},
        ]),
    )

    groups = build_roll_call_groups(arrangement, [], {"defaultLayout": {"layoutRows": 5, "layoutCols": 6}})
    by_subject = {item["subject"]: [student["name"] for student in item["students"]] for item in groups}

    assert by_subject["语文"] == ["张三", "李四"]
    assert by_subject["物理"] == ["张三"]
    assert by_subject["历史"] == ["李四"]
    assert by_subject["化学"] == ["张三"]


def test_roll_call_rejects_duplicate_and_out_of_range_seats() -> None:
    arrangement = SimpleNamespace(
        arrangement_mode="normal_mode",
        arranged_students=pd.DataFrame([
            {"姓名": "张三", "考场": "一考场", "考场号": "001", "座位号": "2"},
            {"姓名": "李四", "考场": "一考场", "考场号": "001", "座位号": "2"},
        ]),
    )

    with pytest.raises(ValueError, match="重复"):
        build_roll_call_groups(arrangement, [{"name": "语文"}], {"defaultLayout": {"layoutRows": 1, "layoutCols": 1}})


def test_roll_call_generators_create_valid_files(tmp_path) -> None:
    groups = [{
        "subject": "语文",
        "roomName": "第一考场",
        "roomNo": "001",
        "students": [{"name": "张三", "examNo": "240001", "className": "1班", "seatNo": 1}],
        "seatLayout": {"layoutRows": 5, "layoutCols": 6, "layoutPattern": "S型竖排", "startPos": "left"},
    }]
    xlsx_path = tmp_path / "点名表.xlsx"
    pdf_path = tmp_path / "点名表.pdf"
    base = dict(exam_name="期末考试点名表", school_name="第一中学", groups=groups, instructions="1.缺考打勾")

    RollCallGenerator(RollCallConfig(output_path=str(xlsx_path), export_xlsx=True, **base)).generate()
    RollCallPDFGenerator(RollCallConfig(output_path=str(pdf_path), export_xlsx=False, export_pdf=True, **base)).generate()

    wb = openpyxl.load_workbook(xlsx_path)
    assert wb.sheetnames == ["语文"]
    assert wb["语文"]["A1"].value == "期末考试点名表"
    assert xlsx_path.read_bytes()[:2] == b"PK"
    assert pdf_path.read_bytes()[:5] == b"%PDF-"


def test_roll_call_generator_can_mirror_view(tmp_path) -> None:
    groups = [{
        "subject": "语文",
        "roomName": "第一考场",
        "roomNo": "001",
        "students": [{"name": "张三", "examNo": "240001", "className": "1班", "seatNo": 1}],
        "seatLayout": {"layoutRows": 2, "layoutCols": 2, "layoutPattern": "Z型横排", "startPos": "left"},
    }]
    xlsx_path = tmp_path / "点名表-镜像.xlsx"

    RollCallGenerator(
        RollCallConfig(output_path=str(xlsx_path), export_xlsx=True, groups=groups, mirror_view=True)
    ).generate()

    wb = openpyxl.load_workbook(xlsx_path)
    assert "张三" in str(wb["语文"]["A4"].value)


def test_roll_call_generator_honors_portrait_orientation(tmp_path) -> None:
    groups = [{
        "subject": "语文",
        "roomName": "第一考场",
        "roomNo": "001",
        "students": [{"name": "张三", "examNo": "240001", "className": "1班", "seatNo": 1}],
        "seatLayout": {"layoutRows": 6, "layoutCols": 9, "layoutPattern": "S型竖排", "startPos": "left"},
    }]
    xlsx_path = tmp_path / "点名表-纵向.xlsx"

    RollCallGenerator(
        RollCallConfig(output_path=str(xlsx_path), export_xlsx=True, groups=groups, orientation="portrait")
    ).generate()

    wb = openpyxl.load_workbook(xlsx_path)
    assert wb["语文"].page_setup.orientation == "portrait"
