from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from backend.repository.state_repository import serialize_state

if TYPE_CHECKING:
    from backend.domain.state import AppState


class RecordingStateRepository:
    """Simple in-memory repository used by tests to track save calls."""

    def __init__(self) -> None:
        self.save_calls = 0
        self.delete_calls = 0
        self.export_calls = 0
        self.import_calls = 0
        self.last_saved_state: dict | None = None

    def save(self, state: "AppState") -> None:
        self.save_calls += 1
        self.last_saved_state = serialize_state(state)

    def load(self, state: "AppState") -> None:
        return None

    def delete(self) -> None:
        self.delete_calls += 1

    def export_to(self, path: str, state: "AppState") -> None:
        self.export_calls += 1
        self.last_saved_state = serialize_state(state)

    def import_from(self, path: str, state: "AppState") -> None:
        self.import_calls += 1


@pytest.fixture
def recording_repo() -> RecordingStateRepository:
    return RecordingStateRepository()
