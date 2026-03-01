import os
import random
import time

import pandas as pd

from .stats_sheet import create_stats_sheet_with_formulas


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

    def get_room_capacity(self, room_num):
        """获取指定考场的容量，如果没有特殊设置则返回默认容量"""
        room_str = str(room_num).strip()

        if room_str in self.room_capacities:
            return int(self.room_capacities[room_str])

        room_no_zero = room_str.lstrip("0")
        if room_no_zero in self.room_capacities:
            return int(self.room_capacities[room_no_zero])

        for key in self.room_capacities.keys():
            if str(key).strip().lstrip("0") == room_no_zero:
                return int(self.room_capacities[key])

        if room_str.isdigit() and int(room_str) in self.room_capacities:
            return int(self.room_capacities[int(room_str)])

        return self.max_students_per_room

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

        if self.arrangement_mode == "subject_mode":
            is_valid, message = self.validate_subject_column()
            if not is_valid:
                return False, message

        return True, "列检查通过"

    def validate_column_data(self, column_name, validation_rules, error_prefix=""):
        """通用数据验证框架"""
        if column_name not in self.students.columns:
            return False, f"缺少{column_name}列"

        column_data = self.students[column_name].astype(str).str.strip()
        student_names = self.students["姓名"] if "姓名" in self.students.columns else None

        for index, value in enumerate(column_data):
            student_name = student_names.iloc[index] if student_names is not None else f"第{index+1}行"

            if "length" in validation_rules and len(value) != validation_rules["length"]:
                return (
                    False,
                    f"第{index+1}行数据，学生{student_name}的{error_prefix}\"{value}\"长度有误",
                )

            if "valid_values" in validation_rules:
                valid_values = validation_rules["valid_values"]
                if isinstance(valid_values, set):
                    if not all(char in valid_values for char in value):
                        return (
                            False,
                            f"第{index+1}行数据，学生{student_name}的{error_prefix}\"{value}\"包含无效字符",
                        )
                elif isinstance(valid_values, (list, tuple)):
                    if value not in valid_values:
                        return (
                            False,
                            f"第{index+1}行数据，学生{student_name}的{error_prefix}\"{value}\"格式有误，只能为{'/'.join(map(str, valid_values))}",
                        )

            if validation_rules.get("unique_chars", False) and len(set(value)) != len(value):
                return (
                    False,
                    f"第{index+1}行数据，学生{student_name}的{error_prefix}\"{value}\"包含重复字符",
                )

            if "first_char_in" in validation_rules and value and value[0] not in validation_rules["first_char_in"]:
                return (
                    False,
                    f"第{index+1}行数据，学生{student_name}的{error_prefix}\"{value}\"格式有误，第一个字必须为{'/'.join(validation_rules['first_char_in'])}",
                )

            if "custom_validator" in validation_rules:
                is_valid, error_msg = validation_rules["custom_validator"](value, student_name, index)
                if not is_valid:
                    return False, error_msg

        return True, f"{error_prefix}列校验通过"

    def validate_subject_column(self):
        """校验选科列内容（兼容缩写或全称+分隔符），并规范化为缩写写回"""
        normalized_values = []
        valid_abbr = {"物", "史", "化", "生", "地", "政", "理"}
        full_to_abbr = {"物理": "物", "历史": "史", "化学": "化", "生物": "生", "地理": "地", "政治": "政"}

        def custom_validator(value, student_name, index):
            import re

            val = str(value).strip()

            if re.search(r"[+＋,，/、\s]", val):
                tokens = [t for t in re.split(r"[+＋,，/、\s]+", val) if t]
                abbrs = []
                for t in tokens:
                    if t in full_to_abbr:
                        abbrs.append(full_to_abbr[t])
                    elif t in valid_abbr and len(t) == 1:
                        abbrs.append(t)
                    else:
                        return False, f"第{index+1}行数据，学生{student_name}的选科\"{value}\"包含无效科目\"{t}\""
            else:
                abbrs = list(val)

            abbrs = [("物" if c == "理" else c) for c in abbrs]

            if len(abbrs) != 3:
                return (
                    False,
                    f"第{index+1}行数据，学生{student_name}的选科\"{value}\"应包含3个不同科目（示例：物化生 或 物理+化学+生物）",
                )
            if not all(c in {"物", "史", "化", "生", "地", "政"} for c in abbrs):
                return (
                    False,
                    f"第{index+1}行数据，学生{student_name}的选科\"{value}\"包含无效缩写，示例：物化生 或 物理+化学+生物",
                )
            if len(set(abbrs)) != 3:
                return False, f"第{index+1}行数据，学生{student_name}的选科\"{value}\"包含重复科目"
            if abbrs[0] not in {"物", "史"}:
                return False, f"第{index+1}行数据，学生{student_name}的选科\"{value}\"首选必须是物/史"

            normalized_values.append("".join(abbrs))
            return True, ""

        validation_rules = {"custom_validator": custom_validator}
        ok, msg = self.validate_column_data(self.subject_column, validation_rules, "选科")
        if not ok:
            return False, msg

        self.students[self.subject_column] = normalized_values
        return True, "选科列校验通过"

    def arrange_exam_rooms(self):
        """编排考场（支持两种模式）"""
        if self.students is None:
            return False, "请先加载数据"

        success, message = self.check_required_columns()
        if not success:
            return False, message

        if self.arrangement_mode == "normal_mode":
            return self.arrange_normal_mode()
        elif self.arrangement_mode == "random_mode":
            return self.arrange_random_mode()
        else:
            return self.arrange_subject_mode()

    def arrange_normal_mode(self):
        """顺序编排模式：按考生名册顺序分配考场"""
        return self._arrange_sequential(shuffle=False)

    def arrange_random_mode(self):
        """随机编排模式：将考生名册随机打乱后分配考场"""
        return self._arrange_sequential(shuffle=True)

    def _arrange_sequential(self, shuffle: bool):
        """顺序/随机编排的共同实现，shuffle=True 时随机打乱学生顺序。"""
        if self.room_setting_data:
            room_numbers = sorted(
                self.room_setting_data.keys(), key=lambda x: int(x) if str(x).isdigit() else float("inf")
            )
            rooms = [{"room_num": room_num, "students": []} for room_num in room_numbers]
            self.total_rooms = len(rooms)
        else:
            rooms = [{"room_num": i + 1, "students": []} for i in range(self.total_rooms)]

        students_list = self.students.to_dict("records")
        if shuffle:
            random.shuffle(students_list)

        current_room_index = 0
        for student in students_list:
            current_room = rooms[current_room_index]
            room_capacity = self.get_room_capacity(current_room["room_num"])

            if len(current_room["students"]) >= room_capacity:
                current_room_index += 1
                if current_room_index >= self.total_rooms:
                    return False, f"考场数量不足，无法容纳所有学生。需要至少 {current_room_index + 1} 个考场"

                current_room = rooms[current_room_index]

            current_room["students"].append(student)

        arranged_results = []
        for room in rooms:
            if not room["students"]:
                continue

            for seat_num, student in enumerate(room["students"], 1):
                student_info = student.copy()
                student_info.update({"考场号": room["room_num"], "座位号": f"{seat_num:02d}"})

                if self.room_setting_data and room["room_num"] in self.room_setting_data:
                    student_info["考场"] = self.room_setting_data[room["room_num"]]
                else:
                    student_info["考场"] = f"第{room['room_num']}考场"

                arranged_results.append(student_info)

        mode_label = "随机" if shuffle else "顺序"
        if arranged_results:
            self.arranged_students = pd.DataFrame(arranged_results)
            self._apply_room_names()
            return True, f"{mode_label}编排完成，共编排{len(arranged_results)}名学生"
        else:
            return False, "编排失败，没有学生被分配到考场"

    # 常量定义
    SMALL_GROUP_THRESHOLD = 10

    def _initialize_rooms(self):
        """初始化考场列表"""
        if self.room_setting_data:
            room_numbers = sorted(
                self.room_setting_data.keys(),
                key=lambda x: int(x) if str(x).isdigit() else float("inf")
            )
            self.total_rooms = len(room_numbers)
            return [
                {"room_num": num, "students": [], "subjects": set()}
                for num in room_numbers
            ]
        else:
            return [
                {"room_num": i + 1, "students": [], "subjects": set()}
                for i in range(self.total_rooms)
            ]

    def _group_and_sort_subjects(self):
        """按物理/历史分组并按人数排序"""
        subject_counts = self.students[self.subject_column].value_counts()

        physics_subjects = {
            subject: count
            for subject, count in subject_counts.items()
            if "物" in subject
        }
        history_subjects = {
            subject: count
            for subject, count in subject_counts.items()
            if "史" in subject
        }

        physics_subjects = dict(sorted(physics_subjects.items(), key=lambda x: x[1], reverse=True))
        history_subjects = dict(sorted(history_subjects.items(), key=lambda x: x[1], reverse=True))

        return physics_subjects, history_subjects

    def _assign_large_groups(self, rooms, physics_subjects, history_subjects):
        """分配大组学生（人数 > SMALL_GROUP_THRESHOLD），返回当前房间索引和剩余学生"""
        import secrets

        ordered_subjects = list(physics_subjects.items()) + list(history_subjects.items())
        remaining_students = []
        current_room_index = 0

        for subject, count in ordered_subjects:
            if count <= self.SMALL_GROUP_THRESHOLD:
                # 小组，加入剩余学生列表
                mask = self.students[self.subject_column] == subject
                subject_students = self.students[mask].to_dict("records")
                remaining_students.extend(subject_students)
                continue

            # 大组，分配到考场
            mask = self.students[self.subject_column] == subject
            subject_students = self.students[mask]

            if len(subject_students) > 1:
                random_state = secrets.randbelow(2**32)
                subject_students = subject_students.sample(frac=1, random_state=random_state)

            subject_students_list = subject_students.to_dict("records")
            current_subject_idx = 0
            total_subject_count = len(subject_students_list)

            while current_room_index < len(rooms):
                current_room = rooms[current_room_index]
                room_capacity = self.get_room_capacity(current_room["room_num"])
                remaining_count = total_subject_count - current_subject_idx

                if remaining_count >= room_capacity:
                    end_idx = current_subject_idx + room_capacity
                    current_room["students"] = subject_students_list[current_subject_idx:end_idx]
                    current_room["subjects"].add(subject)
                    current_subject_idx = end_idx
                    current_room_index += 1
                else:
                    break

            if current_subject_idx < total_subject_count:
                remaining_students.extend(subject_students_list[current_subject_idx:])

        return current_room_index, remaining_students

    def _sort_students_by_subject_count(self, students_list):
        """按科目人数排序学生"""
        if not students_list:
            return students_list

        students_df = pd.DataFrame(students_list)
        subject_counts = students_df[self.subject_column].value_counts().to_dict()
        students_df["_sort_key"] = students_df[self.subject_column].map(subject_counts)
        sorted_df = students_df.sort_values("_sort_key", ascending=False).drop("_sort_key", axis=1)
        return sorted_df.to_dict("records")

    def _get_room_category(self, room, physics_students, history_students):
        """确定房间类别（物理类或历史类）"""
        if room["students"]:
            first_subject = room["students"][0].get(self.subject_column, "")
            s = str(first_subject).strip()
            return "physics" if s.startswith("物") or s.startswith("理") else "history"
        else:
            return "physics" if len(physics_students) >= len(history_students) else "history"

    def _assign_remaining_students(self, rooms, remaining_students, current_room_index):
        """分配剩余学生到考场"""
        if not remaining_students:
            return

        remaining_df = pd.DataFrame(remaining_students)
        physics_mask = remaining_df[self.subject_column].str.contains("物", na=False)
        history_mask = remaining_df[self.subject_column].str.contains("史", na=False)

        physics_students = remaining_df[physics_mask].to_dict("records")
        history_students = remaining_df[history_mask | ~(physics_mask | history_mask)].to_dict("records")

        # 按科目人数排序
        physics_students = self._sort_students_by_subject_count(physics_students)
        history_students = self._sort_students_by_subject_count(history_students)

        while current_room_index < len(rooms) and (physics_students or history_students):
            current_room = rooms[current_room_index]
            room_capacity = self.get_room_capacity(current_room["room_num"])
            available_seats = room_capacity - len(current_room["students"])

            if available_seats <= 0:
                current_room_index += 1
                continue

            # 确定房间类别
            room_category = self._get_room_category(current_room, physics_students, history_students)

            if room_category == "physics":
                fill_count = min(available_seats, len(physics_students))
                if fill_count > 0:
                    batch = physics_students[:fill_count]
                    current_room["students"].extend(batch)
                    for student in batch:
                        current_room["subjects"].add(student[self.subject_column])
                    physics_students = physics_students[fill_count:]
            else:
                fill_count = min(available_seats, len(history_students))
                if fill_count > 0:
                    batch = history_students[:fill_count]
                    current_room["students"].extend(batch)
                    for student in batch:
                        current_room["subjects"].add(student[self.subject_column])
                    history_students = history_students[fill_count:]

            current_room_index += 1

    def _generate_results(self, rooms):
        """生成最终编排结果"""
        arranged_results = []

        for room in rooms:
            if not room["students"]:
                continue

            room_subjects_str = ", ".join(sorted(room["subjects"]))

            for seat_num, student in enumerate(room["students"], 1):
                student_info = student.copy()
                student_info.update({
                    "考场号": room["room_num"],
                    "座位号": f"{seat_num:02d}",
                    "考场选科组合": room_subjects_str
                })
                arranged_results.append(student_info)

        if arranged_results:
            self.arranged_students = pd.DataFrame(arranged_results)
            self._apply_room_names()

            parsed_subjects = self.arranged_students[self.subject_column].apply(
                self.parse_subject_combination
            )
            self.arranged_students[["首选", "选科1", "选科2"]] = pd.DataFrame(
                parsed_subjects.tolist(), index=self.arranged_students.index
            )

            return True, f"考场编排完成，共编排{len(arranged_results)}名学生"
        else:
            return False, "编排失败，没有学生被分配到考场"

    def arrange_subject_mode(self):
        """3+1+2选科编排模式（优化版：确保物理类和历史类考场连续）"""
        # 1. 初始化考场
        rooms = self._initialize_rooms()

        # 2. 按物理/历史分组并排序
        physics_subjects, history_subjects = self._group_and_sort_subjects()

        # 3. 分配大组（人数 > 10）
        current_room_index, remaining_students = self._assign_large_groups(
            rooms, physics_subjects, history_subjects
        )

        # 4. 分配剩余学生
        self._assign_remaining_students(rooms, remaining_students, current_room_index)

        # 5. 生成结果
        return self._generate_results(rooms)

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
        """解析选科组合，兼容缩写或全称+分隔符，输出首选/选科1/选科2"""
        subject_mapping = {"物": "物理", "理": "物理", "史": "历史", "化": "化学", "生": "生物", "地": "地理", "政": "政治"}
        full_to_full = {"物理": "物理", "历史": "历史", "化学": "化学", "生物": "生物", "地理": "地理", "政治": "政治"}

        import re

        s = str(subject_str).strip()
        subjects = []

        if re.search(r"[+＋,，/、\s]", s):
            tokens = [t for t in re.split(r"[+＋,，/、\s]+", s) if t]
            for t in tokens[:3]:
                if t in full_to_full:
                    subjects.append(full_to_full[t])
                elif t in subject_mapping:
                    subjects.append(subject_mapping[t])
                else:
                    subjects.append(t)
        else:
            for char in s[:3]:
                if char in subject_mapping:
                    subjects.append(subject_mapping[char])
                else:
                    subjects.append(char)

        while len(subjects) < 3:
            subjects.append("")
        return subjects[:3]

    def save_results(self, output_file="考场编排结果.xlsx"):
        """保存编排结果，包含学生信息和选科统计"""
        if self.arranged_students is None:
            return False, "请先编排考场"

        try:
            with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                if self.subject_column in self.arranged_students.columns:
                    parsed_subjects = self.arranged_students[self.subject_column].apply(self.parse_subject_combination)
                    self.arranged_students[["首选", "选科1", "选科2"]] = pd.DataFrame(
                        parsed_subjects.tolist(), index=self.arranged_students.index
                    )

                export_df = self.arranged_students.copy()
                text_columns = ["班级", "学号", "考号", "考场号", "座位号"]
                for col in text_columns:
                    if col in export_df.columns:
                        export_df[col] = export_df[col].astype(str)

                core_columns = ["班级", "学号", "姓名", "考号", "选科", "首选", "选科1", "选科2", "考场", "考场号", "座位号", "考场选科组合"]
                existing_core_cols = [col for col in core_columns if col in export_df.columns]
                extra_cols = [col for col in export_df.columns if col not in core_columns]
                new_column_order = existing_core_cols + extra_cols
                export_df = export_df[new_column_order]

                export_df.to_excel(writer, sheet_name="学生编排结果", index=False)

                if self.subject_column in self.arranged_students.columns:
                    self._create_stats_sheet_with_formulas(writer, export_df)

            return True, f"编排结果已保存到: {os.path.abspath(output_file)}"
        except FileNotFoundError:
            return False, "输出目录不存在"
        except PermissionError:
            return False, f"文件被占用或没有写入权限: {output_file}"
        except OSError as e:
            return False, f"磁盘空间不足或文件系统错误: {e}"
        except Exception as e:
            return False, f"保存结果失败: {e}"

    def _create_stats_sheet_with_formulas(self, writer, export_df=None):
        """使用公式创建考场选科统计工作表"""
        return create_stats_sheet_with_formulas(self, writer, export_df)
