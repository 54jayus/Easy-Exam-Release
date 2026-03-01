import os
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .pdf_utils import PAGE_HEIGHT, PAGE_WIDTH, register_fonts


class CornerPaperPDFGenerator:
    """
    台角纸 PDF 生成器
    """

    def __init__(self, config):
        self.config = config
        register_fonts()

        # 页面设置 (横向 A4)
        self.page_width, self.page_height = landscape(A4)
        # Margins from Excel: left=0.2, right=0, top=0.1, bottom=0.06 (inch)
        self.left_margin = 0.1 * inch
        self.right_margin = 0.1 * inch  # 给一点余量
        self.top_margin = 0.05 * inch
        self.bottom_margin = 0

        self.content_width = self.page_width - self.left_margin - self.right_margin

        # 模板布局
        self.templates_per_row = 3
        # 计算每个模板的宽度
        # Excel Col Widths: 10.6, 8.6, 12.6, 11.6. Total ~43.4 units.
        # Plus spacing cols.
        # We should just divide content_width by 3.
        self.template_width = self.content_width / self.templates_per_row

        # 动态计算每页行数 (Templates Per Column per Page)
        subject_count = len(self.config.subjects)
        if subject_count <= 3:
            self.templates_per_col_page = 5
        elif 4 <= subject_count <= 5:
            self.templates_per_col_page = 4
        elif 6 <= subject_count <= 9:
            self.templates_per_col_page = 3
        else:  # >= 10
            self.templates_per_col_page = 2

    def generate(self, progress_callback=None):
        output_path = self.config.output_path.replace(".xlsx", ".pdf")
        student_data = self.config.student_data_list

        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            leftMargin=self.left_margin,
            rightMargin=self.right_margin,
            topMargin=self.top_margin,
            bottomMargin=self.bottom_margin,
        )

        elements = []

        # 预计算页码和上下文信息
        page_context_map = {}
        current_page = 1

        if not student_data:
            # 空白模式
            num_templates = self.config.num_templates
            dummy_data = [None] * num_templates

            # 计算空白模式的总页数
            grid_rows = (num_templates + self.templates_per_row - 1) // self.templates_per_row
            pages_count = (grid_rows + self.templates_per_col_page - 1) // self.templates_per_col_page
            if pages_count == 0:
                pages_count = 1

            for p in range(pages_count):
                page_context_map[current_page + p] = ""
            current_page += pages_count

            self._generate_sheet(elements, dummy_data, progress_callback)
        else:
            # 数据模式：按考场分组
            rooms_map = {}
            room_order = []
            seen = set()
            for d in student_data:
                room = d.get("考场", "未命名考场")
                if room not in rooms_map:
                    rooms_map[room] = []
                    room_order.append(room)
                rooms_map[room].append(d)

            total_rooms = len(rooms_map)

            # 预计算页码映射
            for room in room_order:
                data = rooms_map[room]
                count = len(data)
                grid_rows = (count + self.templates_per_row - 1) // self.templates_per_row
                pages_count = (grid_rows + self.templates_per_col_page - 1) // self.templates_per_col_page
                if pages_count == 0:
                    pages_count = 1

                for p in range(pages_count):
                    page_context_map[current_page + p] = room
                current_page += pages_count

            # 生成内容
            for idx, room in enumerate(room_order):
                if progress_callback:
                    progress_callback(idx, total_rooms)

                room_data = rooms_map[room]
                self._generate_sheet(elements, room_data, None)

                if idx < len(room_order) - 1:
                    elements.append(PageBreak())

        total_pages = current_page - 1

        def footer(canvas, doc):
            canvas.saveState()
            page_num = doc.page
            room = page_context_map.get(page_num, "")

            # 页脚格式：第 X 页，共 Y 页，当前考场：XXX
            text = f"第 {page_num} 页，共 {total_pages} 页"
            if room:
                text += f"，当前考场：{room}"

            canvas.setFont("SimSun", 8)
            # 居中显示，位置在页面底部
            # 页面高度 A4 Landscape = 595pt approx.
            # 底部 Margin 是 0.1 inch = 7.2 pt.
            # 我们放在 10pt 处 (稍微高一点点)
            canvas.drawCentredString(self.page_width / 2.0, 5, text)
            canvas.restoreState()

        try:
            doc.build(elements, onFirstPage=footer, onLaterPages=footer)
            return output_path
        except Exception as e:
            if "Permission denied" in str(e):
                raise Exception(f"无法保存文件，请关闭已打开的 PDF 文件: {output_path}")
            raise e

    def _create_template_table(self, data):
        """创建单个台角纸模板的 Table"""
        # 数据提取
        kaochang = data.get("考场", "") if data else ""
        kaochang_no = data.get("考场号", "") if data else ""
        seat_no = data.get("座位号", "") if data else ""
        name = data.get("考生姓名", "") if data else ""
        exam_no = data.get("考生考号", "") if data else ""

        class_no = data.get("班级", "") if data else ""
        student_no = data.get("学号", "") if data else ""

        class_student = ""
        if data and "考生班级学号" in data:
            class_student = data["考生班级学号"]
        elif data:
            class_student = f"{class_no}班{student_no}号"

        # 样式
        style_title = ParagraphStyle("Title", fontName="SimSun", fontSize=14, alignment=1, leading=16)
        style_header = ParagraphStyle("Header", fontName="SimSun", fontSize=10, alignment=1, leading=12)
        style_normal = ParagraphStyle("Normal", fontName="SimSun", fontSize=10, alignment=1, leading=12)

        # 表格数据
        # Row 1: Title
        row1 = [Paragraph(self.config.title, style_title), "", "", ""]

        # Row 2: 考场 info
        row2 = [
            Paragraph("考场", style_header),
            Paragraph(kaochang, style_normal),
            Paragraph("考场号", style_header),
            Paragraph(kaochang_no, style_normal),
        ]

        # Row 3: 座位号 info
        row3 = ["", "", Paragraph("座位号", style_header), Paragraph(seat_no, style_normal)]

        # Row 4: Headers
        row4 = [
            Paragraph("科目", style_header),
            Paragraph("考生姓名", style_header),
            Paragraph("考生考号", style_header),
            Paragraph("考生班级学号", style_header),
        ]

        rows = [row1, row2, row3, row4]

        # Rows 5+: Subjects
        subjects = self.config.subjects
        for sub in subjects:
            r = [
                Paragraph(sub, style_normal),
                Paragraph(name, style_normal),
                Paragraph(exam_no, style_normal),
                Paragraph(class_student, style_normal),
            ]
            rows.append(r)

        # 创建表格
        # Column widths ratios: 10.6, 8.6, 12.6, 11.6
        # Total = 43.4
        total_ratio = 43.4
        # Scale to template_width (minus padding)
        # Leaving some space for cutting line column
        content_w = self.template_width - 10  # 10pt for right gap

        # Modified ratios to give more space to "考生班级学号" (w4)
        # Old: 10.6, 8.6, 12.6, 11.6
        # New: 9.6, 8.6, 12.6, 12.6 (Shifted 1.0 from Subject to Class/No)
        w1 = content_w * (9.6 / total_ratio)
        w2 = content_w * (8.6 / total_ratio)
        w3 = content_w * (12.6 / total_ratio)
        w4 = content_w * (12.6 / total_ratio)
        col_widths = [w1, w2, w3, w4]

        t = Table(rows, colWidths=col_widths)

        # 样式
        ts = [
            ("FONTNAME", (0, 0), (-1, -1), "SimSun"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("SPAN", (0, 0), (3, 0)),  # Merge title
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            # Reduce padding to fit text better
            ("LEFTPADDING", (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
            # Row 3 Empty cells borders?
            # Excel: cell(2, 0) border is thin.
            # So keep grid.
        ]

        # Set Row Heights
        # Title: 18.75pt
        # Others: 13.5pt
        row_heights = [18.75] + [13.5] * (len(rows) - 1)
        t._argH = row_heights

        t.setStyle(TableStyle(ts))
        return t

    def _generate_sheet(self, elements, data_list, progress_callback):
        num_templates = len(data_list)
        total_grid_rows = (num_templates + self.templates_per_row - 1) // self.templates_per_row

        # 外部表格数据
        outer_rows = []

        for grid_row in range(total_grid_rows):
            # 分页检查
            if grid_row > 0 and grid_row % self.templates_per_col_page == 0:
                # 添加分页符
                # 由于我们是在构建大表格的行，不能直接插入 PageBreak 到 Table 中
                # 所以我们必须中断当前的 outer_table，插入 PageBreak，然后开始新的 Table

                # 提交当前的 outer_rows
                if outer_rows:
                    t = Table(outer_rows, colWidths=[self.template_width] * 3)
                    t.setStyle(
                        TableStyle(
                            [
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),  # 行间距从10减小到5
                            ]
                        )
                    )
                    elements.append(t)
                    outer_rows = []

                elements.append(PageBreak())

            current_row_templates = []
            for col_offset in range(self.templates_per_row):
                template_idx = grid_row * self.templates_per_row + col_offset
                if template_idx < num_templates:
                    data = data_list[template_idx]
                    t_template = self._create_template_table(data)
                    current_row_templates.append(t_template)
                else:
                    current_row_templates.append("")

            outer_rows.append(current_row_templates)

        # 提交剩余的
        if outer_rows:
            t = Table(outer_rows, colWidths=[self.template_width] * 3)
            t.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 2),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            elements.append(t)


class AdmissionTicketPDFGenerator:
    """
    准考证 PDF 生成器
    """

    def __init__(self, config):
        self.config = config
        register_fonts()

        # 页面设置 (横向 A4)
        self.page_width, self.page_height = landscape(A4)
        # Margins from Excel: left=0.1, right=0.1, top=0.05, bottom=0.1 (inch) - Matching CornerPaper
        self.left_margin = 0.1 * inch
        self.right_margin = 0.1 * inch
        self.top_margin = 0.05 * inch
        self.bottom_margin = 0.1 * inch

        self.content_width = self.page_width - self.left_margin - self.right_margin

        # 模板布局
        self.templates_per_row = 3
        # 计算每个模板的宽度
        # Excel Col Widths: A=10.63, B=13.63, C=8.63, D=6.63, E=6.63, F=1.63, G=1.00
        # Total Units = 48.78 (Approx)
        # Content cols (A-E): ~46.15 units
        # Spacing cols (F-G): ~2.63 units
        # We divide content_width by 3 to get width per template block (including spacing)
        self.block_width = self.content_width / self.templates_per_row

        # Scale block_width slightly down to ensure fit and create gaps
        # Similar logic to CornerPaperPDFGenerator: content_w = self.template_width - 10
        self.template_content_width = self.block_width - 10

        # Recalculate column widths based on new template_content_width
        # A=10.63, B=13.63, C=8.63, D=6.63, E=6.63 => Total Ratio ~46.15
        total_content_ratio = 46.15
        w1 = self.template_content_width * (8.5 / total_content_ratio)
        w2 = self.template_content_width * (17.5 / total_content_ratio)
        w3 = self.template_content_width * (7.63 / total_content_ratio)
        w4 = self.template_content_width * (6.45 / total_content_ratio)
        w5 = self.template_content_width * (6.45 / total_content_ratio)

        self.col_widths = [w1, w2, w3, w4, w5]
        subject_count = len(self.config.subjects)
        if subject_count <= 3:
            self.templates_per_col_page = 5
        elif 4 <= subject_count <= 5:
            self.templates_per_col_page = 4
        elif 6 <= subject_count <= 9:
            self.templates_per_col_page = 3
        else:  # >= 10
            self.templates_per_col_page = 2

        self.subject_times = getattr(config, "subject_times", [""] * len(self.config.subjects))

    def generate(self, progress_callback=None):
        output_path = self.config.output_path.replace(".xlsx", ".pdf")
        student_data = self.config.student_data_list

        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            leftMargin=self.left_margin,
            rightMargin=self.right_margin,
            topMargin=self.top_margin,
            bottomMargin=self.bottom_margin,
        )

        elements = []

        # 预计算页码和上下文信息
        page_context_map = {}
        current_page = 1

        if not student_data:
            # 空白模式
            num_templates = self.config.num_templates
            dummy_data = [None] * num_templates

            # 计算空白模式的总页数
            grid_rows = (num_templates + self.templates_per_row - 1) // self.templates_per_row
            pages_count = (grid_rows + self.templates_per_col_page - 1) // self.templates_per_col_page
            if pages_count == 0:
                pages_count = 1

            for p in range(pages_count):
                page_context_map[current_page + p] = ""
            current_page += pages_count

            self._generate_sheet(elements, dummy_data, progress_callback)
        else:
            # 数据模式：按班级分组 (用户要求)

            # 辅助排序函数
            def safe_int_sort_key(val):
                if isinstance(val, int):
                    return val
                if isinstance(val, str) and val.isdigit():
                    return int(val)
                match = re.search(r"(\d+)", str(val))
                if match:
                    return int(match.group(1))
                return 0

            # 1. 排序：班级 -> 学号
            student_data.sort(key=lambda x: (safe_int_sort_key(x.get("班级", 0)), safe_int_sort_key(x.get("学号", 0))))

            # 2. 分组：班级
            class_groups = {}
            class_order = []

            for d in student_data:
                bj_val = d.get("班级", "未分类")
                class_name = f"{bj_val}班" if str(bj_val).isdigit() else str(bj_val)

                if class_name not in class_groups:
                    class_groups[class_name] = []
                    class_order.append(class_name)
                class_groups[class_name].append(d)

            total_classes = len(class_groups)

            # 预计算页码映射
            for cls_name in class_order:
                data = class_groups[cls_name]
                count = len(data)
                grid_rows = (count + self.templates_per_row - 1) // self.templates_per_row
                pages_count = (grid_rows + self.templates_per_col_page - 1) // self.templates_per_col_page
                if pages_count == 0:
                    pages_count = 1

                for p in range(pages_count):
                    page_context_map[current_page + p] = cls_name
                current_page += pages_count

            # 生成内容
            for idx, cls_name in enumerate(class_order):
                if progress_callback:
                    progress_callback(idx, total_classes)

                cls_data = class_groups[cls_name]
                self._generate_sheet(elements, cls_data, None)

                if idx < len(class_order) - 1:
                    elements.append(PageBreak())

        total_pages = current_page - 1

        def footer(canvas, doc):
            canvas.saveState()
            page_num = doc.page
            cls_name = page_context_map.get(page_num, "")

            # 页脚格式：第 X 页，共 Y 页，当前班级：XXX
            text = f"第 {page_num} 页，共 {total_pages} 页"
            if cls_name:
                text += f"，当前班级：{cls_name}"

            canvas.setFont("SimSun", 8)
            # 居中显示，位置在页面底部
            canvas.drawCentredString(self.page_width / 2.0, 5, text)
            canvas.restoreState()

        try:
            doc.build(elements, onFirstPage=footer, onLaterPages=footer)
            return output_path
        except Exception as e:
            if "Permission denied" in str(e):
                raise Exception(f"无法保存文件，请关闭已打开的 PDF 文件: {output_path}")
            raise e

    def _create_template_table(self, data):
        """创建单个准考证模板的 Table"""
        def _t(v):
            return "" if v is None else str(v)

        # 数据提取
        kaochang = _t(data.get("考场", "")) if data else ""
        kaochang_no = _t(data.get("考场号", "")) if data else ""
        seat_no = _t(data.get("座位号", "")) if data else ""
        name = _t(data.get("考生姓名", "")) if data else ""
        exam_no = _t(data.get("考生考号", "")) if data else ""

        class_no = _t(data.get("班级", "")) if data else ""
        student_no = _t(data.get("学号", "")) if data else ""

        # 样式
        style_title = ParagraphStyle("Title", fontName="SimSun", fontSize=14, alignment=1, leading=16)
        style_header = ParagraphStyle("Header", fontName="SimSun", fontSize=10, alignment=1, leading=12)
        style_normal = ParagraphStyle("Normal", fontName="SimSun", fontSize=10, alignment=1, leading=12)

        # 表格数据
        # Row 1: Title (Merged A-E)
        row1 = [Paragraph(_t(self.config.title), style_title), "", "", "", ""]

        # Row 2: 考号, 考号值, 班级, 班级值 (Merged C-D for label? No, Excel merge C-D for label "班级")
        # Layout: A=考号, B=Val, C+D=班级, E=Val
        row2 = [
            Paragraph("考号", style_header),
            Paragraph(exam_no, style_normal),
            Paragraph("班级", style_header),
            "",
            Paragraph(class_no, style_normal),
        ]

        # Row 3: 姓名, 姓名值, 学号, 学号值
        # Layout: A=姓名, B=Val, C+D=学号, E=Val
        row3 = [
            Paragraph("姓名", style_header),
            Paragraph(name, style_normal),
            Paragraph("学号", style_header),
            "",
            Paragraph(student_no, style_normal),
        ]

        # Row 4: Headers
        # A=科目, B=时间, C=考场, D=考场号, E=座位号
        row4 = [
            Paragraph("科目", style_header),
            Paragraph("时间", style_header),
            Paragraph("考场", style_header),
            Paragraph("考场号", style_header),
            Paragraph("座位号", style_header),
        ]

        rows = [row1, row2, row3, row4]

        # Rows 5+: Subjects
        subjects = self.config.subjects
        for i, sub in enumerate(subjects):
            time_val = _t(self.subject_times[i]) if i < len(self.subject_times) else ""
            r = [
                Paragraph(_t(sub), style_normal),
                Paragraph(time_val, style_normal),
                Paragraph(kaochang, style_normal),
                Paragraph(kaochang_no, style_normal),
                Paragraph(seat_no, style_normal),
            ]
            rows.append(r)

        # 创建表格
        # Column widths ratios based on Excel
        # A=10.63, B=13.63, C=8.63, D=6.63, E=6.63
        # Total Content Ratio = 46.15

        # We need to fit this into block_width minus spacing (F, G cols in Excel are spacing)
        # F=1.63, G=1.00 => ~2.63 spacing ratio
        # Total Block Ratio = 46.15 + 2.63 = 48.78

        # Use pre-calculated widths
        t = Table(rows, colWidths=self.col_widths)

        # 样式
        ts = [
            ("FONTNAME", (0, 0), (-1, -1), "SimSun"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("SPAN", (0, 0), (4, 0)),  # Merge title A-E
            ("SPAN", (2, 1), (3, 1)),  # Merge Class Label C-D
            ("SPAN", (2, 2), (3, 2)),  # Merge StudentNo Label C-D
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (-1, -1), 1),
            ("RIGHTPADDING", (0, 0), (-1, -1), 1),
        ]

        # Set Row Heights
        # Title: 18.75pt
        # Others: 13.5pt
        row_heights = [18.75] + [13.5] * (len(rows) - 1)
        t._argH = row_heights

        t.setStyle(TableStyle(ts))
        return t

    def _generate_sheet(self, elements, data_list, progress_callback):
        num_templates = len(data_list)
        total_grid_rows = (num_templates + self.templates_per_row - 1) // self.templates_per_row

        # 外部表格数据
        outer_rows = []

        for grid_row in range(total_grid_rows):
            # 分页检查
            if grid_row > 0 and grid_row % self.templates_per_col_page == 0:
                if outer_rows:
                    t = Table(outer_rows, colWidths=[self.block_width] * 3)
                    t.setStyle(
                        TableStyle(
                            [
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),  # 垂直间距
                            ]
                        )
                    )
                    elements.append(t)
                    outer_rows = []

                elements.append(PageBreak())

            current_row_templates = []
            for col_offset in range(self.templates_per_row):
                template_idx = grid_row * self.templates_per_row + col_offset
                if template_idx < num_templates:
                    data = data_list[template_idx]
                    t_template = self._create_template_table(data)
                    current_row_templates.append(t_template)
                else:
                    current_row_templates.append("")

            outer_rows.append(current_row_templates)

        # 提交剩余的
        if outer_rows:
            t = Table(outer_rows, colWidths=[self.block_width] * 3)
            t.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 2),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            elements.append(t)
