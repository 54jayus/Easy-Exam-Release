from collections import defaultdict
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Table, TableStyle
from xml.sax.saxutils import escape

from .pdf_utils import register_fonts


class ExamBagLabelPDFGenerator:
    """
    试卷袋标签 PDF 生成器
    按照 3x3 格式批量生成试卷袋标签（A4 竖版）
    """

    def __init__(self, config):
        self.config = config
        register_fonts()

        registered = set(pdfmetrics.getRegisteredFontNames())

        def _font_can_render(font_name: str, sample: str) -> bool:
            try:
                f = pdfmetrics.getFont(font_name)
                face = getattr(f, "face", None)
                char_to_glyph = getattr(face, "charToGlyph", None)
                if isinstance(char_to_glyph, dict):
                    for ch in sample:
                        if ord(ch) not in char_to_glyph:
                            return False
                    return True
                pdfmetrics.stringWidth(sample, font_name, 12)
                return True
            except Exception:
                return False

        def _try_register_ttf(name: str, path: str) -> bool:
            if name in registered:
                return True
            if not os.path.exists(path):
                return False
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered.add(name)
                return True
            except Exception:
                return False

        def _try_register_ttc(name: str, path: str, subfont_index: int) -> bool:
            if name in registered:
                return True
            if not os.path.exists(path):
                return False
            try:
                pdfmetrics.registerFont(TTFont(name, path, subfontIndex=subfont_index))
                registered.add(name)
                return True
            except Exception:
                return False

        simsun_ttf_paths = ["C:\\Windows\\Fonts\\simsun.ttf", "simsun.ttf"]
        simsun_ttc_paths = ["C:\\Windows\\Fonts\\simsun.ttc", "simsun.ttc"]
        simsunb_ttf_paths = ["C:\\Windows\\Fonts\\simsunb.ttf", "simsunb.ttf"]
        simhei_ttf_paths = ["C:\\Windows\\Fonts\\simhei.ttf", "simhei.ttf"]
        msyhbd_ttc_paths = ["C:\\Windows\\Fonts\\msyhbd.ttc", "msyhbd.ttc"]

        exam_font = "SimSun-ExamBag"
        exam_font_bold = "SimSun-ExamBag-Bold"
        exam_font_heavy = "SimHei-ExamBag"
        exam_font_yahei_bold = "MSYH-ExamBag-Bold"

        for p in simsun_ttf_paths:
            if _try_register_ttf(exam_font, p):
                break
        if exam_font not in registered:
            for p in simsun_ttc_paths:
                if _try_register_ttc(exam_font, p, subfont_index=0):
                    break
        for p in simsunb_ttf_paths:
            if _try_register_ttf(exam_font_bold, p):
                break
        for p in simhei_ttf_paths:
            if _try_register_ttf(exam_font_heavy, p):
                break
        for p in msyhbd_ttc_paths:
            if _try_register_ttc(exam_font_yahei_bold, p, subfont_index=0):
                break

        self.layout_rows = int(getattr(self.config, "layout_rows", 3) or 3)
        self.layout_cols = int(getattr(self.config, "layout_cols", 3) or 3)

        self.left_margin = 0.2 * inch
        self.right_margin = 0.2 * inch
        self.top_margin = 0.1 * inch
        self.bottom_margin = 0.1 * inch

        sample = "学校科目考场应到实到监考教师考试情况"
        bold_candidates = [exam_font_bold, exam_font_yahei_bold, exam_font_heavy, "SimHei", "SimSun-Bold"]
        regular_candidates = [exam_font, "SimSun", "STSong-Light"]

        chosen = None
        for name in bold_candidates:
            if name in registered and _font_can_render(name, sample):
                chosen = name
                break
        if not chosen:
            for name in regular_candidates:
                if name in registered and _font_can_render(name, sample):
                    chosen = name
                    break
        self.font_name = chosen or ("STSong-Light" if "STSong-Light" in registered else "SimSun" if "SimSun" in registered else "Helvetica")
        self.font_size = 14
        self.label_row_height_pt = 250

    def generate(self, progress_callback=None):
        output_path = self._normalize_pdf_path(str(getattr(self.config, "output_path", "") or ""))
        data_list = getattr(self.config, "student_data_list", None) or []

        tmp_path = output_path + ".tmp"
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass

        try:
            page_context_map: dict[int, str] = {}

            doc = SimpleDocTemplate(
                tmp_path,
                pagesize=A4,
                leftMargin=self.left_margin,
                rightMargin=self.right_margin,
                topMargin=self.top_margin,
                bottomMargin=self.bottom_margin,
            )

            elements = []

            if not data_list:
                total_pages = 1
                page_context_map[1] = ""

                def footer(canvas, doc):
                    canvas.saveState()
                    page_num = doc.page
                    subject = page_context_map.get(page_num, "")
                    text = f"第 {page_num} 页，共 {total_pages} 页"
                    if subject:
                        text += f"，当前科目：{subject}"
                    footer_font = "SimSun" if "SimSun" in pdfmetrics.getRegisteredFontNames() else self.font_name
                    canvas.setFont(footer_font, 8)
                    canvas.drawCentredString(A4[0] / 2.0, 5, text)
                    canvas.restoreState()

                elements.append(self._build_page_table(doc, []))
                doc.build(elements, onFirstPage=footer, onLaterPages=footer)
                self._assert_valid_pdf(tmp_path)
                self._replace_file(tmp_path, output_path)
                return output_path

            subjects_map: dict[str, list[dict]] = defaultdict(list)
            subject_order: list[str] = []
            seen: set[str] = set()

            for item in data_list:
                subj = str((item or {}).get("subject", "")).strip()
                subjects_map[subj].append(item)
                if subj not in seen:
                    subject_order.append(subj)
                    seen.add(subj)

            total_subjects = len(subject_order)
            capacity = max(1, self.layout_rows) * max(1, self.layout_cols)

            current_page = 1
            for subj in subject_order:
                items = subjects_map.get(subj, [])
                pages_count = (len(items) + capacity - 1) // capacity if items else 1
                for p in range(pages_count):
                    page_context_map[current_page + p] = subj
                current_page += pages_count
            total_pages = current_page - 1

            def footer(canvas, doc):
                canvas.saveState()
                page_num = doc.page
                subject = page_context_map.get(page_num, "")
                text = f"第 {page_num} 页，共 {total_pages} 页"
                if subject:
                    text += f"，当前科目：{subject}"
                footer_font = "SimSun" if "SimSun" in pdfmetrics.getRegisteredFontNames() else self.font_name
                canvas.setFont(footer_font, 8)
                canvas.drawCentredString(A4[0] / 2.0, 5, text)
                canvas.restoreState()

            for subj_index, subj in enumerate(subject_order):
                if progress_callback:
                    progress_callback(subj_index, total_subjects)

                items = subjects_map.get(subj, [])
                chunks = [items[i : i + capacity] for i in range(0, len(items), capacity)] or [[]]

                for chunk_index, chunk in enumerate(chunks):
                    elements.append(self._build_page_table(doc, chunk))

                    is_last_subject = subj_index == total_subjects - 1
                    is_last_chunk = chunk_index == len(chunks) - 1
                    if not (is_last_subject and is_last_chunk):
                        elements.append(PageBreak())

            doc.build(elements, onFirstPage=footer, onLaterPages=footer)
            self._assert_valid_pdf(tmp_path)
            self._replace_file(tmp_path, output_path)
            return output_path
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            if "Permission denied" in str(e):
                raise Exception(f"无法保存文件，请关闭已打开的 PDF 文件: {output_path}")
            raise e

    def _build_page_table(self, doc: SimpleDocTemplate, items: list[dict]):
        school_name = str(getattr(self.config, "school_name", "") or "xxx学校").strip() or "xxx学校"

        style = ParagraphStyle(
            name="ExamBagLabel",
            fontName=self.font_name,
            fontSize=self.font_size,
            leading=16,
            alignment=0,
            wordWrap="LTR",
        )

        grid: list[list[Paragraph]] = []
        idx = 0
        for _r in range(self.layout_rows):
            row: list[Paragraph] = []
            for _c in range(self.layout_cols):
                item = items[idx] if idx < len(items) else None
                idx += 1

                if item:
                    subject = escape(str(item.get("subject", "") or ""))
                    room = escape(str(item.get("room", "") or ""))
                    count = escape(str(item.get("count", "") or ""))
                    content = (
                        f"学校：{escape(school_name)}<br/><br/>"
                        f"科目：{subject}<br/><br/>"
                        f"考场：{room}（{count}人）<br/><br/>"
                        f"应到：<br/><br/>"
                        f"实到：<br/><br/>"
                        f"监考教师：<br/><br/>"
                        f"考试情况："
                    )
                else:
                    content = ""

                row.append(Paragraph(content, style))
            grid.append(row)

        table = Table(
            grid,
            colWidths=[doc.width / self.layout_cols] * self.layout_cols,
            rowHeights=[
                self.label_row_height_pt if self.layout_rows == 3 else (doc.height / max(1, self.layout_rows))
            ]
            * self.layout_rows,
        )
        table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), self.font_name),
                    ("FONTSIZE", (0, 0), (-1, -1), self.font_size),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        return table

    def _normalize_pdf_path(self, path: str) -> str:
        root, ext = os.path.splitext(path)
        if ext.lower() != ".pdf":
            return root + ".pdf"
        return path

    def _assert_valid_pdf(self, file_path: str):
        try:
            with open(file_path, "rb") as f:
                head = f.read(5)
            if head != b"%PDF-":
                raise Exception("文件头不是 PDF")
        except Exception as e:
            raise Exception(f"PDF 生成失败（输出文件损坏）：{str(e)}")

    def _replace_file(self, src: str, dst: str):
        os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
        os.replace(src, dst)
