from collections import defaultdict

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Table, TableStyle

from .pdf_utils import register_fonts


class StudentInfoTablePDFGenerator:
    def __init__(self, config):
        self.config = config
        self.include_subject_fields = bool(getattr(config, "include_subject_fields", False))
        self.group_mode = str(getattr(config, "group_mode", "class") or "class")

    def generate(self, progress_callback=None):
        register_fonts()

        out_path = self.config.output_path
        title_value = getattr(self.config, "title", "") or ""
        data_list = getattr(self.config, "student_data_list", None) or []

        grouped = self._group_data(data_list)
        group_order = sorted(grouped.keys(), key=self._group_sort_key)

        doc = SimpleDocTemplate(
            out_path,
            pagesize=A4,
            leftMargin=10 * mm,
            rightMargin=10 * mm,
            topMargin=10 * mm,
            bottomMargin=10 * mm,
        )

        font_name = "SimSun"
        headers = self._headers()
        col_widths = self._build_col_widths(doc.width)

        story = []

        if not group_order:
            blank_rows = 42 if self.group_mode == "examroom" else 50
            layout = self._compute_layout(doc.height, blank_rows, include_summary=False)
            table_data = [self._title_row(title_value, len(headers), font_name), headers]
            table_data += [[""] * len(headers) for _ in range(blank_rows)]
            row_heights = [layout["title_h"], layout["header_h"]] + [layout["body_h"]] * blank_rows
            story.append(self._build_table(table_data, col_widths, row_heights, font_name, layout["font_size"]))
            doc.build(story)
            return out_path

        total_groups = len(group_order)
        for group_index, group_key in enumerate(group_order, start=1):
            students = grouped[group_key]
            group_label = self._group_display_name(group_key, students)
            layout = self._compute_layout(doc.height, len(students), include_summary=True)
            chunks = self._split_students_for_pages(students, layout["max_rows_mid"], layout["max_rows_last"])
            for chunk_index, chunk in enumerate(chunks):
                table_data = [self._title_row(title_value, len(headers), font_name), headers]
                for row in chunk["rows"]:
                    table_data.append(self._row_values(row))
                if chunk["is_last_page_of_class"]:
                    table_data.append(self._count_row(group_label, len(students), len(headers)))
                row_heights = [layout["title_h"], layout["header_h"]] + [layout["body_h"]] * len(chunk["rows"])
                if chunk["is_last_page_of_class"]:
                    row_heights.append(layout["summary_h"])
                story.append(self._build_table(table_data, col_widths, row_heights, font_name, layout["font_size"]))
                if chunk_index != len(chunks) - 1:
                    story.append(PageBreak())

            if progress_callback:
                progress_callback(group_index, total_groups)

            if group_index != total_groups:
                story.append(PageBreak())

        doc.build(story)
        return out_path

    def _headers(self):
        if self.include_subject_fields:
            return ["班级", "学号", "姓名", "考号", "首选", "选科1", "选科2", "考场", "考场号", "座位"]
        return ["班级", "学号", "姓名", "考号", "考场", "考场号", "座位"]

    def _group_data(self, data_list):
        if self.group_mode == "examroom":
            return self._group_by_examroom(data_list)
        return self._group_by_class(data_list)

    def _group_sort_key(self, group_key):
        if self.group_mode == "examroom":
            return self._examroom_sort_key(group_key)
        return self._class_sort_key(group_key)

    def _group_display_name(self, group_key, students):
        if self.group_mode == "examroom":
            room = str((students[0] if students else {}).get("考场", "")).strip()
            if room:
                return room
            key = str(group_key).strip()
            return key or "考场"
        return str(group_key).strip()

    def _title_row(self, title_value, col_count, font_name):
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle("StudentInfoTitle", parent=styles["Title"], fontName=font_name, fontSize=14, leading=16, alignment=1)
        row = [""] * col_count
        row[0] = Paragraph(str(title_value or ""), title_style)
        return row

    def _row_values(self, item):
        if self.include_subject_fields:
            return [
                str(item.get("班级", "")),
                str(item.get("学号", "")),
                str(item.get("考生姓名", item.get("姓名", ""))),
                str(item.get("考生考号", item.get("考号", ""))),
                str(item.get("首选", item.get("类别", ""))),
                str(item.get("选科1", item.get("选1", ""))),
                str(item.get("选科2", item.get("选2", ""))),
                str(item.get("考场", "")),
                str(item.get("考场号", "")),
                str(item.get("座位号", item.get("座位", ""))),
            ]
        return [
            str(item.get("班级", "")),
            str(item.get("学号", "")),
            str(item.get("考生姓名", item.get("姓名", ""))),
            str(item.get("考生考号", item.get("考号", ""))),
            str(item.get("考场", "")),
            str(item.get("考场号", "")),
            str(item.get("座位号", item.get("座位", ""))),
        ]

    def _count_row(self, class_name, count, col_count):
        row = [""] * col_count
        label = f"{class_name} 计数".strip()
        label_col = 0
        if self.group_mode == "examroom":
            label_col = 7 if self.include_subject_fields else 4
        row[label_col] = label
        if col_count >= 3:
            row[2] = str(count)
        elif col_count >= 2:
            row[1] = str(count)
        return row

    def _build_col_widths(self, available_width):
        if self.include_subject_fields:
            weights = [5, 5, 7, 12, 5, 5, 5, 9, 6, 5]
        else:
            weights = [5, 5, 7, 12, 9, 6, 5]
        total = sum(weights)
        return [available_width * (w / total) for w in weights]

    def _compute_layout(self, available_height, student_count, include_summary=True):
        if self.group_mode == "examroom":
            title_h = 22
            header_h = 20
            summary_h = 16.5 if include_summary else 0
            min_body_h = 16.5
            max_body_h = 16.5
            safety_gap = 24
        else:
            title_h = 22
            header_h = 20
            summary_h = 16 if include_summary else 0
            min_body_h = 11
            max_body_h = 16
            safety_gap = 24

        safe_count = max(1, int(student_count))
        body_h_fit = (available_height - title_h - header_h - summary_h - safety_gap) / safe_count
        body_h = min(max_body_h, body_h_fit)
        body_h = max(min_body_h, body_h)

        if self.include_subject_fields:
            font_size = 8
            if body_h < 13:
                font_size = 7
            if body_h < 12:
                font_size = 6
        else:
            font_size = 9
            if body_h < 13:
                font_size = 8
            if body_h < 12:
                font_size = 7

        max_rows_last = int((available_height - title_h - header_h - summary_h - safety_gap) // min_body_h)
        max_rows_last = max(5, max_rows_last)
        max_rows_mid = int((available_height - title_h - header_h - safety_gap) // min_body_h)
        max_rows_mid = max(5, max_rows_mid)

        if safe_count <= max_rows_last:
            max_rows_last = safe_count
            max_rows_mid = safe_count

        return {
            "title_h": title_h,
            "header_h": header_h,
            "summary_h": summary_h,
            "body_h": body_h,
            "font_size": font_size,
            "max_rows_mid": max_rows_mid,
            "max_rows_last": max_rows_last,
        }

    def _split_students_for_pages(self, students, max_rows_mid, max_rows_last):
        n = len(students)
        if n <= max_rows_last:
            return [{"rows": students, "is_last_page_of_class": True}]

        chunks = []
        start = 0
        while start < n:
            remaining = n - start
            if remaining <= max_rows_last:
                chunks.append({"rows": students[start:], "is_last_page_of_class": True})
                break
            end = start + max_rows_mid
            chunks.append({"rows": students[start:end], "is_last_page_of_class": False})
            start = end
        return chunks

    def _build_table(self, table_data, col_widths, row_heights, font_name, font_size):
        table = Table(table_data, colWidths=col_widths, rowHeights=row_heights, repeatRows=2)

        style = TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("FONTSIZE", (0, 0), (-1, 0), 14),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#F2F2F2")),
                ("LINEBELOW", (0, 1), (-1, 1), 1, colors.black),
                ("SPAN", (0, 0), (-1, 0)),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
        table.setStyle(style)
        return table

    def _group_by_class(self, data_list):
        grouped = defaultdict(list)
        for item in data_list:
            class_value = item.get("班级", "")
            grouped[str(class_value).strip()].append(item)
        for _, students in grouped.items():
            students.sort(key=self._class_student_sort_key)
        return grouped

    def _group_by_examroom(self, data_list):
        grouped = defaultdict(list)
        for item in data_list:
            examroom_no = item.get("考场号", "")
            grouped[str(examroom_no).strip()].append(item)
        for _, students in grouped.items():
            students.sort(key=self._examroom_student_sort_key)
        return grouped

    def _class_sort_key(self, class_name):
        s = str(class_name).strip()
        if s.isdigit():
            return (0, int(s))
        return (1, s)

    def _class_student_sort_key(self, item):
        sn = str(item.get("学号", "")).strip()
        exam_no = str(item.get("考生考号", "")).strip()
        if sn.isdigit():
            return (0, int(sn), exam_no)
        return (1, sn, exam_no)

    def _examroom_sort_key(self, examroom_no):
        s = str(examroom_no).strip()
        if s.isdigit():
            return (0, int(s))
        if s:
            return (1, s)
        return (2, "")

    def _seat_sort_key(self, seat_value):
        s = str(seat_value).strip()
        if s.isdigit():
            return (0, int(s))
        return (1, s)

    def _examroom_student_sort_key(self, item):
        examroom_no = str(item.get("考场号", "")).strip()
        seat = item.get("座位号", item.get("座位", ""))
        class_value = str(item.get("班级", "")).strip()
        sn = str(item.get("学号", "")).strip()
        return (self._examroom_sort_key(examroom_no), self._seat_sort_key(seat), self._class_sort_key(class_value), self._seat_sort_key(sn))
