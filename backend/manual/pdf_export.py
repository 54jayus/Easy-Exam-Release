from __future__ import annotations

import html
import os
import re
from pathlib import Path
from typing import Any

from backend.printing.core.generators.pdf.pdf_utils import register_fonts


def _md_inline_to_rl(text: str) -> str:
    parts = re.split(r"(`[^`]+`)", text or "")
    out: list[str] = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            code = part[1:-1]
            font = "Courier" if getattr(code, "isascii", lambda: False)() else "SimSun"
            out.append(f"<font face='{font}'>{html.escape(code)}</font>")
        else:
            out.append(html.escape(part))
    t = "".join(out)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return t


def _parse_markdown_blocks(markdown_text: str) -> list[dict[str, Any]]:
    lines = (markdown_text or "").splitlines()
    blocks: list[dict[str, Any]] = []
    i = 0
    in_code = False
    code_lines: list[str] = []

    def flush_paragraph(buf: list[str]) -> None:
        text = "\n".join([l.strip() for l in buf]).strip()
        if text:
            blocks.append({"type": "p", "text": text})

    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            if in_code:
                blocks.append({"type": "code", "text": "\n".join(code_lines)})
                in_code = False
                code_lines = []
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue

        m = re.match(r"^(#{1,3})\s+(.+?)\s*$", line)
        if m:
            level = len(m.group(1))
            blocks.append({"type": f"h{level}", "text": m.group(2).strip()})
            i += 1
            continue

        if "|" in line and re.match(r"^\s*\|?.+\|.+\|?\s*$", line):
            table = [line]
            j = i + 1
            while j < len(lines) and "|" in lines[j]:
                table.append(lines[j])
                j += 1
            rows = [[c.strip() for c in tl.strip().strip("|").split("|")] for tl in table]
            if len(rows) >= 2:
                body = rows[2:] if re.match(r"^\s*:?-{3,}:?\s*$", rows[1][0]) else rows[1:]
                blocks.append({"type": "table", "rows": [rows[0]] + body})
                i = j
                continue

        if re.match(r"^\s*[-*]\s+.+$", line):
            items: list[str] = []
            j = i
            while j < len(lines):
                mm = re.match(r"^\s*[-*]\s+(.+)$", lines[j])
                if not mm:
                    break
                items.append(mm.group(1).strip())
                j += 1
            blocks.append({"type": "ul", "items": items})
            i = j
            continue

        if re.match(r"^\s*\d+\.\s+.+$", line):
            items = []
            j = i
            while j < len(lines):
                mm = re.match(r"^\s*\d+\.\s+(.+)$", lines[j])
                if not mm:
                    break
                items.append(mm.group(1).strip())
                j += 1
            blocks.append({"type": "ol", "items": items})
            i = j
            continue

        if not line.strip():
            i += 1
            continue

        buf = [line]
        j = i + 1
        while (
            j < len(lines)
            and lines[j].strip()
            and not re.match(r"^(#{1,3})\s+(.+?)\s*$", lines[j])
            and not re.match(r"^\s*[-*]\s+.+$", lines[j])
            and not re.match(r"^\s*\d+\.\s+.+$", lines[j])
            and not lines[j].strip().startswith("```")
        ):
            if "|" in lines[j] and re.match(r"^\s*\|?.+\|.+\|?\s*$", lines[j]):
                break
            buf.append(lines[j])
            j += 1
        flush_paragraph(buf)
        i = j

    if in_code and code_lines:
        blocks.append({"type": "code", "text": "\n".join(code_lines)})
    return blocks


def export_manual_pdf(file_path: str, *, markdown_text: str) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer, Table, TableStyle
    from reportlab.platypus.tableofcontents import TableOfContents

    register_fonts()
    font_name = "SimSun"

    style_h1 = ParagraphStyle("H1", fontName=font_name, fontSize=16, leading=20, spaceAfter=10, spaceBefore=8)
    style_h2 = ParagraphStyle("H2", fontName=font_name, fontSize=13, leading=18, spaceAfter=8, spaceBefore=10)
    style_h3 = ParagraphStyle("H3", fontName=font_name, fontSize=11.5, leading=16, spaceAfter=6, spaceBefore=8)
    style_toc_title = ParagraphStyle("TOCTitle", fontName=font_name, fontSize=16, leading=20, spaceAfter=10, spaceBefore=8)
    style_p = ParagraphStyle("P", fontName=font_name, fontSize=10.5, leading=15, spaceAfter=4)
    style_code = ParagraphStyle("CODE", fontName=font_name, fontSize=9.5, leading=12)

    toc = TableOfContents()
    toc.levelStyles = [
        ParagraphStyle("TOC1", fontName=font_name, fontSize=11, leading=14, leftIndent=0, spaceBefore=2, spaceAfter=2),
        ParagraphStyle("TOC2", fontName=font_name, fontSize=10, leading=13, leftIndent=12, spaceBefore=1, spaceAfter=1),
        ParagraphStyle("TOC3", fontName=font_name, fontSize=9.5, leading=12, leftIndent=24, spaceBefore=1, spaceAfter=1),
    ]

    class ManualDocTemplate(SimpleDocTemplate):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._heading_id = 0

        def beforeDocument(self):
            self._heading_id = 0

        def afterFlowable(self, flowable):
            if not isinstance(flowable, Paragraph):
                return
            style_name = getattr(flowable.style, "name", "")
            if style_name not in ("H1", "H2", "H3"):
                return
            level = {"H1": 0, "H2": 1, "H3": 2}[style_name]
            text = flowable.getPlainText()
            self._heading_id += 1
            key = f"toc_{level}_{self._heading_id}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=False)
            toc.addEntry(level, text, self.page)

    doc = ManualDocTemplate(
        file_path,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
    )

    story: list[Any] = []
    story.append(Paragraph("目录", style_toc_title))
    story.append(Spacer(1, 6))
    story.append(toc)
    story.append(PageBreak())

    blocks = _parse_markdown_blocks(markdown_text)
    for b in blocks:
        t = b["type"]
        if t == "h1":
            story.append(Paragraph(_md_inline_to_rl(b["text"]), style_h1))
        elif t == "h2":
            story.append(Paragraph(_md_inline_to_rl(b["text"]), style_h2))
        elif t == "h3":
            story.append(Paragraph(_md_inline_to_rl(b["text"]), style_h3))
        elif t == "p":
            story.append(Paragraph(_md_inline_to_rl(b["text"]), style_p))
        elif t == "ul":
            for item in b["items"]:
                story.append(Paragraph("• " + _md_inline_to_rl(item), style_p))
            story.append(Spacer(1, 2))
        elif t == "ol":
            for idx, item in enumerate(b["items"], start=1):
                story.append(Paragraph(f"{idx}. " + _md_inline_to_rl(item), style_p))
            story.append(Spacer(1, 2))
        elif t == "code":
            story.append(Preformatted(b["text"], style_code, dedent=0))
            story.append(Spacer(1, 4))
        elif t == "table":
            data = [[Paragraph(_md_inline_to_rl(c), style_p) for c in row] for row in b["rows"]]
            tbl = Table(data, hAlign="LEFT")
            tbl.setStyle(
                TableStyle(
                    [
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("FONTNAME", (0, 0), (-1, -1), font_name),
                        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                )
            )
            story.append(tbl)
            story.append(Spacer(1, 6))

    doc.multiBuild(story)

