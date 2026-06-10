from __future__ import annotations

from collections import OrderedDict

import openpyxl
from openpyxl.styles import Alignment, Border, Font, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.pagebreak import Break

from backend.printing.core.seat_layout import get_seat_mapping, mirror_layout_start_pos, normalize_layout


class RollCallGenerator:
    def __init__(self, config):
        self.config = config
        thin = Side(style="thin", color="666666")
        self.border = Border(left=thin, right=thin, top=thin, bottom=thin)

    @staticmethod
    def _sheet_name(name: str, used: set[str]) -> str:
        base = str(name or "科目").translate(str.maketrans({c: "" for c in ':\\/?*[]'}))[:28] or "科目"
        candidate = base
        index = 2
        while candidate in used:
            candidate = f"{base[:25]}-{index}"
            index += 1
        used.add(candidate)
        return candidate

    def generate(self, progress_callback=None):
        groups = self.config.groups or []
        if not groups:
            raise ValueError("没有可生成的点名表数据")

        by_subject = OrderedDict()
        for group in groups:
            by_subject.setdefault(group.get("subject") or "科目", []).append(group)

        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        used = set()
        total = len(groups)
        done = 0
        for subject, subject_groups in by_subject.items():
            ws = wb.create_sheet(self._sheet_name(subject, used))
            max_cols = max(normalize_layout(group.get("seatLayout"))["layoutCols"] for group in subject_groups)
            max_end_row = 1
            current_row = 1
            for index, group in enumerate(subject_groups):
                end_row = self._draw_page(ws, current_row, group, max_cols)
                max_end_row = max(max_end_row, end_row)
                done += 1
                if progress_callback:
                    progress_callback(done, total)
                if index < len(subject_groups) - 1:
                    ws.row_breaks.append(Break(id=end_row))
                current_row = end_row + 1

            landscape = self._is_landscape(max_cols)
            ws.page_setup.orientation = "landscape" if landscape else "portrait"
            ws.page_setup.paperSize = ws.PAPERSIZE_A4
            ws.page_setup.fitToWidth = 1
            ws.page_setup.fitToHeight = 1
            ws.sheet_properties.pageSetUpPr.fitToPage = True
            ws.page_margins.left = 0.2
            ws.page_margins.right = 0.2
            ws.page_margins.top = 0.25
            ws.page_margins.bottom = 0.25
            ws.print_area = f"A1:{get_column_letter(max_cols)}{max_end_row}"

        wb.save(self.config.output_path)
        return self.config.output_path

    def _is_landscape(self, max_cols: int) -> bool:
        mode = str(getattr(self.config, "orientation", "auto") or "auto")
        if mode == "landscape":
            return True
        if mode == "portrait":
            return False
        return max_cols >= 8

    def _draw_page(self, ws, start_row: int, group: dict, sheet_cols: int) -> int:
        layout = normalize_layout(mirror_layout_start_pos(group.get("seatLayout"), self.config.mirror_view))
        rows = layout["layoutRows"]
        cols = layout["layoutCols"]
        mapping = get_seat_mapping(layout)
        subject = str(group.get("subject") or "")
        room_name = str(group.get("roomName") or "")
        room_no = str(group.get("roomNo") or "")
        students = group.get("students") or []
        by_seat = {int(item["seatNo"]): item for item in students}
        font_size = max(7, min(11, 12 - max(0, cols - 6) - max(0, rows - 7) // 2))

        title_row = start_row
        ws.merge_cells(start_row=title_row, start_column=1, end_row=title_row, end_column=sheet_cols)
        ws.cell(title_row, 1, self.config.exam_name).font = Font(name="宋体", size=16, bold=True)
        ws.cell(title_row, 1).alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[title_row].height = 28

        info_row = title_row + 1
        ws.merge_cells(start_row=info_row, start_column=1, end_row=info_row, end_column=sheet_cols)
        ws.cell(info_row, 1, f"学校：{self.config.school_name}    科目：{subject}    考场：{room_name}    考场号：{room_no}    人数：{len(students)}")
        ws.cell(info_row, 1).font = Font(name="宋体", size=10)
        ws.cell(info_row, 1).alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[info_row].height = 22

        sign_row = info_row + 1
        ws.merge_cells(start_row=sign_row, start_column=1, end_row=sign_row, end_column=sheet_cols)
        sign_text = "主监考（签名）：________________    副监考（签名）：________________" if self.config.template_mode == "full" else ""
        ws.cell(sign_row, 1, sign_text)
        ws.cell(sign_row, 1).alignment = Alignment(horizontal="right", vertical="center")
        ws.cell(sign_row, 1).font = Font(name="宋体", size=10)
        ws.row_dimensions[sign_row].height = 22 if sign_text else 8

        grid_start = sign_row + 1
        row_height = max(38, min(62, 360 / max(1, rows)))
        col_width = max(11, min(22, 95 / max(1, cols)))
        valid_positions = set(mapping.values())
        pos_to_seat = {position: seat for seat, position in mapping.items()}
        for col in range(1, sheet_cols + 1):
            ws.column_dimensions[get_column_letter(col)].width = col_width

        for row in range(rows):
            ws.row_dimensions[grid_start + row].height = row_height
            for col in range(sheet_cols):
                cell = ws.cell(grid_start + row, col + 1)
                if col >= cols or (row, col) not in valid_positions:
                    continue
                seat = pos_to_seat[(row, col)]
                student = by_seat.get(seat)
                if student:
                    lines = [f"{seat}. {student.get('name', '')}"]
                    if self.config.show_exam_no:
                        lines.append(str(student.get("examNo") or ""))
                    if self.config.show_class and student.get("className"):
                        lines.append(str(student.get("className")))
                    if self.config.show_checkbox:
                        lines.append("□ 缺考")
                    cell.value = "\n".join(lines)
                else:
                    cell.value = f"{seat}.\n" + ("□ 缺考" if self.config.show_checkbox else "")
                cell.font = Font(name="宋体", size=font_size)
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = self.border

        footer_row = grid_start + rows
        if self.config.template_mode == "full":
            ws.merge_cells(start_row=footer_row, start_column=1, end_row=footer_row + 2, end_column=max(1, sheet_cols * 2 // 3))
            note = ws.cell(footer_row, 1, self.config.notes_title)
            note.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            note.font = Font(name="宋体", size=9)
            note.border = self.border
            instruction_start = max(2, sheet_cols * 2 // 3 + 1)
            ws.merge_cells(start_row=footer_row, start_column=instruction_start, end_row=footer_row + 2, end_column=sheet_cols)
            instruction = ws.cell(footer_row, instruction_start, self.config.instructions)
            instruction.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
            instruction.font = Font(name="宋体", size=8)
            instruction.border = self.border
            for row in range(footer_row, footer_row + 3):
                ws.row_dimensions[row].height = 28
            return footer_row + 2
        return footer_row
