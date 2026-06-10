import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas
from reportlab.platypus import Frame, PageTemplate, Paragraph, SimpleDocTemplate, Table, TableStyle
from xml.sax.saxutils import escape

from .pdf_utils import PAGE_HEIGHT, PAGE_WIDTH, register_fonts
from backend.printing.core.seat_layout import get_seat_mapping, layout_for_room, normalize_layout


class DeskLabelPDFGenerator:
    """
    桌角纸 PDF 生成器
    """

    def __init__(self, config):
        self.config = config
        register_fonts()

        # 页面设置
        self.margin = 5 * mm
        self.page_width = PAGE_WIDTH
        self.page_height = PAGE_HEIGHT
        self.content_width = self.page_width - 2 * self.margin
        self.content_height = self.page_height - 2 * self.margin

        # 布局参数
        self.rows = self.config.layout_rows
        self.cols = self.config.layout_cols

        self.grid_line_width = 0.5
        self.frame_padding = 6
        self.safe_gap = 2 * mm + 2 * self.frame_padding
        self.cell_padding_left = 3
        self.cell_padding_right = 3
        self.cell_padding_top = 1
        self.cell_padding_bottom = 1

        # 计算单元格尺寸
        # ReportLab 的 Table 在临界情况下会因为线宽/舍入导致表格高度略超出 Frame，从而把最后一行挤到下一页。
        # 这里为宽高预留少量“安全余量”，确保一整张表稳定落在同一页。
        effective_width = self.content_width - (self.cols + 1) * self.grid_line_width - self.safe_gap
        effective_height = self.content_height - (self.rows + 1) * self.grid_line_width - self.safe_gap
        if effective_width <= 0:
            effective_width = self.content_width
        if effective_height <= 0:
            effective_height = self.content_height

        self.cell_width = effective_width / self.cols
        self.cell_height = effective_height / self.rows

    def _fit_font_size(self, text, max_width, base_size, min_size):
        try:
            size = base_size
            while size > min_size and pdfmetrics.stringWidth(text, "SimSun", size) > max_width:
                size -= 1
            return size
        except Exception:
            return base_size

    def _get_seat_mapping(self, rows, cols, pattern, start_pos):
        """
        复用 DeskLabelGenerator 的座位映射逻辑
        这里简单复制一份，或者重构 shared logic。
        为简单起见，这里复制逻辑。
        """
        one_based = get_seat_mapping({
            "layoutRows": rows,
            "layoutCols": cols,
            "layoutPattern": pattern,
            "startPos": start_pos,
            "customColCounts": self.config.custom_col_counts,
        })
        return {seat - 1: position for seat, position in one_based.items()}

    def generate(self, progress_callback=None):
        output_path = self.config.output_path.replace(".xlsx", ".pdf")
        student_data = self.config.student_data_list

        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            leftMargin=self.margin,
            rightMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin,
        )

        elements = []

        if not student_data:
            # 空白模式
            total_count = self.config.total_count
            fake_data = [{"考生姓名": "", "考生考号": "", "考场": "", "考场号": "", "座位号": ""} for _ in range(total_count)]
            self._generate_content(elements, fake_data, progress_callback)
        else:
            # 数据模式：按考场分组
            rooms_map = {}
            room_order = []
            seen = set()
            for item in student_data:
                room = item.get("考场", "未命名考场")
                if room not in rooms_map:
                    rooms_map[room] = []
                rooms_map[room].append(item)
                if room not in seen:
                    room_order.append(room)
                    seen.add(room)

            total_rooms = len(rooms_map)
            for idx, room in enumerate(room_order):
                if progress_callback:
                    progress_callback(idx, total_rooms)

                room_data = rooms_map[room]
                room_no = room_data[0].get("考场号", "") if room_data else ""
                room_layout = layout_for_room(self.config.seat_layout, room_no) if self.config.seat_layout else None
                self._generate_content(elements, room_data, None, room_layout)

                # 每个考场之后添加分页符（除非是最后一个考场）
                if idx < len(room_order) - 1:
                    # 实际上 SimpleDocTemplate 自动分页，这里需要强制分页
                    from reportlab.platypus import PageBreak

                    elements.append(PageBreak())

        try:
            doc.build(elements)
            return output_path
        except Exception as e:
            # 如果文件被占用
            if "Permission denied" in str(e):
                raise Exception(f"无法保存文件，请关闭已打开的 PDF 文件: {output_path}")
            raise e

    def _generate_content(self, elements, data_list, progress_callback, layout=None):
        # 分页处理
        effective = normalize_layout(layout or {
            "layoutRows": self.rows,
            "layoutCols": self.cols,
            "layoutPattern": getattr(self.config, "layout_pattern", "S型横排"),
            "startPos": getattr(self.config, "start_pos", "left"),
            "customColCounts": self.config.custom_col_counts,
        })
        rows = effective["layoutRows"]
        cols = effective["layoutCols"]
        capacity = len(get_seat_mapping(effective))
        chunks = [data_list[i : i + capacity] for i in range(0, len(data_list), capacity)]

        seat_mapping = {seat - 1: position for seat, position in get_seat_mapping(effective).items()}
        cell_width = (self.content_width - (cols + 1) * self.grid_line_width - self.safe_gap) / cols
        cell_height = (self.content_height - (rows + 1) * self.grid_line_width - self.safe_gap) / rows

        style = ParagraphStyle(
            name="DeskLabel",
            fontName="SimSun",
            fontSize=10,
            leading=12,
            alignment=0,
            wordWrap="LTR",
        )

        for chunk_idx, chunk in enumerate(chunks):
            # 准备表格数据
            # grid[row][col]
            grid_data = [["" for _ in range(cols)] for _ in range(rows)]
            
            pos_to_student = {}
            for idx, student in enumerate(chunk):
                pos = seat_mapping.get(idx)
                if not pos:
                    continue
                pos_to_student[pos] = student

            for r in range(rows):
                for c in range(cols):
                    student = pos_to_student.get((r, c))
                    if student:
                        name = escape(str(student.get("考生姓名", "") or ""))
                        num = escape(str(student.get("考生考号", "") or ""))
                        room = escape(str(student.get("考场", "") or ""))
                        room_num = escape(str(student.get("考场号", "") or ""))
                        seat = escape(str(student.get("座位号", "") or ""))

                        max_line_width = cell_width - self.cell_padding_left - self.cell_padding_right - 2
                        num_line = f"考号：{num}"
                        num_size = self._fit_font_size(num_line, max_line_width, base_size=10, min_size=7)
                        num_line_html = f'<font size="{num_size}">{num_line}</font>'

                        text = (
                            f"姓名：{name}<br/>"
                            f"{num_line_html}<br/>"
                            f"考场：{room}<br/>"
                            f"考场号：{room_num}<br/>"
                            f"座位号：{seat}"
                        )
                    else:
                        text = "姓名：<br/>考号：<br/>考场：<br/>考场号：<br/>座位号："
                    grid_data[r][c] = Paragraph(text, style)

            # grid_data 已填满

            # 创建表格
            # 设置列宽和行高
            col_widths = [cell_width] * cols
            row_heights = [cell_height] * rows

            table = Table(grid_data, colWidths=col_widths, rowHeights=row_heights)

            # 设置样式
            table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), "SimSun"),
                        ("FONTSIZE", (0, 0), (-1, -1), 10),
                        ("GRID", (0, 0), (-1, -1), self.grid_line_width, colors.black),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), self.cell_padding_left),
                        ("RIGHTPADDING", (0, 0), (-1, -1), self.cell_padding_right),
                        ("TOPPADDING", (0, 0), (-1, -1), self.cell_padding_top),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), self.cell_padding_bottom),
                    ]
                )
            )

            elements.append(table)

            # 如果不是最后一块，添加分页
            if chunk_idx < len(chunks) - 1:
                from reportlab.platypus import PageBreak

                elements.append(PageBreak())
