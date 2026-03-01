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


class TicketTabMixin:
    def initTab3(self):
        """初始化准考证 Tab"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)
        
        # === 左侧：设置区域 ===
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        
        # 1. 基础配置组
        group_basic = QGroupBox("基础配置")
        layout_basic = QFormLayout()
        layout_basic.setContentsMargins(15, 25, 15, 25)
        layout_basic.setVerticalSpacing(10)
        
        self.ticketTitleEdit = QLineEdit("xxx考试准考证")
        self.ticketTitleEdit.setMinimumHeight(32)
        layout_basic.addRow("准考证标题:", self.ticketTitleEdit)
        
        # 科目设置按钮 (复用逻辑)
        btnSubjectConfig = QPushButton("设置考试科目")
        btnSubjectConfig.setToolTip("点击设置考试科目列表")
        btnSubjectConfig.setMinimumHeight(32)
        layout_basic.addRow("科目管理:", btnSubjectConfig)
        btnSubjectConfig.clicked.connect(self.open_subject_config_ticket)
        
        group_basic.setLayout(layout_basic)
        left_layout.addWidget(group_basic)
        
        # 2. 数据来源组
        group_source = QGroupBox("数据来源")
        layout_source = QVBoxLayout()
        layout_source.setContentsMargins(15, 25, 15, 25)
        layout_source.setSpacing(10)
        
        # 模式选择
        mode_layout = QHBoxLayout()
        self.ticketRadioEmpty = QRadioButton("生成空白模板")
        self.ticketRadioImport = QRadioButton("导入考生数据")
        self.ticketRadioExamroom = QRadioButton("从考场编排导入") # New option
        self.ticketRadioEmpty.setChecked(True)
        
        self.ticketBtnGroup = QButtonGroup()
        self.ticketBtnGroup.addButton(self.ticketRadioEmpty, 0)
        self.ticketBtnGroup.addButton(self.ticketRadioImport, 1)
        self.ticketBtnGroup.addButton(self.ticketRadioExamroom, 2)
        
        mode_layout.addWidget(self.ticketRadioEmpty)
        mode_layout.addWidget(self.ticketRadioImport)
        mode_layout.addWidget(self.ticketRadioExamroom)
        mode_layout.addStretch()
        layout_source.addLayout(mode_layout)
        
        # 动态设置区域 (堆叠控件)
        self.ticketStackSettings = QWidget()
        stackLayout = QVBoxLayout()
        stackLayout.setContentsMargins(0, 10, 0, 0)
        
        # -> 数量设置
        self.ticketGroupCount = QWidget()
        layoutCount = QHBoxLayout()
        layoutCount.addWidget(QLabel("生成数量:"))
        self.ticketSpinCount = QSpinBox()
        self.ticketSpinCount.setRange(1, 50000)
        self.ticketSpinCount.setValue(800)
        self.ticketSpinCount.setMinimumWidth(100)
        self.ticketSpinCount.setMinimumHeight(32)
        layoutCount.addWidget(self.ticketSpinCount)
        layoutCount.addStretch()
        self.ticketGroupCount.setLayout(layoutCount)
        
        # -> 文件导入设置
        self.ticketGroupImport = QWidget()
        layoutImport = QHBoxLayout()
        self.ticketImportFileEdit = QLineEdit()
        self.ticketImportFileEdit.setPlaceholderText("请选择Excel文件")
        self.ticketImportFileEdit.setReadOnly(True)
        self.ticketImportFileEdit.setMinimumHeight(32)
        layoutImport.addWidget(self.ticketImportFileEdit)
        
        self.ticketBtnImportBrowse = QPushButton("浏览...")
        self.ticketBtnImportBrowse.setMinimumHeight(32)
        self.ticketBtnImportBrowse.clicked.connect(self.browse_ticket_import_file)
        layoutImport.addWidget(self.ticketBtnImportBrowse)
        self.ticketGroupImport.setLayout(layoutImport)
        
        # -> 考场编排导入设置 (New Group for Ticket)
        self.ticketGroupExamroom = QWidget()
        layoutExamroomTicket = QHBoxLayout()
        self.lblTicketExamroomStatus = QLabel("未检测到编排数据")
        self.lblTicketExamroomStatus.setStyleSheet("color: #666; font-style: italic;")
        layoutExamroomTicket.addWidget(self.lblTicketExamroomStatus)
        
        self.btnTicketExamroomRefresh = QPushButton("刷新数据")
        self.btnTicketExamroomRefresh.setMinimumHeight(32)
        self.btnTicketExamroomRefresh.clicked.connect(self.refresh_examroom_data)
        layoutExamroomTicket.addWidget(self.btnTicketExamroomRefresh)
        layoutExamroomTicket.addStretch()
        self.ticketGroupExamroom.setLayout(layoutExamroomTicket)
        
        stackLayout.addWidget(self.ticketGroupCount)
        stackLayout.addWidget(self.ticketGroupImport)
        stackLayout.addWidget(self.ticketGroupExamroom)
        self.ticketStackSettings.setLayout(stackLayout)
        
        layout_source.addWidget(self.ticketStackSettings)
        group_source.setLayout(layout_source)
        left_layout.addWidget(group_source)
        
        # 3. 输出与执行组
        group_action = QGroupBox("输出与执行")
        layout_action = QVBoxLayout()
        layout_action.setContentsMargins(15, 25, 15, 25)
        layout_action.setSpacing(10)
        
        # 路径选择
        layout_path = QHBoxLayout()
        layout_path.addWidget(QLabel("保存路径:"))
        self.ticketPathEdit = QLineEdit()
        self.ticketPathEdit.setMinimumHeight(32)
        layout_path.addWidget(self.ticketPathEdit)
        
        btnBrowse = QPushButton("...")
        btnBrowse.setFixedWidth(40)
        btnBrowse.setMinimumHeight(32)
        btnBrowse.clicked.connect(self.browse_ticket_file)
        layout_path.addWidget(btnBrowse)
        layout_action.addLayout(layout_path)
        
        layout_formats = QHBoxLayout()
        self.ticketCheckExportXLSX = QCheckBox("生成Excel")
        self.ticketCheckExportXLSX.setChecked(False)
        self.ticketCheckExportXLSX.setToolTip("勾选后生成 Excel 文件（可编辑）。")
        layout_formats.addWidget(self.ticketCheckExportXLSX)

        self.ticketCheckExportPDF = QCheckBox("生成PDF(打印推荐)")
        self.ticketCheckExportPDF.setChecked(True)
        self.ticketCheckExportPDF.setToolTip("勾选后生成 PDF 文件（打印效果更精准）。")
        layout_formats.addWidget(self.ticketCheckExportPDF)
        layout_action.addLayout(layout_formats)

        # 开始按钮
        self.ticketBtnGenerate = QPushButton("开始生成")
        self.ticketBtnGenerate.setMinimumHeight(40)
        self.ticketBtnGenerate.clicked.connect(self.start_generation)
        self.ticketBtnGenerate.setStyleSheet("""
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
        layout_action.addWidget(self.ticketBtnGenerate)
        
        group_action.setLayout(layout_action)
        left_layout.addWidget(group_action)
        
        left_layout.addStretch()
        
        # === 右侧：预览区域 ===
        right_layout = QVBoxLayout()
        group_preview = QGroupBox("模板预览")
        layout_preview = QVBoxLayout()
        
        self.ticketTablePreview = QTableWidget()
        self.ticketTablePreview.setFocusPolicy(Qt.NoFocus)
        self.ticketTablePreview.setSelectionMode(QAbstractItemView.NoSelection)
        self.ticketTablePreview.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.ticketTablePreview.verticalHeader().setVisible(False)
        self.ticketTablePreview.horizontalHeader().setVisible(False)
        
        # 标题变动时更新预览
        self.ticketTitleEdit.textChanged.connect(self.update_ticket_preview)
        
        layout_preview.addWidget(self.ticketTablePreview)
        layout_preview.setAlignment(Qt.AlignHCenter)
        group_preview.setLayout(layout_preview)
        right_layout.addWidget(group_preview)
        
        # === 组合布局 ===
        main_layout.addLayout(left_layout, 4)
        main_layout.addLayout(right_layout, 6)
        
        # 初始状态
        self.ticketGroupImport.setVisible(False)
        self.ticketGroupExamroom.setVisible(False)
        
        self.ticketBtnGroup.buttonClicked[int].connect(self.switch_ticket_mode)
        
        self.tab3.setLayout(main_layout)
        
        # 延迟更新预览
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(0, self.update_ticket_preview)
