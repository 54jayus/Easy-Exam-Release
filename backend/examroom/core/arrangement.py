import os
import random

import pandas as pd

from .stats_sheet import create_stats_sheet_with_formulas
from .helpers import (
    format_subject_time,
    get_gaokao_time_settings,
    get_room_capacity,
    get_room_name,
    get_subject_order,
    parse_subject_combination,
    validate_column_data,
    validate_subject_column,
)
from .gaokao_helpers import (
    arrange_gaokao_mode,
    arrange_elective_exam,
    arrange_unified_exams,
    extract_subject_from_combination,
    fill_rooms_sequential,
    get_room_list,
    shuffle_students,
)
from .gaokao_exports import (
    export_gaokao_seat_tables,
    export_gaokao_stats_table,
    export_gaokao_student_table,
    export_gaokao_timeslot_tables,
    merge_gaokao_results,
    save_gaokao_results,
)
from .sequential_strategy import arrange_sequential
from .subject_strategy import (
    arrange_subject_mode as arrange_subject_mode_strategy,
    assign_large_groups,
    assign_remaining_students,
    generate_results,
    get_room_category,
    group_and_sort_subjects,
    initialize_rooms,
    sort_students_by_subject_count,
)
from .standard_exports import save_results as save_standard_results


class ExamArrangement:
    """考场编排类"""

    def __init__(
        self,
        file_path,
        max_students_per_room=42,
        total_rooms=20,
        room_setting_data=None,
        arrangement_mode="subject_mode",
        room_capacities=None,
    ):
        self.file_path = file_path
        self.max_students_per_room = max_students_per_room
        self.total_rooms = total_rooms
        self.room_setting_data = room_setting_data  # 考场设置数据
        self.arrangement_mode = arrangement_mode  # 编排模式
        self.room_capacities = room_capacities or {}  # 考场容量设置 {room_num: capacity}
        self.students = None
        self.arranged_students = None
        self.subject_column = "选科"  # 用户指定的选科列名
        self.gaokao_results = None  # 高考模式编排结果
        self.gaokao_time_settings = None  # 高考模式时间设置

    def get_room_capacity(self, room_num):
        return get_room_capacity(self, room_num)

    def load_data(self):
        """加载学生数据"""
        try:
            self.students = pd.read_excel(self.file_path, dtype={"考号": str, "班级": str, "学号": str})
            return True, f"成功加载数据，共{len(self.students)}名学生"
        except FileNotFoundError:
            return False, f"文件不存在: {self.file_path}"
        except PermissionError:
            return False, f"文件被占用或没有访问权限: {self.file_path}"
        except pd.errors.EmptyDataError:
            return False, "Excel文件为空或没有数据"
        except pd.errors.ParserError:
            return False, "Excel文件格式错误，无法解析"
        except ValueError as e:
            return False, f"数据格式错误: {e}"
        except Exception as e:
            return False, f"加载数据失败: {e}"

    def check_required_columns(self):
        """检查是否包含必要的列"""
        if self.arrangement_mode == "normal_mode" or self.arrangement_mode == "random_mode":
            required_columns = ["班级", "学号", "考号", "姓名"]
        else:
            # subject_mode 和 gaokao_mode 都需要选科列
            required_columns = ["班级", "学号", "考号", "姓名", self.subject_column]

        missing_columns = [col for col in required_columns if col not in self.students.columns]

        if missing_columns:
            return False, f"缺少必要的列: {', '.join(missing_columns)}"

        def digit_custom_validator_factory(column_name):
            def custom_validator(value, student_name, index):
                val = str(value).strip()
                if val.isdigit():
                    return True, ""
                return False, f"第{index+1}行数据，学生{student_name}的{column_name}\"{value}\"只能填写数字"

            return custom_validator

        for column_name in ["班级", "学号"]:
            ok, msg = self.validate_column_data(
                column_name, {"custom_validator": digit_custom_validator_factory(column_name)}, column_name
            )
            if not ok:
                return False, msg

        if self.arrangement_mode == "subject_mode" or self.arrangement_mode == "gaokao_mode":
            is_valid, message = self.validate_subject_column()
            if not is_valid:
                return False, message

        return True, "列检查通过"

    def validate_column_data(self, column_name, validation_rules, error_prefix=""):
        return validate_column_data(self, column_name, validation_rules, error_prefix)

    def validate_subject_column(self):
        return validate_subject_column(self)

    def arrange_exam_rooms(self):
        """编排考场（支持四种模式）"""
        if self.students is None:
            return False, "请先加载数据"

        success, message = self.check_required_columns()
        if not success:
            return False, message

        if self.arrangement_mode == "normal_mode":
            return self.arrange_normal_mode()
        elif self.arrangement_mode == "random_mode":
            return self.arrange_random_mode()
        elif self.arrangement_mode == "gaokao_mode":
            return self.arrange_gaokao_mode()
        else:
            return self.arrange_subject_mode()

    def arrange_normal_mode(self):
        """顺序编排模式：按考生名册顺序分配考场"""
        return self._arrange_sequential(shuffle=False)

    def arrange_random_mode(self):
        """随机编排模式：将考生名册随机打乱后分配考场"""
        return self._arrange_sequential(shuffle=True)

    def _arrange_sequential(self, shuffle: bool):
        return arrange_sequential(self, shuffle)

    # 常量定义
    SMALL_GROUP_THRESHOLD = 10

    def _initialize_rooms(self):
        return initialize_rooms(self)

    def _group_and_sort_subjects(self):
        return group_and_sort_subjects(self)

    def _assign_large_groups(self, rooms, physics_subjects, history_subjects):
        return assign_large_groups(self, rooms, physics_subjects, history_subjects)

    def _sort_students_by_subject_count(self, students_list):
        return sort_students_by_subject_count(self, students_list)

    def _get_room_category(self, room, physics_students, history_students):
        return get_room_category(self, room, physics_students, history_students)

    def _assign_remaining_students(self, rooms, remaining_students, current_room_index):
        return assign_remaining_students(self, rooms, remaining_students, current_room_index)

    def _generate_results(self, rooms):
        return generate_results(self, rooms)

    def arrange_subject_mode(self):
        return arrange_subject_mode_strategy(self)

    def _apply_room_names(self):
        """Apply room names mapping based on room_setting_data"""
        if self.arranged_students is not None and "考场号" in self.arranged_students.columns:
            def _norm_room_key(v):
                s = str(v).strip()
                if s.lower() == "nan":
                    return ""
                return s

            def _strip_zeros(s: str) -> str:
                t = str(s).strip()
                if not t:
                    return ""
                if t.isdigit():
                    return t.lstrip("0") or "0"
                return t

            mapping = self.room_setting_data or {}
            existing = None
            if "考场" in self.arranged_students.columns:
                existing = self.arranged_students["考场"].fillna("").astype(str).apply(lambda x: "" if str(x).strip().lower() == "nan" else str(x))
                blank_mask = existing.astype(str).str.strip().eq("")
            else:
                blank_mask = None

            if mapping:
                norm_map = { _norm_room_key(k): str(v) for k, v in mapping.items() }
                stripped_map = { _strip_zeros(k): str(v) for k, v in norm_map.items() if _strip_zeros(k) }

                def _lookup(room_no):
                    key = _norm_room_key(room_no)
                    if key in norm_map:
                        return norm_map[key]
                    stripped = _strip_zeros(key)
                    if stripped and stripped in stripped_map:
                        return stripped_map[stripped]
                    return f"第{key}考场" if key else "第考场"

                computed = self.arranged_students["考场号"].apply(_lookup)
                if blank_mask is None:
                    self.arranged_students["考场"] = computed
                else:
                    self.arranged_students.loc[blank_mask, "考场"] = computed[blank_mask]
            else:
                computed = self.arranged_students["考场号"].apply(lambda x: f"第{str(x).strip()}考场")
                if blank_mask is None:
                    self.arranged_students["考场"] = computed
                else:
                    self.arranged_students.loc[blank_mask, "考场"] = computed[blank_mask]

    def parse_subject_combination(self, subject_str):
        return parse_subject_combination(subject_str)

    # ==================== 高考模式编排方法 ====================

    def _get_gaokao_time_settings(self):
        return get_gaokao_time_settings(self)

    def _format_subject_time(self, subject: str, is_self_study: bool = False) -> str:
        return format_subject_time(self, subject, is_self_study=is_self_study)

    def _get_subject_order(self) -> list:
        return get_subject_order()

    def _shuffle_students(self, students_df):
        return shuffle_students(students_df)

    def _get_room_list(self):
        return get_room_list(self)

    def _fill_rooms_sequential(self, students_list, start_room_index=0):
        return fill_rooms_sequential(self, students_list, start_room_index=start_room_index)

    def _extract_subject_from_combination(self, combination_str, subject_abbr):
        return extract_subject_from_combination(combination_str, subject_abbr)

    def _arrange_unified_exams(self):
        return arrange_unified_exams(self)

    def _get_room_name(self, room_num):
        return get_room_name(self, room_num)

    def _arrange_elective_exam(self, subject):
        return arrange_elective_exam(self, subject)

    def _merge_gaokao_results(self):
        return merge_gaokao_results(self)

    def arrange_gaokao_mode(self):
        return arrange_gaokao_mode(self)

    def save_results(self, output_file="考场编排结果.xlsx"):
        return save_standard_results(self, output_file)

    def save_gaokao_results(self, output_file="高考编排结果.xlsx"):
        return save_gaokao_results(self, output_file)

    def _export_gaokao_student_table(self, writer):
        return export_gaokao_student_table(self, writer)

    def _export_gaokao_seat_tables(self, writer):
        return export_gaokao_seat_tables(self, writer)

    def _export_gaokao_timeslot_tables(self, writer):
        return export_gaokao_timeslot_tables(self, writer)

    def _export_gaokao_stats_table(self, writer):
        return export_gaokao_stats_table(self, writer)

    def _create_stats_sheet_with_formulas(self, writer, export_df=None):
        """使用公式创建考场选科统计工作表"""
        return create_stats_sheet_with_formulas(self, writer, export_df)

