from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from backend.application.printing_service import PrintingService, _normalize_output_path
from backend.domain.state import AppState


def test_normalize_output_path_switches_between_xlsx_and_pdf() -> None:
    assert _normalize_output_path("report.xlsx", ".pdf") == "report.pdf"
    assert _normalize_output_path("report.pdf", ".xlsx") == "report.xlsx"
    assert _normalize_output_path("report", "pdf") == "report.pdf"
    assert _normalize_output_path("report.final.xlsx", ".xlsx") == "report.final.xlsx"


def test_load_from_schedule_returns_error_when_arrangement_is_missing(recording_repo) -> None:
    service = PrintingService(AppState(), recording_repo)

    result = service.load_from_schedule({"type": "corner"})

    assert result == {"error": '暂无考场编排数据，请先在"考场编排"页面完成编排'}


def test_load_from_schedule_uses_student_info_adapter_for_table(monkeypatch, recording_repo) -> None:
    state = AppState()
    state.exam_arrangement = SimpleNamespace(
        arranged_students=pd.DataFrame([{"班级": "1", "学号": "01", "姓名": "张三", "考号": "240001", "考场": "第一考场", "考场号": "001", "座位号": "01"}])
    )
    service = PrintingService(state, recording_repo)

    def fake_loader(df, include_subject_fields=False):
        assert include_subject_fields is True
        assert list(df["姓名"]) == ["张三"]
        return [{"考生姓名": "张三"}]

    monkeypatch.setattr("backend.application.printing_service.load_examroom_data_for_student_info", fake_loader)

    result = service.load_from_schedule({"type": "table"})

    assert result == {"data": [{"考生姓名": "张三"}], "total": 1}


def test_load_from_schedule_routes_corner_ticket_and_exam_bag(monkeypatch, recording_repo) -> None:
    state = AppState()
    state.exam_arrangement = SimpleNamespace(arranged_students=pd.DataFrame([{"姓名": "张三"}]))
    service = PrintingService(state, recording_repo)

    monkeypatch.setattr(
        "backend.application.printing_service.load_examroom_data_for_corner",
        lambda ea: [{"kind": "corner"}],
    )
    monkeypatch.setattr(
        "backend.application.printing_service.load_examroom_data_for_ticket",
        lambda ea: [{"kind": "ticket"}],
    )
    monkeypatch.setattr(
        "backend.application.printing_service.load_examroom_data_for_exam_bag",
        lambda ea: [{"kind": "exam_bag"}],
    )

    assert service.load_from_schedule({"type": "corner"}) == {"data": [{"kind": "corner"}], "total": 1}
    assert service.load_from_schedule({"type": "ticket"}) == {"data": [{"kind": "ticket"}], "total": 1}
    assert service.load_from_schedule({"type": "exam_bag_label"}) == {"data": [{"kind": "exam_bag"}], "total": 1}


def test_preview_data_stores_state_and_truncates_non_table_results(monkeypatch, recording_repo) -> None:
    state = AppState()
    service = PrintingService(state, recording_repo)
    fake_rows = [{"id": i} for i in range(60)]

    monkeypatch.setattr("backend.application.printing_service.DataLoader.load_data", lambda path, mapping: fake_rows)

    result = service.preview_data({"path": "data.xlsx", "mapping": {"name": "姓名"}, "type": "corner"})

    assert result["total"] == 60
    assert len(result["data"]) == 50
    assert state.printing.source_type == "file"
    assert state.printing.data_path == "data.xlsx"
    assert state.printing.mapping == {"name": "姓名"}
    assert state.printing.total == 60
    assert recording_repo.save_calls == 1


def test_generate_rejects_missing_output_format_and_path(recording_repo) -> None:
    service = PrintingService(AppState(), recording_repo)

    no_format = service.generate(
        {
            "type": "table",
            "config": {"exportXlsx": False, "exportPdf": False},
            "sourceType": "empty",
            "outputPath": "out.xlsx",
        }
    )
    no_path = service.generate(
        {
            "type": "table",
            "config": {"exportXlsx": True, "exportPdf": False},
            "sourceType": "empty",
            "outputPath": "",
        }
    )

    assert no_format == {"error": "请至少选择一种输出格式（xlsx 或 pdf）"}
    assert no_path == {"error": "请选择保存路径"}
