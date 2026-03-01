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
        # 统一将room_num转为字符串查找，去除可能的前导零
        room_str = str(room_num).strip()

        # 尝试直接匹配字符串key
        if room_str in self.room_capacities:
            return int(self.room_capacities[room_str])

        # 尝试去除前导零匹配（例如 '001' -> '1'）
        room_no_zero = room_str.lstrip("0")
        if room_no_zero in self.room_capacities:
            return int(self.room_capacities[room_no_zero])

        # 尝试匹配带前导零的形式（例如 '1' -> '001', '01', '0001'）
        # 遍历所有key进行尝试
        for key in self.room_capacities.keys():
            if str(key).strip().lstrip("0") == room_no_zero:
                return int(self.room_capacities[key])

        # 尝试转为整数查找
        if room_str.isdigit() and int(room_str) in self.room_capacities:
            return int(self.room_capacities[int(room_str)])

        return self.max_students_per_room

    def load_data(self):
        """加载学生数据"""
        try:
            # 读取Excel文件，确保考号以文本类型读入
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
            # 顺序编排模式和随机编排模式：不需要选科列
            required_columns = ["班级", "学号", "考号", "姓名"]
        else:
            # 3+1+2选科编排模式：需要选科列
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
            ok, msg = self.validate_column_data(column_name, {"custom_validator": digit_custom_validator_factory(column_name)}, column_name)
            if not ok:
                return False, msg

        # 只在3+1+2模式下校验选科列内容
        if self.arrangement_mode == "subject_mode":
            # 校验选科列内容
            is_valid, message = self.validate_subject_column()
            if not is_valid:
                return False, message

        return True, "列检查通过"

    def validate_column_data(self, column_name, validation_rules, error_prefix=""):
        """通用数据验证框架

        Args:
            column_name: 要验证的列名
            validation_rules: 验证规则字典，包含:
                - 'valid_values': 有效值集合或列表
                - 'length': 期望长度（可选）
                - 'unique_chars': 是否要求字符唯一（可选）
                - 'first_char_in': 第一个字符必须在指定集合中（可选）
                - 'custom_validator': 自定义验证函数（可选）
            error_prefix: 错误信息前缀

        Returns:
            tuple: (是否通过, 错误信息)
        """
        if column_name not in self.students.columns:
            return False, f"缺少{column_name}列"

        # 使用向量化操作预处理数据
        column_data = self.students[column_name].astype(str).str.strip()
        student_names = self.students["姓名"] if "姓名" in self.students.columns else None

        # 批量验证
        for index, value in enumerate(column_data):
            student_name = student_names.iloc[index] if student_names is not None else f"第{index+1}行"

            # 长度验证
            if "length" in validation_rules and len(value) != validation_rules["length"]:
                return (
                    False,
                    f"第{index+1}行数据，学生{student_name}的{error_prefix}\"{value}\"长度有误",
                )

            # 有效值验证
            if "valid_values" in validation_rules:
                valid_values = validation_rules["valid_values"]
                if isinstance(valid_values, set):
                    # 字符集验证（如选科）
                    if not all(char in valid_values for char in value):
                        return (
                            False,
                            f"第{index+1}行数据，学生{student_name}的{error_prefix}\"{value}\"包含无效字符",
                        )
                elif isinstance(valid_values, (list, tuple)):
                    # 枚举值验证（如性别）
                    if value not in valid_values:
                        return (
                            False,
                            f"第{index+1}行数据，学生{student_name}的{error_prefix}\"{value}\"格式有误，只能为{'/'.join(map(str, valid_values))}",
                        )

            # 字符唯一性验证
            if validation_rules.get("unique_chars", False) and len(set(value)) != len(value):
                return (
                    False,
                    f"第{index+1}行数据，学生{student_name}的{error_prefix}\"{value}\"包含重复字符",
                )

            # 首字符验证
            if "first_char_in" in validation_rules and value and value[0] not in validation_rules["first_char_in"]:
                return (
                    False,
                    f"第{index+1}行数据，学生{student_name}的{error_prefix}\"{value}\"格式有误，第一个字必须为{'/'.join(validation_rules['first_char_in'])}",
                )

            # 自定义验证
            if "custom_validator" in validation_rules:
                is_valid, error_msg = validation_rules["custom_validator"](value, student_name, index)
                if not is_valid:
                    return False, error_msg

        return True, f"{error_prefix}列校验通过"

    def validate_subject_column(self):
        """校验选科列内容（兼容缩写或全称+分隔符），并规范化为缩写写回"""
        # 目标：支持如下输入并统一规范化为缩写：
        # - 缩写：物化生 / 史政地
        # - 全称+分隔符：物理+化学+生物、历史,政治,地理、物理 化学 生物 等

        normalized_values = []
        valid_abbr = {"物", "史", "化", "生", "地", "政", "理"}  # 理视作物理缩写
        full_to_abbr = {"物理": "物", "历史": "史", "化学": "化", "生物": "生", "地理": "地", "政治": "政"}

        def custom_validator(value, student_name, index):
            import re

            val = str(value).strip()

            # 判断是否包含分隔符（+、＋、,、，、/、、或空格）
            if re.search(r"[+＋,，/、\s]", val):
                tokens = [t for t in re.split(r"[+＋,，/、\s]+", val) if t]
                abbrs = []
                for t in tokens:
                    # 全称映射为缩写
                    if t in full_to_abbr:
                        abbrs.append(full_to_abbr[t])
                    # 已是缩写（单字符）
                    elif t in valid_abbr and len(t) == 1:
                        abbrs.append(t)
                    else:
                        return False, f"第{index+1}行数据，学生{student_name}的选科\"{value}\"包含无效科目\"{t}\""
            else:
                # 无分隔符：期望是缩写如“物化生”或含“理”
                abbrs = list(val)

            # 规范化：将“理”统一为“物”（物理）
            abbrs = [("物" if c == "理" else c) for c in abbrs]

            # 规则校验
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

        # 使用通用验证框架，仅启用自定义验证
        validation_rules = {"custom_validator": custom_validator}
        ok, msg = self.validate_column_data(self.subject_column, validation_rules, "选科")
        if not ok:
            return False, msg

        # 校验通过，回写规范化后的缩写到数据列，统一后续统计与分组
        self.students[self.subject_column] = normalized_values
        return True, "选科列校验通过"

    def arrange_exam_rooms(self):
        """编排考场（支持两种模式）"""
        if self.students is None:
            return False, "请先加载数据"

        # 检查必要的列
        success, message = self.check_required_columns()
        if not success:
            return False, message

        # 根据编排模式选择不同的编排逻辑
        if self.arrangement_mode == "normal_mode":
            return self.arrange_normal_mode()
        elif self.arrangement_mode == "random_mode":
            return self.arrange_random_mode()
        else:
            return self.arrange_subject_mode()

    def arrange_normal_mode(self):
        """顺序编排模式：按考生名册顺序分配考场"""
        # 预分配考场列表
        if self.room_setting_data:
            room_numbers = sorted(self.room_setting_data.keys(), key=lambda x: int(x) if str(x).isdigit() else float("inf"))
            rooms = [{"room_num": room_num, "students": []} for room_num in room_numbers]
            self.total_rooms = len(rooms)
        else:
            rooms = [{"room_num": i + 1, "students": []} for i in range(self.total_rooms)]

        # 将学生数据转换为字典列表，保持原始顺序
        students_list = self.students.to_dict("records")

        # 按顺序分配学生到考场
        current_room_index = 0
        for student in students_list:
            # 动态获取当前考场容量
            current_room = rooms[current_room_index]
            room_capacity = self.get_room_capacity(current_room["room_num"])

            # 如果当前考场已满，移动到下一个考场
            if len(current_room["students"]) >= room_capacity:
                current_room_index += 1
                if current_room_index >= self.total_rooms:
                    return False, f"考场数量不足，无法容纳所有学生。需要至少 {current_room_index + 1} 个考场"

                # 更新当前考场引用（因为index变了）
                current_room = rooms[current_room_index]

            # 将学生分配到当前考场
            current_room["students"].append(student)

        # 为每个学生分配座位号并生成结果
        arranged_results = []
        for room in rooms:
            if not room["students"]:  # 跳过空考场
                continue

            # 为当前考场的所有学生分配座位号
            for seat_num, student in enumerate(room["students"], 1):
                student_info = student.copy()
                student_info.update(
                    {"考场号": room["room_num"], "座位号": f"{seat_num:02d}"}  # 确保座位号为文本类型且单位数补前置0
                )

                # 添加考场名称（如果有考场设置）
                if self.room_setting_data and room["room_num"] in self.room_setting_data:
                    student_info["考场"] = self.room_setting_data[room["room_num"]]
                else:
                    student_info["考场"] = f"第{room['room_num']}考场"

                arranged_results.append(student_info)

        if arranged_results:
            self.arranged_students = pd.DataFrame(arranged_results)
            return True, f"顺序编排完成，共编排{len(arranged_results)}名学生"
        else:
            return False, "编排失败，没有学生被分配到考场"

    def arrange_random_mode(self):
        """随机编排模式：将考生名册随机打乱后分配考场"""
        # 预分配考场列表
        if self.room_setting_data:
            room_numbers = sorted(self.room_setting_data.keys(), key=lambda x: int(x) if str(x).isdigit() else float("inf"))
            rooms = [{"room_num": room_num, "students": []} for room_num in room_numbers]
            self.total_rooms = len(rooms)
        else:
            rooms = [{"room_num": i + 1, "students": []} for i in range(self.total_rooms)]

        # 将学生数据转换为字典列表，然后随机打乱
        students_list = self.students.to_dict("records")
        random.shuffle(students_list)  # 随机打乱学生顺序

        # 按随机顺序分配学生到考场
        current_room_index = 0
        for student in students_list:
            # 动态获取当前考场容量
            current_room = rooms[current_room_index]
            room_capacity = self.get_room_capacity(current_room["room_num"])

            # 如果当前考场已满，移动到下一个考场
            if len(current_room["students"]) >= room_capacity:
                current_room_index += 1
                if current_room_index >= self.total_rooms:
                    return False, f"考场数量不足，无法容纳所有学生。需要至少 {current_room_index + 1} 个考场"

                # 更新当前考场引用
                current_room = rooms[current_room_index]

            # 将学生分配到当前考场
            current_room["students"].append(student)

        # 为每个学生分配座位号并生成结果
        arranged_results = []
        for room in rooms:
            if not room["students"]:  # 跳过空考场
                continue

            # 为当前考场的所有学生分配座位号
            for seat_num, student in enumerate(room["students"], 1):
                student_info = student.copy()
                student_info.update(
                    {"考场号": room["room_num"], "座位号": f"{seat_num:02d}"}  # 确保座位号为文本类型且单位数补前置0
                )

                # 添加考场名称（如果有考场设置）
                if self.room_setting_data and room["room_num"] in self.room_setting_data:
                    student_info["考场"] = self.room_setting_data[room["room_num"]]
                else:
                    student_info["考场"] = f"第{room['room_num']}考场"

                arranged_results.append(student_info)

        if arranged_results:
            self.arranged_students = pd.DataFrame(arranged_results)
            return True, f"随机编排完成，共编排{len(arranged_results)}名学生"
        else:
            return False, "编排失败，没有学生被分配到考场"

    def arrange_subject_mode(self):
        """3+1+2选科编排模式（优化版：确保物理类和历史类考场连续）"""

        # 使用向量化操作统计选科组合人数并排序
        subject_counts = self.students[self.subject_column].value_counts()

        # 预分配考场列表 - 使用列表推导式提高性能
        if self.room_setting_data:
            room_numbers = sorted(self.room_setting_data.keys(), key=lambda x: int(x) if str(x).isdigit() else float("inf"))
            rooms = [{"room_num": room_num, "students": [], "subjects": set()} for room_num in room_numbers]
            self.total_rooms = len(rooms)
        else:
            rooms = [{"room_num": i + 1, "students": [], "subjects": set()} for i in range(self.total_rooms)]

        # 预分配剩余学生缓冲区
        remaining_students = []
        current_room_index = 0

        # 按物理类/历史类分组选科组合
        physics_subjects = {}  # 物理类选科组合
        history_subjects = {}  # 历史类选科组合

        for subject, count in subject_counts.items():
            if "物" in subject:
                physics_subjects[subject] = count
            else:
                history_subjects[subject] = count

        # 按人数排序（从多到少）
        physics_subjects = dict(sorted(physics_subjects.items(), key=lambda x: x[1], reverse=True))
        history_subjects = dict(sorted(history_subjects.items(), key=lambda x: x[1], reverse=True))

        # 合并为有序的选科组合列表（物理类优先，然后历史类）
        ordered_subjects = list(physics_subjects.items()) + list(history_subjects.items())

        # 使用生成器处理大数据集，减少内存占用
        def process_subjects_efficiently():
            """生成器函数，高效处理选科组合"""
            for subject, count in ordered_subjects:
                # 使用布尔索引进行向量化筛选
                mask = self.students[self.subject_column] == subject
                subject_students = self.students[mask].copy()

                # 随机打乱（如果需要）
                if len(subject_students) > 1:
                    subject_students = subject_students.sample(frac=1, random_state=int(time.time())).reset_index(drop=True)

                yield subject, count, subject_students.to_dict("records")

        # 遍历选科组合，按优化后的顺序编排
        for subject, count, subject_students_list in process_subjects_efficiently():
            # 预计算参数，避免重复计算
            is_small_group = count <= 10

            if is_small_group:
                # 小组合直接加入缓冲区
                remaining_students.extend(subject_students_list)
            else:
                # 动态分配考场（支持不同考场不同容量）
                current_subject_idx = 0
                total_subject_count = len(subject_students_list)

                while current_room_index < self.total_rooms:
                    # 获取当前考场的容量
                    current_room = rooms[current_room_index]
                    room_capacity = self.get_room_capacity(current_room["room_num"])

                    # 检查剩余学生是否足够填满当前考场
                    remaining_count = total_subject_count - current_subject_idx

                    if remaining_count >= room_capacity:
                        # 填满当前考场
                        end_idx = current_subject_idx + room_capacity
                        current_room["students"] = subject_students_list[current_subject_idx:end_idx]
                        current_room["subjects"].add(subject)

                        # 更新索引
                        current_subject_idx = end_idx
                        current_room_index += 1
                    else:
                        # 不够填满当前考场，停止整考场分配
                        break

                # 将该科目剩余未分配的学生加入缓冲区
                if current_subject_idx < total_subject_count:
                    remaining_students.extend(subject_students_list[current_subject_idx:])

        # 安排剩余学生到混合考场（性能优化版本）
        if remaining_students:
            # 使用向量化操作分类学生
            remaining_df = pd.DataFrame(remaining_students)

            # 创建物理类和历史类的布尔掩码
            physics_mask = remaining_df[self.subject_column].str.contains("物", na=False)
            history_mask = remaining_df[self.subject_column].str.contains("史", na=False)

            # 分离物理类和历史类学生
            physics_students = remaining_df[physics_mask].to_dict("records")
            history_students = remaining_df[history_mask | ~(physics_mask | history_mask)].to_dict("records")  # 未知类别归入历史类

            # 使用向量化操作统计选科人数并排序
            def sort_students_by_subject_count(students_list):
                if not students_list:
                    return students_list

                students_df = pd.DataFrame(students_list)
                subject_counts = students_df[self.subject_column].value_counts().to_dict()

                # 添加排序键并排序
                students_df["_sort_key"] = students_df[self.subject_column].map(subject_counts)
                sorted_df = students_df.sort_values("_sort_key", ascending=False).drop("_sort_key", axis=1)
                return sorted_df.to_dict("records")

            physics_students = sort_students_by_subject_count(physics_students)
            history_students = sort_students_by_subject_count(history_students)

            # 尾部考场优化：尽量保证每个混合考场的主选科目一致
            def get_main_category(subject_str):
                try:
                    s = str(subject_str).strip()
                    return "physics" if s.startswith("物") or s.startswith("理") else "history"
                except Exception:
                    return "history"

            # 仅按单一类别填充每个剩余考场，不强求满员
            while current_room_index < self.total_rooms and (physics_students or history_students):
                current_room = rooms[current_room_index]
                # 动态获取当前考场容量
                room_capacity = self.get_room_capacity(current_room["room_num"])
                available_seats = room_capacity - len(current_room["students"])

                if available_seats <= 0:
                    current_room_index += 1
                    continue

                # 已有学生的房间遵循已有主选类别；空房间依据剩余人数多的一侧决定主选
                room_category = None
                if current_room["students"]:
                    first_subject = current_room["students"][0].get(self.subject_column, "")
                    room_category = get_main_category(first_subject)
                else:
                    room_category = "physics" if len(physics_students) >= len(history_students) else "history"

                if room_category == "physics":
                    fill_count = min(available_seats, len(physics_students))
                    if fill_count > 0:
                        batch = physics_students[:fill_count]
                        current_room["students"].extend(batch)
                        for student in batch:
                            current_room["subjects"].add(student[self.subject_column])
                        physics_students = physics_students[fill_count:]
                    # 不再用历史类填充该房间，直接进入下一个房间
                    current_room_index += 1
                else:
                    fill_count = min(available_seats, len(history_students))
                    if fill_count > 0:
                        batch = history_students[:fill_count]
                        current_room["students"].extend(batch)
                        for student in batch:
                            current_room["subjects"].add(student[self.subject_column])
                        history_students = history_students[fill_count:]
                    current_room_index += 1

        # 为每个学生分配座位号（性能优化版本）
        # 预计算总学生数，预分配结果列表
        total_students = sum(len(room["students"]) for room in rooms)
        arranged_results = []

        # 使用生成器和批量操作优化结果生成
        for room in rooms:
            if not room["students"]:  # 跳过空考场
                continue

            room_subjects_str = ", ".join(sorted(room["subjects"]))  # 预计算选科组合字符串

            # 批量处理当前考场的所有学生
            for seat_num, student in enumerate(room["students"], 1):
                # 使用字典更新而非复制，提高性能
                student_info = student.copy()
                student_info.update(
                    {"考场号": room["room_num"], "座位号": f"{seat_num:02d}", "考场选科组合": room_subjects_str}
                )
                arranged_results.append(student_info)

        # 直接从列表创建DataFrame，避免中间转换
        if arranged_results:
            self.arranged_students = pd.DataFrame(arranged_results)

            # 立即添加首选、选科1、选科2字段，确保UI界面能显示
            parsed_subjects = self.arranged_students[self.subject_column].apply(self.parse_subject_combination)
            self.arranged_students[["首选", "选科1", "选科2"]] = pd.DataFrame(parsed_subjects.tolist(), index=self.arranged_students.index)

            return True, f"考场编排完成，共编排{len(arranged_results)}名学生"
        else:
            return False, "编排失败，没有学生被分配到考场"

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
            # 创建一个ExcelWriter对象
            with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
                # 根据编排模式决定是否处理选科信息
                if self.arrangement_mode == "subject_mode" and self.subject_column in self.arranged_students.columns:
                    # 3+1+2模式：解析选科组合，添加首选、选科1、选科2列
                    parsed_subjects = self.arranged_students[self.subject_column].apply(self.parse_subject_combination)
                    self.arranged_students[["首选", "选科1", "选科2"]] = pd.DataFrame(
                        parsed_subjects.tolist(), index=self.arranged_students.index
                    )

                # 保存学生编排结果到第一个工作表，确保所有数据以文本类型导出
                # 将需要保持为文本的列转换为字符串类型
                export_df = self.arranged_students.copy()
                text_columns = ["班级", "学号", "考号", "考场号", "座位号"]
                for col in text_columns:
                    if col in export_df.columns:
                        export_df[col] = export_df[col].astype(str)

                # 重新排列列顺序：核心列在前，其他列（如性别等）在后
                core_columns = ["班级", "学号", "姓名", "考号", "选科", "首选", "选科1", "选科2", "考场", "考场号", "座位号", "考场选科组合"]
                # 找出实际存在的核心列
                existing_core_cols = [col for col in core_columns if col in export_df.columns]
                # 找出额外的列
                extra_cols = [col for col in export_df.columns if col not in core_columns]
                # 组合新顺序
                new_column_order = existing_core_cols + extra_cols
                export_df = export_df[new_column_order]

                export_df.to_excel(writer, sheet_name="学生编排结果", index=False)

                # 只在3+1+2模式下创建选科统计工作表
                if self.arrangement_mode == "subject_mode" and self.subject_column in self.arranged_students.columns:
                    # 使用公式创建考场选科统计工作表
                    # 传入export_df以便获取正确的列索引
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
