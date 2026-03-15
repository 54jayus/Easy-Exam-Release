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
        self.gaokao_results = None  # 高考模式编排结果

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

    # ==================== 高考模式编排方法 ====================

    def _shuffle_students(self, students_df):
        """使用安全随机数打乱学生顺序"""
        import secrets
        random_state = secrets.randbelow(2**32)
        return students_df.sample(frac=1, random_state=random_state).reset_index(drop=True)

    def _get_room_list(self):
        """获取考场号列表（按顺序）"""
        if self.room_setting_data is not None:
            # 使用考场设置中的考场号
            return [str(row['考场号']) for _, row in self.room_setting_data.iterrows()]
        else:
            # 如果没有考场设置，使用1到total_rooms的顺序编号
            return [str(i) for i in range(1, self.total_rooms + 1)]

    def _fill_rooms_sequential(self, students_list, start_room_index=0):
        """
        将学生顺序填充到考场
        参数:
            students_list: 学生DataFrame
            start_room_index: 起始考场索引（在考场列表中的位置）
        返回: (考场分配结果列表, 最后使用的考场索引)
        """
        room_list = self._get_room_list()
        rooms = []
        current_room_index = start_room_index
        current_room_students = []

        for idx, student in students_list.iterrows():
            if current_room_index >= len(room_list):
                raise ValueError(f"考场数量不足，需要至少{current_room_index + 1}个考场")

            room_num = room_list[current_room_index]
            room_capacity = self.get_room_capacity(room_num)

            if len(current_room_students) >= room_capacity:
                # 当前考场已满，保存并进入下一个考场
                rooms.append({
                    'room_num': room_num,
                    'students': current_room_students
                })
                current_room_index += 1
                current_room_students = []

            current_room_students.append(student)

        # 添加最后一个考场
        if current_room_students:
            if current_room_index >= len(room_list):
                raise ValueError(f"考场数量不足，需要至少{current_room_index + 1}个考场")
            room_num = room_list[current_room_index]
            rooms.append({
                'room_num': room_num,
                'students': current_room_students
            })

        return rooms, current_room_index

    def _extract_subject_from_combination(self, combination_str, subject_abbr):
        """从选科组合中提取是否包含某科目"""
        return subject_abbr in str(combination_str)

    def _arrange_unified_exams(self):
        """
        编排统考科目（语数英+物理/历史）
        返回: DataFrame包含所有学生的统考编排结果
        """
        # 1. 按物理/历史分组
        physics_students = self.students[self.students[self.subject_column].str.startswith('物')].copy()
        history_students = self.students[self.students[self.subject_column].str.startswith('史')].copy()

        # 2. 随机打乱物理组学生
        physics_students = self._shuffle_students(physics_students)

        # 3. 编排物理组学生（从考场索引0开始）
        physics_rooms, last_physics_index = self._fill_rooms_sequential(physics_students, 0)

        # 4. 随机打乱历史组学生
        history_students = self._shuffle_students(history_students)

        # 5. 编排历史组学生（从物理组的下一个考场开始）
        history_rooms, last_history_index = self._fill_rooms_sequential(history_students, last_physics_index + 1)

        # 6. 合并所有考场，为每个学生分配座位号
        all_rooms = physics_rooms + history_rooms
        result_records = []

        for room in all_rooms:
            room_num = room['room_num']
            # 获取考场名称
            room_name = self._get_room_name(room_num)

            for seat_idx, student in enumerate(room['students'], start=1):
                seat_num = f"{seat_idx:02d}"  # 格式化为01, 02, ...

                record = student.to_dict()
                record['考场号'] = room_num
                record['考场'] = room_name
                record['座位号'] = seat_num

                result_records.append(record)

        result_df = pd.DataFrame(result_records)
        return result_df

    def _get_room_name(self, room_num):
        """获取考场名称"""
        if self.room_setting_data is not None:
            # 从考场设置中查找
            room_str = str(room_num).strip()
            for _, row in self.room_setting_data.iterrows():
                setting_room_num = str(row.get('考场号', '')).strip()
                if setting_room_num == room_str or setting_room_num.lstrip('0') == room_str.lstrip('0'):
                    return str(row.get('考场', f'第{room_num}考场'))
        return f'第{room_num}考场'

    def _arrange_elective_exam(self, subject):
        """
        编排单个选考科目
        参数:
            subject: 科目名称（如"化学"）
        返回: DataFrame包含所有学生的该科目编排结果，包含科目类型列
        """
        # 科目缩写映射
        subject_abbr_map = {
            '化学': '化',
            '地理': '地',
            '政治': '政',
            '生物': '生'
        }
        subject_abbr = subject_abbr_map.get(subject, subject[0])

        # 1. 分离考试学生和自习学生
        exam_students = self.students[self.students[self.subject_column].str.contains(subject_abbr)].copy()
        self_study_students = self.students[~self.students[self.subject_column].str.contains(subject_abbr)].copy()

        # 2. 随机打乱考试学生
        exam_students = self._shuffle_students(exam_students)

        # 3. 编排考试学生到考试考场（从考场索引0开始）
        exam_rooms, last_exam_index = self._fill_rooms_sequential(exam_students, 0)

        # 4. 随机打乱自习学生
        self_study_students = self._shuffle_students(self_study_students)

        # 5. 编排自习学生到自习考场（从考试考场的下一个开始）
        self_study_rooms, last_self_study_index = self._fill_rooms_sequential(self_study_students, last_exam_index + 1)

        # 6. 合并所有考场，为每个学生分配座位号和科目类型
        all_rooms = exam_rooms + self_study_rooms
        result_records = []

        for room_idx, room in enumerate(all_rooms):
            room_num = room['room_num']
            room_name = self._get_room_name(room_num)
            is_exam_room = room_idx < len(exam_rooms)  # 判断是否为考试考场

            for seat_idx, student in enumerate(room['students'], start=1):
                seat_num = f"{seat_idx:02d}"

                record = student.to_dict()
                record['考场号'] = room_num
                record['考场'] = room_name
                record['座位号'] = seat_num
                record['科目类型'] = subject if is_exam_room else '自习'

                result_records.append(record)

        result_df = pd.DataFrame(result_records)
        return result_df

    def _merge_gaokao_results(self):
        """
        合并所有科目的编排结果为学生中心视图
        返回: DataFrame，每行一个学生，包含9个科目的完整信息
        """
        # 从统考结果开始
        unified_df = self.gaokao_results['unified']

        # 创建基础DataFrame，包含学生基本信息
        result_df = unified_df[['班级', '学号', '考号', '姓名', self.subject_column]].copy()

        # 定义9个科目（按考试顺序）
        subjects = ['语文', '数学', '英语', '物理', '化学', '地理', '政治', '生物']

        # 为每个科目添加4列：科目状态、考场号、考场、座位号
        for subject in subjects:
            if subject in ['语文', '数学', '英语', '物理']:
                # 统考科目：从unified_df获取数据
                result_df[f'{subject}科目'] = subject
                result_df[f'{subject}考场号'] = unified_df['考场号']
                result_df[f'{subject}考场'] = unified_df['考场']
                result_df[f'{subject}座位号'] = unified_df['座位号']
            else:
                # 选考科目：从electives获取数据
                elective_df = self.gaokao_results['electives'][subject]

                # 按考号合并
                for idx, row in result_df.iterrows():
                    exam_id = row['考号']
                    elective_row = elective_df[elective_df['考号'] == exam_id]

                    if not elective_row.empty:
                        elective_row = elective_row.iloc[0]
                        result_df.at[idx, f'{subject}科目'] = elective_row['科目类型']
                        result_df.at[idx, f'{subject}考场号'] = elective_row['考场号']
                        result_df.at[idx, f'{subject}考场'] = elective_row['考场']
                        result_df.at[idx, f'{subject}座位号'] = elective_row['座位号']

        return result_df

    def arrange_gaokao_mode(self):
        """
        高考模式编排：统考(语数英+物/历史) + 选考(化地政生)
        返回: (成功标志, 消息)
        """
        # 1. 编排统考科目
        unified_result = self._arrange_unified_exams()

        # 2. 编排选考科目
        elective_results = {}
        for subject in ['化学', '地理', '政治', '生物']:
            elective_results[subject] = self._arrange_elective_exam(subject)

        # 3. 保存结果
        self.gaokao_results = {
            'unified': unified_result,
            'electives': elective_results
        }

        # 4. 合并为学生中心视图
        self.arranged_students = self._merge_gaokao_results()

        return True, f"高考模式编排完成，共编排{len(self.students)}名学生"

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

    def save_gaokao_results(self, output_file="高考编排结果.xlsx"):
        """保存高考模式编排结果（3种表格）"""
        if self.arranged_students is None:
            return False, "请先编排考场"

        if self.gaokao_results is None:
            return False, "高考模式编排结果不存在"

        try:
            with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                # 表格A: 学生中心视图（1个sheet）
                self._export_gaokao_student_table(writer)

                # 表格B: 座位中心视图（1个sheet）
                self._export_gaokao_seat_tables(writer)

                # 表格C: 时间段视图（5个sheet）
                self._export_gaokao_timeslot_tables(writer)

            return True, f"高考编排结果已保存至 {os.path.abspath(output_file)}"
        except PermissionError:
            return False, f"文件被占用或没有写入权限: {output_file}"
        except Exception as e:
            return False, f"保存结果失败: {e}"

    def _export_gaokao_student_table(self, writer):
        """导出考场安排（学生）表"""
        export_df = self.arranged_students.copy()

        # 确保文本列格式正确
        text_columns = ['班级', '学号', '考号']
        for col in text_columns:
            if col in export_df.columns:
                export_df[col] = export_df[col].astype(str)

        # 确保考场号和座位号也是文本格式
        subjects = ['语文', '数学', '英语', '物理', '化学', '地理', '政治', '生物']
        for subject in subjects:
            for suffix in ['考场号', '座位号']:
                col_name = f'{subject}{suffix}'
                if col_name in export_df.columns:
                    export_df[col_name] = export_df[col_name].astype(str)

        export_df.to_excel(writer, sheet_name="考场安排（学生）", index=False)

    def _export_gaokao_seat_tables(self, writer):
        """导出考场安排（座位）表 - 1个sheet包含所有科目"""
        # 收集所有唯一的考场号和座位号组合
        unified_df = self.gaokao_results['unified']
        electives = self.gaokao_results['electives']

        # 从统考结果获取所有考场和座位
        seats = unified_df[['考场号', '考场', '座位号']].drop_duplicates().sort_values(['考场号', '座位号'])

        # 创建座位表的基础DataFrame
        seat_records = []

        for _, seat_row in seats.iterrows():
            room_num = seat_row['考场号']
            room_name = seat_row['考场']
            seat_num = seat_row['座位号']

            record = {
                '考场号': room_num,
                '考场': room_name,
                '座位号': seat_num
            }

            # 为每个科目添加5列数据
            subjects_data = {
                '语文': unified_df,
                '数学': unified_df,
                '英语': unified_df,
                '物理': unified_df,
                '化学': electives['化学'],
                '地理': electives['地理'],
                '政治': electives['政治'],
                '生物': electives['生物']
            }

            for subject, df in subjects_data.items():
                # 查找该座位在该科目下的学生
                student_row = df[(df['考场号'] == room_num) & (df['座位号'] == seat_num)]

                if not student_row.empty:
                    student_row = student_row.iloc[0]
                    if subject in ['语文', '数学', '英语', '物理']:
                        # 统考科目
                        record[f'{subject}科目'] = subject
                    else:
                        # 选考科目
                        record[f'{subject}科目'] = student_row.get('科目类型', '自习')

                    record[f'{subject}姓名'] = student_row.get('姓名', '')
                    record[f'{subject}考号'] = str(student_row.get('考号', ''))
                    record[f'{subject}班级'] = str(student_row.get('班级', ''))
                    record[f'{subject}学号'] = str(student_row.get('学号', ''))
                else:
                    # 该座位在该科目下没有学生
                    record[f'{subject}科目'] = ''
                    record[f'{subject}姓名'] = ''
                    record[f'{subject}考号'] = ''
                    record[f'{subject}班级'] = ''
                    record[f'{subject}学号'] = ''

            seat_records.append(record)

        seat_df = pd.DataFrame(seat_records)
        seat_df.to_excel(writer, sheet_name="考场安排（座位）", index=False)

    def _export_gaokao_timeslot_tables(self, writer):
        """导出各科考试时间编排结果表 - 5个sheet"""
        # Sheet 1: 统考编排结果（语数英+物理/历史）
        unified_df = self.gaokao_results['unified'].copy()
        unified_df['科目'] = unified_df[self.subject_column].str[0].map({'物': '物理', '史': '历史'})

        # 调整列顺序
        columns_order = ['考场号', '考场', '座位号', '考号', '姓名', '班级', '学号', '科目']
        existing_cols = [col for col in columns_order if col in unified_df.columns]
        unified_export = unified_df[existing_cols].copy()  # 添加 .copy()

        # 确保文本列格式正确
        for col in ['考场号', '座位号', '考号', '班级', '学号']:
            if col in unified_export.columns:
                unified_export.loc[:, col] = unified_export[col].astype(str)  # 使用 .loc

        unified_export.to_excel(writer, sheet_name="统考编排结果", index=False)

        # Sheet 2-5: 选考科目编排结果
        for subject in ['化学', '地理', '政治', '生物']:
            elective_df = self.gaokao_results['electives'][subject].copy()

            # 重命名科目类型列为科目
            elective_df['科目'] = elective_df['科目类型']
            elective_df = elective_df.drop(columns=['科目类型'])

            # 调整列顺序
            elective_export = elective_df[existing_cols].copy()  # 添加 .copy()

            # 确保文本列格式正确
            for col in ['考场号', '座位号', '考号', '班级', '学号']:
                if col in elective_export.columns:
                    elective_export.loc[:, col] = elective_export[col].astype(str)  # 使用 .loc

            elective_export.to_excel(writer, sheet_name=f"{subject}编排结果", index=False)

    def _create_stats_sheet_with_formulas(self, writer, export_df=None):
        """使用公式创建考场选科统计工作表"""
        return create_stats_sheet_with_formulas(self, writer, export_df)
