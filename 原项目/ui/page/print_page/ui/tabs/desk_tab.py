import os

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QCheckBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..widgets.desk_preview_widget import DeskLabelPreviewWidget, SeatPreviewWidget


class DeskTabMixin:
    def initTab2(self):
        """初始化桌角纸 Tab (重构版)"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        
        # === 左侧：设置区域 ===
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        
        # 1. 布局设置组
        group_layout = QGroupBox("布局设置")
        layout_layout = QFormLayout()
        layout_layout.setContentsMargins(15, 25, 15, 25)
        layout_layout.setVerticalSpacing(10)
        
        self.btnLayoutSettings = QPushButton("座位布局设置")
        self.btnLayoutSettings.setMinimumHeight(32)
        self.btnLayoutSettings.clicked.connect(self.open_layout_settings)
        layout_layout.addRow("布局选择:", self.btnLayoutSettings)
        
        self.lblCurrentLayout = QLabel("当前设置: 7行×6列 | Z型竖排 | 左手位")
        self.lblCurrentLayout.setStyleSheet("color: gray;")
        self.lblCurrentLayout.setWordWrap(True) # 允许换行
        layout_layout.addRow("", self.lblCurrentLayout)
        
        # 保存当前的布局参数
        self.desk_layout_rows = 7
        self.desk_layout_cols = 6
        self.desk_layout_capacity = 42
        self.desk_layout_name = "7行×6列"
        self.desk_layout_pattern = "Z型竖排"
        self.desk_layout_start_pos = "left" # Default left
        self.desk_layout_custom_counts = None
        
        group_layout.setLayout(layout_layout)
        left_layout.addWidget(group_layout)
        
        # 2. 数据来源组
        group_source = QGroupBox("数据来源")
        layout_source = QVBoxLayout()
        layout_source.setContentsMargins(15, 25, 15, 25)
        layout_source.setSpacing(10)
        
        # 模式选择
        mode_layout = QHBoxLayout()
        self.deskRadioEmpty = QRadioButton("生成空白模板")
        self.deskRadioImport = QRadioButton("导入考生数据")
        self.deskRadioExamroom = QRadioButton("从考场编排导入")
        self.deskRadioEmpty.setChecked(True)
        
        self.deskBtnGroup = QButtonGroup()
        self.deskBtnGroup.addButton(self.deskRadioEmpty, 0)
        self.deskBtnGroup.addButton(self.deskRadioImport, 1)
        self.deskBtnGroup.addButton(self.deskRadioExamroom, 2)
        
        mode_layout.addWidget(self.deskRadioEmpty)
        mode_layout.addWidget(self.deskRadioImport)
        mode_layout.addWidget(self.deskRadioExamroom)
        mode_layout.addStretch()
        layout_source.addLayout(mode_layout)
        
        # 动态设置区域
        self.deskStackSettings = QWidget()
        stackLayout = QVBoxLayout()
        stackLayout.setContentsMargins(0, 10, 0, 0)
        
        # -> 数量设置
        self.deskGroupCount = QWidget()
        layoutCount = QHBoxLayout()
        layoutCount.addWidget(QLabel("生成数量:"))
        self.deskSpinCount = QSpinBox()
        self.deskSpinCount.setRange(1, 50000)
        self.deskSpinCount.setValue(800)
        self.deskSpinCount.setMinimumWidth(100)
        self.deskSpinCount.setMinimumHeight(32)
        layoutCount.addWidget(self.deskSpinCount)
        layoutCount.addStretch()
        self.deskGroupCount.setLayout(layoutCount)
        
        # -> 文件导入设置
        self.deskGroupImport = QWidget()
        layoutImport = QHBoxLayout()
        self.deskImportFileEdit = QLineEdit()
        self.deskImportFileEdit.setPlaceholderText("请上传按考场号、座位号排序的数据表")
        self.deskImportFileEdit.setReadOnly(True)
        self.deskImportFileEdit.setMinimumHeight(32)
        layoutImport.addWidget(self.deskImportFileEdit)
        
        self.deskBtnImportBrowse = QPushButton("浏览...")
        self.deskBtnImportBrowse.setMinimumHeight(32)
        self.deskBtnImportBrowse.clicked.connect(self.browse_desk_import_file)
        layoutImport.addWidget(self.deskBtnImportBrowse)
        self.deskGroupImport.setLayout(layoutImport)
        
        # -> 考场编排导入
        self.deskGroupExamroom = QWidget()
        layoutExamroom = QHBoxLayout()
        self.lblDeskExamroomStatus = QLabel("未检测到编排数据")
        self.lblDeskExamroomStatus.setStyleSheet("color: #666; font-style: italic;")
        layoutExamroom.addWidget(self.lblDeskExamroomStatus)
        
        self.btnDeskExamroomRefresh = QPushButton("刷新数据")
        self.btnDeskExamroomRefresh.setMinimumHeight(32)
        self.btnDeskExamroomRefresh.clicked.connect(self.refresh_examroom_data)
        layoutExamroom.addWidget(self.btnDeskExamroomRefresh)
        layoutExamroom.addStretch()
        self.deskGroupExamroom.setLayout(layoutExamroom)
        
        stackLayout.addWidget(self.deskGroupCount)
        stackLayout.addWidget(self.deskGroupImport)
        stackLayout.addWidget(self.deskGroupExamroom)
        self.deskStackSettings.setLayout(stackLayout)
        
        layout_source.addWidget(self.deskStackSettings)
        group_source.setLayout(layout_source)
        left_layout.addWidget(group_source)
        
        # 3. 输出与执行
        group_action = QGroupBox("输出与执行")
        layout_action = QVBoxLayout()
        layout_action.setContentsMargins(15, 25, 15, 25)
        layout_action.setSpacing(10)
        
        layout_path = QHBoxLayout()
        layout_path.addWidget(QLabel("保存路径:"))
        self.deskPathEdit = QLineEdit()
        self.deskPathEdit.setMinimumHeight(32)
        self.deskPathEdit.setText(os.path.join(os.getcwd(), "桌角纸_批量生成.xlsx"))
        layout_path.addWidget(self.deskPathEdit)
        
        btnBrowse = QPushButton("...")
        btnBrowse.setFixedWidth(40)
        btnBrowse.setMinimumHeight(32)
        btnBrowse.clicked.connect(self.browse_desk_file)
        layout_path.addWidget(btnBrowse)
        layout_action.addLayout(layout_path)
        
        layout_formats = QHBoxLayout()
        self.deskCheckExportXLSX = QCheckBox("生成Excel")
        self.deskCheckExportXLSX.setChecked(False)
        self.deskCheckExportXLSX.setToolTip("勾选后生成 Excel 文件（可编辑）。")
        layout_formats.addWidget(self.deskCheckExportXLSX)

        self.deskCheckExportPDF = QCheckBox("生成PDF(打印推荐)")
        self.deskCheckExportPDF.setChecked(True)
        self.deskCheckExportPDF.setToolTip("勾选后生成 PDF 文件（打印效果更精准）。")
        layout_formats.addWidget(self.deskCheckExportPDF)
        layout_action.addLayout(layout_formats)
        
        self.deskBtnGenerate = QPushButton("开始生成")
        self.deskBtnGenerate.setMinimumHeight(40)
        self.deskBtnGenerate.clicked.connect(self.start_generation)
        self.deskBtnGenerate.setStyleSheet("""
            QPushButton {
                background-color: #0078d7; 
                color: white; 
                font-weight: bold; 
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0063b1;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        layout_action.addWidget(self.deskBtnGenerate)
        
        group_action.setLayout(layout_action)
        left_layout.addWidget(group_action)
        
        left_layout.addStretch()
        
        # === 右侧：预览区域 ===
        right_layout = QVBoxLayout()
        group_preview = QGroupBox("模板预览")
        layout_preview = QVBoxLayout()
        
        # 使用 TabWidget 切换两种预览
        self.deskPreviewTabs = QTabWidget()
        
        # Tab 1: 座位布局
        self.deskLayoutPreview = SeatPreviewWidget()
        self.deskLayoutPreview.setMinimumSize(300, 400)
        self.deskPreviewTabs.addTab(self.deskLayoutPreview, "座位布局")
        
        # Tab 2: 桌角纸
        self.deskContentPreview = DeskLabelPreviewWidget()
        self.deskContentPreview.setMinimumSize(300, 400)
        self.deskPreviewTabs.addTab(self.deskContentPreview, "桌角纸")
        
        layout_preview.addWidget(self.deskPreviewTabs)
        group_preview.setLayout(layout_preview)
        right_layout.addWidget(group_preview)
        
        # === 组合 ===
        main_layout.addLayout(left_layout, 4)
        main_layout.addLayout(right_layout, 6)
        
        # 初始状态
        self.deskGroupImport.setVisible(False)
        self.deskGroupExamroom.setVisible(False)
        self.deskBtnGroup.buttonClicked[int].connect(self.switch_desk_mode)
        
        self.tab2.setLayout(main_layout)
        
        # 初始化预览
        self.update_desk_preview()
