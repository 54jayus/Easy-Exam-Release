from __future__ import annotations

import re
from datetime import datetime

from .gaokao_defaults import GAOKAO_SUBJECT_ORDER, build_gaokao_time_defaults, normalize_gaokao_time_settings


def get_room_capacity(arrangement, room_num):
    """获取指定考场的容量，如果没有特殊设置则返回默认容量"""
    room_str = str(room_num).strip()

    if room_str in arrangement.room_capacities:
        return int(arrangement.room_capacities[room_str])

    room_no_zero = room_str.lstrip("0")
    if room_no_zero in arrangement.room_capacities:
        return int(arrangement.room_capacities[room_no_zero])

    for key in arrangement.room_capacities.keys():
        if str(key).strip().lstrip("0") == room_no_zero:
            return int(arrangement.room_capacities[key])

    if room_str.isdigit() and int(room_str) in arrangement.room_capacities:
        return int(arrangement.room_capacities[int(room_str)])

    return arrangement.max_students_per_room


def validate_column_data(arrangement, column_name, validation_rules, error_prefix=""):
    """通用数据验证框架"""
    if column_name not in arrangement.students.columns:
        return False, f"缺少{column_name}列"

    column_data = arrangement.students[column_name].astype(str).str.strip()
    student_names = arrangement.students["姓名"] if "姓名" in arrangement.students.columns else None

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


def validate_subject_column(arrangement):
    """校验选科列内容（兼容缩写或全称+分隔符），并规范化为缩写写回"""
    normalized_values = []
    valid_abbr = {"物", "史", "化", "生", "地", "政", "理"}
    full_to_abbr = {"物理": "物", "历史": "史", "化学": "化", "生物": "生", "地理": "地", "政治": "政"}

    def custom_validator(value, student_name, index):
        val = str(value).strip()

        if re.search(r"[+＋,，/、\s]", val):
            tokens = [token for token in re.split(r"[+＋,，/、\s]+", val) if token]
            abbrs = []
            for token in tokens:
                if token in full_to_abbr:
                    abbrs.append(full_to_abbr[token])
                elif token in valid_abbr and len(token) == 1:
                    abbrs.append(token)
                else:
                    return False, f"第{index+1}行数据，学生{student_name}的选科\"{value}\"包含无效科目\"{token}\""
        else:
            abbrs = list(val)

        abbrs = [("物" if char == "理" else char) for char in abbrs]

        if len(abbrs) != 3:
            return (
                False,
                f"第{index+1}行数据，学生{student_name}的选科\"{value}\"应包含3个不同科目（示例：物化生 或 物理+化学+生物）",
            )
        if not all(char in {"物", "史", "化", "生", "地", "政"} for char in abbrs):
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
    ok, msg = validate_column_data(arrangement, arrangement.subject_column, validation_rules, "选科")
    if not ok:
        return False, msg

    arrangement.students[arrangement.subject_column] = normalized_values
    return True, "选科列校验通过"


def parse_subject_combination(subject_str):
    """解析选科组合，兼容缩写或全称+分隔符，输出首选/选科1/选科2"""
    subject_mapping = {"物": "物理", "理": "物理", "史": "历史", "化": "化学", "生": "生物", "地": "地理", "政": "政治"}
    full_to_full = {"物理": "物理", "历史": "历史", "化学": "化学", "生物": "生物", "地理": "地理", "政治": "政治"}

    value = str(subject_str).strip()
    subjects = []

    if re.search(r"[+＋,，/、\s]", value):
        tokens = [token for token in re.split(r"[+＋,，/、\s]+", value) if token]
        for token in tokens[:3]:
            if token in full_to_full:
                subjects.append(full_to_full[token])
            elif token in subject_mapping:
                subjects.append(subject_mapping[token])
            else:
                subjects.append(token)
    else:
        for char in value[:3]:
            if char in subject_mapping:
                subjects.append(subject_mapping[char])
            else:
                subjects.append(char)

    while len(subjects) < 3:
        subjects.append("")
    return subjects[:3]


def get_gaokao_time_settings(arrangement):
    """获取高考时间设置，如果没有则返回默认值"""
    if arrangement.gaokao_time_settings:
        return normalize_gaokao_time_settings(arrangement.gaokao_time_settings)
    return build_gaokao_time_defaults()


def format_subject_time(arrangement, subject: str, is_self_study: bool = False) -> str:
    """格式化科目时间为 6月8日09:00-10:15 形式。"""
    settings = get_gaokao_time_settings(arrangement)

    try:
        if is_self_study and subject in settings.get("selfStudyTimes", {}):
            time_config = settings["selfStudyTimes"][subject]
        elif subject in settings.get("examTimes", {}):
            time_config = settings["examTimes"][subject]
        else:
            return ""

        date_str = time_config.get("date", "")
        start_time = time_config.get("startTime", "")
        end_time = time_config.get("endTime", "")

        if not all([date_str, start_time, end_time]):
            return ""

        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{date_obj.month}月{date_obj.day}日{start_time}-{end_time}"
    except Exception:
        return ""


def get_subject_order():
    """返回科目的考试顺序"""
    return GAOKAO_SUBJECT_ORDER


def get_room_name(arrangement, room_num):
    """获取考场名称"""
    room_str = str(room_num).strip()

    if hasattr(arrangement, "room_setting_df") and arrangement.room_setting_df is not None:
        for _, row in arrangement.room_setting_df.iterrows():
            setting_room_num = str(row.get("考场号", "")).strip()
            if setting_room_num == room_str or setting_room_num.lstrip("0") == room_str.lstrip("0"):
                return str(row.get("考场", f"第{room_num}考场"))

    elif arrangement.room_setting_data is not None and hasattr(arrangement.room_setting_data, "iterrows"):
        for _, row in arrangement.room_setting_data.iterrows():
            setting_room_num = str(row.get("考场号", "")).strip()
            if setting_room_num == room_str or setting_room_num.lstrip("0") == room_str.lstrip("0"):
                return str(row.get("考场", f"第{room_num}考场"))

    return f"第{room_num}考场"
