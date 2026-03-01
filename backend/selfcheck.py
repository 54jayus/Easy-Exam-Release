from __future__ import annotations

import importlib
import os
import tempfile


def main() -> int:
    import backend  # noqa: F401

    from backend.assistant import AssistantEngine  # noqa: F401
    from backend.licensing import LicenseManager  # noqa: F401
    from backend.manual import export_manual_pdf, load_manual_markdown  # noqa: F401
    from backend.proctoring import (  # noqa: F401
        DataImporter,
        Schedule,
        Teacher,
        build_empty_overview_template_df,
        export_schedule_to_excel,
        export_schedule_workbook_to_excel,
        import_schedule_from_excel,
        import_teachers_with_validation,
        parse_schedule_from_excel,
        write_teacher_template_xlsx,
        write_empty_overview_template_xlsx,
    )

    from backend.examroom import ExamArrangement  # noqa: F401
    from backend.printing import GeneratorFactory  # noqa: F401
    from backend.printing.core.config import AdmissionTicketConfig
    from backend.subjects import generate_subject_template_xlsx, import_subjects_from_excel  # noqa: F401

    out_path = os.path.join(tempfile.gettempdir(), "examdesk_selfcheck_ticket.pdf")
    cfg = AdmissionTicketConfig(
        output_path=out_path,
        export_xlsx=False,
        export_pdf=True,
        subjects=["科目"],
        subject_times=["02-13 09:00-11:00"],
        title="测试准考证",
        num_templates=1,
        student_data_list=[
            {
                "考场": "示例考场",
                "考场号": "001",
                "座位号": "01",
                "考生姓名": "张三",
                "考生考号": "243800622",
                "班级": 6,
                "学号": 22,
            }
        ],
    )
    generator = GeneratorFactory.create_generator(cfg)
    generator.generate()
    try:
        os.remove(out_path)
    except Exception:
        pass

    print("backend selfcheck: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
