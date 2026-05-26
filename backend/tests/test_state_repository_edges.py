from __future__ import annotations

import pandas as pd
import pytest

from backend.domain.state import AppState
from backend.repository.state_repository import (
    StateRepository,
    _deserialize_gaokao_results,
    _serialize_gaokao_results,
)


def test_state_repository_load_ignores_invalid_json(tmp_path) -> None:
    state_file = tmp_path / "state.json"
    state_file.write_text("{invalid json", encoding="utf-8")
    state = AppState()
    state.subjects = [{"id": "keep"}]

    StateRepository(str(state_file)).load(state)

    assert state.subjects == [{"id": "keep"}]


def test_state_repository_delete_removes_persisted_file(tmp_path) -> None:
    state_file = tmp_path / "state.json"
    repo = StateRepository(str(state_file))
    repo.save(AppState())

    repo.delete()

    assert state_file.exists() is False


def test_state_repository_import_rejects_invalid_json_without_mutating_state(tmp_path) -> None:
    state_file = tmp_path / "grade1.examstate"
    state_file.write_text("{invalid json", encoding="utf-8")
    repo = StateRepository(str(tmp_path / "state.json"))
    state = AppState()
    state.subjects = [{"id": "keep"}]

    with pytest.raises(Exception):
        repo.import_from(str(state_file), state)

    assert state.subjects == [{"id": "keep"}]


def test_state_repository_import_rejects_invalid_document_without_mutating_state(tmp_path) -> None:
    state_file = tmp_path / "grade1.examstate"
    state_file.write_text('{"version":"1.0.0","state":[]}', encoding="utf-8")
    repo = StateRepository(str(tmp_path / "state.json"))
    state = AppState()
    state.subjects = [{"id": "keep"}]

    with pytest.raises(ValueError, match="格式无效"):
        repo.import_from(str(state_file), state)

    assert state.subjects == [{"id": "keep"}]


def test_gaokao_result_helpers_preserve_non_empty_frames_and_empty_markers() -> None:
    serialized = _serialize_gaokao_results(
        {
            "unified": pd.DataFrame(),
            "electives": {
                "化学": pd.DataFrame([{"考号": "240001"}]),
                "政治": pd.DataFrame(),
            },
        }
    )

    assert serialized == {
        "unified": None,
        "electives": {
            "化学": [{"考号": "240001"}],
            "政治": None,
        },
    }

    restored = _deserialize_gaokao_results(serialized)

    assert restored["unified"] is None
    assert restored["electives"]["化学"].to_dict("records") == [{"考号": "240001"}]
    assert restored["electives"]["政治"] is None
