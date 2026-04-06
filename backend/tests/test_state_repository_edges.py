from __future__ import annotations

import pandas as pd

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
