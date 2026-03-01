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
    QTabWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)


class StudentInfoTabMixin:
    def initTab4(self):
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(25)

        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)

        group_basic = QGroupBox("基础配置")
        layout_basic = QFormLayout()
        layout_basic.setContentsMargins(15, 25, 15, 25)
        layout_basic.setVerticalSpacing(10)

        self.studentInfoTitleEdit = QLineEdit("xxx考试座位安排-班级")
        self.studentInfoTitleEdit.setMinimumHeight(32)
        layout_basic.addRow("表格标题:", self.studentInfoTitleEdit)

        group_basic.setLayout(layout_basic)
        left_layout.addWidget(group_basic)

        group_source = QGroupBox("数据来源")
        layout_source = QVBoxLayout()
        layout_source.setContentsMargins(15, 25, 15, 25)
        layout_source.setSpacing(10)

        mode_layout = QHBoxLayout()
        self.studentInfoRadioEmpty = QRadioButton("生成空白模板")
        self.studentInfoRadioImport = QRadioButton("导入考生数据")
        self.studentInfoRadioExamroom = QRadioButton("从考场编排导入")
        self.studentInfoRadioEmpty.setChecked(True)

        self.studentInfoBtnGroup = QButtonGroup()
        self.studentInfoBtnGroup.addButton(self.studentInfoRadioEmpty, 0)
        self.studentInfoBtnGroup.addButton(self.studentInfoRadioImport, 1)
        self.studentInfoBtnGroup.addButton(self.studentInfoRadioExamroom, 2)

        mode_layout.addWidget(self.studentInfoRadioEmpty)
        mode_layout.addWidget(self.studentInfoRadioImport)
        mode_layout.addWidget(self.studentInfoRadioExamroom)
        mode_layout.addStretch()
        layout_source.addLayout(mode_layout)

        self.studentInfoStackSettings = QWidget()
        stack_layout = QVBoxLayout()
        stack_layout.setContentsMargins(0, 10, 0, 0)

        self.studentInfoGroupEmpty = QWidget()
        layout_empty = QHBoxLayout()
        layout_empty.addWidget(QLabel("将生成空白表格模板"))
        layout_empty.addStretch()
        self.studentInfoGroupEmpty.setLayout(layout_empty)

        self.studentInfoGroupImport = QWidget()
        layout_import = QHBoxLayout()
        self.studentInfoImportFileEdit = QLineEdit()
        self.studentInfoImportFileEdit.setPlaceholderText("请选择Excel文件")
        self.studentInfoImportFileEdit.setReadOnly(True)
        self.studentInfoImportFileEdit.setMinimumHeight(32)
        layout_import.addWidget(self.studentInfoImportFileEdit)

        self.studentInfoBtnImportBrowse = QPushButton("浏览...")
        self.studentInfoBtnImportBrowse.setMinimumHeight(32)
        self.studentInfoBtnImportBrowse.clicked.connect(self.browse_student_info_import_file)
        layout_import.addWidget(self.studentInfoBtnImportBrowse)
        self.studentInfoGroupImport.setLayout(layout_import)

        self.studentInfoGroupExamroom = QWidget()
        layout_examroom = QHBoxLayout()
        self.lblStudentInfoExamroomStatus = QLabel("未检测到编排数据")
        self.lblStudentInfoExamroomStatus.setStyleSheet("color: #666; font-style: italic;")
        layout_examroom.addWidget(self.lblStudentInfoExamroomStatus)

        self.btnStudentInfoExamroomRefresh = QPushButton("刷新数据")
        self.btnStudentInfoExamroomRefresh.setMinimumHeight(32)
        self.btnStudentInfoExamroomRefresh.clicked.connect(self.refresh_examroom_data)
        layout_examroom.addWidget(self.btnStudentInfoExamroomRefresh)
        layout_examroom.addStretch()
        self.studentInfoGroupExamroom.setLayout(layout_examroom)

        stack_layout.addWidget(self.studentInfoGroupEmpty)
        stack_layout.addWidget(self.studentInfoGroupImport)
        stack_layout.addWidget(self.studentInfoGroupExamroom)
        self.studentInfoStackSettings.setLayout(stack_layout)
        layout_source.addWidget(self.studentInfoStackSettings)
        group_source.setLayout(layout_source)
        left_layout.addWidget(group_source)

        group_action = QGroupBox("输出与执行")
        layout_action = QVBoxLayout()
        layout_action.setContentsMargins(15, 25, 15, 25)
        layout_action.setSpacing(10)

        layout_path = QHBoxLayout()
        layout_path.addWidget(QLabel("保存路径:"))
        self.studentInfoPathEdit = QLineEdit()
        self.studentInfoPathEdit.setMinimumHeight(32)
        layout_path.addWidget(self.studentInfoPathEdit)

        btn_browse = QPushButton("...")
        btn_browse.setFixedWidth(40)
        btn_browse.setMinimumHeight(32)
        btn_browse.clicked.connect(self.browse_student_info_file)
        layout_path.addWidget(btn_browse)
        layout_action.addLayout(layout_path)

        layout_formats = QHBoxLayout()
        self.studentInfoCheckExportXLSX = QCheckBox("生成Excel")
        self.studentInfoCheckExportXLSX.setChecked(False)
        self.studentInfoCheckExportXLSX.setToolTip("勾选后生成 Excel 文件（可编辑）。")
        layout_formats.addWidget(self.studentInfoCheckExportXLSX)

        self.studentInfoCheckExportPDF = QCheckBox("生成PDF(打印推荐)")
        self.studentInfoCheckExportPDF.setChecked(True)
        self.studentInfoCheckExportPDF.setToolTip("勾选后生成 PDF 文件（适合打印）。")
        layout_formats.addWidget(self.studentInfoCheckExportPDF)

        layout_formats.addStretch()
        layout_action.addLayout(layout_formats)

        self.studentInfoBtnGenerate = QPushButton("开始生成")
        self.studentInfoBtnGenerate.setMinimumHeight(40)
        self.studentInfoBtnGenerate.clicked.connect(self.start_generation)
        self.studentInfoBtnGenerate.setStyleSheet(
            """
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
        """
        )
        layout_action.addWidget(self.studentInfoBtnGenerate)

        group_action.setLayout(layout_action)
        left_layout.addWidget(group_action)
        left_layout.addStretch()

        right_layout = QVBoxLayout()
        group_preview = QGroupBox("模板预览")
        layout_preview = QVBoxLayout()
        layout_preview.setContentsMargins(9, 9, 9, 9)
        layout_preview.setSpacing(6)

        self.studentInfoPreviewTabs = QTabWidget()

        self.studentInfoTablePreviewClass = QTableWidget()
        self.studentInfoTablePreviewClass.setFocusPolicy(Qt.NoFocus)
        self.studentInfoTablePreviewClass.setSelectionMode(QAbstractItemView.NoSelection)
        self.studentInfoTablePreviewClass.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.studentInfoTablePreviewClass.verticalHeader().setVisible(False)
        self.studentInfoTablePreviewClass.horizontalHeader().setVisible(False)
        self.studentInfoPreviewPageClass = QWidget()
        self.studentInfoPreviewPageClassLayout = QVBoxLayout(self.studentInfoPreviewPageClass)
        self.studentInfoPreviewPageClassLayout.setContentsMargins(0, 0, 0, 0)
        self.studentInfoPreviewPageClassLayout.setSpacing(0)
        self.studentInfoPreviewPageClassLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.studentInfoPreviewPageClassLayout.addWidget(self.studentInfoTablePreviewClass)
        self.studentInfoPreviewTabs.addTab(self.studentInfoPreviewPageClass, "班级")

        self.studentInfoTablePreviewExamroom = QTableWidget()
        self.studentInfoTablePreviewExamroom.setFocusPolicy(Qt.NoFocus)
        self.studentInfoTablePreviewExamroom.setSelectionMode(QAbstractItemView.NoSelection)
        self.studentInfoTablePreviewExamroom.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.studentInfoTablePreviewExamroom.verticalHeader().setVisible(False)
        self.studentInfoTablePreviewExamroom.horizontalHeader().setVisible(False)
        self.studentInfoPreviewPageExamroom = QWidget()
        self.studentInfoPreviewPageExamroomLayout = QVBoxLayout(self.studentInfoPreviewPageExamroom)
        self.studentInfoPreviewPageExamroomLayout.setContentsMargins(0, 0, 0, 0)
        self.studentInfoPreviewPageExamroomLayout.setSpacing(0)
        self.studentInfoPreviewPageExamroomLayout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.studentInfoPreviewPageExamroomLayout.addWidget(self.studentInfoTablePreviewExamroom)
        self.studentInfoPreviewTabs.addTab(self.studentInfoPreviewPageExamroom, "考场")

        layout_preview.addWidget(self.studentInfoPreviewTabs)
        group_preview.setLayout(layout_preview)
        right_layout.addWidget(group_preview)

        main_layout.addLayout(left_layout, 4)
        main_layout.addLayout(right_layout, 6)

        self.studentInfoGroupImport.setVisible(False)
        self.studentInfoGroupExamroom.setVisible(False)

        self.studentInfoBtnGroup.buttonClicked[int].connect(self.switch_student_info_mode)
        self.studentInfoTitleEdit.textChanged.connect(self.update_student_info_preview)
        self.studentInfoPreviewTabs.currentChanged.connect(self.on_student_info_preview_tab_changed)

        self.tab4.setLayout(main_layout)

        from PyQt5.QtCore import QTimer

        QTimer.singleShot(0, self.update_student_info_preview)
