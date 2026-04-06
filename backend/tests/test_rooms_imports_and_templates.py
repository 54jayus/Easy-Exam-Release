from __future__ import annotations

import pandas as pd

from backend.application.rooms_service import RoomsService
from backend.domain.state import AppState


def test_generate_template_settings_creates_instruction_sheet(tmp_path, recording_repo) -> None:
    path = tmp_path / "settings-template.xlsx"
    service = RoomsService(AppState(), recording_repo)

    result = service.generate_template({"type": "settings", "path": str(path)})

    assert result == {}
    book = pd.ExcelFile(path)
    assert book.sheet_names == ["Sheet1", "填写说明"]

    settings_df = pd.read_excel(path, sheet_name="Sheet1", dtype={"考场号": str}).fillna("")
    instructions_df = pd.read_excel(path, sheet_name="填写说明").fillna("")

    assert len(settings_df) == 30
    assert settings_df.iloc[0].to_dict() == {"序号": 1, "考场号": "001", "考场": "第1考场", "考场人数": 30}
    assert "必须从1开始连续编号" in instructions_df.iloc[0]["序号"]


def test_generate_template_student_subject_contains_subject_examples(tmp_path, recording_repo) -> None:
    path = tmp_path / "student-subject-template.xlsx"
    service = RoomsService(AppState(), recording_repo)

    result = service.generate_template({"type": "student_subject", "path": str(path)})

    assert result == {}
    df = pd.read_excel(path, sheet_name="Sheet1").fillna("")
    assert "选科" in df.columns
    assert set(df["选科"].tolist()) >= {"物化生", "物化地", "史政地"}


def test_import_settings_validates_sequence_and_capacity(tmp_path, recording_repo) -> None:
    service = RoomsService(AppState(), recording_repo)
    bad_seq = tmp_path / "bad-seq.xlsx"
    bad_capacity = tmp_path / "bad-capacity.xlsx"

    pd.DataFrame(
        [
            {"序号": 1, "考场号": "001", "考场": "第一考场", "考场人数": 30},
            {"序号": 3, "考场号": "002", "考场": "第二考场", "考场人数": 30},
        ]
    ).to_excel(bad_seq, index=False)
    pd.DataFrame(
        [{"序号": 1, "考场号": "001", "考场": "第一考场", "考场人数": 0}]
    ).to_excel(bad_capacity, index=False)

    seq_result = service.import_settings({"path": str(bad_seq)})
    capacity_result = service.import_settings({"path": str(bad_capacity)})

    assert seq_result == {"error": "序号列必须从1开始顺序编号，不能有缺失或重复"}
    assert capacity_result == {"error": '"考场人数"必须为正整数'}


def test_import_settings_persists_defaults_and_updates_config(tmp_path, recording_repo) -> None:
    state = AppState()
    service = RoomsService(state, recording_repo)
    path = tmp_path / "settings.xlsx"

    pd.DataFrame(
        [
            {"序号": 1, "考场号": "001", "考场": "", "考场人数": 30},
            {"序号": 2, "考场号": "002", "考场": "第二考场", "考场人数": 35},
        ]
    ).to_excel(path, index=False)

    result = service.import_settings({"path": str(path)})

    assert result["settings"] == [
        {"roomNum": "001", "roomName": "第001考场", "capacity": 30},
        {"roomNum": "002", "roomName": "第二考场", "capacity": 35},
    ]
    assert state.rooms.config["totalRooms"] == 2
    assert state.rooms.config["seatsPerRoom"] == 30
    assert recording_repo.save_calls == 1


def test_import_students_validates_duplicates_and_numeric_fields(tmp_path, recording_repo) -> None:
    service = RoomsService(AppState(), recording_repo)
    dup_path = tmp_path / "dup.xlsx"
    bad_digit_path = tmp_path / "bad-digit.xlsx"

    pd.DataFrame(
        [
            {"班级": "1", "学号": "01", "考号": "240001", "姓名": "张三"},
            {"班级": "1", "学号": "02", "考号": "240001", "姓名": "李四"},
        ]
    ).to_excel(dup_path, index=False)
    pd.DataFrame(
        [{"班级": "高一", "学号": "01A", "考号": "240001", "姓名": "张三"}]
    ).to_excel(bad_digit_path, index=False)

    dup_result = service.import_students({"path": str(dup_path)})
    digit_result = service.import_students({"path": str(bad_digit_path)})

    assert dup_result == {"error": "导入失败：存在重复的考号: 240001"}
    assert "只能填写数字" in digit_result["error"]


def test_import_students_persists_preview_and_path(tmp_path, recording_repo) -> None:
    state = AppState()
    service = RoomsService(state, recording_repo)
    path = tmp_path / "students.xlsx"

    pd.DataFrame(
        [
            {"班级": "1", "学号": "01", "考号": "240001", "姓名": "张三"},
            {"班级": "1", "学号": "02", "考号": "240002", "姓名": "李四"},
        ]
    ).to_excel(path, index=False)

    result = service.import_students({"path": str(path)})

    assert result["total"] == 2
    assert result["message"] == "成功加载数据，共2名学生"
    assert state.rooms.student_path == str(path)
    assert state.rooms.students_preview[0]["姓名"] == "张三"
    assert recording_repo.save_calls == 1
