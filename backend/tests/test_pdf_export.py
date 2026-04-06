from __future__ import annotations

from backend.manual.pdf_export import _md_inline_to_rl, _parse_markdown_blocks, export_manual_pdf


def test_md_inline_to_rl_escapes_html_and_formats_code_and_bold() -> None:
    text = "示例 <tag> **加粗** `print(1)` `中文代码`"

    result = _md_inline_to_rl(text)

    assert "&lt;tag&gt;" in result
    assert "<b>加粗</b>" in result
    assert "<font face='Courier'>print(1)</font>" in result
    assert "<font face='SimSun'>中文代码</font>" in result


def test_parse_markdown_blocks_extracts_common_block_types() -> None:
    markdown = """# 标题

普通段落
- 条目一
- 条目二
1. 第一步
2. 第二步
| 列1 | 列2 |
| --- | --- |
| A | B |

```python
print("ok")
```
"""

    blocks = _parse_markdown_blocks(markdown)

    assert blocks == [
        {"type": "h1", "text": "标题"},
        {"type": "p", "text": "普通段落"},
        {"type": "ul", "items": ["条目一", "条目二"]},
        {"type": "ol", "items": ["第一步", "第二步"]},
        {"type": "table", "rows": [["列1", "列2"], ["A", "B"]]},
        {"type": "code", "text": 'print("ok")'},
    ]


def test_export_manual_pdf_creates_non_empty_pdf(tmp_path) -> None:
    output = tmp_path / "manual.pdf"

    export_manual_pdf(
        str(output),
        markdown_text="""# 使用手册

## 快速开始
普通说明段落。

- 导入学生
- 编排考场

| 步骤 | 说明 |
| --- | --- |
| 1 | 准备数据 |
| 2 | 导出结果 |
""",
    )

    assert output.exists()
    assert output.stat().st_size > 0
    assert output.read_bytes().startswith(b"%PDF")
