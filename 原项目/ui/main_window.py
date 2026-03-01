#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主窗口界面
"""

import os
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton,QStackedWidget, QStatusBar, QLabel, QDialog)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import QTimer, QSize, Qt
from .page.proctor_page import ProctorPage
from .page.subject_page import SubjectPage
from .page.examroom_page import ExamroomPage
from .page.print_page import PrintPage
from .page.help_page import HelpPage

class MainWindow(QMainWindow):
    """
    主窗口类
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('智能考务系统')
        self.setGeometry(350, 150, 1200, 800)
        self.setWindowIcon(QIcon(self.get_resource_path("ui/pic/system.svg")))
        self.ai_assistant_dialog = None
        self.init_ui()
             
    def init_ui(self):
        """
        初始化用户界面
        """

        # self.setStyleSheet("""
        #     QGroupBox {
        #         font-size: 16px;
        #         font-weight: bold;
        #         color: #2c3e50;
        #         border: 2px solid #3498db;
        #         border-radius: 8px;
        #         margin-top: 20px;
        #         padding-top: 4px;
        #         background-color: #f8f9fa;
        #     }
        #     QGroupBox::title {
        #         subcontrol-origin: margin;
        #         subcontrol-position: top left;
        #         left: 10px;
        #         padding: 10px 5px 0 5px;
        #         color: #3498db;
        #     }
        #     QTextEdit {
        #         background-color: white;
        #         border: 1px solid #bdc3c7;
        #         border-radius: 8px;
        #         padding: 10px;
        #         font-size: 13px;
        #         color: #34495e;
        #     }
                     
        # """)
        # 设置窗口字体
        self.setFont(QFont("", 12))

        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget) 
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 0)  # 设置底部边距为0
        # 创建顶部功能页面切换工具栏
        self.create_function_toolbar(main_layout)
  
        # 创建堆叠部件用于切换不同功能页面
        self.stacked_widget=QStackedWidget()
        main_layout.addWidget(self.stacked_widget)
        
        # 创建各个功能页面
        self.create_pages()

        # 创建状态栏
        self.create_status_bar()
    
    def get_resource_path(self, relative_path):
        """获取资源文件的绝对路径"""
        if hasattr(sys, '_MEIPASS'):
            # 如果是打包后的exe文件
            return os.path.join(sys._MEIPASS, relative_path)
        # 如果是python脚本
        return os.path.join(os.path.abspath("."), relative_path)
    def create_function_toolbar(self, parent_layout):
        """
        创建功能选项卡
        """
        toolbar_layout=QHBoxLayout()
        toolbar_layout.setSpacing(0)

        # 创建选项卡样式
        tab_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 10px 20px;
                font-size: 18px;
                border-radius: 0px;
                border-bottom: 3px solid transparent;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: white;
                border-bottom: 3px solid #4A90E2;
                font-weight: bold;
            }
        """

        #创建功能切换按钮
        self.function_btn1=QPushButton()
        self.function_btn1.setText("科目设置")
        self.function_btn1.setIcon(QIcon(self.get_resource_path("ui/pic/subject.svg")))
        self.function_btn1.setIconSize(QSize(20,20))
        self.function_btn1.setCheckable(True)
        self.function_btn1.setChecked(True)
        self.function_btn1.setStyleSheet(tab_style)
        self.function_btn1.clicked.connect(lambda: self.switch_page(0))
        toolbar_layout.addWidget(self.function_btn1)

        self.function_btn2=QPushButton()
        self.function_btn2.setText("监考编排")
        self.function_btn2.setIcon(QIcon(self.get_resource_path("ui/pic/proctor.svg")))
        self.function_btn2.setIconSize(QSize(20,20))
        self.function_btn2.setCheckable(True)
        self.function_btn2.setStyleSheet(tab_style)
        self.function_btn2.clicked.connect(lambda: self.switch_page(1))
        toolbar_layout.addWidget(self.function_btn2)

        self.function_btn3=QPushButton()
        self.function_btn3.setText("考场编排")
        self.function_btn3.setIcon(QIcon(self.get_resource_path("ui/pic/examroom.svg")))
        self.function_btn3.setIconSize(QSize(20,20))
        self.function_btn3.setCheckable(True)
        self.function_btn3.setStyleSheet(tab_style)
        self.function_btn3.clicked.connect(lambda: self.switch_page(2))
        toolbar_layout.addWidget(self.function_btn3)

        self.function_btn_print=QPushButton()
        self.function_btn_print.setText("资料打印")
        self.function_btn_print.setIcon(QIcon(self.get_resource_path("ui/pic/print.svg")))
        self.function_btn_print.setIconSize(QSize(20,20))
        self.function_btn_print.setCheckable(True)
        self.function_btn_print.setStyleSheet(tab_style)
        self.function_btn_print.clicked.connect(lambda: self.switch_page(3))
        toolbar_layout.addWidget(self.function_btn_print)

        self.function_btn4=QPushButton()
        self.function_btn4.setText("使用说明")
        self.function_btn4.setIcon(QIcon(self.get_resource_path("ui/pic/help.svg")))
        self.function_btn4.setIconSize(QSize(20,20))
        self.function_btn4.setCheckable(True)
        self.function_btn4.setStyleSheet(tab_style)
        self.function_btn4.clicked.connect(lambda: self.switch_page(4))
        toolbar_layout.addWidget(self.function_btn4)

        toolbar_layout.addStretch()

        self.ai_assistant_btn = QPushButton()
        self.ai_assistant_btn.setText("AI助手")
        # 尝试使用内置 SVG 图标
        try:
            from .page.ai_assistant_dialog import SvgIcon
            icon = SvgIcon.icon(SvgIcon.PATH_BRAIN, "#4A90E2", 20)
            self.ai_assistant_btn.setIcon(icon)
        except ImportError:
            self.ai_assistant_btn.setIcon(QIcon(self.get_resource_path("ui/pic/help.svg")))
            
        self.ai_assistant_btn.setIconSize(QSize(20, 20))
        self.ai_assistant_btn.setStyleSheet(tab_style)
        self.ai_assistant_btn.clicked.connect(self.open_ai_assistant)
        toolbar_layout.addWidget(self.ai_assistant_btn)
        parent_layout.addLayout(toolbar_layout)

        # 保存所有功能按钮的引用
        self.function_buttons = [self.function_btn1, self.function_btn2, self.function_btn3, self.function_btn_print, self.function_btn4]

    def open_ai_assistant(self):
        # 检查是否已配置 API KEY
        has_key = False
        api_key = ""
        try:
            cert_path = "license.cert"
            if hasattr(sys, '_MEIPASS'):
                cert_path = os.path.join(os.path.dirname(sys.executable), "license.cert")
            
            if os.path.exists(cert_path):
                with open(cert_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if len(lines) >= 2:
                        line = lines[1].strip()
                        if line.startswith("API_KEY:"):
                            api_key = line.split("API_KEY:", 1)[1].strip()
                            if api_key:
                                has_key = True
        except Exception:
            pass

        if not has_key:
            from .page.api_setting_dialog import ApiSettingDialog
            dialog = ApiSettingDialog(self)
            if dialog.exec_() != QDialog.Accepted:
                return
            # 设置成功后重新打开
            self.open_ai_assistant()
            return

        # 验证 API KEY
        if not hasattr(self, "_api_test_worker"):
            from .page.api_setting_dialog import ApiTestWorker
            self._api_test_worker = ApiTestWorker(api_key)
            self._api_test_worker.finished.connect(self._on_api_test_finished)
            
            # 显示加载提示
            self.ai_assistant_btn.setEnabled(False)
            self.ai_assistant_btn.setText("验证中...")
            self._api_test_worker.start()
        else:
            # 正在验证中
            pass

    def _on_api_test_finished(self, success, error_msg):
        self.ai_assistant_btn.setEnabled(True)
        self.ai_assistant_btn.setText("AI助手")
        self._api_test_worker.deleteLater()
        del self._api_test_worker

        if success:
            if self.ai_assistant_dialog is None:
                from .page.ai_assistant_dialog import AiAssistantDialog, SvgIcon

                self.ai_assistant_dialog = AiAssistantDialog(self)
                self.ai_assistant_dialog.show()
            else:
                self.ai_assistant_dialog.show()
                self.ai_assistant_dialog.raise_()
                self.ai_assistant_dialog.activateWindow()
                if self.ai_assistant_dialog._is_compact:
                    self.ai_assistant_dialog.toggle_compact()
        else:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "API 验证失败", f"无法连接到 AI 服务，请检查 API KEY。\n原因：{error_msg}")
            
            from .page.api_setting_dialog import ApiSettingDialog
            dialog = ApiSettingDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                self.open_ai_assistant()
        
    def create_status_bar(self):
        """
        创建状态栏，显示版权信息、版本信息和注册码有效时间
        """
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建水平布局用于放置状态信息
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(5, 0, 5, 0)  # 减少边距: 左、上、右、下
        status_layout.setSpacing(15)  # 设置组件之间的间距
        
        # 版权信息
        self.copyright_label = QLabel("© 2026 智能考务系统")
        self.copyright_label.setStyleSheet("color: #666666; font-size: 12px;")
        
        # 版本信息
        self.version_label = QLabel("版本: v2.0.0118")
        self.version_label.setStyleSheet("color: #666666; font-size: 12px;")
        
        # 注册码有效时间
        self.license_label = QLabel("正在获取许可证信息...")
        self.license_label.setStyleSheet("color: #666666; font-size: 12px;")
        
        # 当前任务信息（靠右显示）
        self.current_task_label = QLabel("当前任务：科目设置")
        self.current_task_label.setStyleSheet("color: red; font-size: 12px;padding-right: 10px;")
        self.current_task_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 将标签添加到布局中
        status_layout.addWidget(self.copyright_label)
        status_layout.addWidget(self.version_label)
        status_layout.addWidget(self.license_label)
        status_layout.addStretch()  # 添加弹性空间使内容靠左对齐
        status_layout.addWidget(self.current_task_label)
        
        # 创建一个 QWidget 来包含布局
        status_widget = QWidget()
        status_widget.setLayout(status_layout)
        
        # 将包含布局的 widget 添加到状态栏
        self.status_bar.addWidget(status_widget, 1)
        
        # 定时更新许可证信息
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_license_info)
        self.timer.start(60000)  # 每分钟更新一次
        
        # 立即更新一次
        self.update_license_info()
    
    def update_current_task(self, index):
        """
        更新当前任务显示
        """
        task_names = ["科目设置", "监考编排", "考场编排", "资料打印", "使用说明"]
        if 0 <= index < len(task_names):
            self.current_task_label.setText(f"当前任务：{task_names[index]}")
    def update_license_info(self):
        """
        更新许可证信息显示
        """
        try:
            from client_license import NetworkTimeLicenseManager
            license_manager = NetworkTimeLicenseManager()
            
            # 检查证书文件是否存在
            if os.path.exists(license_manager.cert_file):
                cert_valid, expire_date, err_msg = license_manager._verify_cert_file()
                if cert_valid and expire_date:
                    # 计算剩余天数
                    current_time = license_manager.get_beijing_time()
                    if current_time:
                        days_left = (expire_date - current_time).days + 1
                        if days_left > 0:
                            self.license_label.setText(f"许可证有效期至: {expire_date.strftime('%Y-%m-%d')} (剩余{days_left}天)")
                            self.license_label.setStyleSheet("color: #00AA00;")  # 绿色
                        else:
                            self.license_label.setText("许可证已过期")
                            self.license_label.setStyleSheet("color: #FF0000;")  # 红色
                    else:
                        self.license_label.setText("无法获取网络时间")
                        self.license_label.setStyleSheet("color: #FF0000;")  # 红色
                else:
                    self.license_label.setText("许可证无效")
                    self.license_label.setStyleSheet("color: #FF0000;")  # 红色
            else:
                self.license_label.setText("未找到许可证")
                self.license_label.setStyleSheet("color: #FF0000;")  # 红色
        except Exception as e:
            self.license_label.setText("许可证信息获取失败")
            self.license_label.setStyleSheet("color: #FF0000;")  # 红色
            
    def create_pages(self):
        """
        创建各个功能页面
        """
        # 创建科目设置页面
        self.subject_page =SubjectPage(self)
        self.stacked_widget.addWidget(self.subject_page)

        # 创建监考编排页面
        self.proctor_page=ProctorPage(self)
        self.stacked_widget.addWidget(self.proctor_page)

        # 创建考场编排页面
        self.examroom_page = ExamroomPage(self)
        self.stacked_widget.addWidget(self.examroom_page)

        # 创建资料打印页面
        self.print_page = PrintPage(self.subject_page, self.examroom_page)
        self.stacked_widget.addWidget(self.print_page)

        # 创建使用说明页面
        self.help_page = HelpPage(self)
        self.stacked_widget.addWidget(self.help_page)

        # 连接科目设置页面的科目数量变化信号到监考编排页面
        self.subject_page.subject_count_spin.valueChanged.connect(self.proctor_page.update_subject_count)
        
        # 连接科目设置页面的科目信息变化信号到监考编排页面
        self.subject_page.table.cellChanged.connect(self.update_proctor_subject_info)
        self.subject_page.subject_count_spin.valueChanged.connect(self.update_proctor_subject_info)
        
        # 注意：监考编排和考场编排的考场数据保持独立，不进行同步

    def update_proctor_subject_info(self):
        """
        更新监考编排页面中的科目信息
        """
        # 获取科目名称列表
        subject_names = [subject['name'] for subject in self.subject_page.subjects]
        # 获取考试时间列表
        exam_times = [subject['time'] for subject in self.subject_page.subjects]
        # 更新监考编排页面的科目名称
        self.proctor_page.update_subject_names(subject_names,exam_times)
        
    def switch_page(self,index):
        """
        切换页面
        """
        for i,btn in enumerate(self.function_buttons):
            if i== index:
                btn.setChecked(True)
            else:
                btn.setChecked(False)
        
        # 切换对应页面
        self.stacked_widget.setCurrentIndex(index)

        # 更新状态栏当前任务显示
        self.update_current_task(index)

    def create_menu_button(self, text, icon_name=None, callback=None):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        
        # 如果是 AI 助手按钮，尝试使用 SvgIcon
        if text == "AI助手" and icon_name:
            try:
                from .page.ai_assistant_dialog import SvgIcon
                icon = SvgIcon.icon(SvgIcon.PATH_BRAIN, "#1890ff", 16)
                btn.setIcon(icon)
            except ImportError:
                pass
        
        # 设置样式
        btn.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: #333333;
                font-size: 14px;
                padding: 5px 10px;
                text-align: left;
            }
            QPushButton:hover {
                color: #1890ff;
                background-color: #e6f7ff;
                border-radius: 4px;
            }
        """)
        
        if callback:
            btn.clicked.connect(callback)
            
        return btn
