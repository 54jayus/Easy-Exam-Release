from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QRect

class SeatPreviewWidget(QWidget):
    """
    动态绘制座位布局预览的组件
    绘制内容：
    1. 顶部讲台
    2. 下方座位网格
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = 6
        self.cols = 7
        self.pattern = "S型横排"
        self.start_pos = "left" # "left" or "right"
        self.custom_counts = None # 自定义每列人数
        self.seat_data = {} # seat_num -> display_text
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        
    def set_layout_params(self, rows, cols, pattern, custom_counts=None, start_pos="left"):
        """设置布局参数并重绘"""
        self.rows = rows
        self.cols = cols
        self.pattern = pattern
        self.custom_counts = custom_counts
        self.start_pos = start_pos
        self.seat_data = {} # 重置数据
        self.update() # 触发 paintEvent

    def set_seat_data(self, data_map):
        """设置每个座位的显示数据"""
        self.seat_data = data_map
        self.update()

    def get_seat_grid(self):
        """
        根据布局参数计算每个位置的座位号
        返回: 2D array [row][col] -> seat_number (int)
        """
        grid = [[0] * self.cols for _ in range(self.rows)]
        
        current_seat = 1
        
        # 辅助函数：判断该位置是否有效
        def is_valid_pos(r, c):
            if self.custom_counts:
                # 检查 c 是否越界 (虽然 cols 应该是 len(custom_counts))
                if c < len(self.custom_counts):
                    # 只有当 r < 该列人数时才有效
                    return r < self.custom_counts[c]
            return True

        # 如果 start_pos == "right", 我们可以在逻辑上翻转列
        # 为了复用逻辑，我们可以定义一个映射：logic_col -> actual_col
        # Start Left: actual_col = logic_col
        # Start Right: actual_col = (cols - 1) - logic_col
        
        def get_actual_col(logic_col):
            if self.start_pos == "left":
                return self.cols - 1 - logic_col
            return logic_col

        if self.pattern == "Z型横排":
            # Z-Horizontal: Always Left->Right (in logic)
            for r in range(self.rows):
                for c in range(self.cols):
                    actual_c = get_actual_col(c)
                    if is_valid_pos(r, actual_c):
                        grid[r][actual_c] = current_seat
                        current_seat += 1
                        
        elif self.pattern == "S型横排":
            # Snake Horizontal
            # Row 0 (Even): L->R
            # Row 1 (Odd): R->L
            
            for r in range(self.rows):
                is_even_row = (r % 2 == 0)
                
                if is_even_row:
                    # L -> R
                    for c in range(self.cols):
                        actual_c = get_actual_col(c)
                        if is_valid_pos(r, actual_c):
                            grid[r][actual_c] = current_seat
                            current_seat += 1
                else:
                    # R -> L
                    for c in range(self.cols - 1, -1, -1):
                        actual_c = get_actual_col(c)
                        if is_valid_pos(r, actual_c):
                            grid[r][actual_c] = current_seat
                            current_seat += 1
                        
        elif self.pattern == "Z型竖排":
            # Z-Vertical: Column by Column
            
            for c in range(self.cols):
                for r in range(self.rows):
                    actual_c = get_actual_col(c)
                    if is_valid_pos(r, actual_c):
                        grid[r][actual_c] = current_seat
                        current_seat += 1
                        
        elif self.pattern == "S型竖排":
            # Snake Vertical
            # Col 0 Down, Col 1 Up...
            
            for c in range(self.cols):
                is_even_col = (c % 2 == 0)
                actual_c = get_actual_col(c)
                
                if is_even_col: # Down
                    for r in range(self.rows):
                        if is_valid_pos(r, actual_c):
                            grid[r][actual_c] = current_seat
                            current_seat += 1
                else: # Up
                    for r in range(self.rows - 1, -1, -1):
                        if is_valid_pos(r, actual_c):
                            grid[r][actual_c] = current_seat
                            current_seat += 1
                            
        return grid

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 绘制参数
        w = self.width()
        h = self.height()
        margin = 10
        
        # 1. 绘制讲台 (顶部区域)
        podium_height = 40
        podium_rect = QRect(margin + 20, margin, w - 2 * (margin + 20), podium_height)
        
        painter.setPen(QPen(QColor("#dcdfe6"), 1))
        painter.setBrush(QColor("#f2f6fc")) # 浅色背景
        painter.drawRect(podium_rect)
        
        painter.setPen(QPen(QColor("#606266")))
        painter.drawText(podium_rect, Qt.AlignCenter, "讲台")
        
        # 2. 绘制座位区
        # 计算可用区域
        grid_top = margin + podium_height + 20
        grid_h = h - grid_top - margin
        grid_w = w - 2 * margin
        
        if grid_h <= 0 or grid_w <= 0:
            return

        # 计算单元格大小
        cell_gap = 5
        
        # 安全检查: 防止除零
        cols_count = max(1, self.cols)
        rows_count = max(1, self.rows)
        
        cell_w = (grid_w - (cols_count - 1) * cell_gap) / cols_count
        cell_h = (grid_h - (rows_count - 1) * cell_gap) / rows_count
        
        if cell_h > 50: 
            cell_h = 50
            
        painter.setFont(QFont("Arial", 9))
        
        # 获取座位号 Grid
        seat_grid = self.get_seat_grid()
        
        for r in range(self.rows):
            for c in range(self.cols):
                seat_num = seat_grid[r][c]
                if seat_num == 0:
                    continue # 0 表示空位，不绘制
                    
                x = margin + c * (cell_w + cell_gap)
                y = grid_top + r * (cell_h + cell_gap)
                
                rect = QRect(int(x), int(y), int(cell_w), int(cell_h))
                
                # 绘制格子边框（加粗）
                painter.setPen(QPen(QColor("#dcdfe6"), 2)) # 边框线宽改为2
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(rect)
                
                # 绘制内容 (优先显示数据，否则显示座位号)
                painter.setPen(QPen(QColor("#606266")))
                
                text_to_draw = str(seat_num)
                if self.seat_data and seat_num in self.seat_data:
                    text_to_draw = self.seat_data[seat_num]
                    # 如果有数据，可能需要更小的字体或多行显示
                    painter.setFont(QFont("Arial", 8)) # 稍微调小
                else:
                    painter.setFont(QFont("Arial", 9))
                    
                painter.drawText(rect, Qt.AlignCenter, text_to_draw)

class DeskLabelPreviewWidget(QWidget):
    """
    桌角纸内容预览组件
    展示第一个考场的实际打印效果
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rows = 7
        self.cols = 6
        self.start_pos = "left"
        self.data_list = [] # List of dicts for one room
        self.setStyleSheet("background-color: white; border: 1px solid #ccc;")
        # 宋体 9pt
        self.font_style = QFont("SimSun", 9)

    def set_data(self, rows, cols, start_pos, data_list):
        self.rows = max(1, rows)
        self.cols = max(1, cols)
        self.start_pos = start_pos
        self.data_list = data_list
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        # 去掉抗锯齿以获得更清晰的线条（类似Excel）
        # painter.setRenderHint(QPainter.Antialiasing)
        
        w = self.width()
        h = self.height()
        margin = 10
        
        # 可用区域
        grid_w = w - 2 * margin
        grid_h = h - 2 * margin
        
        if grid_w <= 0 or grid_h <= 0:
            return
            
        # 计算单元格大小
        cell_w = grid_w / self.cols
        cell_h = grid_h / self.rows
        
        # 动态计算字体大小
        # 预留上下 padding 各 2px
        available_h = cell_h - 4 
        # 假设有 5 行文字，每行需要的空间比例约为 1/6
        pixel_size = int(available_h / 6.5)
        # 限制范围，最小6px，最大12px
        pixel_size = max(6, min(pixel_size, 12))
        
        font = QFont("SimSun")
        font.setPixelSize(pixel_size)
        painter.setFont(font)
        
        pen = QPen(QColor("#000000"), 1)
        painter.setPen(pen)
        
        # 1. 绘制统一网格线 (解决边框重叠变粗问题)
        # 外边框
        painter.drawRect(QRect(margin, margin, int(grid_w), int(grid_h)))
        
        # 内部竖线
        for c in range(1, self.cols):
            x = margin + c * cell_w
            painter.drawLine(int(x), margin, int(x), margin + int(grid_h))
            
        # 内部横线
        for r in range(1, self.rows):
            y = margin + r * cell_h
            painter.drawLine(margin, int(y), margin + int(grid_w), int(y))
        
        # 2. 绘制文字内容
        capacity = self.rows * self.cols
        display_data = self.data_list if self.data_list else []
        
        for idx in range(capacity):
            # 逻辑位置
            r = idx % self.rows
            c = idx // self.rows
            
            # 视觉位置 (Visual Column)
            visual_r = r
            # 强制左手位显示，忽略 start_pos，始终从左上角开始（对应生成逻辑）
            visual_c = c
            
            # 获取数据
            if idx < len(display_data):
                item = display_data[idx]
                name = str(item.get('考生姓名', ''))
                no = str(item.get('考生考号', ''))
                room = str(item.get('考场', ''))
                room_no = str(item.get('考场号', ''))
                seat = str(item.get('座位号', ''))
            else:
                # 占位符
                name = ""
                no = ""
                room = ""
                room_no = ""
                seat = ""
            
            content = (
                f"姓名：{name}\n"
                f"考号：{no}\n"
                f"考场：{room}\n"
                f"考场号：{room_no}\n"
                f"座位号：{seat}"
            )
            
            # 计算绘制区域
            x = margin + visual_c * cell_w
            y = margin + visual_r * cell_h
            rect = QRect(int(x), int(y), int(cell_w), int(cell_h))
            
            # 画文本 (不画 Rect，只画 Text)
            # 留一点内边距 (2px)
            text_rect = rect.adjusted(2, 2, -2, -2)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter | Qt.TextWordWrap, content)
