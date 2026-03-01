import re


def check_examroom_data(examroom_page):
    """检查是否有可用的考场编排数据"""
    if not examroom_page:
        return None

    if hasattr(examroom_page, "arrangement_result"):
        df = examroom_page.arrangement_result
        if df is not None and not df.empty:
            return df

    return None


def extract_number(text):
    """从字符串中提取第一个数字序列"""
    if not text:
        return ""
    match = re.search(r"\d+", str(text))
    if match:
        return match.group()
    return text


def load_examroom_data_for_corner(df):
    """加载并转换考场编排数据用于台角纸"""
    if df is None:
        return None

    data_list = []
    for _, row in df.iterrows():
        item = {}
        item["考生姓名"] = str(row.get("姓名", ""))
        item["考生考号"] = str(row.get("考号", ""))

        bj_str = str(row.get("班级", ""))
        xh_str = str(row.get("学号", ""))

        if bj_str.lower() == "nan":
            bj_str = ""
        if xh_str.lower() == "nan":
            xh_str = ""

        bj_num = extract_number(bj_str)
        xh_num = extract_number(xh_str)

        if bj_num and xh_num:
            item["考生班级学号"] = f"{bj_num}班{xh_num}号"
        else:
            item["考生班级学号"] = f"{bj_str}{xh_str}"

        item["班级"] = bj_num if bj_num else bj_str
        item["学号"] = xh_num if xh_num else xh_str

        item["考场"] = str(row.get("考场", ""))
        item["考场号"] = str(row.get("考场号", ""))
        item["座位号"] = str(row.get("座位号", ""))

        data_list.append(item)
    return data_list


def load_examroom_data_for_ticket(df):
    """加载并转换考场编排数据用于准考证"""
    if df is None:
        return None

    data_list = []
    for _, row in df.iterrows():
        item = {}
        item["考生姓名"] = str(row.get("姓名", ""))
        item["考生考号"] = str(row.get("考号", ""))

        bj_str = str(row.get("班级", ""))
        xh_str = str(row.get("学号", ""))

        if bj_str.lower() == "nan":
            bj_str = ""
        if xh_str.lower() == "nan":
            xh_str = ""

        item["班级"] = extract_number(bj_str)
        item["学号"] = xh_str

        item["考场"] = str(row.get("考场", ""))
        item["考场号"] = str(row.get("考场号", ""))
        item["座位号"] = str(row.get("座位号", ""))

        data_list.append(item)
    return data_list


def load_examroom_data_for_student_info(df, include_subject_fields=False):
    if df is None:
        return None

    data_list = []
    for _, row in df.iterrows():
        item = {}
        item["班级"] = extract_number(str(row.get("班级", "")).strip())
        item["学号"] = extract_number(str(row.get("学号", "")).strip())
        item["考生姓名"] = str(row.get("姓名", ""))
        item["考生考号"] = str(row.get("考号", ""))
        item["考场"] = str(row.get("考场", ""))
        item["考场号"] = str(row.get("考场号", ""))
        item["座位号"] = str(row.get("座位号", ""))
        if include_subject_fields:
            item["首选"] = str(row.get("首选", ""))
            item["选科1"] = str(row.get("选科1", ""))
            item["选科2"] = str(row.get("选科2", ""))
        data_list.append(item)
    return data_list
