from __future__ import annotations

import html
import re
from typing import Any


def slugify(text: str) -> str:
    safe = re.sub(r"\s+", "-", (text or "").strip())
    safe = re.sub(r"[^\w\u4e00-\u9fff\-]+", "", safe)
    safe = re.sub(r"-{2,}", "-", safe).strip("-")
    return safe[:60] or "section"


def build_sections(markdown_text: str) -> list[dict[str, Any]]:
    lines = (markdown_text or "").splitlines()
    sections: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    used: set[str] = set()

    def finalize() -> None:
        nonlocal current
        if not current:
            return
        current["content"] = "\n".join(current["content"]).strip()
        sections.append(current)
        current = None

    for line in lines:
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            finalize()
            level = len(m.group(1))
            title = m.group(2).strip()
            base = slugify(title)
            anchor = base
            idx = 2
            while anchor in used:
                anchor = f"{base}-{idx}"
                idx += 1
            used.add(anchor)
            current = {"level": level, "title": title, "anchor": anchor, "content": []}
        else:
            if current is None:
                current = {"level": 1, "title": "文档", "anchor": "top", "content": []}
                used.add("top")
            current["content"].append(line)
    finalize()
    return sections


def _md_inline_to_html(text: str) -> str:
    t = html.escape(text or "")
    t = re.sub(
        r"`([^`]+)`",
        lambda m: f"<code style='background:#F3F4F6; padding:1px 4px; border-radius:4px;'>{m.group(1)}</code>",
        t,
    )
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href='\2'>\1</a>", t)
    t = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"<span>\1</span>", t)
    return t


def markdown_to_html(markdown_text: str, *, sections: list[dict[str, Any]] | None = None) -> str:
    sections = list(sections or build_sections(markdown_text))
    lines = (markdown_text or "").splitlines()
    html_lines = [
        "<html><head><meta charset='utf-8'></head><body style='font-size:13px; line-height:1.7; color:#111827;'>"
    ]

    in_code = False
    code_lines: list[str] = []
    in_ul = False
    in_ol = False
    in_table = False
    table_lines: list[str] = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            html_lines.append("</ul>")
        if in_ol:
            html_lines.append("</ol>")
        in_ul = False
        in_ol = False

    def flush_code() -> None:
        nonlocal in_code, code_lines
        if not in_code:
            return
        code = "\n".join(code_lines)
        html_lines.append(
            "<pre style='background:#F3F4F6; padding:10px; border-radius:8px; overflow:auto;'><code>"
            + html.escape(code)
            + "</code></pre>"
        )
        in_code = False
        code_lines = []

    def flush_table() -> None:
        nonlocal in_table, table_lines
        if not in_table:
            return
        rows: list[list[str]] = []
        for tl in table_lines:
            rows.append([c.strip() for c in tl.strip().strip("|").split("|")])
        in_table = False
        table_lines = []
        if len(rows) < 2:
            return
        header = rows[0]
        body = rows[2:] if re.match(r"^\s*:?-{3,}:?\s*$", rows[1][0]) else rows[1:]
        html_lines.append("<table style='border-collapse:collapse; width:100%; margin:10px 0;'>")
        html_lines.append("<tr>")
        for h in header:
            html_lines.append(
                f"<th style='border:1px solid #E5E7EB; background:#F9FAFB; padding:6px 8px; text-align:left;'>{_md_inline_to_html(h)}</th>"
            )
        html_lines.append("</tr>")
        for r in body:
            html_lines.append("<tr>")
            for c in r:
                html_lines.append(
                    f"<td style='border:1px solid #E5E7EB; padding:6px 8px; vertical-align:top;'>{_md_inline_to_html(c)}</td>"
                )
            html_lines.append("</tr>")
        html_lines.append("</table>")

    for raw in lines:
        line = raw.rstrip("\n")

        if line.strip().startswith("```"):
            flush_table()
            close_lists()
            if in_code:
                flush_code()
            else:
                in_code = True
                code_lines = []
            continue

        if in_code:
            code_lines.append(line)
            continue

        if "|" in line and re.match(r"^\s*\|?.+\|.+\|?\s*$", line):
            table_lines.append(line)
            in_table = True
            continue
        if in_table:
            flush_table()

        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            close_lists()
            level = len(m.group(1))
            title = m.group(2).strip()
            anchor = slugify(title)
            for s in sections:
                if s["title"] == title and s["level"] == level:
                    anchor = s["anchor"]
                    break
            size = {1: 20, 2: 16, 3: 14, 4: 13, 5: 12, 6: 12}.get(level, 13)
            html_lines.append(f"<a name='{html.escape(anchor)}'></a>")
            html_lines.append(
                f"<div style='font-size:{size}px; font-weight:700; margin:14px 0 8px 0;'>{_md_inline_to_html(title)}</div>"
            )
            continue

        if not line.strip():
            flush_table()
            close_lists()
            html_lines.append("<div style='height:8px;'></div>")
            continue

        ul = re.match(r"^\s*[-*]\s+(.+)$", line)
        if ul:
            flush_table()
            if in_ol:
                html_lines.append("</ol>")
                in_ol = False
            if not in_ul:
                html_lines.append("<ul style='margin:6px 0 6px 22px;'>")
                in_ul = True
            html_lines.append(f"<li>{_md_inline_to_html(ul.group(1).strip())}</li>")
            continue

        ol = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if ol:
            flush_table()
            if in_ul:
                html_lines.append("</ul>")
                in_ul = False
            if not in_ol:
                html_lines.append("<ol style='margin:6px 0 6px 22px;'>")
                in_ol = True
            html_lines.append(f"<li>{_md_inline_to_html(ol.group(1).strip())}</li>")
            continue

        close_lists()
        html_lines.append(f"<div style='margin:2px 0;'>{_md_inline_to_html(line.strip())}</div>")

    flush_table()
    close_lists()
    flush_code()
    html_lines.append("</body></html>")
    return "\n".join(html_lines)

