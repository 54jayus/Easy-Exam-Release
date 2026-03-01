from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QLabel, QPushButton, QFormLayout, QMessageBox)
from PyQt5.QtCore import Qt

class ColumnMappingDialog(QDialog):
    """
    列映射对话框
    用户选择 Excel 列与 目标字段 的对应关系
    """
    REQUIRED_FIELDS = [
        '考场', '考场号', '座位号', 
        '考生姓名', '考生考号', 
        '班级', '学号'
    ]

    def __init__(self, excel_headers, parent=None):
        super().__init__(parent)
        self.excel_headers = excel_headers
        self.mapping = {}
        self.initUI()
        self.auto_match()

    def initUI(self):
        self.setWindowTitle("导入数据列映射")
        self.resize(400, 350)
        
        layout = QVBoxLayout()

        # 说明
        layout.addWidget(QLabel("请为以下字段选择对应的Excel列："))

        # 表单布局
        form_layout = QFormLayout()
        self.combos = {}

        for field in self.REQUIRED_FIELDS:
            combo = QComboBox()
            combo.addItem("-- 请选择 --", None)
            for header in self.excel_headers:
                combo.addItem(str(header), header)
            
            self.combos[field] = combo
            form_layout.addRow(f"{field} *:", combo)

        layout.addLayout(form_layout)

        # 按钮
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("确定导入")
        btn_ok.clicked.connect(self.validate_and_accept)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_ok)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def auto_match(self):
        """
        自动匹配逻辑
        """
        # 预定义同义词映射表
        synonyms = {
            '考生考号': ['考号', '考生号', '考生考号', '准考证号'],
            '考生姓名': ['姓名', '考生姓名', '学生姓名'],
            '考场': ['考场', '考室'],
            '考场号': ['考场号', '考室号'],
            '座位号': ['座位号', '座号'],
            '班级': ['班级', '班'],
            '学号': ['学号']
        }

        for field, combo in self.combos.items():
            # 1. 尝试完全匹配
            if field in self.excel_headers:
                index = combo.findText(field)
                if index >= 0:
                    combo.setCurrentIndex(index)
                    continue
            
            # 2. 尝试同义词匹配
            potential_matches = synonyms.get(field, [])
            for match in potential_matches:
                if match in self.excel_headers:
                    index = combo.findText(match)
                    if index >= 0:
                        combo.setCurrentIndex(index)
                        break

    def validate_and_accept(self):
        """验证所有必填项都已选择"""
        self.mapping = {}
        missing_fields = []

        for field, combo in self.combos.items():
            selected_header = combo.currentData()
            if not selected_header:
                missing_fields.append(field)
            else:
                self.mapping[field] = selected_header
        
        if missing_fields:
            QMessageBox.warning(self, "映射不完整", f"请为以下字段选择对应的列：\n{', '.join(missing_fields)}")
            return

        self.accept()

    def get_mapping(self):
        return self.mapping
