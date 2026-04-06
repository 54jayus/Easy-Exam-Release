from __future__ import annotations

from backend.manual.markdown import build_sections, markdown_to_html, slugify
from backend.manual.search import _tokenize_query, format_context_snippets, search_sections


def test_manual_search_tokenizes_and_matches_sections() -> None:
    sections = [
        {"title": "考场编排", "content": "支持导入考生和导出结果"},
        {"title": "资料打印", "content": "可以生成准考证和台角纸"},
    ]

    tokens = _tokenize_query("考场导入失败")
    result = search_sections(sections, "考场导入失败", top_k=1)

    assert "考场" in tokens
    assert "导入" in tokens
    assert result == [{"title": "考场编排", "content": "支持导入考生和导出结果"}]


def test_manual_format_context_snippets_truncates_when_needed() -> None:
    sections = [{"title": "章节一", "content": "A" * 400}]

    snippet = format_context_snippets(sections, max_chars=220)

    assert "### 章节一" in snippet
    assert "内容截断" in snippet


def test_manual_markdown_builds_sections_and_html() -> None:
    markdown = "# 标题\n\n- 列表项\n\n## 子标题\n\n| 列1 | 列2 |\n| --- | --- |\n| A | B |\n"

    sections = build_sections(markdown)
    html = markdown_to_html(markdown, sections=sections)

    assert slugify("资料打印 / Guide") == "资料打印-Guide"
    assert sections[0]["title"] == "标题"
    assert sections[1]["title"] == "子标题"
    assert "<ul" in html
    assert "<table" in html
    assert "子标题" in html
