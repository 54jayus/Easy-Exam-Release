from __future__ import annotations

import pytest

import backend.printing.core.factory as factory_module
from backend.printing.core.config import (
    AdmissionTicketConfig,
    BaseConfig,
    CornerPaperConfig,
    DeskLabelConfig,
    ExamBagLabelConfig,
    StudentInfoTableConfig,
)
from backend.printing.core.factory import GeneratorFactory


def test_generator_factory_uses_excel_generators_by_default(monkeypatch) -> None:
    captured: list[tuple[str, object]] = []

    def stub(name: str):
        def _build(config):
            captured.append((name, config))
            return name

        return _build

    monkeypatch.setattr(factory_module, "CornerPaperGenerator", stub("corner-xlsx"))
    monkeypatch.setattr(factory_module, "DeskLabelGenerator", stub("desk-xlsx"))
    monkeypatch.setattr(factory_module, "AdmissionTicketGenerator", stub("ticket-xlsx"))
    monkeypatch.setattr(factory_module, "StudentInfoTableGenerator", stub("table-xlsx"))
    monkeypatch.setattr(factory_module, "ExamBagLabelGenerator", stub("bag-xlsx"))

    assert GeneratorFactory.create_generator(CornerPaperConfig(output_path="a.xlsx")) == "corner-xlsx"
    assert GeneratorFactory.create_generator(DeskLabelConfig(output_path="a.xlsx")) == "desk-xlsx"
    assert GeneratorFactory.create_generator(AdmissionTicketConfig(output_path="a.xlsx")) == "ticket-xlsx"
    assert GeneratorFactory.create_generator(StudentInfoTableConfig(output_path="a.xlsx")) == "table-xlsx"
    assert GeneratorFactory.create_generator(ExamBagLabelConfig(output_path="a.xlsx")) == "bag-xlsx"

    assert [name for name, _ in captured] == [
        "corner-xlsx",
        "desk-xlsx",
        "ticket-xlsx",
        "table-xlsx",
        "bag-xlsx",
    ]


def test_generator_factory_uses_pdf_generators_when_only_pdf_is_requested(monkeypatch) -> None:
    captured: list[tuple[str, object]] = []

    def stub(name: str):
        def _build(config):
            captured.append((name, config))
            return name

        return _build

    monkeypatch.setattr(factory_module, "CornerPaperPDFGenerator", stub("corner-pdf"))
    monkeypatch.setattr(factory_module, "DeskLabelPDFGenerator", stub("desk-pdf"))
    monkeypatch.setattr(factory_module, "AdmissionTicketPDFGenerator", stub("ticket-pdf"))
    monkeypatch.setattr(factory_module, "StudentInfoTablePDFGenerator", stub("table-pdf"))
    monkeypatch.setattr(factory_module, "ExamBagLabelPDFGenerator", stub("bag-pdf"))

    assert GeneratorFactory.create_generator(CornerPaperConfig(output_path="a.pdf", export_xlsx=False, export_pdf=True)) == "corner-pdf"
    assert GeneratorFactory.create_generator(DeskLabelConfig(output_path="a.pdf", export_xlsx=False, export_pdf=True)) == "desk-pdf"
    assert GeneratorFactory.create_generator(AdmissionTicketConfig(output_path="a.pdf", export_xlsx=False, export_pdf=True)) == "ticket-pdf"
    assert GeneratorFactory.create_generator(StudentInfoTableConfig(output_path="a.pdf", export_xlsx=False, export_pdf=True)) == "table-pdf"
    assert GeneratorFactory.create_generator(ExamBagLabelConfig(output_path="a.pdf", export_xlsx=False, export_pdf=True)) == "bag-pdf"

    assert [name for name, _ in captured] == [
        "corner-pdf",
        "desk-pdf",
        "ticket-pdf",
        "table-pdf",
        "bag-pdf",
    ]


def test_generator_factory_prefers_excel_generator_when_both_formats_are_enabled(monkeypatch) -> None:
    monkeypatch.setattr(factory_module, "CornerPaperGenerator", lambda config: "corner-xlsx")
    monkeypatch.setattr(factory_module, "CornerPaperPDFGenerator", lambda config: "corner-pdf")

    result = GeneratorFactory.create_generator(
        CornerPaperConfig(output_path="a.xlsx", export_xlsx=True, export_pdf=True)
    )

    assert result == "corner-xlsx"


def test_generator_factory_rejects_unsupported_config_type() -> None:
    with pytest.raises(ValueError, match="Unsupported config type"):
        GeneratorFactory.create_generator(BaseConfig(output_path="a.xlsx"))
