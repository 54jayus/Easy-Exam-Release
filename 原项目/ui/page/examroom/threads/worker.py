from PyQt5.QtCore import QThread, pyqtSignal

from ..core.arrangement import ExamArrangement


class WorkerThread(QThread):
    """工作线程，用于执行耗时操作"""

    finished = pyqtSignal(bool, str, object)  # 添加object参数用于传递结果
    progress = pyqtSignal(str)

    def __init__(self, task_type, *args):
        super().__init__()
        self.task_type = task_type
        self.args = args

    def run(self):
        try:
            if self.task_type == "arrange":
                if len(self.args) == 6:
                    file_path, max_students, total_rooms, room_setting_data, arrangement_mode, room_capacities = self.args
                elif len(self.args) == 5:
                    file_path, max_students, total_rooms, room_setting_data, arrangement_mode = self.args
                    room_capacities = None
                elif len(self.args) == 4:
                    file_path, max_students, total_rooms, room_setting_data = self.args
                    arrangement_mode = "subject_mode"  # 默认模式
                    room_capacities = None
                else:
                    file_path, max_students, total_rooms = self.args
                    room_setting_data = None
                    arrangement_mode = "subject_mode"  # 默认模式
                    room_capacities = None

                self.progress.emit("正在加载学生数据...")

                arrangement = ExamArrangement(file_path, max_students, total_rooms, room_setting_data, arrangement_mode, room_capacities)
                success, message = arrangement.load_data()
                if not success:
                    self.finished.emit(False, message, None)
                    return

                self.progress.emit("正在编排考场...")
                success, message = arrangement.arrange_exam_rooms()
                if not success:
                    self.finished.emit(False, message, None)
                    return

                # 返回编排结果而不是保存到文件
                self.finished.emit(True, message, arrangement.arranged_students)

        except FileNotFoundError as e:
            self.finished.emit(False, f"文件不存在: {str(e)}", None)
        except PermissionError as e:
            self.finished.emit(False, f"文件被占用或没有访问权限: {str(e)}", None)
        except ValueError as e:
            self.finished.emit(False, f"数据格式错误: {str(e)}", None)
        except Exception as e:
            self.finished.emit(False, f"操作失败: {str(e)}", None)
