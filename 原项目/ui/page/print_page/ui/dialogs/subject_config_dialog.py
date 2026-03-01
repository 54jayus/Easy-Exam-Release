from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QSpinBox, QLineEdit, QPushButton, QListWidget, 
                             QListWidgetItem, QMessageBox, QWidget, QScrollArea)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon

class SubjectConfigDialog(QDialog):
    def __init__(self, subjects=None, times=None, parent=None, subject_source=None):
        super().__init__(parent)
        self.subject_source = subject_source
        # Default to 8 empty subjects if None provided
        self.subjects = subjects if subjects is not None else [''] * 8
        self.times = times if times is not None else [''] * len(self.subjects)
        
        # Ensure times list length matches subjects
        if len(self.times) < len(self.subjects):
            self.times.extend([''] * (len(self.subjects) - len(self.times)))
            
        self.initUI()

    def initUI(self):
        self.setWindowTitle("科目与时间设置")
        self.resize(550, 600)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 0. Sync Button
        btn_sync = QPushButton(" 从科目设置中获取数据")
        # Try to load icon from relative path, assuming CWD is project root
        btn_sync.setIcon(QIcon("ui/pic/subject.svg"))
        btn_sync.setMinimumHeight(35)
        btn_sync.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
                text-align: left;
                padding-left: 15px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #999;
            }
        """)
        btn_sync.clicked.connect(self.sync_from_settings)
        layout.addWidget(btn_sync)
        
        # 1. Quantity setting
        h_layout = QHBoxLayout()
        lbl_count = QLabel("科目数量:")
        lbl_count.setStyleSheet("font-weight: bold; font-size: 14px;")
        h_layout.addWidget(lbl_count)
        
        self.spinCount = QSpinBox()
        self.spinCount.setRange(1, 20) # Limit to reasonable number
        self.spinCount.setValue(len(self.subjects))
        self.spinCount.setFixedWidth(80)
        self.spinCount.setStyleSheet("font-size: 14px; padding: 2px;")
        self.spinCount.valueChanged.connect(self.update_subject_inputs)
        h_layout.addWidget(self.spinCount)
        h_layout.addStretch()
        
        layout.addLayout(h_layout)
        
        # 2. Header Row
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 10, 20, 0) # Right margin for scrollbar
        
        lbl_idx = QLabel("序号")
        lbl_idx.setFixedWidth(40)
        lbl_idx.setAlignment(Qt.AlignCenter)
        lbl_idx.setStyleSheet("font-weight: bold; color: #555;")
        
        lbl_name = QLabel("科目名称")
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_name.setStyleSheet("font-weight: bold; color: #555;")
        
        lbl_time = QLabel("考试时间")
        lbl_time.setAlignment(Qt.AlignCenter)
        lbl_time.setStyleSheet("font-weight: bold; color: #555;")
        
        header_layout.addWidget(lbl_idx)
        header_layout.addWidget(lbl_name, 1) # Ratio 1
        header_layout.addWidget(lbl_time, 2) # Ratio 2 (Time usually longer)
        
        layout.addLayout(header_layout)
        
        # 3. Subject names input area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QScrollArea.NoFrame)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setSpacing(10)
        self.scroll_layout.setContentsMargins(0, 5, 0, 5)
        
        self.subject_inputs = []
        self.time_inputs = []
        
        self.update_subject_inputs(len(self.subjects))
        
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
        # 4. Buttons
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("保存设置")
        btn_save.setMinimumHeight(35)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border-radius: 4px;
                font-size: 14px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #0063b1;
            }
        """)
        btn_save.clicked.connect(self.save_subjects)
        
        btn_cancel = QPushButton("取消")
        btn_cancel.setMinimumHeight(35)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-size: 14px;
                padding: 0 20px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_save)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def update_subject_inputs(self, count):
        # Save current values
        current_subjects = []
        current_times = []
        
        for i in range(len(self.subject_inputs)):
            current_subjects.append(self.subject_inputs[i].text())
            current_times.append(self.time_inputs[i].text())
            
        # Clear layout
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.subject_inputs = []
        self.time_inputs = []
        
        for i in range(count):
            h_box = QHBoxLayout()
            
            # Index
            lbl = QLabel(f"{i+1}")
            lbl.setFixedWidth(40)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #666;")
            h_box.addWidget(lbl)
            
            # Subject Name
            line_edit_name = QLineEdit()
            line_edit_name.setPlaceholderText("例如：语文")
            line_edit_name.setMinimumHeight(30)
            
            # Subject Time
            line_edit_time = QLineEdit()
            line_edit_time.setPlaceholderText("例如：9:00-11:30")
            line_edit_time.setMinimumHeight(30)
            
            # Restore value logic
            if i < len(current_subjects):
                line_edit_name.setText(current_subjects[i])
                line_edit_time.setText(current_times[i])
            elif i < len(self.subjects):
                line_edit_name.setText(self.subjects[i])
                # Restore time if within range, else empty
                if i < len(self.times):
                    line_edit_time.setText(self.times[i])
            
            self.subject_inputs.append(line_edit_name)
            self.time_inputs.append(line_edit_time)
            
            h_box.addWidget(line_edit_name, 1)
            h_box.addWidget(line_edit_time, 2)
            
            self.scroll_layout.addLayout(h_box)
            
        self.scroll_layout.addStretch()

    def save_subjects(self):
        new_subjects = []
        new_times = []
        
        for i in range(len(self.subject_inputs)):
            new_subjects.append(self.subject_inputs[i].text().strip())
            new_times.append(self.time_inputs[i].text().strip())
        
        self.subjects = new_subjects
        self.times = new_times
        self.accept()

    def get_subjects(self):
        return self.subjects

    def get_times(self):
        return self.times

    def sync_from_settings(self):
        """从全局科目设置中同步数据"""
        if not self.subject_source:
             QMessageBox.warning(self, "提示", "无法获取科目设置数据源，请检查程序初始化状态。")
             return
             
        # 获取源数据
        source_subjects = self.subject_source.subjects
        count = len(source_subjects)
        
        if count == 0:
            QMessageBox.information(self, "提示", "科目设置中没有数据。")
            return
            
        # 1. 更新数量 (这会触发 update_subject_inputs 重建UI)
        self.spinCount.setValue(count)
        
        # 2. 填充数据
        # 由于 setValue 触发的 update_subject_inputs 是同步的，
        # UI 控件现在已经是新的数量了，我们可以直接设置文本。
        
        for i, src_sub in enumerate(source_subjects):
            if i < len(self.subject_inputs):
                name = src_sub.get('name', '')
                date_str = src_sub.get('date', '') # yyyy-MM-dd
                time_str = src_sub.get('time', '') # HH:mm-HH:mm
                
                # 格式化日期: 2025-09-01 -> 9月1日
                formatted_date = ""
                if date_str:
                    try:
                        qd = QDate.fromString(date_str, 'yyyy-MM-dd')
                        if qd.isValid():
                            formatted_date = f"{qd.month()}月{qd.day()}日"
                        else:
                            # 尝试其他格式
                            formatted_date = date_str
                    except:
                        formatted_date = date_str
                
                # 组合时间: x月x日hh:mm-hh:mm
                final_time_str = ""
                
                # 如果 formatted_date 已经是中文日期，直接拼接
                # 如果 time_str 存在
                
                if formatted_date and time_str:
                    final_time_str = f"{formatted_date}{time_str}"
                elif formatted_date:
                    final_time_str = formatted_date
                else:
                    final_time_str = time_str
                    
                self.subject_inputs[i].setText(name)
                self.time_inputs[i].setText(final_time_str)
        
        QMessageBox.information(self, "成功", f"已同步 {count} 个科目数据。")
