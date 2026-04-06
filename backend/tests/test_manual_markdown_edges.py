from __future__ import annotations

from backend.manual.markdown import _md_inline_to_html, build_sections, markdown_to_html, slugify


def test_slugify_trims_collapses_and_falls_back_to_section() -> None:
    assert slugify("  A / B !!  ") == "A-B"
    assert slugify("----") == "section"


def test_build_sections_creates_top_section_and_unique_anchors() -> None:
    sections = build_sections("前言\n\n# 标题\n内容\n# 标题\n第二段")

    assert sections == [
        {"level": 1, "title": "文档", "anchor": "top", "content": "前言"},
        {"level": 1, "title": "标题", "anchor": "标题", "content": "内容"},
        {"level": 1, "title": "标题", "anchor": "标题-2", "content": "第二段"},
    ]


def test_md_inline_to_html_renders_images_before_links() -> None:
    result = _md_inline_to_html("![图示](demo.png) [文档](guide.html)")

    assert "<span>图示</span>" in result
    assert "<a href='guide.html'>文档</a>" in result
    assert "!<a href='demo.png'>" not in result


def test_markdown_to_html_uses_unique_anchors_for_duplicate_headings() -> None:
    markdown = "# 标题\n第一段\n# 标题\n第二段"

    html = markdown_to_html(markdown)

    assert html.count("<a name='标题'></a>") == 1
    assert html.count("<a name='标题-2'></a>") == 1
