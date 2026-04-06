from __future__ import annotations

from backend.manual.search import format_context_snippets, search_sections


def test_manual_search_prefers_title_matches_over_content_frequency() -> None:
    sections = [
        {"title": "导入设置", "content": "简要说明"},
        {"title": "常见问题", "content": "导入 导入"},
    ]

    result = search_sections(sections, "导入", top_k=1)

    assert result == [{"title": "导入设置", "content": "简要说明"}]


def test_manual_search_returns_empty_for_blank_query() -> None:
    sections = [{"title": "导入设置", "content": "说明"}]

    assert search_sections(sections, "   ", top_k=3) == []


def test_manual_format_context_snippets_returns_empty_when_budget_is_too_small() -> None:
    sections = [{"title": "章节一", "content": "A" * 400}]

    snippet = format_context_snippets(sections, max_chars=80)

    assert snippet == ""
