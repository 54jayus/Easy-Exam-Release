import re


def is_gaokao_mode(exam_arrangement):
    """检测是否为高考模式"""
    return (
        exam_arrangement is not None
        and hasattr(exam_arrangement, 'gaokao_results')
        and exam_arrangement.gaokao_results is not None
        and hasattr(exam_arrangement, 'arrangement_mode')
        and exam_arrangement.arrangement_mode == 'gaokao_mode'
    )


def safe_int_sort_key(val):
    """安全地将值转换为整数用于排序"""
    if isinstance(val, int):
        return val
    if isinstance(val, str) and val.isdigit():
        return int(val)
    match = re.search(r'(\d+)', str(val))
    if match:
        return int(match.group(1))
    return 0


def _format_class_student(class_no, student_no):
    """格式化班级学号为 "x班x号" 格式"""
    class_num = extract_number(class_no)
    student_num = extract_number(student_no)

    if class_num and student_num:
        return f"{class_num}班{student_num}号"
    elif class_num:
        return f"{class_num}班{student_no}号"
    else:
        return f"{class_no}{student_no}"


def _format_time(time_settings, subject, is_self_study=False):
    """格式化时间字符串为 "x月x日 hh:mm-hh:mm" 格式"""
    if not time_settings:
        return ""

    # 选择正确的时间配置
    if is_self_study:
        time_config = time_settings.get('selfStudyTimes', {}).get(subject)
    else:
        time_config = time_settings.get('examTimes', {}).get(subject)

    if not time_config:
        return ""

    try:
        from datetime import datetime
        date_str = time_config.get('date', '')
        start_time = time_config.get('startTime', '')
        end_time = time_config.get('endTime', '')

        if not date_str or not start_time or not end_time:
            return ""

        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        month = date_obj.month
        day = date_obj.day

        # 保持时间格式为 hh:mm（不去掉前导零）
        return f"{month}月{day}日 {start_time}-{end_time}"
    except Exception:
        return ""


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


def load_examroom_data_for_corner(df_or_exam_arrangement):
    """
    加载并转换考场编排数据用于台角纸

    参数:
        df_or_exam_arrangement: DataFrame（普通模式）或 ExamArrangement 对象（高考模式）
    """
    # 检测是否为高考模式
    if hasattr(df_or_exam_arrangement, 'gaokao_results'):
        if is_gaokao_mode(df_or_exam_arrangement):
            return _load_gaokao_data_for_corner(df_or_exam_arrangement)

    # 普通模式（保持原有逻辑）
    df = df_or_exam_arrangement
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


def load_examroom_data_for_ticket(df_or_exam_arrangement):
    """
    加载并转换考场编排数据用于准考证

    参数:
        df_or_exam_arrangement: DataFrame（普通模式）或 ExamArrangement 对象（高考模式）
    """
    # 检测是否为高考模式
    if hasattr(df_or_exam_arrangement, 'gaokao_results'):
        if is_gaokao_mode(df_or_exam_arrangement):
            return _load_gaokao_data_for_ticket(df_or_exam_arrangement)

    # 普通模式（保持原有逻辑）
    df = df_or_exam_arrangement
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


def _load_gaokao_data_for_ticket(exam_arrangement):
    """
    加载高考模式数据用于准考证（学生视角）
    每个学生显示8个科目，每个科目有不同的考场和座位
    """
    if not exam_arrangement or not exam_arrangement.gaokao_results:
        return []

    gaokao_results = exam_arrangement.gaokao_results
    unified_df = gaokao_results.get('unified')
    electives_dict = gaokao_results.get('electives')  # 这是一个字典 {科目: DataFrame}
    time_settings = exam_arrangement.gaokao_time_settings or {}

    if unified_df is None or unified_df.empty:
        return []

    # 科目顺序
    subject_order = ['语文', '数学', '物理历史', '英语', '化学', '地理', '政治', '生物']

    # 构建学生数据字典
    student_data = {}

    # 从 unified 获取所有学生基本信息和统考科目数据
    # unified 中每个学生一行，包含统考科目的考场和座位（语文、数学、英语、物理/历史共用）
    for _, row in unified_df.iterrows():
        student_id = str(row.get('考号', ''))
        if not student_id:
            continue

        # 获取首选科目（物理或历史）
        subject_combination = str(row.get('选科', ''))
        preferred_subject = '物理' if subject_combination.startswith('物') else '历史'

        student_data[student_id] = {
            '考生姓名': str(row.get('姓名', '')),
            '考生考号': student_id,
            '班级': str(row.get('班级', '')),
            '学号': str(row.get('学号', '')),
            '首选': preferred_subject,
            '统考考场': str(row.get('考场', '')),
            '统考考场号': str(row.get('考场号', '')),
            '统考座位号': str(row.get('座位号', '')),
            '科目数据': {}
        }

        # 统考科目（语文、数学、英语）使用统考考场
        for subject in ['语文', '数学', '英语']:
            student_data[student_id]['科目数据'][subject] = {
                '科目': subject,
                '考场': student_data[student_id]['统考考场'],
                '考场号': student_data[student_id]['统考考场号'],
                '座位号': student_data[student_id]['统考座位号'],
                '时间': _format_time(time_settings, subject, False)
            }

        # 物理/历史也使用统考考场
        # 注意：时间配置中使用"物理历史"作为键
        student_data[student_id]['科目数据'][preferred_subject] = {
            '科目': preferred_subject,
            '考场': student_data[student_id]['统考考场'],
            '考场号': student_data[student_id]['统考考场号'],
            '座位号': student_data[student_id]['统考座位号'],
            '时间': _format_time(time_settings, '物理历史', False)  # 使用"物理历史"查找时间
        }

    # 从 electives 获取选考科目数据
    if electives_dict:
        for subject in ['化学', '地理', '政治', '生物']:
            if subject not in electives_dict:
                continue

            elective_df = electives_dict[subject]
            if elective_df is None or elective_df.empty:
                continue

            for _, row in elective_df.iterrows():
                student_id = str(row.get('考号', ''))
                if not student_id or student_id not in student_data:
                    continue

                # 检查科目类型：如果是"自习"则为自习科目，否则为考试科目
                subject_type = str(row.get('科目类型', ''))
                is_self_study = subject_type == '自习'

                if is_self_study:
                    # 自习科目
                    student_data[student_id]['科目数据'][subject] = {
                        '科目': '自习',
                        '考场': str(row.get('考场', '')),
                        '考场号': str(row.get('考场号', '')),
                        '座位号': str(row.get('座位号', '')),
                        '时间': _format_time(time_settings, subject, True)
                    }
                else:
                    student_data[student_id]['科目数据'][subject] = {
                        '科目': subject,
                        '考场': str(row.get('考场', '')),
                        '考场号': str(row.get('考场号', '')),
                        '座位号': str(row.get('座位号', '')),
                        '时间': _format_time(time_settings, subject, False)
                    }

    # 转换为列表格式
    data_list = []
    for student_id, student_info in student_data.items():
        subject_data_list = []

        for subject in subject_order:
            if subject == '物理历史':
                # 使用首选科目
                preferred = student_info.get('首选', '物理')
                if preferred in student_info['科目数据']:
                    subject_data_list.append(student_info['科目数据'][preferred])
                else:
                    # 未找到，显示自习
                    subject_data_list.append({
                        '科目': '自习',
                        '考场': '',
                        '考场号': '',
                        '座位号': '',
                        '时间': _format_time(time_settings, preferred, True)
                    })
            else:
                # 其他科目
                if subject in student_info['科目数据']:
                    subject_data_list.append(student_info['科目数据'][subject])
                else:
                    # 未选择的科目，需要查找该学生在该科目时段的自习考场
                    # 从 electives 中查找该学生的自习记录
                    self_study_room = ''
                    self_study_room_no = ''
                    self_study_seat = ''

                    if electives_dict and subject in electives_dict:
                        elective_df = electives_dict[subject]
                        if elective_df is not None and not elective_df.empty:
                            for _, row in elective_df.iterrows():
                                if str(row.get('考号', '')) == student_id:
                                    self_study_room = str(row.get('考场', ''))
                                    self_study_room_no = str(row.get('考场号', ''))
                                    self_study_seat = str(row.get('座位号', ''))
                                    break

                    subject_data_list.append({
                        '科目': '自习',
                        '考场': self_study_room,
                        '考场号': self_study_room_no,
                        '座位号': self_study_seat,
                        '时间': _format_time(time_settings, subject, True)
                    })

        data_list.append({
            '考生姓名': student_info['考生姓名'],
            '考生考号': student_info['考生考号'],
            '班级': extract_number(student_info['班级']),
            '学号': student_info['学号'],
            '科目数据': subject_data_list
        })

    # 排序：班级 -> 学号
    data_list.sort(key=lambda x: (safe_int_sort_key(x.get('班级', 0)), safe_int_sort_key(x.get('学号', 0))))

    return data_list


def _load_gaokao_data_for_corner(exam_arrangement):
    """
    加载高考模式数据用于台角纸（座位视角）
    每个座位显示9个科目，不同科目可能是不同学生
    """
    if not exam_arrangement or not exam_arrangement.gaokao_results:
        return []

    gaokao_results = exam_arrangement.gaokao_results
    unified_df = gaokao_results.get('unified')
    electives_dict = gaokao_results.get('electives')  # 这是一个字典 {科目: DataFrame}

    if unified_df is None or unified_df.empty:
        return []

    # 科目顺序 - 物理历史合并为一个时间段
    subject_order = ['语文', '数学', '物理历史', '英语', '化学', '地理', '政治', '生物']

    # 【性能优化】构建索引字典，避免重复遍历 DataFrame
    # 统考科目索引：{(考场, 座位号): row_data}
    unified_index = {}
    for _, row in unified_df.iterrows():
        room = str(row.get('考场', ''))
        seat = str(row.get('座位号', ''))
        if room and seat:
            key = (room, seat)
            unified_index[key] = {
                '姓名': str(row.get('姓名', '')),
                '考号': str(row.get('考号', '')),
                '班级': str(row.get('班级', '')),
                '学号': str(row.get('学号', '')),
                '选科': str(row.get('选科', '')),
                '考场号': str(row.get('考场号', ''))
            }

    # 选考科目索引：{科目: {(考场, 座位号): row_data}}
    electives_index = {}
    if electives_dict:
        for subject, elective_df in electives_dict.items():
            if elective_df is None or elective_df.empty:
                continue
            electives_index[subject] = {}
            for _, row in elective_df.iterrows():
                room = str(row.get('考场', ''))
                seat = str(row.get('座位号', ''))
                if room and seat:
                    key = (room, seat)
                    electives_index[subject][key] = {
                        '姓名': str(row.get('姓名', '')),
                        '考号': str(row.get('考号', '')),
                        '班级': str(row.get('班级', '')),
                        '学号': str(row.get('学号', '')),
                        '科目类型': str(row.get('科目类型', ''))
                    }

    # 收集所有考场-座位组合
    seat_positions = set()
    # 从统考索引收集
    for (room, seat), data in unified_index.items():
        room_no = data['考场号']
        seat_positions.add((room, room_no, seat))
    # 从选考索引收集
    for subject_index in electives_index.values():
        for (room, seat) in subject_index.keys():
            # 需要从 unified_index 获取考场号
            if (room, seat) in unified_index:
                room_no = unified_index[(room, seat)]['考场号']
            else:
                # 如果统考中没有，尝试从第一个选考科目获取
                room_no = ''
                for subj, idx in electives_index.items():
                    if (room, seat) in idx:
                        # 从原始 DataFrame 获取考场号
                        elective_df = electives_dict.get(subj)
                        if elective_df is not None:
                            for _, row in elective_df.iterrows():
                                if str(row.get('考场', '')) == room and str(row.get('座位号', '')) == seat:
                                    room_no = str(row.get('考场号', ''))
                                    break
                        break
            seat_positions.add((room, room_no, seat))

    # 为每个座位构建科目数据
    data_list = []

    for room, room_no, seat in sorted(seat_positions, key=lambda x: (safe_int_sort_key(x[1]), safe_int_sort_key(x[2]))):
        seat_data = {
            '考场': room,
            '考场号': room_no,
            '座位号': seat,
            '科目数据': []
        }

        key = (room, seat)

        for subject in subject_order:
            student_found = False

            if subject == '物理历史':
                # 物理历史时间段：从统考索引查找
                if key in unified_index:
                    row_data = unified_index[key]
                    subject_combination = row_data['选科']
                    preferred_subject = '物理' if subject_combination.startswith('物') else '历史'

                    seat_data['科目数据'].append({
                        '科目': preferred_subject,
                        '考生姓名': row_data['姓名'],
                        '考生考号': row_data['考号'],
                        '考生班级学号': _format_class_student(row_data['班级'], row_data['学号'])
                    })
                    student_found = True

            elif subject in ['语文', '数学', '英语']:
                # 其他统考科目：从统考索引查找
                if key in unified_index:
                    row_data = unified_index[key]
                    seat_data['科目数据'].append({
                        '科目': subject,
                        '考生姓名': row_data['姓名'],
                        '考生考号': row_data['考号'],
                        '考生班级学号': _format_class_student(row_data['班级'], row_data['学号'])
                    })
                    student_found = True
            else:
                # 选考科目：从选考索引查找
                if subject in electives_index and key in electives_index[subject]:
                    row_data = electives_index[subject][key]
                    subject_type = row_data['科目类型']
                    is_self_study = subject_type == '自习'
                    subject_display = '自习' if is_self_study else subject

                    seat_data['科目数据'].append({
                        '科目': subject_display,
                        '考生姓名': row_data['姓名'],
                        '考生考号': row_data['考号'],
                        '考生班级学号': _format_class_student(row_data['班级'], row_data['学号'])
                    })
                    student_found = True

            # 如果该科目该座位无人，留空
            if not student_found:
                seat_data['科目数据'].append({
                    '科目': '',
                    '考生姓名': '',
                    '考生考号': '',
                    '考生班级学号': ''
                })

        data_list.append(seat_data)

    return data_list

