from __future__ import annotations

import sys
from pathlib import Path

from backend.manual.loader import get_app_base_dir, load_manual_markdown


def test_get_app_base_dir_prefers_environment(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EXAMFLOW_APP_DIR", str(tmp_path))

    assert get_app_base_dir() == tmp_path.resolve()


def test_get_app_base_dir_uses_frozen_executable(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("EXAMFLOW_APP_DIR", raising=False)
    monkeypatch.delenv("EXAMDESK_APP_DIR", raising=False)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(tmp_path / "app.exe"), raising=False)

    assert get_app_base_dir() == tmp_path.resolve()


def test_load_manual_markdown_uses_first_existing_candidate(monkeypatch, tmp_path) -> None:
    backend_resources = tmp_path / "backend" / "resources"
    backend_resources.mkdir(parents=True)
    manual_path = backend_resources / "使用说明书.md"
    manual_path.write_text("# Manual\n\nLoaded", encoding="utf-8")
    monkeypatch.setenv("EXAMFLOW_APP_DIR", str(tmp_path))

    content = load_manual_markdown()

    assert content == "# Manual\n\nLoaded"


def test_load_manual_markdown_returns_placeholder_when_missing(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("EXAMFLOW_APP_DIR", str(tmp_path))

    content = load_manual_markdown()

    assert "说明书内容未加载" in content
