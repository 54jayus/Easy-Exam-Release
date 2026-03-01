#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
使用说明页面
"""

import html
import os
import re
import sys

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QTextBrowser,
    QSplitter,
    QFileDialog,
    QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont

class HelpPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._markdown = self._get_manual_markdown()
        self._sections = self._build_sections(self._markdown)
        self._full_html = self._markdown_to_html(self._markdown)
        self._toc_item_by_anchor = {}
        self._anchor_scroll_map = {}
        self._sorted_anchor_scroll = []
        self._ignore_scroll_sync = False
        self._ignore_toc_sync = False
        self._scroll_map_retry = 0
        self._initial_state_done = False
        self._rebuild_scheduled = False
        self._pending_initial_state = False
        self.init_ui()
        
    def init_ui(self):
        """
        初始化使用说明页面界面
        """
        self.setObjectName("HelpPage")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        self._create_toolbar(main_layout)
        self._create_content_area(main_layout)
        self._apply_styles()

        self.content_view.setHtml(self._full_html)
        self._build_toc_tree()
        self._ignore_toc_sync = True
        self._apply_toc_filter()
        self._ignore_toc_sync = False
        self.content_view.verticalScrollBar().rangeChanged.connect(self._on_scroll_range_changed)
        if self.toc_tree.topLevelItemCount() > 0:
            self._ignore_toc_sync = True
            self.toc_tree.setCurrentItem(self.toc_tree.topLevelItem(0))
            self._ignore_toc_sync = False

    def showEvent(self, event):
        super().showEvent(event)
        self._schedule_rebuild_scroll_map(initial=not self._initial_state_done)

    def _on_scroll_range_changed(self, _min_v, max_v):
        if not self.isVisible():
            return
        if max_v <= 0:
            return
        if not self._initial_state_done:
            self._schedule_rebuild_scroll_map(initial=True, delay_ms=60)
            return
        if len(self._sorted_anchor_scroll) < 2:
            self._schedule_rebuild_scroll_map(initial=False, delay_ms=80)

    def _schedule_rebuild_scroll_map(self, initial=False, delay_ms=50):
        if initial and not self._initial_state_done:
            self._pending_initial_state = True
        if getattr(self, "_rebuild_scheduled", False):
            return
        self._rebuild_scheduled = True
        QTimer.singleShot(delay_ms, self._try_rebuild_scroll_map)

    def _try_rebuild_scroll_map(self):
        self._rebuild_scheduled = False
        if not self.isVisible():
            return
        sb = self.content_view.verticalScrollBar()
        if sb.maximum() <= 0:
            self._schedule_rebuild_scroll_map(initial=not self._initial_state_done, delay_ms=100)
            return
        self._scroll_map_retry = 0
        ready = self._recompute_anchor_scroll_map()
        if not ready:
            self._schedule_rebuild_scroll_map(initial=not self._initial_state_done, delay_ms=120)
            return
        if getattr(self, "_pending_initial_state", False) and not self._initial_state_done:
            self._pending_initial_state = False
            self._finalize_initial_state()
        
    def _create_toolbar(self, parent_layout):
        """
        创建工具栏
        """
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(8)

        title = QLabel("使用说明")
        title.setObjectName("HelpTitle")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)

        self.btn_open_manual = QPushButton("导出说明书")
        self.btn_open_manual.setObjectName("HelpPrimaryButton")
        self.btn_open_manual.clicked.connect(self._export_manual_pdf)

        self.search_input = QLineEdit()
        self.search_input.setObjectName("HelpSearch")
        self.search_input.setPlaceholderText("搜索目录…")
        self.search_input.textChanged.connect(self._apply_toc_filter)

        toolbar_layout.addWidget(title)
        toolbar_layout.addStretch(1)
        toolbar_layout.addWidget(self.btn_open_manual)
        toolbar_layout.addWidget(self.search_input, 1)
        parent_layout.addLayout(toolbar_layout)
    
    def _create_content_area(self, parent_layout):
        """
        创建帮助内容显示区域
        """
        splitter = QSplitter(Qt.Horizontal)
        splitter.setObjectName("HelpSplitter")
        splitter.setChildrenCollapsible(False)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(8)

        left_title = QLabel("目录")
        left_title.setObjectName("HelpSidebarTitle")

        self.toc_tree = QTreeWidget()
        self.toc_tree.setObjectName("HelpTopicTree")
        self.toc_tree.setHeaderHidden(True)
        self.toc_tree.setAnimated(True)
        self.toc_tree.currentItemChanged.connect(self._on_toc_changed)

        left_layout.addWidget(left_title)
        left_layout.addWidget(self.toc_tree, 1)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        self.right_title = QLabel("使用说明")
        self.right_title.setObjectName("HelpSidebarTitle")

        self.content_view = QTextBrowser()
        self.content_view.setObjectName("HelpContent")
        self.content_view.setOpenExternalLinks(True)
        self.content_view.verticalScrollBar().valueChanged.connect(self._on_content_scrolled)

        right_layout.addWidget(self.right_title)
        right_layout.addWidget(self.content_view, 1)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 900])

        parent_layout.addWidget(splitter, 1)

        self.status_label = QLabel("")
        self.status_label.setObjectName("HelpStatus")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        parent_layout.addWidget(self.status_label)

    def _apply_styles(self):
        self.setStyleSheet(
            """
            QWidget#HelpPage { background: #FFFFFF; }
            QLabel#HelpTitle { color: #111827; }
            QLineEdit#HelpSearch {
                min-height: 30px;
                padding: 6px 10px;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                background: #FFFFFF;
            }
            QLineEdit#HelpSearch:focus { border-color: #2563EB; }
            QPushButton {
                min-height: 30px;
                padding: 6px 12px;
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                background: #F9FAFB;
                color: #111827;
            }
            QPushButton:hover { background: #F3F4F6; }
            QPushButton:disabled { background: #F9FAFB; color: #9CA3AF; border-color: #E5E7EB; }
            QPushButton#HelpPrimaryButton { background: #2563EB; color: #FFFFFF; border-color: #2563EB; }
            QPushButton#HelpPrimaryButton:hover { background: #1D4ED8; }
            QLabel#HelpSidebarTitle { color: #111827; font-weight: 600; }
            QTreeWidget#HelpTopicTree {
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 6px;
                background: #FFFFFF;
            }
            QTreeWidget#HelpTopicTree::item {
                padding: 8px 10px;
                margin: 2px 0;
                border-radius: 8px;
            }
            QTreeWidget#HelpTopicTree::item:selected {
                background: #EEF2FF;
                color: #111827;
            }
            QTextBrowser#HelpContent {
                border: 1px solid #E5E7EB;
                border-radius: 10px;
                padding: 10px;
                background: #FFFFFF;
            }
            QLabel#HelpStatus { color: #6B7280; }
            """
        )

        self.btn_open_manual.setToolTip("将使用说明书导出为 PDF")

    def _build_toc_tree(self):
        self._toc_item_by_anchor = {}
        self.toc_tree.clear()

        stack = {}
        for s in self._sections:
            if s["level"] < 2:
                continue
            parent = stack.get(s["level"] - 1)
            item = QTreeWidgetItem([s["title"]])
            item.setData(0, Qt.UserRole, s["anchor"])
            if parent is None:
                self.toc_tree.addTopLevelItem(item)
            else:
                parent.addChild(item)
            self._toc_item_by_anchor[s["anchor"]] = item

            stack[s["level"]] = item
            for lvl in list(stack.keys()):
                if lvl > s["level"]:
                    stack.pop(lvl, None)

        self.toc_tree.expandToDepth(0)

    def _apply_toc_filter(self):
        query = (self.search_input.text() or "").strip().lower()
        visible_count = 0

        section_by_anchor = {s["anchor"]: s for s in self._sections}

        def matches(item):
            anchor = item.data(0, Qt.UserRole) or ""
            section = section_by_anchor.get(anchor)
            if section is None:
                return False
            if not query:
                return True
            return query in section["title"].lower() or query in section["content"].lower()

        def apply_recursive(item):
            nonlocal visible_count
            child_visible = False
            for i in range(item.childCount()):
                if apply_recursive(item.child(i)):
                    child_visible = True

            self_visible = matches(item)
            visible = self_visible or child_visible
            item.setHidden(not visible)
            if visible:
                visible_count += 1
                if query and (self_visible or child_visible):
                    p = item.parent()
                    while p is not None:
                        p.setExpanded(True)
                        p = p.parent()
            return visible

        for i in range(self.toc_tree.topLevelItemCount()):
            apply_recursive(self.toc_tree.topLevelItem(i))

        if visible_count == 0:
            self.status_label.setText("未找到匹配目录项，可尝试清空搜索条件")
            return

        self.status_label.setText(f"共 {visible_count} 条目录项，可搜索筛选")
        current = self.toc_tree.currentItem()
        if current is None or current.isHidden():
            self._select_first_visible()

    def _on_toc_changed(self, current, previous):
        if self._ignore_toc_sync or not current:
            return
        anchor = current.data(0, Qt.UserRole)
        if anchor:
            self._ignore_scroll_sync = True
            self.content_view.scrollToAnchor(anchor)
            self._ignore_scroll_sync = False

    def _select_first_visible(self):
        def find_visible(item):
            if not item.isHidden():
                return item
            for i in range(item.childCount()):
                found = find_visible(item.child(i))
                if found is not None:
                    return found
            return None

        for i in range(self.toc_tree.topLevelItemCount()):
            found = find_visible(self.toc_tree.topLevelItem(i))
            if found is not None:
                self.toc_tree.setCurrentItem(found)
                return

    def _recompute_anchor_scroll_map(self):
        sb = self.content_view.verticalScrollBar()
        old = sb.value()

        self._anchor_scroll_map = {}
        self._sorted_anchor_scroll = []

        self.content_view.setUpdatesEnabled(False)
        sb.blockSignals(True)
        try:
            anchor_values = []
            idx = 0
            for s in self._sections:
                if s["level"] < 2:
                    continue
                self.content_view.scrollToAnchor(s["anchor"])
                QApplication.processEvents()
                anchor_values.append((sb.value(), idx, s["anchor"]))
                idx += 1

            unique_values = len({v for v, _, _ in anchor_values})
            if unique_values <= 2 and len(anchor_values) >= 5 and self._scroll_map_retry < 3:
                self._scroll_map_retry += 1
                return False

            self._anchor_scroll_map = {anchor: v for v, _, anchor in anchor_values}
            self._sorted_anchor_scroll = sorted(anchor_values, key=lambda t: (t[0], t[1]))
        finally:
            sb.setValue(old)
            sb.blockSignals(False)
            self.content_view.setUpdatesEnabled(True)
        return True

    def _finalize_initial_state(self):
        self._scroll_map_retry = 0
        ready = self._recompute_anchor_scroll_map()
        if not ready:
            self._schedule_rebuild_scroll_map(initial=True, delay_ms=120)
            return

        anchor = ""
        if self._sorted_anchor_scroll:
            anchor = self._sorted_anchor_scroll[0][2]
        else:
            for s in self._sections:
                if s["level"] >= 2:
                    anchor = s["anchor"]
                    break

        if anchor:
            self._ignore_scroll_sync = True
            self.content_view.verticalScrollBar().setValue(0)
            self.content_view.scrollToAnchor(anchor)
            self._ignore_scroll_sync = False

        item = self._toc_item_by_anchor.get(anchor) if anchor else None
        self._ignore_toc_sync = True
        if item is None:
            self._select_first_visible()
        else:
            self.toc_tree.setCurrentItem(item)
        self._ignore_toc_sync = False
        self._initial_state_done = True

    def _on_content_scrolled(self, value):
        if self._ignore_scroll_sync or not self._sorted_anchor_scroll:
            return

        if len(self._sorted_anchor_scroll) < 2:
            self._schedule_rebuild_scroll_map(initial=False)
            return

        threshold = value + 6
        chosen = None
        chosen_v = None
        for v, idx, anchor in self._sorted_anchor_scroll:
            if v > threshold:
                break
            if chosen_v is None or v > chosen_v:
                chosen_v = v
                chosen = (v, idx, anchor)
            elif v == chosen_v and idx < chosen[1]:
                chosen = (v, idx, anchor)

        if chosen is None:
            return
        anchor = chosen[2]
        item = self._toc_item_by_anchor.get(anchor)
        if item is None:
            return
        if self.toc_tree.currentItem() is item:
            return

        self._ignore_toc_sync = True
        self.toc_tree.setCurrentItem(item)
        self._ignore_toc_sync = False

    def _get_base_path(self):
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            return sys._MEIPASS
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def _try_read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception:
            return ""

    def _get_manual_markdown(self):
        base = self._get_base_path()
        content = self._try_read_file(os.path.join(base, "使用说明书.md"))
        if content.strip():
            return content
        return self._embedded_manual_markdown()

    def _embedded_manual_markdown(self):
        return self._try_read_file(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "使用说明书.md"))) or "# 智能考务系统使用说明书\n\n（说明书内容未加载）\n"

    def _slugify(self, text):
        safe = re.sub(r"\s+", "-", text.strip())
        safe = re.sub(r"[^\w\u4e00-\u9fff\-]+", "", safe)
        return safe[:60] or "section"

    def _build_sections(self, markdown_text):
        lines = markdown_text.splitlines()
        sections = []
        current = None
        used = set()

        def finalize():
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
                base = self._slugify(title)
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

    def _markdown_to_html(self, markdown_text):
        lines = markdown_text.splitlines()
        html_lines = [
            "<html><head><meta charset='utf-8'></head><body style='font-size:13px; line-height:1.7; color:#111827;'>"
        ]

        in_code = False
        code_lines = []
        in_ul = False
        in_ol = False
        in_table = False
        table_lines = []

        def close_lists():
            nonlocal in_ul, in_ol
            if in_ul:
                html_lines.append("</ul>")
            if in_ol:
                html_lines.append("</ol>")
            in_ul = False
            in_ol = False

        def flush_code():
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

        def flush_table():
            nonlocal in_table, table_lines
            if not in_table:
                return
            rows = []
            for tl in table_lines:
                row = [c.strip() for c in tl.strip().strip("|").split("|")]
                rows.append(row)
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
                    f"<th style='border:1px solid #E5E7EB; background:#F9FAFB; padding:6px 8px; text-align:left;'>{self._md_inline_to_html(h)}</th>"
                )
            html_lines.append("</tr>")
            for r in body:
                html_lines.append("<tr>")
                for c in r:
                    html_lines.append(
                        f"<td style='border:1px solid #E5E7EB; padding:6px 8px; vertical-align:top;'>{self._md_inline_to_html(c)}</td>"
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
                anchor = self._slugify(title)
                for s in self._sections:
                    if s["title"] == title and s["level"] == level:
                        anchor = s["anchor"]
                        break
                size = {1: 20, 2: 16, 3: 14, 4: 13, 5: 12, 6: 12}.get(level, 13)
                html_lines.append(f"<a name='{html.escape(anchor)}'></a>")
                html_lines.append(
                    f"<div style='font-size:{size}px; font-weight:700; margin:14px 0 8px 0;'>{self._md_inline_to_html(title)}</div>"
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
                html_lines.append(f"<li>{self._md_inline_to_html(ul.group(1).strip())}</li>")
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
                html_lines.append(f"<li>{self._md_inline_to_html(ol.group(1).strip())}</li>")
                continue

            close_lists()
            html_lines.append(f"<div style='margin:2px 0;'>{self._md_inline_to_html(line.strip())}</div>")

        flush_table()
        close_lists()
        flush_code()
        html_lines.append("</body></html>")
        return "\n".join(html_lines)

    def _md_inline_to_html(self, text):
        t = html.escape(text)
        t = re.sub(r"`([^`]+)`", lambda m: f"<code style='background:#F3F4F6; padding:1px 4px; border-radius:4px;'>{m.group(1)}</code>", t)
        t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"<a href='\2'>\1</a>", t)
        t = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"<span>\1</span>", t)
        return t

    def _export_manual_pdf(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出使用说明书为 PDF", "智能考务系统使用说明书.pdf", "PDF Files (*.pdf)"
        )
        if not file_path:
            return
        try:
            self._export_manual_pdf_to_path(file_path)
            reply = QMessageBox.question(
                self,
                "导出成功",
                f"已导出到：\n{file_path}\n\n是否打开文件所在文件夹？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                try:
                    folder = os.path.dirname(file_path)
                    if folder and os.path.exists(folder):
                        os.startfile(folder)
                except Exception:
                    pass
        except Exception as e:
            QMessageBox.critical(self, "导出失败", f"导出PDF时出错：\n{str(e)}")

    def _export_manual_pdf_to_path(self, file_path):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted, PageBreak
        from reportlab.lib import colors
        from reportlab.platypus.tableofcontents import TableOfContents
        from ui.page.print_page.core.generators.pdf.pdf_utils import register_fonts

        register_fonts()
        font_name = "SimSun"

        # Initialize styles
        style_h1 = ParagraphStyle("H1", fontName=font_name, fontSize=16, leading=20, spaceAfter=10, spaceBefore=8)
        style_h2 = ParagraphStyle("H2", fontName=font_name, fontSize=13, leading=18, spaceAfter=8, spaceBefore=10)
        style_h3 = ParagraphStyle("H3", fontName=font_name, fontSize=11.5, leading=16, spaceAfter=6, spaceBefore=8)
        style_toc_title = ParagraphStyle("TOCTitle", fontName=font_name, fontSize=16, leading=20, spaceAfter=10, spaceBefore=8)
        style_p = ParagraphStyle("P", fontName=font_name, fontSize=10.5, leading=15, spaceAfter=4)
        style_code = ParagraphStyle("CODE", fontName=font_name, fontSize=9.5, leading=12)

        # Initialize TOC
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
                # self.notify("TOCEntry", (level, text, self.page))
                toc.addEntry(level, text, self.page)

        doc = ManualDocTemplate(
            file_path,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=16 * mm,
            bottomMargin=16 * mm,
        )

        story = []
        story.append(Paragraph("目录", style_toc_title))
        story.append(Spacer(1, 6))
        story.append(toc)
        story.append(PageBreak())

        blocks = self._parse_markdown_blocks(self._markdown)
        for b in blocks:
            t = b["type"]
            if t == "h1":
                story.append(Paragraph(self._md_inline_to_rl(b["text"]), style_h1))
            elif t == "h2":
                story.append(Paragraph(self._md_inline_to_rl(b["text"]), style_h2))
            elif t == "h3":
                story.append(Paragraph(self._md_inline_to_rl(b["text"]), style_h3))
            elif t == "p":
                story.append(Paragraph(self._md_inline_to_rl(b["text"]), style_p))
            elif t == "ul":
                for item in b["items"]:
                    story.append(Paragraph("• " + self._md_inline_to_rl(item), style_p))
                story.append(Spacer(1, 2))
            elif t == "ol":
                for idx, item in enumerate(b["items"], start=1):
                    story.append(Paragraph(f"{idx}. " + self._md_inline_to_rl(item), style_p))
                story.append(Spacer(1, 2))
            elif t == "code":
                story.append(Preformatted(b["text"], style_code, dedent=0))
                story.append(Spacer(1, 4))
            elif t == "table":
                data = [[Paragraph(self._md_inline_to_rl(c), style_p) for c in row] for row in b["rows"]]
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

    def _md_inline_to_rl(self, text):
        parts = re.split(r"(`[^`]+`)", text)
        out = []
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

    def _parse_markdown_blocks(self, markdown_text):
        lines = markdown_text.splitlines()
        blocks = []
        i = 0
        in_code = False
        code_lines = []

        def flush_paragraph(buf):
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
                items = []
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
