from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

from backend.printing.core.config import StudentInfoTableConfig
from backend.printing.core.generators.pdf.student_info_pdf import StudentInfoTablePDFGenerator


def test_examroom_pdf_layout_shrinks_rows_to_fit_single_room_page(tmp_path) -> None:
    generator = StudentInfoTablePDFGenerator(
        StudentInfoTableConfig(
            output_path=str(tmp_path / "student-info.pdf"),
            export_xlsx=False,
            export_pdf=True,
            group_mode="examroom",
        )
    )

    available_height = A4[1] - 20 * mm
    layout = generator._compute_layout(available_height, 50, include_summary=True)

    assert layout["body_h"] < 16.5
    assert layout["body_h"] >= 10
    assert layout["max_rows_last"] == 50
    assert layout["max_rows_mid"] == 50
