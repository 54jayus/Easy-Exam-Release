#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import QWidget, QVBoxLayout
from .ui.windows.print_window import MainWindow as PrintWindow

class PrintPage(QWidget):
    """
    资料打印页面，封装了功能迁移中的打印功能
    """
    def __init__(self, subject_page=None, examroom_page=None):
        super().__init__()
        self.subject_page = subject_page
        self.examroom_page = examroom_page
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 实例化功能迁移中的主窗口
        self.print_widget = PrintWindow(subject_page=self.subject_page, examroom_page=self.examroom_page)
        
        # 将其添加到布局中
        layout.addWidget(self.print_widget)
