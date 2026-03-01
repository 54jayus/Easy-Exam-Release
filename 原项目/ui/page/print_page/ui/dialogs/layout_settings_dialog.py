import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QPushButton, QGroupBox, QFrame, QWidget, QLineEdit)
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QPainter, QPen, QColor, QFont

from ..widgets.desk_preview_widget import SeatPreviewWidget

class LayoutSettingsDialog(QDialog):
    """
    座位布局设置对话框
    """
    def __init__(self, current_layout_name=None, 
                 current_pattern="S型横排", 
                 current_custom_counts=None,
                 current_start_pos="left",
                 parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置座位布局") 
        self.setFixedSize(900, 500) 
        
        # 预定义布局
        self.layouts = {
            "5行×6列": {"rows": 5, "cols": 6},
            "6行×5列": {"rows": 6, "cols": 5},
            "6行×7列": {"rows": 6, "cols": 7},
            "7行×6列": {"rows": 7, "cols": 6},
            "5行×9列": {"rows": 5, "cols": 9},
            "9行×5列": {"rows": 9, "cols": 5},
        }
        
        # 保存自定义参数
        self.custom_counts_data = current_custom_counts
        
        # Normalize layout name
        if current_layout_name == "自定义":
             self.current_layout_name = "自定义"
        elif current_layout_name not in self.layouts:
            self.current_layout_name = "6行×5列"
        else:
            self.current_layout_name = current_layout_name
            
        self.patterns = ["S型横排", "S型竖排", "Z型横排", "Z型竖排"]
        self.current_pattern = current_pattern if current_pattern in self.patterns else "S型横排"
        self.current_start_pos = current_start_pos if current_start_pos in ["left", "right"] else "left"
        
        self.initUI()
        
    def initUI(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(30)
        
        # === 左侧：设置区域 ===
        left_layout = QVBoxLayout()
        left_layout.setSpacing(20)
        left_layout.setAlignment(Qt.AlignTop)
        
        # 1. 座位布局方式
        row1 = QHBoxLayout()
        lbl1 = QLabel("* 座位布局方式")
        lbl1.setStyleSheet("color: #606266; font-weight: bold;")
        self.comboLayout = QComboBox()
        # Filter keys to show clean names first
        keys = ["5行×6列", "6行×5列", "6行×7列", "7行×6列", "5行×9列", "9行×5列", "自定义"]
        self.comboLayout.addItems(keys)
        
        # Handle current text setting
        self.comboLayout.setCurrentText(self.current_layout_name)
        
        self.comboLayout.currentIndexChanged.connect(self.on_layout_changed)
        self.comboLayout.setMinimumHeight(35)
        row1.addWidget(lbl1)
        row1.addWidget(self.comboLayout)
        left_layout.addLayout(row1)
        
        # -> 自定义输入区域 (默认隐藏)
        self.customGroup = QGroupBox("自定义每列人数")
        custom_layout = QVBoxLayout()
        
        lbl_custom = QLabel("请输入每列人数 (用逗号分隔):")
        lbl_custom.setStyleSheet("color: #606266;")
        custom_layout.addWidget(lbl_custom)
        
        self.editCustomCounts = QLineEdit()
        self.editCustomCounts.setPlaceholderText("例如: 7,7,8,8")
        self.editCustomCounts.setMinimumHeight(35)
        self.editCustomCounts.textChanged.connect(self.update_preview)
        if self.custom_counts_data:
            self.editCustomCounts.setText(",".join(map(str, self.custom_counts_data)))
            
        custom_layout.addWidget(self.editCustomCounts)
        
        self.customGroup.setLayout(custom_layout)
        left_layout.addWidget(self.customGroup)
        
        # 2. 座位排列方式
        row2 = QHBoxLayout()
        lbl2 = QLabel("* 座位排列方式")
        lbl2.setStyleSheet("color: #606266; font-weight: bold;")
        self.comboPattern = QComboBox()
        self.comboPattern.addItems(self.patterns)
        self.comboPattern.setCurrentText(self.current_pattern)
        self.comboPattern.currentIndexChanged.connect(self.update_preview)
        self.comboPattern.setMinimumHeight(35)
        row2.addWidget(lbl2)
        row2.addWidget(self.comboPattern)
        left_layout.addLayout(row2)

        # 3. 起始位置
        row3 = QHBoxLayout()
        lbl3 = QLabel("* 座位起始位")
        lbl3.setStyleSheet("color: #606266; font-weight: bold;")
        self.comboStartPos = QComboBox()
        self.comboStartPos.addItem("左手位（面向讲台左侧）", "left")
        self.comboStartPos.addItem("右手位（面向讲台右侧）", "right")
        # 设置当前选中项
        index = self.comboStartPos.findData(self.current_start_pos)
        if index >= 0:
            self.comboStartPos.setCurrentIndex(index)
        self.comboStartPos.currentIndexChanged.connect(self.update_preview)
        self.comboStartPos.setMinimumHeight(35)
        row3.addWidget(lbl3)
        row3.addWidget(self.comboStartPos)
        left_layout.addLayout(row3)
        
        left_layout.addStretch()
        
        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btnCancel = QPushButton("关闭")
        self.btnCancel.setFixedSize(80, 32)
        self.btnCancel.clicked.connect(self.reject)
        
        self.btnOK = QPushButton("确定")
        self.btnOK.setFixedSize(80, 32)
        self.btnOK.setStyleSheet("background-color: #0078d7; color: white; border-radius: 4px;")
        self.btnOK.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btnCancel)
        btn_layout.addWidget(self.btnOK)
        left_layout.addLayout(btn_layout)
        
        # === 右侧：预览区域 ===
        # Use existing widget logic
        self.previewWidget = SeatPreviewWidget()
        self.previewWidget.setMinimumSize(400, 300)
        
        # === 组合 ===
        main_layout.addLayout(left_layout, 4)
        main_layout.addWidget(self.previewWidget, 6)
        
        self.setLayout(main_layout)
        
        # 初始化状态
        self.on_layout_changed()
        
    def on_layout_changed(self):
        """布局选择变更时触发"""
        name = self.comboLayout.currentText()
        is_custom = (name == "自定义")
        self.customGroup.setVisible(is_custom)
        self.update_preview()
        
    def update_preview(self):
        """更新预览图"""
        if not hasattr(self, 'comboLayout') or not hasattr(self, 'comboPattern') or not hasattr(self, 'editCustomCounts') or not hasattr(self, 'comboStartPos'):
            return
            
        layout_name = self.comboLayout.currentText()
        pattern = self.comboPattern.currentText()
        start_pos = self.comboStartPos.currentData()
        
        rows = 0
        cols = 0
        custom_counts = None
        
        if layout_name == "自定义":
            # 解析自定义输入
            text = self.editCustomCounts.text().strip()
            # 替换中文逗号
            text = text.replace("，", ",")
            if text:
                try:
                    parts = [int(x.strip()) for x in text.split(",") if x.strip()]
                    if parts:
                        custom_counts = parts
                        cols = len(parts)
                        rows = max(parts)
                except:
                    pass
            
            # 如果解析失败，给默认值防止崩溃
            if rows == 0 or cols == 0:
                rows = 1
                cols = 1
                
        elif layout_name in self.layouts:
            rows = self.layouts[layout_name]["rows"]
            cols = self.layouts[layout_name]["cols"]
            
        self.previewWidget.set_layout_params(rows, cols, pattern, custom_counts, start_pos)
            
    def get_layout(self):
        """返回选中的布局信息 (name, rows, cols, capacity, pattern, custom_counts, start_pos)"""
        name = self.comboLayout.currentText()
        pattern = self.comboPattern.currentText()
        start_pos = self.comboStartPos.currentData()
        
        custom_counts = None
        
        if name == "自定义":
            # 重新解析一遍以确保返回正确数据
            text = self.editCustomCounts.text().strip().replace("，", ",")
            try:
                parts = [int(x.strip()) for x in text.split(",") if x.strip()]
                if parts:
                    custom_counts = parts
                    cols = len(parts)
                    rows = max(parts)
                    capacity = sum(parts)
                else:
                    # Fallback
                    rows, cols, capacity = 6, 5, 30
            except:
                rows, cols, capacity = 6, 5, 30
        else:
            info = self.layouts[name]
            rows = info["rows"]
            cols = info["cols"]
            capacity = rows * cols
            
        return name, rows, cols, capacity, pattern, custom_counts, start_pos
