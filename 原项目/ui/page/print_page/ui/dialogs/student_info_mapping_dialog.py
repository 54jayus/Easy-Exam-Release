from PyQt5.QtWidgets import (
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)


class StudentInfoColumnMappingDialog(QDialog):
    REQUIRED_FIELDS = [
        "考场",
        "考场号",
        "座位号",
        "考生姓名",
        "考生考号",
        "班级",
        "学号",
    ]

    SUBJECT_FIELDS = ["首选", "选科1", "选科2"]

    def __init__(self, excel_headers, parent=None):
        super().__init__(parent)
        self.excel_headers = excel_headers
        self.mapping = {}
        self.initUI()
        self.auto_match()

    def initUI(self):
        self.setWindowTitle("导入数据列映射")
        self.resize(420, 420)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("请为以下字段选择对应的Excel列："))

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

        layout.addWidget(QLabel("3+1+2 选科字段（可选，需同时设置）:"))

        subject_form = QFormLayout()
        for field in self.SUBJECT_FIELDS:
            combo = QComboBox()
            combo.addItem("-- 不导入 --", None)
            for header in self.excel_headers:
                combo.addItem(str(header), header)
            self.combos[field] = combo
            subject_form.addRow(f"{field}:", combo)
        layout.addLayout(subject_form)

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
        synonyms = {
            "考生考号": ["考号", "考生号", "考生考号", "准考证号"],
            "考生姓名": ["姓名", "考生姓名", "学生姓名"],
            "考场": ["考场", "考室"],
            "考场号": ["考场号", "考室号"],
            "座位号": ["座位号", "座号"],
            "班级": ["班级", "班"],
            "学号": ["学号"],
            "首选": ["首选", "类别", "科类"],
            "选科1": ["选科1", "选1", "选科一"],
            "选科2": ["选科2", "选2", "选科二"],
        }

        for field, combo in self.combos.items():
            if field in self.excel_headers:
                index = combo.findText(field)
                if index >= 0:
                    combo.setCurrentIndex(index)
                    continue

            potential_matches = synonyms.get(field, [])
            for match in potential_matches:
                if match in self.excel_headers:
                    index = combo.findText(match)
                    if index >= 0:
                        combo.setCurrentIndex(index)
                        break

    def validate_and_accept(self):
        self.mapping = {}
        missing_fields = []

        for field in self.REQUIRED_FIELDS:
            combo = self.combos[field]
            selected_header = combo.currentData()
            if not selected_header:
                missing_fields.append(field)
            else:
                self.mapping[field] = selected_header

        if missing_fields:
            QMessageBox.warning(self, "映射不完整", f"请为以下字段选择对应的列：\n{', '.join(missing_fields)}")
            return

        subject_selected = {f: self.combos[f].currentData() for f in self.SUBJECT_FIELDS}
        picked = [f for f, v in subject_selected.items() if v]
        if picked and len(picked) != len(self.SUBJECT_FIELDS):
            QMessageBox.warning(self, "映射不完整", "“首选、选科1、选科2”需要同时设置或同时不设置。")
            return

        for f, v in subject_selected.items():
            if v:
                self.mapping[f] = v

        self.accept()

    def get_mapping(self):
        return self.mapping

