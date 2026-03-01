from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics
from PyQt5.QtWidgets import QHeaderView, QTableWidgetItem


def build_corner_table_preview(table, title, subjects):
    table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    font = table.font()
    font.setPointSize(10)
    table.setFont(font)

    rows = 4 + len(subjects)
    table.setRowCount(rows)
    table.setColumnCount(4)
    table.clearSpans()

    header = table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Fixed)

    fm = QFontMetrics(table.font())
    char_w = fm.width("0")
    padding = 15

    col_widths = [
        char_w * 12 + padding,
        char_w * 10 + padding,
        char_w * 14 + padding,
        char_w * 13 + padding,
    ]

    for i, w in enumerate(col_widths):
        table.setColumnWidth(i, w)

    frame_width = table.frameWidth()
    total_width = sum(col_widths) + (frame_width * 2)
    table.setFixedWidth(total_width)

    preview_row_height = 25
    title_row_height = 35

    total_height = 0
    table.setRowHeight(0, title_row_height)
    total_height += title_row_height

    for r in range(1, rows):
        table.setRowHeight(r, preview_row_height)
        total_height += preview_row_height

    total_height += frame_width * 2
    table.setFixedHeight(total_height)

    def set_item(r, c, text, is_bold=False, font_size=10):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)

        f = item.font()
        f.setBold(is_bold)
        f.setPointSize(font_size)
        item.setFont(f)

        table.setItem(r, c, item)

    set_item(0, 0, title, is_bold=True, font_size=14)
    table.setSpan(0, 0, 1, 4)

    set_item(1, 0, "考场", is_bold=True)
    set_item(1, 1, "高二1班")
    set_item(1, 2, "考场号", is_bold=True)
    set_item(1, 3, "001")

    set_item(2, 0, "")
    set_item(2, 1, "")
    set_item(2, 2, "座位号", is_bold=True)
    set_item(2, 3, "01")

    headers = ["科目", "考生姓名", "考生考号", "考生班级学号"]
    for c, h in enumerate(headers):
        set_item(3, c, h, is_bold=True)

    for i, subj in enumerate(subjects):
        r = 4 + i
        set_item(r, 0, subj)
        set_item(r, 1, "张三")
        set_item(r, 2, "2410010615")
        set_item(r, 3, "5班16号")


def build_ticket_table_preview(table, title, subjects, subject_times):
    table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    font = table.font()
    font.setPointSize(10)
    table.setFont(font)

    rows = 4 + len(subjects)
    table.setRowCount(rows)
    table.setColumnCount(5)
    table.clearSpans()

    header = table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Fixed)

    fm = QFontMetrics(table.font())
    char_w = fm.width("0")
    padding = 15

    col_widths = [
        char_w * 7.5 + padding,
        char_w * 17 + padding,
        char_w * 7.5 + padding,
        char_w * 6 + padding,
        char_w * 6 + padding,
    ]

    for i, w in enumerate(col_widths):
        table.setColumnWidth(i, w)

    frame_width = table.frameWidth()
    total_width = sum(col_widths) + (frame_width * 2) - 2
    table.setFixedWidth(total_width)

    row_heights = [35] + [25] * (rows - 1)
    total_height = sum(row_heights) + (frame_width * 2) - 2

    for r, h in enumerate(row_heights):
        table.setRowHeight(r, h)

    table.setFixedHeight(total_height)

    def set_item(r, c, text, is_bold=False, font_size=10):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)

        f = item.font()
        f.setBold(is_bold)
        f.setPointSize(font_size)
        item.setFont(f)
        table.setItem(r, c, item)

    set_item(0, 0, title, is_bold=True, font_size=14)
    table.setSpan(0, 0, 1, 5)

    set_item(1, 0, "考号", is_bold=True)
    set_item(1, 1, "2410010615")
    set_item(1, 2, "班级", is_bold=True)
    table.setSpan(1, 2, 1, 2)
    set_item(1, 4, "高三5班")

    set_item(2, 0, "姓名", is_bold=True)
    set_item(2, 1, "张三")
    set_item(2, 2, "学号", is_bold=True)
    table.setSpan(2, 2, 1, 2)
    set_item(2, 4, "16")

    set_item(3, 0, "科目", is_bold=True)
    set_item(3, 1, "时间", is_bold=True)
    set_item(3, 2, "考场", is_bold=True)
    set_item(3, 3, "考场号", is_bold=True)
    set_item(3, 4, "座位号", is_bold=True)

    for i in range(len(subjects)):
        r = 4 + i
        subj = subjects[i] if i < len(subjects) else ""
        subj_time = subject_times[i] if i < len(subject_times) else ""

        set_item(r, 0, subj)
        set_item(r, 1, subj_time)

        if subj:
            set_item(r, 2, "高二1班")
            set_item(r, 3, "001")
            set_item(r, 4, "01")
        else:
            set_item(r, 2, "")
            set_item(r, 3, "")
            set_item(r, 4, "")


def build_student_info_table_preview(table, title, class_name, class_rows, include_subject_fields=False, sort_mode="class"):
    table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    table.horizontalHeader().setVisible(False)
    table.verticalHeader().setVisible(False)

    font = table.font()
    font.setPointSize(10)
    table.setFont(font)

    headers = ["班级", "学号", "姓名", "考号", "考场", "考场号", "座位"] if not include_subject_fields else ["班级", "学号", "姓名", "考号", "首选", "选科1", "选科2", "考场", "考场号", "座位"]
    data_rows = list(class_rows or [])

    def parse_int(v):
        s = str(v).strip()
        if s.isdigit():
            return (0, int(s))
        return (1, s)

    if sort_mode == "examroom":
        def seat_key(row):
            examroom_no = row.get("考场号", "")
            seat = row.get("座位号", row.get("座位", ""))
            return (parse_int(examroom_no), parse_int(seat), parse_int(row.get("班级", "")), parse_int(row.get("学号", "")))
        data_rows.sort(key=seat_key)
    else:
        def sn_key(row):
            return (parse_int(row.get("班级", "")), parse_int(row.get("学号", "")), parse_int(row.get("考生考号", row.get("考号", ""))))
        data_rows.sort(key=sn_key)
    n = len(data_rows)

    first_count = 6
    last_count = 6
    omit_count = max(0, n - (first_count + last_count))
    if omit_count <= 0:
        visible = data_rows
        has_ellipsis = False
    else:
        visible = data_rows[:first_count] + [None] + data_rows[-last_count:]
        has_ellipsis = True

    rows = 2 + len(visible) + 1
    cols = len(headers)
    table.setRowCount(rows)
    table.setColumnCount(cols)
    table.clearSpans()

    header = table.horizontalHeader()
    header.setSectionResizeMode(QHeaderView.Fixed)

    fm = QFontMetrics(table.font())
    char_w = fm.width("0")
    padding = 18

    if include_subject_fields:
        col_widths = [
            char_w * 5 + padding,
            char_w * 5 + padding,
            char_w * 7 + padding,
            char_w * 12 + padding,
            char_w * 5 + padding,
            char_w * 5 + padding,
            char_w * 5 + padding,
            char_w * 9 + padding,
            char_w * 6 + padding,
            char_w * 5 + padding,
        ]
    else:
        col_widths = [
            char_w * 5 + padding,
            char_w * 5 + padding,
            char_w * 7 + padding,
            char_w * 12 + padding,
            char_w * 9 + padding,
            char_w * 6 + padding,
            char_w * 5 + padding,
        ]

    for i, w in enumerate(col_widths):
        table.setColumnWidth(i, w)

    frame_width = table.frameWidth()
    total_width = sum(col_widths) + (frame_width * 2) - 2
    table.setFixedWidth(total_width)

    body_row_height = 25
    ellipsis_row_height = 32
    row_heights = [35, 28] + [body_row_height] * len(visible) + [body_row_height]
    for r, h in enumerate(row_heights):
        table.setRowHeight(r, h)

    def set_item(r, c, text, is_bold=False, font_size=10):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignCenter)
        item.setFlags(item.flags() ^ Qt.ItemIsEditable)
        f = item.font()
        f.setBold(is_bold)
        f.setPointSize(font_size)
        item.setFont(f)
        table.setItem(r, c, item)

    set_item(0, 0, title or "", is_bold=True, font_size=14)
    table.setSpan(0, 0, 1, cols)

    for c, h in enumerate(headers):
        set_item(1, c, h, is_bold=True)

    start_row = 2
    for i, row in enumerate(visible):
        r = start_row + i
        if row is None:
            item = QTableWidgetItem(f"…… 中间省略 {omit_count} 行（共 {n} 人，仅预览前{first_count}行+后{last_count}行） ……")
            item.setTextAlignment(Qt.AlignCenter)
            item.setFlags(item.flags() ^ Qt.ItemIsEditable)
            f = item.font()
            f.setPointSize(10)
            f.setItalic(True)
            item.setFont(f)
            table.setItem(r, 0, item)
            table.setSpan(r, 0, 1, cols)
            table.setRowHeight(r, ellipsis_row_height)
            continue
        if include_subject_fields:
            values = [
                row.get("班级", ""),
                row.get("学号", ""),
                row.get("考生姓名", row.get("姓名", "")),
                row.get("考生考号", row.get("考号", "")),
                row.get("首选", row.get("类别", "")),
                row.get("选科1", row.get("选1", "")),
                row.get("选科2", row.get("选2", "")),
                row.get("考场", ""),
                row.get("考场号", ""),
                row.get("座位号", row.get("座位", "")),
            ]
        else:
            values = [
                row.get("班级", ""),
                row.get("学号", ""),
                row.get("考生姓名", row.get("姓名", "")),
                row.get("考生考号", row.get("考号", "")),
                row.get("考场", ""),
                row.get("考场号", ""),
                row.get("座位号", row.get("座位", "")),
            ]
        for c, v in enumerate(values):
            set_item(r, c, v)

    summary_row = rows - 1
    if sort_mode == "examroom":
        label_col = 7 if include_subject_fields else 4
    else:
        label_col = 0
    set_item(summary_row, label_col, f"{class_name} 计数", is_bold=True)
    set_item(summary_row, 2, n, is_bold=True)
    for c in range(cols):
        if table.item(summary_row, c) is None:
            set_item(summary_row, c, "")
    table.setRowHeight(summary_row, body_row_height)

    sum_rows_height = sum(table.rowHeight(r) for r in range(table.rowCount()))
    extra_height = (frame_width * 2) - 2
    if table.horizontalHeader().isVisible():
        extra_height += table.horizontalHeader().height()
    table.setFixedHeight(sum_rows_height + extra_height)
