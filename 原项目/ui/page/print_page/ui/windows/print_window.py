import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QSpinBox, QLineEdit, QPushButton, 
                             QProgressBar, QFileDialog, QMessageBox, QTextEdit,
                             QTabWidget, QFormLayout, QRadioButton, QButtonGroup, 
                             QDialog, QGroupBox, QTableWidget, 
                             QAbstractItemView, QCheckBox)
from PyQt5.QtCore import Qt, QSize
from ..services.print_job_builder import BuildCancelled, BuildError, build_config_for_current_tab
from ..services.desk_preview_builder import build_desk_preview_payload
from ..services.examroom_status_service import get_examroom_status
from ..services.table_preview_builder import build_corner_table_preview, build_ticket_table_preview, build_student_info_table_preview
from ..services.import_flow import load_desk_import
from ..threads import GeneratorThread
from ...core.config import AdmissionTicketConfig, CornerPaperConfig, DeskLabelConfig
from ...core.adapters.examroom_adapter import check_examroom_data, load_examroom_data_for_student_info
from ...core.utils.data_loader import DataLoader
from ..dialogs.column_mapping_dialog import ColumnMappingDialog
from ..dialogs.student_info_mapping_dialog import StudentInfoColumnMappingDialog
from ..dialogs.layout_settings_dialog import LayoutSettingsDialog
from ..dialogs.subject_config_dialog import SubjectConfigDialog
from ..tabs import CornerTabMixin, DeskTabMixin, TicketTabMixin, StudentInfoTabMixin


class MainWindow(CornerTabMixin, DeskTabMixin, TicketTabMixin, StudentInfoTabMixin, QWidget):
    def __init__(self, subject_page=None, examroom_page=None):
        super().__init__()
        self.subject_page = subject_page
        self.examroom_page = examroom_page
        self._generation_in_progress = False
        self._student_info_titles = {
            "class": "xxx考试座位安排-班级",
            "examroom": "xxx考试座位安排-考场",
        }
        self._student_info_last_mode = "class"
        self.studentInfo_mapping = None
        self.studentInfo_cached_data = None
        self.studentInfo_include_subject_fields = False
        # 默认科目 (8个空字符串)
        self.subjects = [''] * 8
        self.subject_times = [''] * 8
        self.initUI()

    def initUI(self):
        

        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)

        # 1. 标签页控件
        self.tabs = QTabWidget()
        self.tab1 = QWidget() # 台角纸
        self.tab2 = QWidget() # 桌角纸
        self.tab3 = QWidget() # 准考证
        self.tab4 = QWidget() # 考生信息表
        
        self.tabs.addTab(self.tab2, "桌角纸生成")
        self.tabs.addTab(self.tab1, "台角纸生成")
        self.tabs.addTab(self.tab3, "准考证生成")
        self.tabs.addTab(self.tab4, "考生信息表生成")
        
        self.initTab1()
        self.initTab2()
        self.initTab3()
        self.initTab4()
        
        # 切换Tab时自动更新默认文件名 (Moved after init to ensure attributes exist)
        self.tabs.currentChanged.connect(self.update_default_path)
        
        # 设置伸缩因子，让上半部分占据更多空间 (3:1)
        main_layout.addWidget(self.tabs, 3)

        # 2. 公共区域 (保存路径、按钮、日志)
        common_layout = QVBoxLayout()
        
        # 进度条 (Move up)
        self.progressBar = QProgressBar()
        self.progressBar.setAlignment(Qt.AlignCenter)
        common_layout.addWidget(self.progressBar)

        # 日志区 (Move down)
        lbl_log = QLabel("运行日志:")
        common_layout.addWidget(lbl_log)
        self.logText = QTextEdit()
        self.logText.setReadOnly(True)
        # self.logText.setMaximumHeight(100) # Removed maximum height to fill space
        self.logText.setStyleSheet("background-color: #f0f0f0; border: 1px solid #ccc;")
        common_layout.addWidget(self.logText)

        main_layout.addLayout(common_layout, 1)
        self.setLayout(main_layout)
        
        # 初始化默认路径 (需要在所有 Tab 初始化完成后调用)
        self.update_default_path()
        self._student_info_last_mode = self._student_info_group_mode()

    def switch_mode(self, mode_id):
        # 0: Empty, 1: Import, 2: Examroom
        self.groupCount.setVisible(mode_id == 0)
        self.groupImport.setVisible(mode_id == 1)
        self.groupExamroom.setVisible(mode_id == 2)
        
        if mode_id == 2:
            self.refresh_examroom_data()

    def open_subject_config(self):
        # 仅传递 subjects，times 留空或默认
        dialog = SubjectConfigDialog(subjects=self.subjects, parent=self, subject_source=self.subject_page)
        if dialog.exec_() == QDialog.Accepted:
            self.subjects = dialog.get_subjects()
            # 同时也更新时间（虽然台角纸不用，但保持同步）
            self.subject_times = dialog.get_times()
            # 可以在这里打印日志或者提示用户科目已更新
            self.log(f"科目已更新，共 {len(self.subjects)} 个科目")
            self.update_preview()
            self.update_ticket_preview() # 同步更新准考证预览

    def update_preview(self):
        build_corner_table_preview(self.tablePreview, self.titleEdit.text(), self.subjects)

    def browse_import_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "选择数据文件", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if fileName:
            self.importFileEdit.setText(fileName)

    def switch_desk_mode(self, mode_id):
        self.deskGroupCount.setVisible(mode_id == 0)
        self.deskGroupImport.setVisible(mode_id == 1)
        self.deskGroupExamroom.setVisible(mode_id == 2)
        if mode_id == 2:
            self.refresh_examroom_data()
        self.update_desk_preview() # 切换模式时更新预览

    def open_layout_settings(self):
        dialog = LayoutSettingsDialog(
            current_layout_name=self.desk_layout_name, 
            current_pattern=getattr(self, 'desk_layout_pattern', "S型横排"),
            current_custom_counts=getattr(self, 'desk_layout_custom_counts', None),
            current_start_pos=getattr(self, 'desk_layout_start_pos', "left"),
            parent=self
        )
        if dialog.exec_() == QDialog.Accepted:
            name, rows, cols, capacity, pattern, custom_counts, start_pos = dialog.get_layout()
            self.desk_layout_name = name
            self.desk_layout_rows = rows
            self.desk_layout_cols = cols
            self.desk_layout_capacity = capacity
            self.desk_layout_pattern = pattern
            self.desk_layout_custom_counts = custom_counts
            self.desk_layout_start_pos = start_pos
            
            start_pos_text = "左手位" if start_pos == "left" else "右手位"
            self.lblCurrentLayout.setText(f"当前设置: {name} | {pattern} | {start_pos_text}")
            self.update_desk_preview()

    def update_desk_preview(self):
        """
        更新桌角纸预览图
        根据当前选择的模式（空白/导入/编排）展示不同内容
        """
        # 1. 确定布局参数
        rows = self.desk_layout_rows
        cols = self.desk_layout_cols
        pattern = getattr(self, 'desk_layout_pattern', "S型横排")
        custom_counts = getattr(self, 'desk_layout_custom_counts', None)
        start_pos = getattr(self, 'desk_layout_start_pos', "left")
        
        # 2. 确定数据来源
        # 0: Empty, 1: Import, 2: Examroom
        mode = self.deskBtnGroup.checkedId()
        room_data_list, student_info_map = build_desk_preview_payload(
            mode,
            getattr(self, "desk_cached_data", None),
            self.examroom_page,
        )
        
        # 3. 更新预览控件
        # Tab 1: Layout
        self.deskLayoutPreview.set_layout_params(rows, cols, pattern, custom_counts, start_pos)
        if hasattr(self.deskLayoutPreview, 'set_seat_data'):
            self.deskLayoutPreview.set_seat_data(student_info_map)
            
        # Tab 2: Content
        self.deskContentPreview.set_data(rows, cols, start_pos, room_data_list)

    def browse_desk_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "保存文件", self.deskPathEdit.text(), "输出文件 (*.xlsx *.pdf);;All Files (*)", options=options)
        if fileName:
            self.deskPathEdit.setText(self._strip_output_ext(fileName))

    def browse_desk_import_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "选择数据文件", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if fileName:
            # 立即校验数据
            try:
                def mapping_provider(headers):
                    dialog = ColumnMappingDialog(headers, self)
                    if dialog.exec_() != QDialog.Accepted:
                        return None
                    return dialog.get_mapping()

                mapping, data_list, sort_result = load_desk_import(fileName, mapping_provider)
                if not mapping:
                    return

                is_sorted, msg = sort_result

                if is_sorted:
                    self.desk_mapping = mapping
                    self.desk_cached_data = data_list
                    self.deskImportFileEdit.setText(fileName)
                    QMessageBox.information(self, "导入成功", f"成功读取 {len(data_list)} 条数据。\n{msg}")
                else:
                    QMessageBox.warning(self, "数据异常", f"读取了 {len(data_list)} 条数据，但发现排序问题：\n{msg}\n\n建议重新排序后再导入。")
                    self.deskImportFileEdit.clear()
                    self.desk_cached_data = None # 清除无效数据

                # 更新预览
                self.update_desk_preview()
                    
            except Exception as e:
                QMessageBox.critical(self, "导入失败", str(e))
                self.deskImportFileEdit.clear()

    def switch_ticket_mode(self, mode_id):
        # 0: Empty, 1: Import, 2: Examroom
        self.ticketGroupCount.setVisible(mode_id == 0)
        self.ticketGroupImport.setVisible(mode_id == 1)
        self.ticketGroupExamroom.setVisible(mode_id == 2)
        
        if mode_id == 2:
            self.refresh_examroom_data()
        
    def open_subject_config_ticket(self):
        # 传递 subjects 和 times
        dialog = SubjectConfigDialog(subjects=self.subjects, times=self.subject_times, parent=self, subject_source=self.subject_page)
        if dialog.exec_() == QDialog.Accepted:
            self.subjects = dialog.get_subjects()
            self.subject_times = dialog.get_times()
            self.log(f"科目已更新，共 {len(self.subjects)} 个科目")
            self.update_ticket_preview()
            self.update_preview() # 同时也更新台角纸预览

    def update_ticket_preview(self):
        build_ticket_table_preview(
            self.ticketTablePreview,
            self.ticketTitleEdit.text(),
            self.subjects,
            self.subject_times,
        )
            

    def refresh_examroom_data(self):
        """刷新并显示考场编排数据状态"""
        status_text, color = get_examroom_status(self.examroom_page)
            
        # Update Tab 1 UI
        self.lblExamroomStatus.setText(status_text)
        self.lblExamroomStatus.setStyleSheet(f"color: {color}; font-style: italic;")

                # Update Tab 2 UI (Desk)
        self.lblDeskExamroomStatus.setText(status_text)
        self.lblDeskExamroomStatus.setStyleSheet(f"color: {color}; font-style: italic;")

        # Update Tab 3 UI
        self.lblTicketExamroomStatus.setText(status_text)
        self.lblTicketExamroomStatus.setStyleSheet(f"color: {color}; font-style: italic;")

        if hasattr(self, "lblStudentInfoExamroomStatus"):
            self.lblStudentInfoExamroomStatus.setText(status_text)
            self.lblStudentInfoExamroomStatus.setStyleSheet(f"color: {color}; font-style: italic;")
        
        # 尝试更新桌角纸预览（如果当前处于桌角纸页面且选中了编排模式，或者为了保持一致性直接更新）
        self.update_desk_preview()
        if hasattr(self, "update_student_info_preview"):
            self.update_student_info_preview()

    def browse_ticket_import_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "选择数据文件", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if fileName:
            self.ticketImportFileEdit.setText(fileName)

    def browse_ticket_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "保存文件", self.ticketPathEdit.text(), "输出文件 (*.xlsx *.pdf);;All Files (*)", options=options)
        if fileName:
            self.ticketPathEdit.setText(self._strip_output_ext(fileName))

    def browse_student_info_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "保存文件", self.studentInfoPathEdit.text(), "输出文件 (*.xlsx *.pdf);;All Files (*)", options=options)
        if fileName:
            self.studentInfoPathEdit.setText(self._strip_output_ext(fileName))

    def update_default_path(self):
        """根据当前 Tab 更新默认文件名"""
        idx = self.tabs.currentIndex()
        cwd = os.getcwd()
        if idx == 0:
            name = "桌角纸_批量生成"
            self.deskPathEdit.setText(os.path.join(cwd, name))
        elif idx == 1:
            name = "台角纸_批量生成"
            self.pathEdit.setText(os.path.join(cwd, name))
        elif idx == 2:
            name = "准考证_批量生成"
            self.ticketPathEdit.setText(os.path.join(cwd, name))
        elif idx == 3:
            self._apply_student_info_default_path(cwd=cwd)

    def _student_info_group_mode(self):
        if hasattr(self, "studentInfoPreviewTabs") and self.studentInfoPreviewTabs.currentIndex() == 1:
            return "examroom"
        return "class"

    def _student_info_default_title(self, group_mode):
        return "xxx考试座位安排-考场" if group_mode == "examroom" else "xxx考试座位安排-班级"

    def _student_info_default_basename(self, group_mode):
        return "考生信息表（考场）_批量生成" if group_mode == "examroom" else "考生信息表（班级）_批量生成"

    def _apply_student_info_default_title(self):
        if not hasattr(self, "studentInfoTitleEdit"):
            return
        group_mode = self._student_info_group_mode()
        desired = self._student_info_default_title(group_mode)
        current = (self.studentInfoTitleEdit.text() or "").strip()
        if current == "" or current in {"座位安排-班级", "座位安排-考场", "xxx考试座位安排-班级", "xxx考试座位安排-考场"}:
            self.studentInfoTitleEdit.setText(desired)

    def _apply_student_info_default_path(self, cwd=None):
        if not hasattr(self, "studentInfoPathEdit"):
            return
        group_mode = self._student_info_group_mode()
        desired_base = self._student_info_default_basename(group_mode)
        known_bases = {
            "考生信息表_批量生成",
            "考生信息表（班级）_批量生成",
            "考生信息表（考场）_批量生成",
        }
        current = (self.studentInfoPathEdit.text() or "").strip()
        if cwd is None:
            cwd = os.getcwd()
        dir_path = cwd if not current else (os.path.dirname(current) or cwd)
        if (not current) or (os.path.basename(current) in known_bases):
            self.studentInfoPathEdit.setText(os.path.join(dir_path, desired_base))

    def on_student_info_preview_tab_changed(self, _index):
        if hasattr(self, "tabs") and self.tabs.currentIndex() != 3:
            return
        if not hasattr(self, "studentInfoTitleEdit"):
            return

        prev_mode = getattr(self, "_student_info_last_mode", None) or "class"
        prev_title = (self.studentInfoTitleEdit.text() or "").strip()
        if prev_title != "":
            self._student_info_titles[prev_mode] = prev_title

        new_mode = self._student_info_group_mode()
        self._student_info_last_mode = new_mode

        desired = (self._student_info_titles.get(new_mode) or "").strip()
        if desired == "":
            desired = self._student_info_default_title(new_mode)
            self._student_info_titles[new_mode] = desired

        if (self.studentInfoTitleEdit.text() or "").strip() != desired:
            self.studentInfoTitleEdit.setText(desired)

        self._apply_student_info_default_path()

    def _strip_output_ext(self, path):
        lower = path.lower()
        if lower.endswith(".xlsx"):
            return path[:-5]
        if lower.endswith(".pdf"):
            return path[:-4]
        return path

    def browse_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "保存文件", self.pathEdit.text(), "输出文件 (*.xlsx *.pdf);;All Files (*)", options=options)
        if fileName:
            self.pathEdit.setText(self._strip_output_ext(fileName))

    def log(self, message):
        self.logText.append(message)
        cursor = self.logText.textCursor()
        cursor.movePosition(cursor.End)
        self.logText.setTextCursor(cursor)

    def start_generation(self):
        if getattr(self, "_generation_in_progress", False):
            return
        self._generation_in_progress = True

        def mapping_provider(headers):
            dialog = ColumnMappingDialog(headers, self)
            if dialog.exec_() != QDialog.Accepted:
                return None
            return dialog.get_mapping()

        def confirm(kind, title, message):
            if kind == "warning":
                res = QMessageBox.warning(self, title, message, QMessageBox.Yes | QMessageBox.No)
                return res == QMessageBox.Yes
            res = QMessageBox.question(self, title, message, QMessageBox.Yes | QMessageBox.No)
            return res == QMessageBox.Yes

        try:
            config = build_config_for_current_tab(
                self,
                mapping_provider=mapping_provider,
                confirm=confirm,
                log=self.log,
            )
        except BuildCancelled:
            self._generation_in_progress = False
            return
        except BuildError as e:
            if e.level == "critical":
                QMessageBox.critical(self, e.title, e.message)
            else:
                QMessageBox.warning(self, e.title, e.message)
            self._generation_in_progress = False
            return
        except Exception as e:
            self._generation_in_progress = False
            QMessageBox.critical(self, "生成失败", str(e))
            return

        if not config:
            self._generation_in_progress = False
            return

        # 锁定 UI
        self.set_ui_enabled(False)
        self.progressBar.setValue(0)
        self.logText.clear()
        
        if (isinstance(config, CornerPaperConfig) or isinstance(config, AdmissionTicketConfig) or isinstance(config, DeskLabelConfig)) and config.student_data_list:
             self.log(f"准备生成 {len(config.student_data_list)} 个模板...")

        # 启动线程
        self.thread = GeneratorThread(config)
        self.thread.progress.connect(self.progressBar.setValue)
        self.thread.log.connect(self.log)
        self.thread.finished.connect(self.on_finished)
        self.thread.error.connect(self.on_error)
        self.thread.start()

    def on_finished(self, path):
        self.set_ui_enabled(True)
        self._generation_in_progress = False
        reply = QMessageBox.question(self, "成功", f"生成成功！\n文件路径: {path}\n\n是否打开所在文件夹？", 
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        
        if reply == QMessageBox.Yes:
            try:
                subprocess_cmd = f'explorer /select,"{os.path.normpath(path)}"'
                os.system(subprocess_cmd)
            except:
                pass

    def on_error(self, err_msg):
        self.set_ui_enabled(True)
        self._generation_in_progress = False
        self.progressBar.setValue(0) # 重置进度条
        
        # 优化 Permission denied 提示
        if "Permission denied" in err_msg:
            err_msg = f"文件被占用，请关闭文件后重试！\n详细错误: {err_msg}"
            
        self.log(f"错误: {err_msg}")
        QMessageBox.critical(self, "生成失败", err_msg)

    def set_ui_enabled(self, enabled):
        self.btnGenerate.setEnabled(enabled)
        self.deskBtnGenerate.setEnabled(enabled) # Disable Desk button too
        self.ticketBtnGenerate.setEnabled(enabled)
        if hasattr(self, "studentInfoBtnGenerate"):
            self.studentInfoBtnGenerate.setEnabled(enabled)
        self.pathEdit.setEnabled(enabled)
        self.deskPathEdit.setEnabled(enabled)
        self.ticketPathEdit.setEnabled(enabled)
        if hasattr(self, "studentInfoPathEdit"):
            self.studentInfoPathEdit.setEnabled(enabled)
        self.tabs.setEnabled(enabled)

    def browse_student_info_import_file(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "选择数据文件", "", "Excel Files (*.xlsx);;All Files (*)", options=options)
        if fileName:
            try:
                headers = DataLoader.get_headers(fileName)
                if not headers:
                    raise Exception("文件为空或无法读取表头")

                dialog = StudentInfoColumnMappingDialog(headers, self)
                if dialog.exec_() != QDialog.Accepted:
                    return

                mapping = dialog.get_mapping()
                data_list = DataLoader.load_student_info_data(fileName, mapping)
                include_subject_fields = all(k in mapping for k in ["首选", "选科1", "选科2"])

                self.studentInfo_mapping = mapping
                self.studentInfo_cached_data = data_list
                self.studentInfo_include_subject_fields = include_subject_fields
                self.studentInfoImportFileEdit.setText(fileName)
                QMessageBox.information(self, "导入成功", f"成功读取 {len(data_list)} 条数据。")
                self.update_student_info_preview()
            except Exception as e:
                QMessageBox.critical(self, "导入失败", str(e))
                self.studentInfoImportFileEdit.clear()
                self.studentInfo_mapping = None
                self.studentInfo_cached_data = None
                self.studentInfo_include_subject_fields = False

    def switch_student_info_mode(self, mode_id):
        self.studentInfoGroupEmpty.setVisible(mode_id == 0)
        self.studentInfoGroupImport.setVisible(mode_id == 1)
        self.studentInfoGroupExamroom.setVisible(mode_id == 2)
        if mode_id == 2:
            self.refresh_examroom_data()
        self.update_student_info_preview()

    def update_student_info_preview(self):
        title = self.studentInfoTitleEdit.text() if hasattr(self, "studentInfoTitleEdit") else ""
        include_subject_fields = False
        sample_row = {
            "考生姓名": "张三",
            "考生考号": "2410010615",
            "班级": "5",
            "学号": "16",
            "考场": "高二1班",
            "考场号": "001",
            "座位号": "01",
        }
        if include_subject_fields:
            sample_row = {**sample_row, "首选": "", "选科1": "", "选科2": ""}

        def parse_int(v):
            s = str(v).strip()
            if s.isdigit():
                return (0, int(s))
            return (1, s)

        if hasattr(self, "studentInfoRadioImport") and self.studentInfoRadioImport.isChecked():
            include_subject_fields = bool(getattr(self, "studentInfo_include_subject_fields", False))
            data_list = getattr(self, "studentInfo_cached_data", None) or []

        elif hasattr(self, "studentInfoRadioExamroom") and self.studentInfoRadioExamroom.isChecked():
            df = check_examroom_data(self.examroom_page)
            if df is not None and hasattr(self.examroom_page, "mode_combo"):
                include_subject_fields = self.examroom_page.mode_combo.currentData() == "subject_mode"
                include_subject_fields = include_subject_fields and all(c in df.columns for c in ["首选", "选科1", "选科2"])

            data_list = load_examroom_data_for_student_info(df, include_subject_fields=include_subject_fields) or []
        else:
            data_list = []

        if include_subject_fields:
            sample_row = {**sample_row, "首选": "", "选科1": "", "选科2": ""}

        by_class = {}
        by_examroom = {}
        for item in data_list:
            c = str(item.get("班级", "")).strip()
            rno = str(item.get("考场号", "")).strip()
            by_class.setdefault(c, []).append(item)
            by_examroom.setdefault(rno, []).append(item)

        if by_class:
            class_name = sorted(by_class.keys(), key=lambda x: parse_int(x))[0]
            class_rows = by_class[class_name]
        else:
            class_name = str(sample_row.get("班级", "示例")).strip() or "示例"
            class_rows = [sample_row]

        def examroom_key(v):
            s = str(v).strip()
            if s == "":
                return (2, "")
            return parse_int(s)

        if by_examroom:
            examroom_no = sorted(by_examroom.keys(), key=examroom_key)[0]
            examroom_rows = by_examroom[examroom_no]
            examroom_label = str((examroom_rows[0] or {}).get("考场", "")).strip() or examroom_no or "考场"
        else:
            examroom_label = str(sample_row.get("考场", "")).strip() or str(sample_row.get("考场号", "")).strip() or "考场"
            examroom_rows = [sample_row]

        build_student_info_table_preview(
            self.studentInfoTablePreviewClass,
            title,
            class_name,
            class_rows,
            include_subject_fields=include_subject_fields,
            sort_mode="class",
        )
        build_student_info_table_preview(
            self.studentInfoTablePreviewExamroom,
            title,
            examroom_label,
            examroom_rows,
            include_subject_fields=include_subject_fields,
            sort_mode="examroom",
        )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())
