import os

import pandas as pd
from PyQt5.QtCore import QEvent, QPoint, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QToolTip,
    QVBoxLayout,
    QWidget,
)

from ..core.arrangement import ExamArrangement
from ..threads.worker import WorkerThread
from .dialogs import TemplateSuccessDialog


class ExamroomPage(QWidget):
    """考场编排页面"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.student_file_path = None  # 学生名册文件路径
        self.room_setting_data = None  # 考场设置数据
        self.room_capacities = None  # 考场容量设置数据
        self.df_original = None  # 原始编排结果数据
        self.arrangement_result = None  # 编排结果
        self.init_ui()

    def init_ui(self):
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 0)

        # 创建工具栏（顶部按钮区域）
        self.create_toolbar(main_layout)

        # 创建参数设置区域
        self.create_parameter_settings(main_layout)

        # 设置参数设置区域不拉伸
        main_layout.setStretchFactor(main_layout.itemAt(main_layout.count() - 2).widget(), 0)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(20)
        main_layout.addWidget(self.progress_bar)

        # 创建结果显示区域
        self.create_result_area(main_layout)

        # 设置结果显示区域拉伸
        main_layout.setStretchFactor(main_layout.itemAt(main_layout.count() - 1).widget(), 1)

    def eventFilter(self, obj, event):
        """事件过滤器，用于自定义Tooltip位置"""
        if event.type() == QEvent.ToolTip:
            if isinstance(obj, QPushButton):
                # 获取Tooltip内容
                tooltip = obj.toolTip()
                if tooltip:
                    # 计算显示位置：按钮左下角
                    global_pos = obj.mapToGlobal(QPoint(0, obj.height()))
                    # 显示Tooltip
                    QToolTip.showText(global_pos, tooltip, obj)
                    return True  # 拦截事件，阻止默认显示
        return super().eventFilter(obj, event)

    def create_toolbar(self, parent_layout):
        """创建工具栏"""
        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(5)

        # 生成模板文件按钮
        self.template_btn = QPushButton("生成模板文件")
        self.template_btn.clicked.connect(self.generate_template)
        self.template_btn.installEventFilter(self)
        toolbar_layout.addWidget(self.template_btn)

        # 导入考场设置按钮
        self.import_room_setting_btn = QPushButton("导入考场设置")
        self.import_room_setting_btn.clicked.connect(self.import_room_setting)
        self.import_room_setting_btn.installEventFilter(self)
        toolbar_layout.addWidget(self.import_room_setting_btn)

        # 清除考场设置按钮
        self.clear_room_setting_btn = QPushButton("清除考场设置")
        self.clear_room_setting_btn.clicked.connect(self.clear_room_setting)
        self.clear_room_setting_btn.setEnabled(False)  # 初始状态为禁用
        self.clear_room_setting_btn.installEventFilter(self)
        toolbar_layout.addWidget(self.clear_room_setting_btn)

        # 导入考生名册按钮
        self.import_btn = QPushButton("导入考生名册")
        self.import_btn.clicked.connect(self.import_student_file)
        self.import_btn.setEnabled(False)  # 初始状态为禁用，需先导入考场设置
        self.import_btn.setToolTip("请先导入考场设置")
        self.import_btn.installEventFilter(self)
        toolbar_layout.addWidget(self.import_btn)

        # 开始考场编排按钮
        self.arrange_btn = QPushButton("开始考场编排")
        self.arrange_btn.clicked.connect(self.start_arrange)
        self.arrange_btn.setEnabled(False)  # 初始状态为禁用
        self.arrange_btn.setToolTip("请先导入考场设置和考生名册")
        self.arrange_btn.installEventFilter(self)
        toolbar_layout.addWidget(self.arrange_btn)

        # 导出考场编排按钮
        self.export_arrange_btn = QPushButton("导出考场编排")
        self.export_arrange_btn.clicked.connect(self.export_arrange_result)
        self.export_arrange_btn.setEnabled(False)  # 初始状态为禁用
        self.export_arrange_btn.setToolTip("请先完成考场编排")
        self.export_arrange_btn.installEventFilter(self)
        toolbar_layout.addWidget(self.export_arrange_btn)

        toolbar_layout.addStretch()
        parent_layout.addLayout(toolbar_layout)

    def create_parameter_settings(self, parent_layout):
        """创建参数设置区域"""
        param_group = QGroupBox("参数设置")
        param_layout = QHBoxLayout(param_group)
        param_layout.setSpacing(10)

        # 编排模式选择区域
        mode_setting_label = QLabel("编排模式：")
        mode_setting_label.setStyleSheet("font-weight: bold; color: #555;font-size: 16px;")
        param_layout.addWidget(mode_setting_label)

        # 编排模式下拉框
        self.mode_combo = QComboBox()
        self.mode_combo.addItem("3+1+2选科编排", "subject_mode")
        self.mode_combo.addItem("顺序编排", "normal_mode")
        self.mode_combo.addItem("随机编排", "random_mode")
        self.mode_combo.setFixedWidth(120)
        self.mode_combo.setToolTip(
            "选择编排模式：\n3+1+2选科编排 - 按照新高考选科要求进行考场分配\n顺序编排 - 直接按照考生名册顺序进行考场分配\n随机编排 - 将考生名册随机打乱后进行考场分配"
        )
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
        param_layout.addWidget(self.mode_combo)

        # 添加分隔间距
        param_layout.addSpacing(20)

        # 考场设置区域
        exam_setting_label = QLabel("考场设置：")
        exam_setting_label.setStyleSheet("font-weight: bold; color: #555;font-size: 16px;")
        param_layout.addWidget(exam_setting_label)

        # 互换位置：先考场总数，再考场人数
        param_layout.addWidget(QLabel("考场总数:"))
        self.total_rooms_spin = QSpinBox()
        self.total_rooms_spin.setRange(1, 200)
        self.total_rooms_spin.setValue(1)
        self.total_rooms_spin.setFixedWidth(50)
        self.total_rooms_spin.setEnabled(False)  # 初始禁用
        self.total_rooms_spin.setToolTip("请通过导入考场设置，设置考场总数和考场人数")
        param_layout.addWidget(self.total_rooms_spin)

        param_layout.addWidget(QLabel("考场人数:"))
        self.max_students_spin = QSpinBox()
        self.max_students_spin.setRange(0, 200)  # 允许0作为特殊值
        self.max_students_spin.setValue(42)
        self.max_students_spin.setFixedWidth(50)
        self.max_students_spin.setEnabled(False)  # 初始禁用
        self.max_students_spin.setToolTip("请通过导入考场设置，设置考场总数和考场人数")
        param_layout.addWidget(self.max_students_spin)

        # 添加分隔间距
        param_layout.addSpacing(20)

        param_layout.addStretch()
        parent_layout.addWidget(param_group)

    def create_result_area(self, parent_layout):
        """创建结果显示区域"""
        # 创建水平布局来放置表格和日志区域
        h_layout = QHBoxLayout()

        # 创建左侧表格区域的垂直布局
        table_layout = QVBoxLayout()

        # 添加筛选控件
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(5)
        filter_layout.addWidget(QLabel("筛选:"))

        # 考场号筛选
        filter_layout.addWidget(QLabel("考场号:"))
        self.room_filter = QComboBox()
        self.room_filter.addItem("全部")
        self.room_filter.currentTextChanged.connect(self.filter_table)
        filter_layout.addWidget(self.room_filter)

        # 选科筛选
        filter_layout.addWidget(QLabel("选科:"))
        self.subject_filter = QComboBox()
        self.subject_filter.addItem("全部")
        self.subject_filter.setMinimumWidth(80)  # 设置最小宽度
        self.subject_filter.setMaximumWidth(150)  # 设置最大宽度
        self.subject_filter.currentTextChanged.connect(self.filter_table)
        filter_layout.addWidget(self.subject_filter)

        # 姓名搜索
        filter_layout.addWidget(QLabel("姓名:"))
        self.name_filter = QLineEdit()
        self.name_filter.setPlaceholderText("输入姓名搜索...")
        self.name_filter.textChanged.connect(self.filter_table)
        filter_layout.addWidget(self.name_filter)

        # 清空筛选按钮
        clear_filter_btn = QPushButton("清空筛选")
        clear_filter_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_filter_btn)

        filter_layout.addStretch()
        table_layout.addLayout(filter_layout)

        # 创建表格
        self.result_table = QTableWidget()
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.result_table.setSortingEnabled(True)
        table_layout.addWidget(self.result_table)

        # 添加统计信息标签
        self.stats_label = QLabel("统计信息: 总计 0 名学生")
        self.stats_label.setStyleSheet("color: blue; font-weight: bold;")
        table_layout.addWidget(self.stats_label)

        # 将表格布局添加到水平布局
        h_layout.addLayout(table_layout)

        # 创建右侧日志区域
        self.log_text = QTextEdit()
        self.log_text.setFont(QFont("Microsoft YaHei", 10))
        self.log_text.setReadOnly(True)
        self.log_text.setFixedWidth(300)

        # 创建一个垂直布局来放置日志区域
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(0, 32, 0, 18)
        log_layout.addWidget(self.log_text)

        # 将日志布局添加到水平布局
        h_layout.addLayout(log_layout)

        # 将整个水平布局添加到父布局
        parent_layout.addLayout(h_layout)

    # 新增按钮处理方法
    def import_student_file(self):
        """导入考生名册"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择学生选科情况Excel文件", "", "Excel文件 (*.xlsx *.xls)")
        if file_path:
            try:
                # 预读取文件以显示摘要
                df = pd.read_excel(file_path, dtype={"考号": str, "班级": str, "学号": str})
                required_columns = ["班级", "学号"]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    QMessageBox.warning(self, "错误", f"考生名册缺少必需的列: {', '.join(missing_columns)}")
                    return

                student_names = df["姓名"] if "姓名" in df.columns else None
                for idx, row in df.iterrows():
                    class_value = str(row.get("班级", "")).strip()
                    student_no_value = str(row.get("学号", "")).strip()
                    name = str(student_names.iloc[idx]).strip() if student_names is not None else ""

                    if not class_value.isdigit():
                        row_desc = f"第{idx + 2}行"
                        who = f"学生{name}" if name else row_desc
                        QMessageBox.warning(self, "错误", f"{row_desc}数据，{who}的“班级”只能填写数字：{class_value}")
                        return

                    if not student_no_value.isdigit():
                        row_desc = f"第{idx + 2}行"
                        who = f"学生{name}" if name else row_desc
                        QMessageBox.warning(self, "错误", f"{row_desc}数据，{who}的“学号”只能填写数字：{student_no_value}")
                        return
                student_count = len(df)

                self.student_file_path = file_path
                self.update_button_states()

                # 优化日志显示
                log_msg = f"✅ 成功导入考生名册：{os.path.basename(file_path)}\n   - 学生总数：{student_count} 人"
                self.add_log(log_msg)
                QMessageBox.information(
                    self,
                    "成功",
                    f"成功导入考生名册：\n{os.path.basename(file_path)}\n\n学生总数：{student_count} 人",
                )

            except Exception as e:
                self.add_log(f"❌ 导入考生名册失败: {e}")
                QMessageBox.critical(self, "错误", f"读取考生名册失败: {e}")

    def import_room_setting(self):
        """导入考场设置"""
        file_path, _ = QFileDialog.getOpenFileName(self, "选择考场设置Excel文件", "", "Excel文件 (*.xlsx *.xls)")
        if file_path:
            try:
                # 读取考场设置文件，确保考场号以文本类型读入
                df = pd.read_excel(file_path, dtype={"考场号": str})

                # 检查必需的列（新增“考场人数”为必填列）
                # “考场”列为选填，如果未提供则后续会自动生成默认名称
                required_columns = ["序号", "考场号", "考场人数"]
                missing_columns = [col for col in required_columns if col not in df.columns]
                if missing_columns:
                    QMessageBox.warning(self, "错误", f"考场设置文件缺少必需的列: {', '.join(missing_columns)}")
                    return

                # 处理选填的“考场”列
                if "考场" not in df.columns:
                    # 如果未提供考场名称，默认使用 "第{考场号}考场" 格式
                    df["考场"] = df["考场号"].apply(lambda x: f"第{x}考场")

                # 验证序号列是否从1开始顺序编号
                if not df["序号"].equals(pd.Series(range(1, len(df) + 1))):
                    QMessageBox.warning(self, "错误", "序号列必须从1开始顺序编号，不能有缺失或重复")
                    return

                # 验证考场人数列（必须为正整数）
                if not pd.to_numeric(df["考场人数"], errors="coerce").notnull().all():
                    QMessageBox.warning(self, "错误", "“考场人数”列包含无效数据，必须全部为数字")
                    return
                if (df["考场人数"] <= 0).any():
                    QMessageBox.warning(self, "错误", "“考场人数”必须为正整数")
                    return

                # 存储考场设置数据
                self.room_setting_data = df.set_index("考场号")["考场"].to_dict()
                self.room_capacities = df.set_index("考场号")["考场人数"].to_dict()
                self.room_setting_df = df

                # 更新界面显示
                total_rooms = len(df)
                self.total_rooms_spin.setValue(total_rooms)

                # 检查考场人数是否统一
                unique_capacities = df["考场人数"].unique()
                if len(unique_capacities) == 1:
                    # 人数统一，显示具体数值
                    self.max_students_spin.setValue(int(unique_capacities[0]))
                    # 虽然是QLineEdit但这里为了兼容旧代码暂用setValue，后续会替换控件
                else:
                    # 人数不统一，设置一个特殊值或在UI更新中处理
                    self.max_students_spin.setValue(0)  # 0表示不统一

                # 更新按钮状态和提示
                self.import_room_setting_btn.setEnabled(False)
                self.clear_room_setting_btn.setEnabled(True)
                self.update_ui_for_imported_settings(True)

                # 优化日志显示：显示数据摘要
                log_msg = (
                    f"✅ 成功导入考场设置：{os.path.basename(file_path)}\n"
                    f"   - 考场总数：{total_rooms} 个\n"
                    f"   - 考场人数：{'统一为 ' + str(unique_capacities[0]) if len(unique_capacities) == 1 else '各考场人数不一'}\n"
                    f"   - 最小容量：{df['考场人数'].min()} 人\n"
                    f"   - 最大容量：{df['考场人数'].max()} 人\n"
                    f"   - 总容量：{df['考场人数'].sum()} 人"
                )
                self.add_log(log_msg)

                # 构建详细的成功提示信息
                success_info = (
                    f"成功导入考场设置：\n{os.path.basename(file_path)}\n\n"
                    f"考场总数：{total_rooms} 个\n"
                    f"总容量：{df['考场人数'].sum()} 人"
                )
                QMessageBox.information(self, "成功", success_info)

            except FileNotFoundError:
                QMessageBox.critical(self, "错误", f"考场设置文件不存在: {file_path}")
            except PermissionError:
                QMessageBox.critical(self, "错误", f"文件被占用或没有访问权限: {file_path}")
            except pd.errors.EmptyDataError:
                QMessageBox.critical(self, "错误", "考场设置文件为空或没有数据")
            except KeyError as e:
                QMessageBox.critical(self, "错误", f"考场设置文件缺少必需的列: {e}")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入考场设置文件失败: {str(e)}")

    def clear_room_setting(self):
        """清除考场设置"""
        reply = QMessageBox.question(
            self,
            "确认清除",
            "确定要清除当前的考场设置吗？\n\n清除后将重置考场总数为1，并允许重新导入考场设置。",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # 清除考场设置数据
            self.room_setting_data = None
            self.room_setting_df = None

            # 重置考场总数为1
            self.total_rooms_spin.setValue(1)

            # 保持考场总数控件禁用
            self.total_rooms_spin.setEnabled(False)
            self.total_rooms_spin.setToolTip("请通过导入考场设置，设置考场总数和考场人数")

            # 重置考场人数为默认值，并保持禁用
            self.max_students_spin.setValue(42)
            self.max_students_spin.setSpecialValueText("")
            self.max_students_spin.setEnabled(False)
            self.max_students_spin.setToolTip("请通过导入考场设置，设置考场总数和考场人数")

            # 更新按钮状态
            self.import_room_setting_btn.setEnabled(True)
            self.clear_room_setting_btn.setEnabled(False)
            self.update_button_states()

            # 记录日志
            self.add_log("已清除考场设置，考场总数重置为1")

    def update_room_count(self, count):
        """更新考场总数"""
        self.total_rooms_spin.setValue(count)
        self.add_log(f"考场总数已更新为: {count}")

    def update_ui_for_imported_settings(self, imported=True):
        """根据是否导入考场设置更新UI"""
        if imported:
            # 考场总数设置
            self.total_rooms_spin.setEnabled(False)
            self.total_rooms_spin.setToolTip("考场设置详见考场设置文件")

            # 考场人数设置
            self.max_students_spin.setEnabled(False)
            self.max_students_spin.setToolTip("考场设置详见考场设置文件")
            # 如果是特殊值0，显示“-”
            if self.max_students_spin.value() == 0:
                self.max_students_spin.setSpecialValueText("-")
            else:
                self.max_students_spin.setSpecialValueText("")
        else:
            # 恢复默认状态
            self.total_rooms_spin.setEnabled(False)  # 依然不允许手动修改，强制要求导入
            self.total_rooms_spin.setToolTip("请通过导入考场设置，设置考场总数和考场人数")

            self.max_students_spin.setEnabled(False)  # 依然不允许手动修改，强制要求导入
            self.max_students_spin.setToolTip("请通过导入考场设置，设置考场总数和考场人数")
            self.max_students_spin.setSpecialValueText("")

        self.update_button_states()

    def update_button_states(self):
        """更新按钮状态"""
        # 检查前置条件
        has_room_settings = hasattr(self, "room_setting_data") and self.room_setting_data is not None
        has_student_file = self.student_file_path is not None
        has_arrange_result = hasattr(self, "arrangement_result") and self.arrangement_result is not None

        # 只有导入了考场设置才能导入考生名册
        self.import_btn.setEnabled(has_room_settings)
        if not has_room_settings:
            self.import_btn.setToolTip("请先导入考场设置")
        else:
            self.import_btn.setToolTip("")

        # 只有导入了考场设置和学生名册才能开始考场编排
        can_arrange = has_room_settings and has_student_file
        self.arrange_btn.setEnabled(can_arrange)

        if not has_room_settings:
            self.arrange_btn.setToolTip("请先导入考场设置")
        elif not has_student_file:
            self.arrange_btn.setToolTip("请先导入考生名册")
        else:
            self.arrange_btn.setToolTip("")

        # 只有完成编排后才能导出结果
        self.export_arrange_btn.setEnabled(has_arrange_result)

        if not has_arrange_result:
            self.export_arrange_btn.setToolTip("请先完成考场编排")
        else:
            self.export_arrange_btn.setToolTip("")

    def export_arrange_result(self):
        """导出考场编排结果"""
        # 检查是否有编排结果
        if not hasattr(self, "arrangement_result") or self.arrangement_result is None:
            QMessageBox.warning(self, "警告", "请先进行考场编排！")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "保存考场编排结果", "考场编排结果.xlsx", "Excel文件 (*.xlsx)")
        if file_path:
            try:
                # 获取编排模式
                current_mode = self.mode_combo.currentText()
                if current_mode == "顺序编排":
                    arrangement_mode = "normal_mode"
                elif current_mode == "随机编排":
                    arrangement_mode = "random_mode"
                else:
                    arrangement_mode = "subject_mode"

                # 创建ExamArrangement实例来保存结果
                arrangement = ExamArrangement("", self.max_students_spin.value(), int(self.total_rooms_spin.text()), arrangement_mode=arrangement_mode)
                arrangement.arranged_students = self.arrangement_result

                # 传递考场设置数据到新实例
                if hasattr(self, "room_setting_data"):
                    arrangement.room_setting_data = self.room_setting_data
                if hasattr(self, "room_setting_df"):
                    arrangement.room_setting_df = self.room_setting_df
                success, message = arrangement.save_results(file_path)

                if success:
                    self.add_log(f"✅ 编排结果已导出到: {os.path.basename(file_path)}")
                    QMessageBox.information(self, "成功", f"编排结果已成功导出到:\n{file_path}")

                    # 询问是否打开文件所在文件夹
                    reply = QMessageBox.question(
                        self, "打开文件夹", "是否打开文件所在文件夹？", QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    )

                    if reply == QMessageBox.Yes:
                        # 获取文件所在文件夹路径
                        folder_path = os.path.dirname(os.path.abspath(file_path))
                        # 在Windows系统中打开文件夹
                        try:
                            os.startfile(folder_path)
                        except Exception as e:
                            self.add_log(f"❌ 打开文件夹失败: {str(e)}")
                            QMessageBox.warning(self, "警告", f"无法打开文件夹: {str(e)}")
                else:
                    self.add_log(f"❌ 导出失败: {message}")
                    QMessageBox.critical(self, "错误", f"导出失败: {message}")
            except FileNotFoundError:
                error_msg = "输出目录不存在"
                self.add_log(f"❌ {error_msg}")
                QMessageBox.critical(self, "错误", error_msg)
            except PermissionError:
                error_msg = f"文件被占用或没有写入权限: {file_path}"
                self.add_log(f"❌ {error_msg}")
                QMessageBox.critical(self, "错误", error_msg)
            except OSError as e:
                error_msg = f"磁盘空间不足或文件系统错误: {e}"
                self.add_log(f"❌ {error_msg}")
                QMessageBox.critical(self, "错误", error_msg)
            except Exception as e:
                error_msg = f"导出失败: {str(e)}"
                self.add_log(f"❌ {error_msg}")
                QMessageBox.critical(self, "错误", error_msg)

    def start_arrange(self):
        """开始考场编排"""
        if not hasattr(self, "student_file_path") or not self.student_file_path:
            QMessageBox.warning(self, "警告", "请先导入考生名册！")
            return

        # 获取参数
        students_per_room = self.max_students_spin.value()
        total_rooms = self.total_rooms_spin.value()

        # 校验考场容量是否足够
        try:
            # 读取学生名册获取学生总数
            students_df = pd.read_excel(self.student_file_path)
            total_students = len(students_df)
            total_capacity = students_per_room * total_rooms

            if total_capacity < total_students:
                reply = QMessageBox.question(
                    self,
                    "容量不足警告",
                    f"当前设置的考场容量不足！\n\n"
                    f"学生总数: {total_students} 人\n"
                    f"考场容量: {students_per_room} 人/考场 × {total_rooms} 个考场 = {total_capacity} 人\n"
                    f"缺少容量: {total_students - total_capacity} 人\n\n"
                    f"建议：\n"
                    f"• 增加考场总数至 {(total_students + students_per_room - 1) // students_per_room} 个\n"
                    f"• 或增加每考场人数至 {(total_students + total_rooms - 1) // total_rooms} 人\n\n"
                    f"是否仍要继续编排？（可能导致部分学生无法分配考场）",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )

                if reply == QMessageBox.No:
                    self.log_text.append("❌ 用户取消编排，请调整考场设置后重试")
                    return
                else:
                    self.log_text.append(f"⚠️ 警告：考场容量不足，继续编排可能导致 {total_students - total_capacity} 名学生无法分配")

        except Exception as e:
            self.log_text.append(f"⚠️ 无法验证考场容量: {e}")

        # 获取编排模式
        current_mode = self.mode_combo.currentText()
        if current_mode == "顺序编排":
            arrangement_mode = "normal_mode"
        elif current_mode == "随机编排":
            arrangement_mode = "random_mode"
        else:
            arrangement_mode = "subject_mode"

        # 创建工作线程，传递考场设置数据和编排模式
        self.worker = WorkerThread(
            "arrange",
            self.student_file_path,
            students_per_room,
            total_rooms,
            self.room_setting_data,
            arrangement_mode,
            getattr(self, "room_capacities", None),  # 传递考场容量设置
        )
        self.worker.progress.connect(self.add_log)
        self.worker.finished.connect(self.arrange_finished)

        # 开始编排
        self.arrange_btn.setEnabled(False)
        self.add_log("🚀 开始考场编排...")
        self.worker.start()

    def arrange_finished(self, success, message, arrangement_result=None):
        """考场编排完成"""
        self.arrange_btn.setEnabled(True)

        if success and arrangement_result is not None:
            self.add_log(f"✅ {message}")

            # 添加考场列
            if "考场号" in arrangement_result.columns:
                # 创建考场列
                if self.room_setting_data:
                    # 如果有考场设置，使用映射
                    arrangement_result["考场"] = arrangement_result["考场号"].map(self.room_setting_data).fillna(arrangement_result["考场号"].astype(str))
                    self.add_log("📍 已根据考场设置添加考场信息")
                else:
                    # 如果没有考场设置，考场与考场号一致
                    arrangement_result["考场"] = arrangement_result["考场号"].astype(str)
                    self.add_log("📍 考场信息与考场号一致")

                # 调整列顺序，将考场列放在考场号前面
                columns = list(arrangement_result.columns)
                if "考场" in columns:
                    columns.remove("考场")
                    room_no_index = columns.index("考场号")
                    columns.insert(room_no_index, "考场")
                    arrangement_result = arrangement_result[columns]

            # 保存编排结果到内存
            self.arrangement_result = arrangement_result
            self.df_original = arrangement_result
            self.df_filtered = self.df_original.copy()
            self.update_filter_options()
            self.display_table_data(self.df_filtered)
            # 更新按钮状态，启用导出按钮
            self.update_button_states()
            self.add_log("📊 编排结果已加载到表格，可以查看和导出")
            QMessageBox.information(self, "成功", f"{message}\n\n编排结果已显示在表格中，您可以查看结果并选择导出。")
        else:
            self.add_log(f"❌ {message}")
            QMessageBox.critical(self, "错误", message)

    def generate_template(self):
        """生成模板文件（优化版）"""
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QFont
        from PyQt5.QtWidgets import QCheckBox, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

        # 创建选择对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("生成模板文件")
        dialog.setFixedSize(400, 320)

        # 设置样式表
        dialog.setStyleSheet(
            """
            QDialog {
                background-color: #f5f7fa;
            }
            QLabel#TitleLabel {
                font-size: 16px;
                font-weight: bold;
                color: #333;
                padding-bottom: 5px;
            }
            QCheckBox {
                font-size: 14px;
                color: #555;
                spacing: 8px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QPushButton {
                border-radius: 4px;
                padding: 6px 15px;
                font-size: 14px;
            }
            QPushButton#OkButton {
                background-color: #409EFF;
                color: white;
                border: none;
            }
            QPushButton#OkButton:hover {
                background-color: #66b1ff;
            }
            QPushButton#OkButton:pressed {
                background-color: #3a8ee6;
            }
            QPushButton#CancelButton {
                background-color: #ffffff;
                color: #606266;
                border: 1px solid #dcdfe6;
            }
            QPushButton#CancelButton:hover {
                background-color: #ecf5ff;
                color: #409EFF;
                border-color: #c6e2ff;
            }
            QPushButton#CancelButton:pressed {
                background-color: #ecf5ff;
                border-color: #3a8ee6;
            }
            QFrame#ContentFrame {
                background-color: white;
                border-radius: 8px;
                border: 1px solid #ebeef5;
            }
        """
        )

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # 标题区域
        title_label = QLabel("请选择需要生成的模板文件")
        title_label.setObjectName("TitleLabel")
        layout.addWidget(title_label)

        # 内容区域（白色背景卡片）
        content_frame = QFrame()
        content_frame.setObjectName("ContentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(10)

        # 创建复选框
        examroom_checkbox = QCheckBox("考场设置模板")
        examroom_checkbox.setChecked(True)  # 默认选中
        examroom_checkbox.setToolTip("包含序号、考场号、考场名称、考场人数等设置")
        content_layout.addWidget(examroom_checkbox)

        normal_student_checkbox = QCheckBox("考生名册模板（顺序/随机编排）")
        normal_student_checkbox.setChecked(False)
        normal_student_checkbox.setToolTip("包含考号、姓名")
        content_layout.addWidget(normal_student_checkbox)

        subject_student_checkbox = QCheckBox("考生名册模板（3+1+2选科编排）")
        subject_student_checkbox.setChecked(False)
        subject_student_checkbox.setToolTip("包含考号、姓名、选科")
        content_layout.addWidget(subject_student_checkbox)

        layout.addWidget(content_frame)

        # 底部按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_button = QPushButton("取消")
        cancel_button.setObjectName("CancelButton")
        cancel_button.setCursor(Qt.PointingHandCursor)

        ok_button = QPushButton("立即生成")
        ok_button.setObjectName("OkButton")
        ok_button.setCursor(Qt.PointingHandCursor)

        ok_button.clicked.connect(dialog.accept)
        cancel_button.clicked.connect(dialog.reject)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)

        layout.addLayout(button_layout)

        # 显示对话框
        if dialog.exec_() == QDialog.Accepted:
            # 选择保存路径
            save_dir = QFileDialog.getExistingDirectory(self, "选择保存路径", "")
            if not save_dir:
                return

            generated_files = []

            try:
                # 生成考场设置模板
                if examroom_checkbox.isChecked():
                    # 获取当前设置的考场总数
                    total_rooms = self.total_rooms_spin.value()

                    examroom_template_data = {
                        "序号": list(range(1, total_rooms + 1)),
                        "考场号": [f"{i:03d}" for i in range(1, total_rooms + 1)],  # 001, 002, 003...
                        "考场": [f"第{i}考场" for i in range(1, total_rooms + 1)],
                        "考场人数": [self.max_students_spin.value()] * total_rooms,
                    }

                    df_examroom = pd.DataFrame(examroom_template_data)
                    examroom_file = "考场设置模板.xlsx"
                    examroom_path = os.path.join(save_dir, examroom_file)

                    # 使用xlsxwriter以便增加“填写说明”sheet与样式
                    with pd.ExcelWriter(examroom_path, engine="xlsxwriter") as writer:
                        df_examroom.to_excel(writer, sheet_name="Sheet1", index=False)

                        # 设置主表列宽（Sheet1）
                        wb = writer.book
                        ws = writer.sheets["Sheet1"]
                        ws.set_column(0, 0, 8)
                        ws.set_column(1, 1, 10)
                        ws.set_column(2, 2, 12)
                        ws.set_column(3, 3, 10)

                        # 说明内容，按列写一行
                        examroom_instructions = {
                            "序号": "必填。\n必须从1开始连续编号，不得缺失或重复。",
                            "考场号": "必填。\n建议为三位如001、002。",
                            "考场": "选填。\n设置考场名称，例如：高一1。",
                            "考场人数": "必填。\n正整数，表示每个考场允许的最大人数。",
                        }
                        instr_row = [{col: examroom_instructions.get(col, "") for col in df_examroom.columns}]
                        df_desc = pd.DataFrame(instr_row)
                        df_desc.to_excel(writer, sheet_name="填写说明", index=False)

                        desc_ws = writer.sheets["填写说明"]
                        wrap_left = wb.add_format({"text_wrap": True, "align": "left", "valign": "top"})
                        required_cell = wb.add_format({"text_wrap": True, "align": "left", "valign": "top", "bg_color": "#FFC7CE"})

                        # 与主表一致的列宽
                        desc_ws.set_column(0, 0, 8, wrap_left)
                        desc_ws.set_column(1, 1, 10, wrap_left)
                        desc_ws.set_column(2, 2, 12, wrap_left)
                        desc_ws.set_column(3, 3, 10, wrap_left)

                        # 必填列红底：序号、考场号、考场人数
                        required_cols = {"序号", "考场号", "考场人数"}
                        for idx, col in enumerate(df_examroom.columns):
                            text = examroom_instructions.get(col, "")
                            if col in required_cols:
                                desc_ws.write(1, idx, text, required_cell)
                            else:
                                desc_ws.write(1, idx, text, wrap_left)
                        desc_ws.set_row(1, 100)

                        # 列标题样式
                        required_header = wb.add_format(
                            {"text_wrap": True, "align": "center", "valign": "vcenter", "bg_color": "#FFC7CE", "bold": True, "border": 1}
                        )
                        normal_header = wb.add_format({"text_wrap": True, "align": "center", "valign": "vcenter", "bold": 1, "border": 1})
                        for idx, col in enumerate(df_examroom.columns):
                            fmt = required_header if col in required_cols else normal_header
                            desc_ws.write(0, idx, col, fmt)

                    generated_files.append(examroom_file)
                    self.add_log(f"✅ 考场设置模板文件已生成: {examroom_path}")

                # 生成考生名册模板（顺序编排、随机编排）
                if normal_student_checkbox.isChecked():
                    normal_student_template_data = {
                        "班级": ["1", "1", "1", "1", "1"],
                        "学号": ["1", "2", "3", "4", "5"],
                        "考号": ["240001", "240002", "240003", "240004", "240005"],
                        "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
                    }

                    df_normal_student = pd.DataFrame(normal_student_template_data)
                    normal_student_file = "考生名册模板（顺序编排、随机编排）.xlsx"
                    normal_student_path = os.path.join(save_dir, normal_student_file)

                    with pd.ExcelWriter(normal_student_path, engine="xlsxwriter") as writer:
                        df_normal_student.to_excel(writer, sheet_name="Sheet1", index=False)

                        wb = writer.book
                        ws = writer.sheets["Sheet1"]
                        ws.set_column(0, 0, 10)
                        ws.set_column(1, 1, 10)
                        ws.set_column(2, 2, 15)
                        ws.set_column(3, 3, 15)

                        # 说明内容
                        normal_instructions = {
                            "班级": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                            "学号": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                            "考号": "必填。\n不允许重复。",
                            "姓名": "必填。\n示例：张三。",
                        }
                        instr_row = [{col: normal_instructions.get(col, "") for col in df_normal_student.columns}]
                        df_desc = pd.DataFrame(instr_row)
                        df_desc.to_excel(writer, sheet_name="填写说明", index=False)

                        desc_ws = writer.sheets["填写说明"]
                        wrap_left = wb.add_format({"text_wrap": True, "align": "left", "valign": "top"})
                        required_cell = wb.add_format({"text_wrap": True, "align": "left", "valign": "top", "bg_color": "#FFC7CE"})
                        desc_ws.set_column(0, 0, 10, wrap_left)
                        desc_ws.set_column(1, 1, 10, wrap_left)
                        desc_ws.set_column(2, 2, 15, wrap_left)
                        desc_ws.set_column(3, 3, 15, wrap_left)

                        required_cols = {"班级", "学号", "考号", "姓名"}
                        for idx, col in enumerate(df_normal_student.columns):
                            text = normal_instructions.get(col, "")
                            desc_ws.write(1, idx, text, required_cell if col in required_cols else wrap_left)
                        desc_ws.set_row(1, 100)

                        required_header = wb.add_format(
                            {"text_wrap": True, "align": "center", "valign": "vcenter", "bg_color": "#FFC7CE", "bold": True, "border": 1}
                        )
                        for idx, col in enumerate(df_normal_student.columns):
                            desc_ws.write(0, idx, col, required_header)

                    generated_files.append(normal_student_file)
                    self.add_log(f"✅ {normal_student_file}已生成: {normal_student_path}")

                # 生成考生名册模板（3+1+2选科编排）
                if subject_student_checkbox.isChecked():
                    subject_student_template_data = {
                        "班级": ["1", "1", "1", "1", "1"],
                        "学号": ["1", "2", "3", "4", "5"],
                        "考号": ["240001", "240002", "240003", "240004", "240005"],
                        "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
                        "选科": ["物化生", "物化地", "史政地", "史化生", "物生地"],
                    }

                    df_subject_student = pd.DataFrame(subject_student_template_data)
                    subject_student_file = "考生名册模板（3+1+2选科编排）.xlsx"
                    subject_student_path = os.path.join(save_dir, subject_student_file)

                    with pd.ExcelWriter(subject_student_path, engine="xlsxwriter") as writer:
                        df_subject_student.to_excel(writer, sheet_name="Sheet1", index=False)

                        wb = writer.book
                        ws = writer.sheets["Sheet1"]
                        ws.set_column(0, 0, 10)
                        ws.set_column(1, 1, 10)
                        ws.set_column(2, 2, 15)
                        ws.set_column(3, 3, 15)
                        ws.set_column(4, 4, 25)

                        # 说明内容
                        subject_instructions = {
                            "班级": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                            "学号": "必填。\n仅允许数字（不允许字母/符号/小数）。\n示例：1",
                            "考号": "必填。\n不允许重复。",
                            "姓名": "必填。\n示例：张三。",
                            "选科": "必填。\n支持缩写（如：物化生/史政地）或全称+分隔符。例如：\n物理+化学+生物\n历史,政治,地理\n物理 化学 生物。",
                        }
                        instr_row = [{col: subject_instructions.get(col, "") for col in df_subject_student.columns}]
                        df_desc = pd.DataFrame(instr_row)
                        df_desc.to_excel(writer, sheet_name="填写说明", index=False)

                        desc_ws = writer.sheets["填写说明"]
                        wrap_left = wb.add_format({"text_wrap": True, "align": "left", "valign": "top"})
                        required_cell = wb.add_format({"text_wrap": True, "align": "left", "valign": "top", "bg_color": "#FFC7CE"})
                        desc_ws.set_column(0, 0, 10, wrap_left)
                        desc_ws.set_column(1, 1, 10, wrap_left)
                        desc_ws.set_column(2, 2, 15, wrap_left)
                        desc_ws.set_column(3, 3, 15, wrap_left)
                        desc_ws.set_column(4, 4, 25, wrap_left)

                        required_cols = {"班级", "学号", "考号", "姓名", "选科"}
                        for idx, col in enumerate(df_subject_student.columns):
                            text = subject_instructions.get(col, "")
                            desc_ws.write(1, idx, text, required_cell if col in required_cols else wrap_left)
                        desc_ws.set_row(1, 120)

                        required_header = wb.add_format(
                            {"text_wrap": True, "align": "center", "valign": "vcenter", "bg_color": "#FFC7CE", "bold": True, "border": 1}
                        )
                        for idx, col in enumerate(df_subject_student.columns):
                            desc_ws.write(0, idx, col, required_header)

                    generated_files.append(subject_student_file)
                    self.add_log(f"✅ {subject_student_file}已生成: {subject_student_path}")

                if generated_files:
                    # 构建HTML内容
                    html_content = "<h3>已生成以下文件：</h3><ul>"
                    for file in generated_files:
                        html_content += f"<li>{file}</li>"
                    html_content += "</ul><hr>"

                    html_content += "<h3>模板包含列说明：</h3>"

                    if "考场设置模板.xlsx" in generated_files:
                        html_content += "<p><b>考场设置模板</b>：<br>序号、考场号、考场、考场人数</p>"

                    if "考生名册模板（顺序编排、随机编排）.xlsx" in generated_files:
                        html_content += "<p><b>考生名册模板（顺序编排、随机编排）</b>：<br>班级、学号、考号、姓名</p>"

                    if "考生名册模板（3+1+2选科编排）.xlsx" in generated_files:
                        html_content += "<p><b>考生名册模板（3+1+2选科编排）</b>：<br>班级、学号、考号、姓名、选科</p>"

                    # 显示自定义对话框
                    folder_path = save_dir
                    success_dialog = TemplateSuccessDialog(self, generated_files, html_content, folder_path)
                    success_dialog.exec_()
                else:
                    QMessageBox.warning(self, "提示", "请至少选择一个模板文件进行生成！")

            except PermissionError as e:
                error_msg = f"没有写入权限: {str(e)}"
                self.add_log(f"❌ {error_msg}")
                QMessageBox.critical(self, "错误", error_msg)
            except OSError as e:
                error_msg = f"磁盘空间不足或文件系统错误: {e}"
                self.add_log(f"❌ {error_msg}")
                QMessageBox.critical(self, "错误", error_msg)
            except Exception as e:
                error_msg = f"生成模板文件失败: {str(e)}"
                self.add_log(f"❌ {error_msg}")
                QMessageBox.critical(self, "错误", error_msg)

    def add_log(self, message):
        """添加带时间戳的日志"""
        from datetime import datetime

        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_text.append(f"{timestamp} {message}")

        """更新筛选选项"""
        if not hasattr(self, "df_original") or self.df_original is None:
            return

        # 更新考场号筛选
        self.room_filter.clear()
        self.room_filter.addItem("全部")

        # 优先使用考场设置中的原始考场号，以保持格式一致（如"001"）
        if hasattr(self, "room_setting_data") and self.room_setting_data:
            # 获取考场设置中的所有考场号，并按数字大小排序
            # room_setting_data 是 {room_num: room_name}
            room_nums = list(self.room_setting_data.keys())

            # 尝试按数字排序但保留原始字符串格式
            try:
                # 创建 (数字值, 原始字符串) 的元组列表进行排序
                sorted_rooms = sorted([(int(r) if str(r).isdigit() else float("inf"), str(r)) for r in room_nums], key=lambda x: x[0])
                rooms = [r[1] for r in sorted_rooms if r[0] != float("inf")]
                # 把非数字的考场号加在后面
                rooms.extend([r[1] for r in sorted_rooms if r[0] == float("inf")])
            except Exception:
                # 排序失败则按字符串排序
                rooms = sorted([str(r) for r in room_nums])

            for room in rooms:
                self.room_filter.addItem(str(room))

        elif "考场号" in self.df_original.columns:
            # 如果没有考场设置，则从数据中提取
            # 过滤掉空值，并按数字排序
            rooms = self.df_original["考场号"].dropna().unique()
            try:
                # 尝试按数字排序
                rooms = sorted([str(room).strip() for room in rooms if str(room).strip()], key=lambda x: int(x) if x.isdigit() else float("inf"))
                for room in rooms:
                    self.room_filter.addItem(room)
            except (ValueError, TypeError):
                # 如果无法转换为数字，则按字符串排序
                rooms = sorted([str(room).strip() for room in rooms if str(room).strip()])
                for room in rooms:
                    self.room_filter.addItem(room)

        # 更新选科筛选
        self.subject_filter.clear()
        self.subject_filter.addItem("全部")
        if "选科" in self.df_original.columns:
            # 过滤掉空值和空字符串
            subjects = self.df_original["选科"].dropna().unique()
            subjects = sorted([str(subject).strip() for subject in subjects if str(subject).strip()])
            for subject in subjects:
                self.subject_filter.addItem(subject)

    def update_filter_options(self):
        """更新筛选选项"""
        if not hasattr(self, "df_original") or self.df_original is None:
            return

        # 更新考场号筛选
        self.room_filter.clear()
        self.room_filter.addItem("全部")

        # 优先使用考场设置中的原始考场号，以保持格式一致（如"001"）
        if hasattr(self, "room_setting_data") and self.room_setting_data:
            # 获取考场设置中的所有考场号，并按数字大小排序
            # room_setting_data 是 {room_num: room_name}
            room_nums = list(self.room_setting_data.keys())

            # 尝试按数字排序但保留原始字符串格式
            try:
                # 创建 (数字值, 原始字符串) 的元组列表进行排序
                sorted_rooms = sorted([(int(r) if str(r).isdigit() else float("inf"), str(r)) for r in room_nums], key=lambda x: x[0])
                rooms = [r[1] for r in sorted_rooms if r[0] != float("inf")]
                # 把非数字的考场号加在后面
                rooms.extend([r[1] for r in sorted_rooms if r[0] == float("inf")])
            except Exception:
                # 排序失败则按字符串排序
                rooms = sorted([str(r) for r in room_nums])

            for room in rooms:
                self.room_filter.addItem(str(room))

        elif "考场号" in self.df_original.columns:
            # 如果没有考场设置，则从数据中提取
            # 过滤掉空值，并按数字排序
            rooms = self.df_original["考场号"].dropna().unique()
            try:
                # 尝试按数字排序
                rooms = sorted([str(room).strip() for room in rooms if str(room).strip()], key=lambda x: int(x) if x.isdigit() else float("inf"))
                for room in rooms:
                    self.room_filter.addItem(room)
            except (ValueError, TypeError):
                # 如果无法转换为数字，则按字符串排序
                rooms = sorted([str(room).strip() for room in rooms if str(room).strip()])
                for room in rooms:
                    self.room_filter.addItem(room)

        # 更新选科筛选
        self.subject_filter.clear()
        self.subject_filter.addItem("全部")
        if "选科" in self.df_original.columns:
            # 过滤掉空值和空字符串
            subjects = self.df_original["选科"].dropna().unique()
            subjects = sorted([str(subject).strip() for subject in subjects if str(subject).strip()])
            for subject in subjects:
                self.subject_filter.addItem(subject)

    def display_table_data(self, df):
        """显示表格数据"""
        # 暂停表格更新以提高性能
        self.result_table.setUpdatesEnabled(False)
        self.result_table.clearContents()

        try:
            # 根据编排模式决定显示的列
            current_mode = self.mode_combo.currentText()
            if current_mode == "顺序编排":
                arrangement_mode = "normal_mode"
            elif current_mode == "随机编排":
                arrangement_mode = "random_mode"
            else:
                arrangement_mode = "subject_mode"

            # 按照导出Excel的完全相同顺序排列列
            display_columns = []

            if arrangement_mode == "normal_mode" or arrangement_mode == "random_mode":
                # 顺序模式和随机模式：不显示选科相关列
                normal_order = ["班级", "学号", "姓名", "考号", "考场", "考场号", "座位号"]
            else:
                # 3+1+2模式：显示所有列
                normal_order = ["班级", "学号", "姓名", "考号", "选科", "首选", "选科1", "选科2", "考场", "考场号", "座位号", "考场选科组合"]

            # 添加存在的列，保持原始顺序
            for col in normal_order:
                if col in df.columns:
                    display_columns.append(col)

            # 添加其他未包含的列（排除序号列和选科相关列）
            for col in df.columns:
                if col not in display_columns and col != "序号":
                    # 普通模式下过滤掉选科相关列
                    if arrangement_mode in ["normal_mode", "random_mode"] and col in ["选科", "考场选科组合", "首选", "选科1", "选科2"]:
                        continue
                    display_columns.append(col)

            # 重新排列DataFrame列顺序
            df_display = df[display_columns]

            # 设置表格行列数
            rows = len(df_display)
            cols = len(df_display.columns)
            self.result_table.setRowCount(rows)
            self.result_table.setColumnCount(cols)

            # 设置表头
            self.result_table.setHorizontalHeaderLabels(df_display.columns.tolist())

            # 显示行号（表格自带的序号列）
            self.result_table.setVerticalHeaderLabels([str(i + 1) for i in range(rows)])

            # 设置垂直表头（行号列）的固定宽度和居中对齐
            vertical_header = self.result_table.verticalHeader()
            vertical_header.setFixedWidth(40)
            vertical_header.setVisible(True)
            vertical_header.setDefaultAlignment(Qt.AlignCenter)

            # 性能优化：限制最大显示行数，避免大量数据导致卡顿
            # 如果数据量超过2000行，只显示前2000行，并提示
            MAX_DISPLAY_ROWS = 2000
            display_rows = min(rows, MAX_DISPLAY_ROWS)

            # 填充数据并设置居中对齐
            # 预先将数据转换为字符串矩阵，减少iloc调用的开销
            data_values = df_display.iloc[:display_rows].astype(str).values

            for row in range(display_rows):
                for col in range(cols):
                    item = QTableWidgetItem(data_values[row][col])
                    # 设置文本水平居中
                    item.setTextAlignment(Qt.AlignCenter)
                    self.result_table.setItem(row, col, item)

            if rows > MAX_DISPLAY_ROWS:
                self.stats_label.setText(self.stats_label.text() + f" (仅显示前{MAX_DISPLAY_ROWS}行，请导出查看完整数据)")

            # 设置所有列自适应内容（仅对显示的列进行一次调整）
            header = self.result_table.horizontalHeader()
            # 批量设置模式比循环设置更快
            header.setSectionResizeMode(QHeaderView.ResizeToContents)

            # 更新统计信息
            self.update_stats(df_display)

        finally:
            # 恢复表格更新
            self.result_table.setUpdatesEnabled(True)

    def update_stats(self, df):
        """更新统计信息"""
        total_students = len(df)
        if "考场号" in df.columns:
            total_rooms = df["考场号"].nunique()

            # 检查是否为3+1+2选科编排模式
            current_mode = self.mode_combo.currentData()
            # 只有在3+1+2模式且有原始编排数据时才显示详细统计
            if current_mode == "subject_mode" and hasattr(self, "df_original") and self.df_original is not None:
                original_df = self.df_original
                if "选科" in original_df.columns and "考场号" in original_df.columns:
                    try:
                        # 统计每个考场的选科组合数量
                        room_subjects = original_df.groupby("考场号")["选科"].nunique()

                        single_subject_rooms = (room_subjects == 1).sum()
                        mixed_subject_rooms = (room_subjects > 1).sum()

                        self.stats_label.setText(
                            f"统计信息: 总计 {total_students} 名学生，{total_rooms} 个考场 (单一考场: {single_subject_rooms}，混合考场: {mixed_subject_rooms})"
                        )
                        return
                    except Exception as e:
                        # 如果统计出错，回退到普通显示
                        print(f"统计出错: {e}")

            self.stats_label.setText(f"统计信息: 总计 {total_students} 名学生，{total_rooms} 个考场")
        else:
            self.stats_label.setText(f"统计信息: 总计 {total_students} 名学生")

    def filter_table(self):
        """筛选表格数据"""
        if not hasattr(self, "df_original") or self.df_original is None:
            return

        # 始终从原始数据开始筛选，避免重复筛选导致数据丢失
        df = self.df_original.copy()

        # 考场号筛选 - 使用精确匹配以尊重用户选择的格式
        room_filter = self.room_filter.currentText()
        if room_filter != "全部" and "考场号" in df.columns:
            # 直接使用字符串精确匹配，不去除前导零
            # 这样如果用户选"001"，就只匹配"001"，不会匹配"1"
            # 前提是表格中的数据格式也需要保持一致（这在arrange_finished中已经处理了）
            df = df[df["考场号"].astype(str).str.strip() == room_filter.strip()]

        # 选科筛选 - 使用精确匹配
        subject_filter = self.subject_filter.currentText()
        if subject_filter != "全部" and "选科" in df.columns:
            df = df[df["选科"].astype(str).str.strip() == subject_filter.strip()]

        # 姓名搜索 - 使用模糊匹配
        name_filter = self.name_filter.text().strip()
        if name_filter and "姓名" in df.columns:
            df = df[df["姓名"].astype(str).str.contains(name_filter, case=False, na=False)]

        self.df_filtered = df
        self.display_table_data(df)

    def clear_filters(self):
        """清空所有筛选"""
        self.room_filter.setCurrentText("全部")
        self.subject_filter.setCurrentText("全部")
        self.name_filter.clear()

        if hasattr(self, "df_original") and self.df_original is not None:
            self.df_filtered = self.df_original.copy()
            self.display_table_data(self.df_filtered)

    def on_mode_changed(self):
        """编排模式切换处理"""
        current_mode = self.mode_combo.currentData()
        if current_mode == "normal_mode":
            # 顺序编排模式
            self.add_log("切换到顺序编排模式 - 按考生名册顺序分配考场")
            # 隐藏选科相关的筛选控件
            self.subject_filter.setVisible(False)
            # 找到选科筛选标签并隐藏
            for i in range(self.subject_filter.parent().layout().count()):
                item = self.subject_filter.parent().layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QLabel):
                    if item.widget().text() == "选科:":
                        item.widget().setVisible(False)
                        break
        else:
            # 3+1+2选科编排模式
            self.add_log("切换到3+1+2选科编排模式 - 按新高考选科要求分配考场")
            # 显示选科相关的筛选控件
            self.subject_filter.setVisible(True)
            # 找到选科筛选标签并显示
            for i in range(self.subject_filter.parent().layout().count()):
                item = self.subject_filter.parent().layout().itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QLabel):
                    if item.widget().text() == "选科:":
                        item.widget().setVisible(True)
                        break

        # 如果已有编排结果，提示需要重新编排
        if hasattr(self, "arrangement_result") and self.arrangement_result is not None:
            self.add_log("模式已切换，如需使用新模式请重新进行考场编排")
