from __future__ import annotations

import pandas as pd

from backend.subjects.core import Subject, validate_subjects
from backend.subjects.excel import (
    export_subjects_to_excel,
    generate_subject_template_xlsx,
    import_subjects_from_excel,
)


def test_validate_subjects_rejects_duplicate_names_but_allows_time_overlap() -> None:
    errors = validate_subjects(
        [
            Subject(name="语文", exam_date="2026-06-07", exam_time="09:00-11:30"),
            Subject(name="语文", exam_date="2026-06-07", exam_time="15:00-17:00"),
            Subject(name="数学", exam_date="2026-06-07", exam_time="10:30-12:00"),
        ]
    )

    assert any("科目名称重复" in error for error in errors)
    assert not any("考试时间冲突" in error for error in errors)


def test_import_subjects_from_excel_parses_duration_and_room_count(tmp_path) -> None:
    path = tmp_path / "subjects.xlsx"
    pd.DataFrame(
        [
            {
                "科目名称": "语文",
                "考试日期": "2026/06/07",
                "考试时间": "09:00-11:30",
                "考试时长（分钟）-可留空": "",
                "考场数量（可留空）": 12,
                "备注": "必修",
            },
            {
                "科目名称": "数学",
                "考试日期": "2026-06-07",
                "考试时间": "15:00-17:00",
                "考试时长（分钟）-可留空": 120,
                "考场数量（可留空）": "",
                "备注": "",
            },
        ]
    ).to_excel(path, index=False)

    result = import_subjects_from_excel(str(path))

    assert result.errors == []
    assert result.subjects == [
        Subject(
            name="语文",
            exam_date="2026-06-07",
            exam_time="09:00-11:30",
            remark="必修",
            duration_minutes=150,
            room_count=12,
        ),
        Subject(
            name="数学",
            exam_date="2026-06-07",
            exam_time="15:00-17:00",
            remark="",
            duration_minutes=120,
            room_count=0,
        ),
    ]


def test_import_subjects_from_excel_reports_missing_required_columns(tmp_path) -> None:
    path = tmp_path / "bad-subjects.xlsx"
    pd.DataFrame([{"科目名称": "语文"}]).to_excel(path, index=False)

    result = import_subjects_from_excel(str(path))

    assert result.subjects == []
    assert result.errors == ["文件缺少必需的列: 考试日期, 考试时间"]


def test_export_subjects_to_excel_and_template_generation(tmp_path) -> None:
    export_path = tmp_path / "export.xlsx"
    template_path = tmp_path / "template.xlsx"

    export_subjects_to_excel(
        str(export_path),
        subjects=[
            Subject(
                name="语文",
                exam_date="2026-06-07",
                exam_time="09:00-11:30",
                duration_minutes=150,
                room_count=20,
            )
        ],
    )
    generate_subject_template_xlsx(str(template_path))

    exported = pd.read_excel(export_path).fillna("")
    template = pd.ExcelFile(template_path)

    assert exported.to_dict("records") == [
        {
            "科目名称": "语文",
            "考试日期": "2026-06-07",
            "考试时间": "09:00-11:30",
            "考试时长（分钟）": 150,
            "考场数量": 20,
            "备注": "",
        }
    ]
    assert template.sheet_names == ["Sheet1", "填写说明"]
