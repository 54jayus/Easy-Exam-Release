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
        mapping = {}
        current_seat = 0
        custom_counts = self.config.custom_col_counts

        def is_valid_pos(r, c):
            if custom_counts:
                if c < len(custom_counts):
                    return r < custom_counts[c]
            return True
        
        # 无论 start_pos 是左手位还是右手位，生成文件时都强制以“右手位”（左上角）作为起始位
        # 这样打印出来的纸张，座位1总是在左上角，符合剪裁习惯
        def get_actual_col(logic_col):
            # if start_pos == "left":
            #     return cols - 1 - logic_col
            return logic_col

        if pattern == "Z型横排":
            for r in range(rows):
                for c in range(cols):
                    actual_c = get_actual_col(c)
                    if is_valid_pos(r, actual_c):
                        mapping[current_seat] = (r, actual_c)
                        current_seat += 1
        elif pattern == "S型横排":
            for r in range(rows):
                is_even_row = r % 2 == 0
                if is_even_row:
                    for c in range(cols):
                        actual_c = get_actual_col(c)
                        if is_valid_pos(r, actual_c):
                            mapping[current_seat] = (r, actual_c)
                            current_seat += 1
                else:
                    for c in range(cols - 1, -1, -1):
                        actual_c = get_actual_col(c)
                        if is_valid_pos(r, actual_c):
                            mapping[current_seat] = (r, actual_c)
                            current_seat += 1
        elif pattern == "Z型竖排":
            for c in range(cols):
                for r in range(rows):
                    actual_c = get_actual_col(c)
                    if is_valid_pos(r, actual_c):
                        mapping[current_seat] = (r, actual_c)
                        current_seat += 1
        elif pattern == "S型竖排":
            for c in range(cols):
                is_even_col = c % 2 == 0
                actual_c = get_actual_col(c)
                if is_even_col:
                    for r in range(rows):
                        if is_valid_pos(r, actual_c):
                            mapping[current_seat] = (r, actual_c)
                            current_seat += 1
                else:
                    for r in range(rows - 1, -1, -1):
                        if is_valid_pos(r, actual_c):
                            mapping[current_seat] = (r, actual_c)
                            current_seat += 1
        return mapping

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
                self._generate_content(elements, room_data, None)

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

    def _generate_content(self, elements, data_list, progress_callback):
        # 分页处理
        capacity = self.rows * self.cols
        chunks = [data_list[i : i + capacity] for i in range(0, len(data_list), capacity)]

        pattern = getattr(self.config, "layout_pattern", "S型横排")
        start_pos = getattr(self.config, "start_pos", "left")
        seat_mapping = self._get_seat_mapping(self.rows, self.cols, pattern, start_pos)

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
            grid_data = [["" for _ in range(self.cols)] for _ in range(self.rows)]
            
            pos_to_student = {}
            for idx, student in enumerate(chunk):
                pos = seat_mapping.get(idx)
                if not pos:
                    continue
                pos_to_student[pos] = student

            for r in range(self.rows):
                for c in range(self.cols):
                    student = pos_to_student.get((r, c))
                    if student:
                        name = escape(str(student.get("考生姓名", "") or ""))
                        num = escape(str(student.get("考生考号", "") or ""))
                        room = escape(str(student.get("考场", "") or ""))
                        room_num = escape(str(student.get("考场号", "") or ""))
                        seat = escape(str(student.get("座位号", "") or ""))

                        max_line_width = self.cell_width - self.cell_padding_left - self.cell_padding_right - 2
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
            col_widths = [self.cell_width] * self.cols
            row_heights = [self.cell_height] * self.rows

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
