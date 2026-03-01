from __future__ import annotations

from typing import List, Sequence

from .core.data_import import DataImporter
from .core.models import Teacher


def import_teachers_with_validation(
    file_path: str,
    *,
    mode: str,
    gender_mix: bool,
    internal_mix: bool,
    subject_count: int,
    subject_names: Sequence[str],
    num_rooms: int | None,
) -> tuple[list[Teacher], list[str], list[str]]:
    try:
        teachers = DataImporter.import_teachers_from_excel(file_path)
    except ValueError as e:
        return [], [str(e)], []
    except Exception as e:
        return [], [f"导入失败: {str(e)}"], []

    errors, warnings = DataImporter.validate_teachers(
        teachers,
        mode,
        gender_mix,
        internal_mix,
        subject_count=subject_count,
        subject_names=list(subject_names),
        source_file_path=file_path,
        num_rooms=num_rooms,
    )

    return teachers, errors, warnings
