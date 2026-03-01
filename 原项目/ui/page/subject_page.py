#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
考试科目设置功能页面
"""

import os
import pandas as pd
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
                             QDateTimeEdit, QPushButton, QTableWidget, QSpinBox,
                             QTableWidgetItem, QGroupBox, QTextEdit, QFileDialog, QMessageBox,
                             QSizePolicy)
from PyQt5.QtCore import Qt, QDate, QTime
from PyQt5.QtGui import QFont

class SubjectPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.subjects = []  # 存储科目信息
        # 初始化默认的一行数据
        self.subjects.append({
            'name': '语文',
            'date': '2025-09-01',
            'time': '09:30-11:30',
            'remark': ''
        })
        self.current_subject_index = 0
        self.init_ui()
    
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 0)  # 设置底部边距为0
        # 创建顶部工具栏
        self.create_toolbar(main_layout)
        
        # 创建参数设置区域
        self.create_parameter_settings(main_layout)
        
        # 创建科目信息输入区域
        self.create_subject_input_area(main_layout)
        
        # 创建结果显示区域
        self.create_result_area(main_layout)
        
    def create_toolbar(self, parent_layout):
        """
        创建工具栏
        """
        toolbar_layout = QHBoxLayout()
        
        # 导入按钮
        self.import_btn = QPushButton('导入科目信息')
        self.import_btn.clicked.connect(self.import_subjects)
        toolbar_layout.addWidget(self.import_btn)
        
        # 生成模板文件按钮
        self.generate_template_btn = QPushButton('生成模板文件')
        self.generate_template_btn.clicked.connect(self.generate_template)
        toolbar_layout.addWidget(self.generate_template_btn)
        
        # 添加导出科目信息按钮
        self.export_btn = QPushButton('导出科目信息')
        self.export_btn.clicked.connect(self.export_subjects)
        toolbar_layout.addWidget(self.export_btn)

        toolbar_layout.addStretch()
        parent_layout.addLayout(toolbar_layout)
    
    def create_parameter_settings(self, parent_layout):
        """
        创建参数设置区域
        """
        param_group = QGroupBox('参数设置')
        param_layout = QHBoxLayout()
        
        # 科目数设置
        subject_count_layout = QHBoxLayout()
        subject_count_layout.addWidget(QLabel('考试科目数:'))
        self.subject_count_spin = QSpinBox()
        self.subject_count_spin.setRange(1, 50)
        self.subject_count_spin.setValue(1)
        self.subject_count_spin.setFixedWidth(50) # 设置宽度为50像素
        self.subject_count_spin.valueChanged.connect(self.on_subject_count_changed)
        subject_count_layout.addWidget(self.subject_count_spin)
        param_layout.addLayout(subject_count_layout)
        
        param_layout.addStretch()
        param_group.setLayout(param_layout)
        parent_layout.addWidget(param_group)
    
    def create_subject_input_area(self, parent_layout):
        """
        创建科目信息输入区域
        """
        input_group = QGroupBox('科目信息设置')
        # 使用水平布局将输入区域和按钮区域并排
        main_layout = QHBoxLayout()
        
        # 输入垂直布局
        input_layout = QVBoxLayout()
        
        # 科目名称标签和输入框
        subject_name_layout = QHBoxLayout()
        self.subject_label = QLabel('科目名称:')
        self.subject_edit = QLineEdit()
        # 设置默认科目名称
        self.subject_edit.setText('语文')
        subject_name_layout.addWidget(self.subject_label)
        subject_name_layout.addWidget(self.subject_edit)
        input_layout.addLayout(subject_name_layout)

        # 考试日期标签和选择框
        date_layout = QHBoxLayout()
        self.date_label = QLabel('考试日期:')
        self.date_edit = QDateTimeEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        # 设置默认考试日期
        self.date_edit.setDate(QDate(2025, 9, 1))
        date_layout.addWidget(self.date_label)
        date_layout.addWidget(self.date_edit)
        date_layout.setStretch(1, 1)  # 让输入框占据剩余空间
        input_layout.addLayout(date_layout)

        # 考试时间标签和选择框
        time_layout = QHBoxLayout()
        self.time_label = QLabel('考试时间:')
        # 修改：使用两个QDateTimeEdit控件来设置考试时间段
        self.time_start_edit = QDateTimeEdit()
        self.time_start_edit.setDisplayFormat('HH:mm')
        self.time_start_edit.setTime(QTime(9, 30))
        self.time_end_edit = QDateTimeEdit()
        self.time_end_edit.setDisplayFormat('HH:mm')
        self.time_end_edit.setTime(QTime(11, 30))

        # 设置两个时间控件大小一致
        self.time_start_edit.setMinimumWidth(100)
        self.time_end_edit.setMinimumWidth(100)
        self.time_start_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.time_end_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # 添加中间的连接符
        self.time_separator = QLabel(' - ')
        time_layout.addWidget(self.time_label)
        time_layout.addWidget(self.time_start_edit)
        time_layout.addWidget(self.time_separator)
        time_layout.addWidget(self.time_end_edit)
        time_layout.setStretch(1, 1)  # 让输入框占据剩余空间
        time_layout.setStretch(3, 1)  # 设置结束时间控件也具有相同的拉伸因子
        input_layout.addLayout(time_layout)
        
        # 备注标签和输入框
        remark_layout = QHBoxLayout()
        self.remark_label = QLabel('备注信息:')
        self.remark_edit = QLineEdit()
        remark_layout.addWidget(self.remark_label)
        remark_layout.addWidget(self.remark_edit)
        input_layout.addLayout(remark_layout)
        
        # 当前科目索引和导航按钮
        navigation_layout = QHBoxLayout()
        self.current_subject_index = 0
        self.subject_index_label = QLabel(f'科目 {self.current_subject_index + 1}/{self.subject_count_spin.value()}')
        navigation_layout.addWidget(self.subject_index_label)
        
        # 上一个/下一个科目按钮
        self.prev_btn = QPushButton('上一个科目')
        self.prev_btn.clicked.connect(self.prev_subject)
        self.prev_btn.setEnabled(False)
        self.next_btn = QPushButton('下一个科目')
        self.next_btn.clicked.connect(self.next_subject)
        self.next_btn.setEnabled(False)
        navigation_layout.addWidget(self.prev_btn)
        navigation_layout.addWidget(self.next_btn)
        input_layout.addLayout(navigation_layout)
        
        # 创建按钮区域
        button_layout = QVBoxLayout()
        self.add_button = QPushButton('添加/更新科目')
        self.add_button.clicked.connect(self.add_or_update_subject)
        self.clear_button = QPushButton('清空所有')
        self.clear_button.clicked.connect(self.clear_all_subjects)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        button_layout.setContentsMargins(60,40,50,10)
        
        # 将输入布局和按钮布局添加到主布局
        main_layout.addLayout(input_layout)
        main_layout.addLayout(button_layout)
        # 设置左右区域的比例，左边60%，右边40%
        main_layout.setStretch(0, 7)  # 左边区域占6份
        main_layout.setStretch(1, 3)  # 右边区域占4份

        input_group.setLayout(main_layout)
        parent_layout.addWidget(input_group)
    
    
    def create_result_area(self, parent_layout):
        """
        创建结果显示区域（参考proctor_page.py的设计）
        """
        # 创建水平布局来放置表格和日志区域
        h_layout = QHBoxLayout()
        
        # 创建科目信息表格
        self.table = QTableWidget()
        self.table.verticalHeader().setFixedWidth(int(self.table.width() * 0.05)) # 设置垂直表头宽度
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignCenter) # 设置垂直表头居中

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['科目名称', '考试日期', '考试时间', '备注信息'])
        self.table.horizontalHeader().setStretchLastSection(True)

        table_width = self.table.width()
        self.table.setColumnWidth(0, int(table_width * 0.2))  # 科目名称 20%
        self.table.setColumnWidth(1, int(table_width * 0.2))  # 考试日期 20%
        self.table.setColumnWidth(2, int(table_width * 0.2))  # 考试时间 20%

        # 连接双击事件
        self.table.cellDoubleClicked.connect(self.on_table_cell_double_clicked)
        h_layout.addWidget(self.table)
        
        # 创建右侧日志区域
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Microsoft YaHei", 10))
        self.log_text.setReadOnly(True)
        self.log_text.setFixedWidth(300)
        
        # 创建一个垂直布局来放置日志区域
        log_layout = QVBoxLayout()

        log_layout.addWidget(self.log_text)
        
        # 将日志布局添加到水平布局
        h_layout.addLayout(log_layout)
        
        # 将整个水平布局添加到父布局
        parent_layout.addLayout(h_layout)
        
        # 初始化显示
        self.update_table()
    
    def log(self, message):
        """
        输出日志到日志区
        """
        if self.log_text:
            self.log_text.append(message)
    
    def on_subject_count_changed(self, value):
        """
        科目数改变时的处理
        """
        # 调整subjects列表大小
        current_count = len(self.subjects)
        if value > current_count:
            # 增加空科目
            for i in range(current_count, value):
                self.subjects.append({
                    'name': '',
                    'date': '',
                    'time': '',
                    'remark': ''
                })
        elif value < current_count:
            # 删除多余科目
            self.subjects = self.subjects[:value]
        
        # 更新导航按钮状态
        self.update_navigation()
        self.update_table()
        self.log(f"科目数已设置为: {value}")
    
    def update_navigation(self):
        """
        更新导航按钮状态
        """
        max_index = self.subject_count_spin.value() - 1
        self.prev_btn.setEnabled(self.current_subject_index > 0)
        self.next_btn.setEnabled(self.current_subject_index < max_index)
        self.subject_index_label.setText(f'科目 {self.current_subject_index + 1}/{self.subject_count_spin.value()}')
        
        # 更新输入框内容
        if 0 <= self.current_subject_index < len(self.subjects):
            subject = self.subjects[self.current_subject_index]
            self.subject_edit.setText(subject['name'])
            # 正确设置日期和时间
            if subject['date']:
                self.date_edit.setDate(QDate.fromString(subject['date'], 'yyyy-MM-dd'))
            if subject['time']:
                # 修改：解析时间段格式并设置开始和结束时间
                time_parts = subject['time'].split('-')
                if len(time_parts) == 2:
                    try:
                        start_time = QTime.fromString(time_parts[0].strip(), 'HH:mm')
                        end_time = QTime.fromString(time_parts[1].strip(), 'HH:mm')
                        self.time_start_edit.setTime(start_time)
                        self.time_end_edit.setTime(end_time)
                    except:
                        pass  # 如果解析失败，保持默认时间
            self.remark_edit.setText(subject['remark'])
    
    def prev_subject(self):
        """
        切换到上一个科目
        """
        if self.current_subject_index > 0:
            # 保存当前科目信息
            self.save_current_subject()
            # 切换到上一个科目
            self.current_subject_index -= 1
            self.update_navigation()
            self.log(f"切换到科目 {self.current_subject_index + 1}")
    
    def next_subject(self):
        """
        切换到下一个科目
        """
        if self.current_subject_index < self.subject_count_spin.value() - 1:
            # 保存当前科目信息
            self.save_current_subject()
            # 切换到下一个科目
            self.current_subject_index += 1
            self.update_navigation()
            self.log(f"切换到科目 {self.current_subject_index + 1}")
    
    def save_current_subject(self):
        """
        保存当前科目信息
        """
        # 添加考试时间逻辑校验
        start_time = self.time_start_edit.time()
        end_time = self.time_end_edit.time()
        
        if start_time >= end_time:
            QMessageBox.warning(self, "时间设置错误", "考试结束时间必须晚于开始时间！")
            return False

        # 新增：科目名称重复校验
        normalized_name = self.subject_edit.text().strip()
        for i, s in enumerate(self.subjects):
            if i != self.current_subject_index and normalized_name and normalized_name == str(s.get('name', '')).strip():
                QMessageBox.warning(self, "输入错误", f"科目名称重复（{normalized_name}）")
                return False

        # 新增：同一日期考试时间冲突校验
        new_date = self.date_edit.date().toString('yyyy-MM-dd')
        new_start_min = start_time.hour() * 60 + start_time.minute()
        new_end_min = end_time.hour() * 60 + end_time.minute()
        for i, s in enumerate(self.subjects):
            if i == self.current_subject_index:
                continue
            other_date = s.get('date', '')
            other_time_str = s.get('time', '')
            if other_date == new_date and other_time_str and '-' in other_time_str:
                parts = other_time_str.split('-')
                if len(parts) == 2:
                    other_start = QTime.fromString(parts[0].strip(), 'HH:mm')
                    other_end = QTime.fromString(parts[1].strip(), 'HH:mm')
                    if other_start.isValid() and other_end.isValid():
                        s_min = other_start.hour() * 60 + other_start.minute()
                        e_min = other_end.hour() * 60 + other_end.minute()
                        # 有交集即为冲突
                        if not (new_end_min <= s_min or new_start_min >= e_min):
                            QMessageBox.warning(self, "输入错误", f"与科目“{s.get('name','')}”在{new_date}考试时间冲突：{start_time.toString('HH:mm')}-{end_time.toString('HH:mm')} 与 {other_time_str}")
                            return False
        
        if 0 <= self.current_subject_index < len(self.subjects):
            self.subjects[self.current_subject_index] = {
                'name': self.subject_edit.text(),
                'date': self.date_edit.date().toString('yyyy-MM-dd'),
                # 修改：保存格式化的时间段
                'time': f"{self.time_start_edit.time().toString('HH:mm')}-{self.time_end_edit.time().toString('HH:mm')}",
                'remark': self.remark_edit.text()
            }
        return True
    
    def add_or_update_subject(self):
        """
        添加或更新科目信息
        """
        # 保存当前科目信息
        if not self.save_current_subject():
            return  # 如果时间校验失败，则不继续执行
        
        # 更新表格显示
        self.update_table()
        self.log(f"科目 {self.current_subject_index + 1} 信息已更新")
        QMessageBox.information(self, "操作成功", f"科目 {self.current_subject_index + 1} 信息已保存")
    
    def update_table(self):
        """
        更新表格显示
        """
        # 在批量更新期间暂时阻断信号，避免触发大量 cellChanged 导致跨页面刷新卡顿
        self.table.blockSignals(True)
        self.table.setRowCount(len(self.subjects))
        for i, subject in enumerate(self.subjects):
            # 科目名称
            name_item = QTableWidgetItem(subject['name'])
            name_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, name_item)
            
            # 考试日期
            date_item = QTableWidgetItem(subject['date'])
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, date_item)
            
            # 考试时间
            time_item = QTableWidgetItem(subject['time'])
            time_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 2, time_item)
            
            # 备注
            remark_item = QTableWidgetItem(subject['remark'])
            remark_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 3, remark_item)
        
        # 设置列宽比例
        
        # self.table.setColumnWidth(3, int(table_width * 0.4))  # 备注信息 55%
        # 恢复信号
        self.table.blockSignals(False)
    
    def clear_all_subjects(self):
        """
        清空所有科目信息
        """
        reply = QMessageBox.question(self, '确认清空', '确定要清空所有科目信息吗？',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.subjects = []
            # 重新初始化科目列表
            for i in range(self.subject_count_spin.value()):
                self.subjects.append({
                    'name': '',
                    'date': '',
                    'time': '',
                    'remark': ''
                })
            
            # 重置当前科目索引
            self.current_subject_index = 0
            self.update_navigation()
            self.update_table()
            self.log("所有科目信息已清空")
            QMessageBox.information(self, "操作成功", "所有科目信息已清空")
    
    def on_table_cell_double_clicked(self, row, column):
        """
        双击表格单元格事件处理
        """
        # 获取当前单元格的项目
        item = self.table.item(row, column)
        if item:
            # 设置单元格为可编辑状态
            self.table.editItem(item)
        else:
            # 如果单元格为空，创建新项目并设置为可编辑
            item = QTableWidgetItem("")
            self.table.setItem(row, column, item)
            self.table.editItem(item)
        
        # 连接单元格内容改变事件
        self.table.cellChanged.connect(self.on_table_cell_changed)
    
    def on_table_cell_changed(self, row, column):
        """
        表格单元格内容改变事件处理
        """
        # 确保行索引在有效范围内
        if row < len(self.subjects):
            # 获取新的值
            item = self.table.item(row, column)
            new_value = item.text() if item else ""
            
            # 添加非空校验
            if column in [0, 1, 2] and not new_value.strip():  # 科目名称、考试日期、考试时间不能为空
                QMessageBox.warning(self, '输入错误', f'第{row+1}行{["科目名称", "考试日期", "考试时间"][column]}不能为空！')
                # 恢复原值
                self.table.cellChanged.disconnect(self.on_table_cell_changed)
                original_value = self.subjects[row][['name', 'date', 'time'][column]]
                item.setText(original_value)
                self.table.cellChanged.connect(self.on_table_cell_changed)
                return
            
            # 更新对应的科目信息
            if column == 0:  # 科目名称
                # 重名校验（去除首尾空格后与其他行比对）
                normalized_name = new_value.strip()
                for i, s in enumerate(self.subjects):
                    if i != row and normalized_name and normalized_name == str(s.get('name', '')).strip():
                        QMessageBox.warning(self, '输入错误', f'第{row+1}行数据错误：科目名称重复（{normalized_name}）')
                        # 恢复原值
                        self.table.cellChanged.disconnect(self.on_table_cell_changed)
                        item.setText(self.subjects[row]['name'])
                        self.table.cellChanged.connect(self.on_table_cell_changed)
                        return
                self.subjects[row]['name'] = new_value
            elif column == 1:  # 考试日期
                # 添加日期格式校验
                if new_value:  # 如果有值才校验
                    date = QDate.fromString(new_value, 'yyyy-MM-dd')
                    if not date.isValid():
                        QMessageBox.warning(self, '格式错误', f'第{row+1}行考试日期格式不正确，应为yyyy-MM-dd格式！（示例：2023-04-15）')
                        # 恢复原值
                        self.table.cellChanged.disconnect(self.on_table_cell_changed)
                        item.setText(self.subjects[row]['date'])
                        self.table.cellChanged.connect(self.on_table_cell_changed)
                        return
                # 同日时间冲突校验：使用该行现有时间与其他行在新日期的时间比对
                existing_time_str = self.subjects[row].get('time', '')
                if existing_time_str and '-' in existing_time_str:
                    parts = existing_time_str.split('-')
                    if len(parts) == 2:
                        cur_start = QTime.fromString(parts[0].strip(), 'HH:mm')
                        cur_end = QTime.fromString(parts[1].strip(), 'HH:mm')
                        if cur_start.isValid() and cur_end.isValid():
                            new_date = new_value
                            cur_s = cur_start.hour() * 60 + cur_start.minute()
                            cur_e = cur_end.hour() * 60 + cur_end.minute()
                            for i, s in enumerate(self.subjects):
                                if i == row:
                                    continue
                                if s.get('date', '') == new_date:
                                    other_time_str = s.get('time', '')
                                    if other_time_str and '-' in other_time_str:
                                        op = other_time_str.split('-')
                                        if len(op) == 2:
                                            other_start = QTime.fromString(op[0].strip(), 'HH:mm')
                                            other_end = QTime.fromString(op[1].strip(), 'HH:mm')
                                            if other_start.isValid() and other_end.isValid():
                                                s_min = other_start.hour() * 60 + other_start.minute()
                                                e_min = other_end.hour() * 60 + other_end.minute()
                                                if not (cur_e <= s_min or cur_s >= e_min):
                                                    QMessageBox.warning(self, '输入错误', f'第{row+1}行与第{i+1}行在{new_date}考试时间冲突：{existing_time_str} 与 {other_time_str}')
                                                    # 恢复原值
                                                    self.table.cellChanged.disconnect(self.on_table_cell_changed)
                                                    item.setText(self.subjects[row]['date'])
                                                    self.table.cellChanged.connect(self.on_table_cell_changed)
                                                    return
                self.subjects[row]['date'] = new_value
            elif column == 2:  # 考试时间
                # 添加时间格式和逻辑校验
                if new_value and '-' in new_value:
                    time_parts = new_value.split('-')
                    if len(time_parts) == 2:
                        try:
                            start_time_str = time_parts[0].strip()
                            end_time_str = time_parts[1].strip()
                            
                            # 校验时间格式
                            start_time = QTime.fromString(start_time_str, 'HH:mm')
                            end_time = QTime.fromString(end_time_str, 'HH:mm')
                            
                            if not start_time.isValid() or not end_time.isValid():
                                QMessageBox.warning(self, '格式错误', f'第{row+1}行考试时间格式不正确，应为HH:mm-HH:mm格式！（示例：09:00-11:00）')
                                # 恢复原值
                                self.table.cellChanged.disconnect(self.on_table_cell_changed)
                                item.setText(self.subjects[row]['time'])
                                self.table.cellChanged.connect(self.on_table_cell_changed)
                                return
                            
                            # 校验时间逻辑
                            if start_time >= end_time:
                                QMessageBox.warning(self, '时间错误', f'第{row+1}行考试结束时间必须晚于开始时间！')
                                # 恢复原值
                                self.table.cellChanged.disconnect(self.on_table_cell_changed)
                                item.setText(self.subjects[row]['time'])
                                self.table.cellChanged.connect(self.on_table_cell_changed)
                                return

                            # 同日时间冲突校验：与其他行在同一日期的时间比对
                            row_date = self.subjects[row].get('date', '')
                            if row_date:
                                new_s = start_time.hour() * 60 + start_time.minute()
                                new_e = end_time.hour() * 60 + end_time.minute()
                                for i, s in enumerate(self.subjects):
                                    if i == row:
                                        continue
                                    if s.get('date', '') == row_date:
                                        other_time_str = s.get('time', '')
                                        if other_time_str and '-' in other_time_str:
                                            op = other_time_str.split('-')
                                            if len(op) == 2:
                                                other_start = QTime.fromString(op[0].strip(), 'HH:mm')
                                                other_end = QTime.fromString(op[1].strip(), 'HH:mm')
                                                if other_start.isValid() and other_end.isValid():
                                                    s_min = other_start.hour() * 60 + other_start.minute()
                                                    e_min = other_end.hour() * 60 + other_end.minute()
                                                    if not (new_e <= s_min or new_s >= e_min):
                                                        QMessageBox.warning(self, '输入错误', f'第{row+1}行与第{i+1}行在{row_date}考试时间冲突：{new_value} 与 {other_time_str}')
                                                        # 恢复原值
                                                        self.table.cellChanged.disconnect(self.on_table_cell_changed)
                                                        item.setText(self.subjects[row]['time'])
                                                        self.table.cellChanged.connect(self.on_table_cell_changed)
                                                        return
                        except:
                            QMessageBox.warning(self, '格式错误', f'第{row+1}行考试时间格式不正确！')
                            # 恢复原值
                            self.table.cellChanged.disconnect(self.on_table_cell_changed)
                            item.setText(self.subjects[row]['time'])
                            self.table.cellChanged.connect(self.on_table_cell_changed)
                            return
                elif new_value:  # 如果有值但格式不对
                    QMessageBox.warning(self, '格式错误', f'第{row+1}行考试时间格式不正确，应为HH:mm-HH:mm格式！')
                    # 恢复原值
                    self.table.cellChanged.disconnect(self.on_table_cell_changed)
                    item.setText(self.subjects[row]['time'])
                    self.table.cellChanged.connect(self.on_table_cell_changed)
                    return
                self.subjects[row]['time'] = new_value
            elif column == 3:  # 备注
                self.subjects[row]['remark'] = new_value
            
            self.log(f"科目 {row+1} 的 {['科目名称', '考试日期', '考试时间', '备注'][column]} 已更新为: {new_value}")
            
            # 同步更新上方输入框的显示（如果当前编辑的是当前科目）
            if row == self.current_subject_index:
                self.update_navigation()
            
            # 确保新创建的项目也居中对齐
            if item:
                item.setTextAlignment(Qt.AlignCenter)
            
            # 断开连接以避免重复触发
            self.table.cellChanged.disconnect(self.on_table_cell_changed)

    def import_subjects(self):
        """
        导入科目信息
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择科目信息文件', '', 'Excel Files (*.xlsx *.xls)')
        
        if not file_path:
            return
        
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 检查必需的列是否存在
            required_columns = ['科目名称', '考试日期', '考试时间']
            if not all(col in df.columns for col in required_columns):
                missing_cols = [col for col in required_columns if col not in df.columns]
                QMessageBox.warning(self, '导入失败', f'文件缺少必需的列: {", ".join(missing_cols)}')
                return
            
            # 清空现有科目
            self.subjects = []
            # 新增：用于校验重名与同日时间冲突
            seen_names = set()
            date_slots = {}  # {date_str: [(start_min, end_min, name, time_str, row_index)]}
            
            # 解析数据并进行时间校验
            for index, row in df.iterrows():
                # 检查必需字段是否为空
                if pd.isna(row['科目名称']) or not str(row['科目名称']).strip():
                    QMessageBox.warning(self, '导入失败', f'第{index+1}行数据错误：科目名称不能为空！')
                    return
                # 新增：科目名称重名校验（去除首尾空格后比较）
                normalized_name = str(row['科目名称']).strip()
                if normalized_name in seen_names:
                    QMessageBox.warning(self, '导入失败', f'第{index+1}行数据错误：科目名称重复（{normalized_name}）')
                    return
                seen_names.add(normalized_name)
                
                if pd.isna(row['考试日期']) or not str(row['考试日期']).strip():
                    QMessageBox.warning(self, '导入失败', f'第{index+1}行数据错误：考试日期不能为空！')
                    return
                
                if pd.isna(row['考试时间']) or not str(row['考试时间']).strip():
                    QMessageBox.warning(self, '导入失败', f'第{index+1}行数据错误：考试时间不能为空！')
                    return
                
                # 解析考试时间
                time_str = str(row['考试时间']) if not pd.isna(row['考试时间']) else ''
                start_time = None
                end_time = None
                if '-' in time_str:
                    time_parts = time_str.split('-')
                    if len(time_parts) == 2:
                        try:
                            start_time_str = time_parts[0].strip()
                            end_time_str = time_parts[1].strip()
                            
                            # 校验时间格式和逻辑
                            # 尝试多种时间格式
                            time_formats = ['HH:mm', 'H:mm']
                            
                            # 尝试解析开始时间
                            for time_format in time_formats:
                                start_time = QTime.fromString(start_time_str, time_format)
                                if start_time.isValid():
                                    break
                            
                            # 尝试解析结束时间
                            for time_format in time_formats:
                                end_time = QTime.fromString(end_time_str, time_format)
                                if end_time.isValid():
                                    break
                            
                            if not start_time or not start_time.isValid() or not end_time or not end_time.isValid():
                                QMessageBox.warning(self, '导入失败', f'第{index+1}行数据错误：考试时间格式不正确，支持格式：HH:mm-HH:mm 或 H:mm-H:mm（如：09:00-11:30 或 9:00-11:30）')
                                return
                            
                            if start_time >= end_time:
                                QMessageBox.warning(self, '导入失败', f'第{index+1}行数据错误：考试结束时间必须晚于开始时间！')
                                return
                            
                            # 将时间标准化为 HH:mm 格式
                            standardized_start_time = start_time.toString('HH:mm')
                            standardized_end_time = end_time.toString('HH:mm')
                            time_str = f"{standardized_start_time}-{standardized_end_time}"
                        except:
                            QMessageBox.warning(self, '导入失败', f'第{index+1}行数据错误：考试时间格式不正确！')
                            return
                else:
                    QMessageBox.warning(self, '导入失败', f'第{index+1}行数据错误：考试时间格式不正确，应为HH:mm-HH:mm或H:mm-H:mm格式！（如：09:00-11:30 或 9:00-11:30）')
                    return
                
                # 校验考试日期格式
                date_value = row['考试日期']
                standardized_date = None
                
                if not pd.isna(date_value):
                    # 如果是datetime对象，直接转换
                    if isinstance(date_value, pd.Timestamp) or hasattr(date_value, 'strftime'):
                        try:
                            standardized_date = date_value.strftime('%Y-%m-%d')
                        except:
                            pass
                    else:
                        # 如果是字符串，尝试多种日期格式
                        date_str = str(date_value).strip()
                        if date_str:
                            date_formats = ['yyyy-MM-dd', 'yyyy/M/d']
                            date = None
                            
                            for date_format in date_formats:
                                date = QDate.fromString(date_str, date_format)
                                if date.isValid():
                                    # 将日期标准化为 yyyy-MM-dd 格式
                                    standardized_date = date.toString('yyyy-MM-dd')
                                    break
                    
                    if not standardized_date:
                        QMessageBox.warning(self, '导入失败', f'第{index+1}行数据错误：考试日期格式不正确，支持格式：yyyy-MM-dd 或 yyyy/M/d（如：2023-10-15 或 2025/8/21）')
                        return
                
                # 新增：同一日期考试时间冲突校验
                try:
                    new_start_min = start_time.hour() * 60 + start_time.minute()
                    new_end_min = end_time.hour() * 60 + end_time.minute()
                except Exception:
                    QMessageBox.warning(self, '导入失败', f'第{index+1}行数据错误：考试时间无法解析，请检查格式！')
                    return
                if standardized_date:
                    for s, e, exist_name, exist_time_str, exist_row in date_slots.get(standardized_date, []):
                        # 时间区间重叠判定：有交集即为冲突
                        if not (new_end_min <= s or new_start_min >= e):
                            QMessageBox.warning(self, '导入失败', f'第{index+1}行（{normalized_name}）与第{exist_row+1}行（{exist_name}）在{standardized_date}考试时间冲突：{time_str} 与 {exist_time_str}')
                            return
                    # 记录本行时间段
                    date_slots.setdefault(standardized_date, []).append((new_start_min, new_end_min, normalized_name, time_str, index))
                
                subject = {
                    'name': normalized_name if not pd.isna(row['科目名称']) else '',
                    'date': standardized_date if standardized_date else str(row['考试日期']) if not pd.isna(row['考试日期']) else '',
                    'time': time_str,
                    'remark': str(row['备注']) if '备注' in df.columns and not pd.isna(row['备注']) else ''
                }
                self.subjects.append(subject)
            
            # 更新科目数
            self.subject_count_spin.setValue(len(df))
            
            # 更新界面
            self.current_subject_index = 0
            self.update_navigation()
            self.update_table()
            
            self.log(f"成功导入 {len(self.subjects)} 个科目信息")
            QMessageBox.information(self, '导入成功', f'成功导入 {len(self.subjects)} 个科目信息')
            
        except Exception as e:
            QMessageBox.critical(self, '导入失败', f'导入科目信息时出错:\n{str(e)}')

    def generate_template(self):
        """
        生成科目信息模板文件
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self, '保存科目信息模板文件', '科目信息模板.xlsx', 'Excel Files (*.xlsx)')
        
        if not file_path:
            return
        
        try:
            # 创建模板数据
            template_data = [
                {
                    '科目名称': '语文',
                    '考试日期': '2023-09-09',
                    '考试时间': '08:00-10:00',
                    '考试时长（分钟）—可以留空': 120,
                    '备注': ''
                },
                {
                    '科目名称': '数学',
                    '考试日期': '2023-09-09',
                    '考试时间': '14:30-16:30',
                    '考试时长（分钟）—可以留空': 120,
                    '备注': ''
                },
                {
                    '科目名称': '英语',
                    '考试日期': '2023-09-10',
                    '考试时间': '08:00-10:00',
                    '考试时长（分钟）—可以留空': 120,
                    '备注': ''
                },
                {
                    '科目名称': '物理',
                    '考试日期': '2023-09-10',
                    '考试时间': '15:00-16:00',
                    '考试时长（分钟）—可以留空': 60,
                    '备注': ''
                }
            ]
            
            # 创建DataFrame
            df = pd.DataFrame(template_data)
            
            # 创建ExcelWriter对象，使用xlsxwriter引擎
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Sheet1', index=False)

            # 获取workbook和worksheet对象
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']

            # 创建居中格式
            center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})

            # 应用居中格式到所有列
            worksheet.set_column(0, 4, None, center_format)

            # 创建居中格式
            center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})

            # 应用居中格式到所有列
            worksheet.set_column(0, 4, None, center_format)

            # 设置列宽
            worksheet.set_column(0, 0, 10)
            worksheet.set_column(1, 2, 15)
            worksheet.set_column(3, 3, 30)
            worksheet.set_column(4, 4, 20)

            # ===== 新增：填写说明 sheet =====
            # 为每列准备说明文本
            instructions = {
                '科目名称': '必填。\n示例：语文、数学、英语等。',
                '考试日期': '必填。\n支持：yyyy-MM-dd 或 yyyy/M/d（自动标准化）。\n示例：2025-10-14 或 2025/8/21。',
                '考试时间': '必填。\n支持：HH:mm-HH:mm 或 H:mm-H:mm。\n示例：08:00-10:00 或 9:00-11:30。',
                '考试时长（分钟）—可以留空': '选填。\n整数分钟；留空时按考试时间段自动计算。',
                '备注': '选填。\n可填特殊说明或补充信息。'
            }

            # 基于主表列顺序，写入一行说明数据
            instruction_row = [{col: instructions.get(col, '') for col in df.columns}]
            df_desc = pd.DataFrame(instruction_row)
            df_desc.to_excel(writer, sheet_name='填写说明', index=False)

            # 设置说明sheet的样式与列宽，并给必填列标红底色
            desc_ws = writer.sheets['填写说明']
            wrap_left = workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top'})
            required_cell = workbook.add_format({'text_wrap': True, 'align': 'left', 'valign': 'top', 'bg_color': '#FFC7CE'})

            # 列宽与主表保持一致
            desc_ws.set_column(0, 0, 10, wrap_left)
            desc_ws.set_column(1, 2, 15, wrap_left)
            desc_ws.set_column(3, 3, 30, wrap_left)
            desc_ws.set_column(4, 4, 20, wrap_left)

            # 给第二行的必填列设置红色底色（科目名称、考试日期、考试时间）
            required_cols = {'科目名称', '考试日期', '考试时间'}
            for idx, col in enumerate(df.columns):
                value = instructions.get(col, '')
                if col in required_cols:
                    desc_ws.write(1, idx, value, required_cell)  # 第二行（索引1）
                else:
                    desc_ws.write(1, idx, value, wrap_left)
            # 设置第二行行高以适配多行文本
            desc_ws.set_row(1, 100)

            # 同时为第一行（列标题）设置边框；必填列浅红底色，非必填列正常底色
            required_header = workbook.add_format({
                'text_wrap': True, 'align': 'center', 'valign': 'vcenter',
                'bg_color': '#FFC7CE', 'bold': True, 'border': 1
            })
            normal_header = workbook.add_format({
                'text_wrap': True, 'align': 'center', 'valign': 'vcenter',
                'bold': True, 'border': 1
            })
            for idx, col in enumerate(df.columns):
                fmt = required_header if col in required_cols else normal_header
                desc_ws.write(0, idx, col, fmt)
            # ===== 新增结束 =====
            writer.close()
            
            self.log(f"科目信息模板文件已生成: {file_path}")
            QMessageBox.information(self, '生成成功', f'科目信息模板文件已生成:\n{file_path}')
            
            # 询问是否打开文件所在文件夹
            reply = QMessageBox.question(self, '打开文件夹', 
                                    '是否打开文件所在文件夹？',
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 获取文件所在文件夹路径
                folder_path = os.path.dirname(os.path.abspath(file_path))
                # 在Windows系统中打开文件夹
                os.startfile(folder_path)
                
        except Exception as e:
            QMessageBox.critical(self, '生成失败', f'生成科目信息模板文件时出错:\n{str(e)}')

    def get_subject_duration(self, subject_index):
        """
        获取指定科目的考试时长（分钟）
        """
        if 0 <= subject_index < len(self.subjects):
            subject = self.subjects[subject_index]
            time_str = subject['time']
            if '-' in time_str:
                time_parts = time_str.split('-')
                if len(time_parts) == 2:
                    start_time = QTime.fromString(time_parts[0].strip(), 'HH:mm')
                    end_time = QTime.fromString(time_parts[1].strip(), 'HH:mm')
                    if start_time.isValid() and end_time.isValid():
                        # 计算分钟数差
                        minutes = start_time.msecsTo(end_time) // 60000
                        return minutes if minutes > 0 else 0
        return 0

    def export_subjects(self):
        """
        导出科目信息到Excel文件
        """
        if not self.subjects:
            QMessageBox.warning(self, '警告', '没有可导出的科目信息')
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, '导出科目信息', '科目信息.xlsx', 'Excel Files (*.xlsx)')
        
        if not file_path:
            return
        
        try:
            # 准备数据
            export_data = []
            for i, subject in enumerate(self.subjects):
                duration = self.get_subject_duration(i)
                export_data.append({
                    '科目名称': subject['name'],
                    '考试日期': subject['date'],
                    '考试时间': subject['time'],
                    '考试时长（分钟）—可以留空': duration,
                    '备注': subject['remark']
                })
            
            # 创建DataFrame
            df = pd.DataFrame(export_data)
            
            # 创建ExcelWriter对象，使用xlsxwriter引擎
            writer = pd.ExcelWriter(file_path, engine='xlsxwriter')
            df.to_excel(writer, sheet_name='Sheet1', index=False)

            # 获取workbook和worksheet对象
            workbook = writer.book
            worksheet = writer.sheets['Sheet1']

            # 创建居中格式
            center_format = workbook.add_format({'align': 'center', 'valign': 'vcenter'})

            # 应用居中格式到所有列
            worksheet.set_column(0, 4, None, center_format)

            # 设置列宽
            worksheet.set_column(0, 0, 10)
            worksheet.set_column(1, 2, 15)
            worksheet.set_column(3, 3, 30)
            worksheet.set_column(4, 4, 20)

            # 保存文件
            writer.close()
            
            self.log(f"科目信息已导出: {file_path}")
            QMessageBox.information(self, '导出成功', f'科目信息已导出到:\n{file_path}')

            # 询问是否打开文件所在文件夹
            reply = QMessageBox.question(self, '打开文件夹', 
                                    '是否打开文件所在文件夹？',
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 获取文件所在文件夹路径
                folder_path = os.path.dirname(os.path.abspath(file_path))
                # 在Windows系统中打开文件夹
                os.startfile(folder_path)

            
        except Exception as e:
            QMessageBox.critical(self, '导出失败', f'导出科目信息时出错:\n{str(e)}')