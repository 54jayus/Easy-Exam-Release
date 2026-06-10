from __future__ import annotations

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

from backend.printing.core.generators.pdf.pdf_utils import register_fonts
from backend.printing.core.seat_layout import get_seat_mapping, mirror_layout_start_pos, normalize_layout


class RollCallPDFGenerator:
    def __init__(self, config):
        self.config = config
        register_fonts()
        registered = set(pdfmetrics.getRegisteredFontNames())
        self.font = "SimSun" if "SimSun" in registered else "STSong-Light"

    def generate(self, progress_callback=None):
        groups = self.config.groups or []
        if not groups:
            raise ValueError("没有可生成的点名表数据")
        pdf = canvas.Canvas(self.config.output_path)
        for index, group in enumerate(groups):
            self._draw_page(pdf, group)
            if progress_callback:
                progress_callback(index + 1, len(groups))
            if index < len(groups) - 1:
                pdf.showPage()
        pdf.save()
        return self.config.output_path

    def _page_size(self, layout: dict):
        mode = self.config.orientation
        if mode == "landscape" or (mode == "auto" and layout["layoutCols"] >= 8):
            return landscape(A4)
        return A4

    def _draw_page(self, pdf, group: dict):
        layout = normalize_layout(mirror_layout_start_pos(group.get("seatLayout"), self.config.mirror_view))
        page_width, page_height = self._page_size(layout)
        pdf.setPageSize((page_width, page_height))
        margin = 12 * mm
        width = page_width - margin * 2
        top = page_height - margin
        subject = str(group.get("subject") or "")
        room_name = str(group.get("roomName") or "")
        room_no = str(group.get("roomNo") or "")
        students = group.get("students") or []
        by_seat = {int(item["seatNo"]): item for item in students}

        pdf.setFont(self.font, 16)
        pdf.drawCentredString(page_width / 2, top - 6 * mm, self.config.exam_name)
        pdf.setFont(self.font, 9)
        info = f"学校：{self.config.school_name}  科目：{subject}  考场：{room_name}  考场号：{room_no}  人数：{len(students)}"
        pdf.drawCentredString(page_width / 2, top - 14 * mm, info)
        header_bottom = top - 21 * mm
        if self.config.template_mode == "full":
            pdf.drawRightString(page_width - margin, header_bottom, "主监考（签名）：____________  副监考（签名）：____________")
            header_bottom -= 6 * mm

        footer_height = 38 * mm if self.config.template_mode == "full" else 4 * mm
        grid_bottom = margin + footer_height
        grid_top = header_bottom
        rows = layout["layoutRows"]
        cols = layout["layoutCols"]
        cell_width = width / cols
        cell_height = (grid_top - grid_bottom) / rows
        if cell_width < 20 * mm or cell_height < 14 * mm:
            raise ValueError(f"{subject}-{room_no or room_name}：当前布局过密，请减少行列数或调整纸张方向")

        mapping = get_seat_mapping(layout)
        pos_to_seat = {position: seat for seat, position in mapping.items()}
        font_size = max(7, min(10, int(min(cell_width / 9, cell_height / 5))))
        for (row, col), seat in pos_to_seat.items():
            x = margin + col * cell_width
            y = grid_top - (row + 1) * cell_height
            pdf.rect(x, y, cell_width, cell_height)
            student = by_seat.get(seat)
            name = str((student or {}).get("name") or "")
            exam_no = str((student or {}).get("examNo") or "")
            class_name = str((student or {}).get("className") or "")
            lines = [f"{seat}. {name}"]
            if self.config.show_exam_no:
                lines.append(exam_no)
            if self.config.show_class and class_name:
                lines.append(class_name)
            if self.config.show_checkbox:
                lines.append("□ 缺考")
            pdf.setFont(self.font, font_size)
            line_y = y + cell_height - 5 * mm
            for line in lines:
                pdf.drawCentredString(x + cell_width / 2, line_y, line)
                line_y -= (font_size + 2)

        if self.config.template_mode == "full":
            footer_top = grid_bottom - 5 * mm
            note_width = width * 0.62
            box_height = footer_height - 8 * mm
            pdf.rect(margin, margin, note_width, box_height)
            pdf.setFont(self.font, 9)
            pdf.drawString(margin + 2 * mm, footer_top, self.config.notes_title)
            instruction_x = margin + note_width + 4 * mm
            pdf.setFont(self.font, 8)
            line_y = footer_top
            for raw_line in str(self.config.instructions or "").splitlines():
                pdf.drawString(instruction_x, line_y, raw_line)
                line_y -= 4 * mm
