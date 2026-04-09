from __future__ import annotations

from dataclasses import asdict
from typing import Any

from backend.domain.state import AppState
from backend.repository.interfaces import IStateRepository
from backend.subjects.core import Subject, _coerce_duration_minutes, _coerce_room_count, validate_subjects
from backend.subjects.excel import (
    export_subjects_to_excel,
    generate_subject_template_xlsx,
    import_subjects_from_excel,
)


class SubjectsService:
    def __init__(self, state: AppState, repo: IStateRepository):
        self._state = state
        self._repo = repo

    def _subject_from_dict(self, data: dict[str, Any]) -> Subject:
        return Subject(
            name=data.get("name", ""),
            exam_date=data.get("exam_date", data.get("date", "")),
            exam_time=data.get("exam_time", data.get("time", "")),
            remark=data.get("remark", ""),
            duration_minutes=_coerce_duration_minutes(
                data.get("duration_minutes", data.get("durationMinutes", data.get("duration", 0)))
            ) or 0,
            room_count=_coerce_room_count(data.get("room_count", data.get("roomCount", 0))) or 0,
        )

    def list(self, _params: dict) -> Any:
        result = []
        for idx, s in enumerate(self._state.subjects):
            s_dict = dict(s)
            s_dict["id"] = str(idx + 1)
            result.append(s_dict)
        return {"subjects": result}

    def _reset_proctoring_if_scheduled(self) -> bool:
        """如果已有监考编排结果，清除它并返回 True。"""
        from backend.domain.state import ProctoringState
        if self._state.proctoring.schedule:
            self._state.proctoring = ProctoringState()
            return True
        return False

    def update(self, params: dict) -> Any:
        subjects_data = params.get("subjects", [])
        self._state.subjects = [asdict(self._subject_from_dict(subject)) for subject in subjects_data]
        proctoring_reset = self._reset_proctoring_if_scheduled()
        self._repo.save(self._state)
        return {"proctoringReset": proctoring_reset}

    def import_from_excel(self, params: dict) -> Any:
        path = params["path"]
        result = import_subjects_from_excel(path)
        self._state.subjects = [asdict(s) for s in result.subjects]
        proctoring_reset = self._reset_proctoring_if_scheduled()
        self._repo.save(self._state)
        response_subjects = []
        for idx, s in enumerate(self._state.subjects):
            s_dict = dict(s)
            s_dict["id"] = str(idx + 1)
            response_subjects.append(s_dict)
        return {"subjects": response_subjects, "errors": result.errors, "proctoringReset": proctoring_reset}

    def export(self, params: dict) -> Any:
        path = params["path"]
        subjects_data = params["subjects"]
        subjects = [self._subject_from_dict(s) for s in subjects_data]
        export_subjects_to_excel(path, subjects=subjects)
        return {}

    def template(self, params: dict) -> Any:
        path = params["path"]
        generate_subject_template_xlsx(path)
        return {}

    def validate(self, params: dict) -> Any:
        subjects_data = params["subjects"]
        subjects = [self._subject_from_dict(s) for s in subjects_data]
        errors = validate_subjects(subjects)
        return {"errors": errors}
