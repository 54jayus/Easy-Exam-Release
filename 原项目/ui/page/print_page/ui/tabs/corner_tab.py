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
    QTableWidget,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtWidgets import QHeaderView


class CornerTabMixin:
    def initTab1(self):
        """初始化台角纸 Tab"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25) # 增加左右间距
        
        # === 左侧：设置区域 ===
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10) # 增加组间距
        
        # 1. 基础配置组
        group_basic = QGroupBox("基础配置")
        layout_basic = QFormLayout()
        layout_basic.setContentsMargins(15, 25, 15, 25) # 增加内部边距
        layout_basic.setVerticalSpacing(10) # 增加表单行间距
        
        self.titleEdit = QLineEdit("xxx考试台角纸")
        self.titleEdit.setMinimumHeight(32) # 增加输入框高度
        layout_basic.addRow("台角纸标题:", self.titleEdit)
        
        # 科目设置按钮
        btnSubjectConfig = QPushButton("设置考试科目")
        btnSubjectConfig.setToolTip("点击设置考试科目列表")
        btnSubjectConfig.setMinimumHeight(32) # 增加按钮高度
        layout_basic.addRow("科目管理:", btnSubjectConfig)
        btnSubjectConfig.clicked.connect(self.open_subject_config)
        
        group_basic.setLayout(layout_basic)
        left_layout.addWidget(group_basic)
        
        # 2. 数据来源组
        group_source = QGroupBox("数据来源")
        layout_source = QVBoxLayout()
        layout_source.setContentsMargins(15, 25, 15, 25) # 增加内部边距
        layout_source.setSpacing(10) # 增加内部控件间距
        
        # 模式选择
        mode_layout = QHBoxLayout()
        self.radioEmpty = QRadioButton("生成空白模板")
        self.radioImport = QRadioButton("导入考生数据")
        self.radioExamroom = QRadioButton("从考场编排导入") # New option
        self.radioEmpty.setChecked(True)
        
        self.btnGroup = QButtonGroup()
        self.btnGroup.addButton(self.radioEmpty, 0)
        self.btnGroup.addButton(self.radioImport, 1)
        self.btnGroup.addButton(self.radioExamroom, 2)
        
        mode_layout.addWidget(self.radioEmpty)
        mode_layout.addWidget(self.radioImport)
        mode_layout.addWidget(self.radioExamroom)
        mode_layout.addStretch()
        layout_source.addLayout(mode_layout)
        
        # 动态设置区域 (堆叠控件)
        self.stackSettings = QWidget()
        stackLayout = QVBoxLayout()
        stackLayout.setContentsMargins(0, 10, 0, 0)
        
        # -> 数量设置
        self.groupCount = QWidget()
        layoutCount = QHBoxLayout()
        layoutCount.addWidget(QLabel("生成数量:"))
        self.spinCount1 = QSpinBox()
        self.spinCount1.setRange(1, 50000)
        self.spinCount1.setValue(800)
        self.spinCount1.setMinimumWidth(100)
        self.spinCount1.setMinimumHeight(32) # 增加高度
        layoutCount.addWidget(self.spinCount1)
        layoutCount.addStretch()
        self.groupCount.setLayout(layoutCount)
        
        # -> 文件导入设置
        self.groupImport = QWidget()
        layoutImport = QHBoxLayout()
        self.importFileEdit = QLineEdit()
        self.importFileEdit.setPlaceholderText("请选择Excel文件")
        self.importFileEdit.setReadOnly(True)
        self.importFileEdit.setMinimumHeight(32) # 增加高度
        layoutImport.addWidget(self.importFileEdit)
        
        self.btnImportBrowse = QPushButton("浏览...")
        self.btnImportBrowse.setMinimumHeight(32) # 增加高度
        self.btnImportBrowse.clicked.connect(self.browse_import_file)
        layoutImport.addWidget(self.btnImportBrowse)
        self.groupImport.setLayout(layoutImport)
        
        # -> 考场编排导入设置 (New Group)
        self.groupExamroom = QWidget()
        layoutExamroom = QHBoxLayout()
        self.lblExamroomStatus = QLabel("未检测到编排数据")
        self.lblExamroomStatus.setStyleSheet("color: #666; font-style: italic;")
        layoutExamroom.addWidget(self.lblExamroomStatus)
        
        self.btnExamroomRefresh = QPushButton("刷新数据")
        self.btnExamroomRefresh.setMinimumHeight(32)
        self.btnExamroomRefresh.clicked.connect(self.refresh_examroom_data)
        layoutExamroom.addWidget(self.btnExamroomRefresh)
        layoutExamroom.addStretch()
        self.groupExamroom.setLayout(layoutExamroom)
        
        stackLayout.addWidget(self.groupCount)
        stackLayout.addWidget(self.groupImport)
        stackLayout.addWidget(self.groupExamroom)
        self.stackSettings.setLayout(stackLayout)
        
        layout_source.addWidget(self.stackSettings)
        group_source.setLayout(layout_source)
        left_layout.addWidget(group_source)
        
        # 3. 输出与执行组
        group_action = QGroupBox("输出与执行")
        layout_action = QVBoxLayout()
        layout_action.setContentsMargins(15, 25, 15, 25) # 增加内部边距
        layout_action.setSpacing(10) # 增加内部控件间距
        
        # 路径选择
        layout_path = QHBoxLayout()
        layout_path.addWidget(QLabel("保存路径:"))
        self.pathEdit = QLineEdit()
        self.pathEdit.setMinimumHeight(32) # 增加高度
        layout_path.addWidget(self.pathEdit)
        
        btnBrowse = QPushButton("...")
        btnBrowse.setFixedWidth(40) # 稍微加宽
        btnBrowse.setMinimumHeight(32) # 增加高度
        btnBrowse.clicked.connect(self.browse_file)
        layout_path.addWidget(btnBrowse)
        layout_action.addLayout(layout_path)
        
        layout_formats = QHBoxLayout()
        self.checkExportXLSX = QCheckBox("生成Excel")
        self.checkExportXLSX.setChecked(False)
        self.checkExportXLSX.setToolTip("勾选后生成 Excel 文件（可编辑）。")
        layout_formats.addWidget(self.checkExportXLSX)

        self.checkExportPDF = QCheckBox("生成PDF(打印推荐)")
        self.checkExportPDF.setChecked(True)
        self.checkExportPDF.setToolTip("勾选后生成 PDF 文件（打印效果更精准）。")
        layout_formats.addWidget(self.checkExportPDF)
        layout_action.addLayout(layout_formats)

        # 开始按钮
        self.btnGenerate = QPushButton("开始生成")
        self.btnGenerate.setMinimumHeight(40) # 增加高度
        self.btnGenerate.clicked.connect(self.start_generation)
        self.btnGenerate.setStyleSheet("""
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
        layout_action.addWidget(self.btnGenerate)
        
        group_action.setLayout(layout_action)
        left_layout.addWidget(group_action)
        
        left_layout.addStretch() # 底部填充
        
        # === 右侧：预览区域 ===
        right_layout = QVBoxLayout()
        group_preview = QGroupBox("模板预览")
        layout_preview = QVBoxLayout()
        
        self.tablePreview = QTableWidget()
        self.tablePreview.setFocusPolicy(Qt.NoFocus) # 去除选中虚线框
        self.tablePreview.setSelectionMode(QAbstractItemView.NoSelection) # 禁止选中
        self.tablePreview.setEditTriggers(QAbstractItemView.NoEditTriggers) # 禁止编辑
        # 隐藏表头
        self.tablePreview.verticalHeader().setVisible(False)
        self.tablePreview.horizontalHeader().setVisible(False)
        
        # 初始化预览
        # self.update_preview()
        
        # 标题变动时更新预览
        self.titleEdit.textChanged.connect(self.update_preview)
        
        layout_preview.addWidget(self.tablePreview)
        # 居中对齐
        layout_preview.setAlignment(Qt.AlignHCenter) 
        group_preview.setLayout(layout_preview)
        right_layout.addWidget(group_preview)
        
        # === 组合布局 ===
        # 设置左右比例 1:1
        main_layout.addLayout(left_layout, 4)
        main_layout.addLayout(right_layout, 6)
        
        # 初始状态
        self.groupImport.setVisible(False)
        self.groupExamroom.setVisible(False)
        
        # 绑定切换事件
        self.btnGroup.buttonClicked[int].connect(self.switch_mode)

        self.tab1.setLayout(main_layout)

        # 延迟调用 update_preview 以确保样式和布局上下文已就绪
        # 这解决了初始化时列宽和行高可能未正确应用的问题
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self.update_preview)
