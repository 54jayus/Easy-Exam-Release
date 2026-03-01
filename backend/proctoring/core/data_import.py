#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
数据导入模块
负责从Excel文件导入监考人员信息
"""

import pandas as pd
from .models import Teacher

class DataImporter:
    """
    数据导入器
    """
    
    @staticmethod
    def import_teachers_from_excel(file_path):
        """
        从Excel文件导入教师信息
        
        Excel格式要求:
        - 列名: 姓名, 性别, 是否本校, 最大监考段数, 不监考科目, 历次监考时长, 预设监考考场(可选)
        """
        try:
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            # 校验表头
            required_columns = ['姓名', '性别', '是否本校', '最大监考段数', '不监考科目', '历次监考时长']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                raise ValueError(f"Excel文件缺少必填列：{', '.join(missing_columns)}。请使用正确的教师信息导入模板。")
            
            teachers = []
            for _, row in df.iterrows():
                # 处理不监考科目，支持多种格式与分隔符
                raw_unavailable = row.get('不监考科目', '')
                unavailable_subjects = []
                if pd.notna(raw_unavailable) and str(raw_unavailable).strip().lower() != 'nan':
                    # 如果是数值（int/float），直接转换为单个编号
                    if isinstance(raw_unavailable, (int, float)):
                        try:
                            unavailable_subjects = [int(float(raw_unavailable))]
                        except Exception:
                            unavailable_subjects = []
                    else:
                        s = str(raw_unavailable).strip()
                        # 统一分隔符：英文逗号、中文逗号、分号、中文分号、顿号、空格
                        import re
                        parts = re.split(r'[,,，,;|；|、|\s]+', s)
                        for p in parts:
                            t = p.strip()
                            if not t:
                                continue
                            # 允许形如“科目12”前缀
                            t = re.sub(r'^科目', '', t)
                            try:
                                if re.match(r'^\d+(\.\d+)?$', t):
                                    unavailable_subjects.append(int(float(t)))
                            except Exception:
                                pass
                
                # 处理性别字段
                gender_str = str(row.get('性别', ''))
                gender = None
                if gender_str.lower() in ['男', 'm', 'male']:
                    gender = 'M'
                elif gender_str.lower() in ['女', 'f', 'female']:
                    gender = 'F'
                
                # 处理是否本校字段
                is_internal_str = str(row.get('是否本校', ''))
                is_internal = None
                if is_internal_str.lower() in ['是', 'y', 'yes', 'true']:
                    is_internal = True
                elif is_internal_str.lower() in ['否', 'n', 'no', 'false']:
                    is_internal = False
                
                # 处理最大监考段数
                max_sessions = int(row.get('最大监考段数', 0)) if str(row.get('最大监考段数', '')).isdigit() else 0

                # 处理历次监考时长（分钟）
                previous_supervision_duration = 0
                prev_val = row.get('历次监考时长', None)
                if prev_val is not None and str(prev_val).strip() and str(prev_val).lower() != 'nan':
                    try:
                        previous_supervision_duration = int(prev_val)
                    except Exception:
                        try:
                            previous_supervision_duration = int(float(str(prev_val).strip()))
                        except Exception:
                            previous_supervision_duration = 0
                
                teacher = Teacher(
                    name=row.get('姓名', ''),
                    gender=gender,
                    is_internal=is_internal,
                    max_sessions=max_sessions,
                    unavailable_subjects=unavailable_subjects,
                    previous_supervision_duration=previous_supervision_duration
                )
                # 解析预设监考考场（可选列）
                try:
                    raw_preset = None
                    if '预设监考考场' in df.columns:
                        raw_preset = row.get('预设监考考场', None)
                    if raw_preset is not None:
                        s = str(raw_preset).strip()
                        if s and s.lower() != 'nan':
                            import re
                            s = re.sub(r'^考场', '', s)
                            if re.match(r'^\d+(\.\d+)?$', s):
                                val = int(float(s))
                                teacher.preset_room = val if val >= 1 else None
                            else:
                                # 非数字则忽略，后续校验阶段给出警告
                                teacher.preset_room = None
                        else:
                            teacher.preset_room = None
                    else:
                        teacher.preset_room = None
                except Exception:
                    # 解析异常则忽略，后续校验阶段给出警告
                    teacher.preset_room = None
                
                teachers.append(teacher)
            
            return teachers
            
        except Exception as e:
            raise Exception(f"导入教师信息失败: {str(e)}")

    @staticmethod
    def validate_teachers(teachers, mode, gender_mix_required=False, internal_mix_required=False, subject_count=None, subject_names=None, source_file_path=None, num_rooms=None):
        errors = []
        warnings = []
        if not teachers:
            errors.append("没有导入任何教师数据")
            return errors, warnings
        
        # 读取原始Excel以做更严格校验与纠正
        df = None
        if source_file_path:
            try:
                import pandas as pd
                df = pd.read_excel(source_file_path)
            except Exception as e:
                errors.append(f"无法读取教师Excel进行校验: {e}")
        
        # 1) 模式相关最低人数
        if mode == "double":
            if len(teachers) < 2:
                errors.append("双教师监考模式至少需要2名教师")
            if gender_mix_required:
                missing_gender = [t.name for t in teachers if not t.gender]
                if missing_gender:
                    errors.append(f"启用了男女搭配要求，但以下教师缺少性别信息: {missing_gender}")
            if internal_mix_required:
                missing_internal = [t.name for t in teachers if t.is_internal is None]
                if missing_internal:
                    errors.append(f"启用了本外校搭配要求，但以下教师缺少本校信息: {missing_internal}")
        else:
            if len(teachers) < 1:
                errors.append("单教师监考模式至少需要1名教师")
        
        # 预处理：名字去重检查
        names = [t.name for t in teachers]
        dup_names = sorted({n for n in names if names.count(n) > 1 and n})
        if dup_names:
            errors.append(f"教师姓名存在重复，不允许导入：{dup_names}。建议在重复姓名后加数字1、2区分")
        
        # 建立行映射（基于姓名）
        name_to_row = {}
        if df is not None and '姓名' in df.columns:
            for _, row in df.iterrows():
                n = str(row.get('姓名', '')).strip()
                if n:
                    name_to_row[n] = row

        # 预设监考考场规范化与范围校验（可选）
        if df is not None and '预设监考考场' in df.columns:
            import re
            for t in teachers:
                raw_val = None
                if t.name in name_to_row:
                    raw_val = name_to_row[t.name].get('预设监考考场', None)
                is_empty = raw_val is None or (str(raw_val).strip() == '' or str(raw_val).lower() == 'nan')
                if is_empty:
                    # 空值则清空预设
                    t.preset_room = None
                    continue
                s = str(raw_val).strip()
                s = re.sub(r'^考场', '', s)
                if re.match(r'^\d+(\.\d+)?$', s):
                    try:
                        val = int(float(s))
                        if num_rooms is not None:
                            if val < 1 or val > int(num_rooms):
                                warnings.append(f"教师 {t.name} 的预设监考考场越界：{val}（有效范围1..{num_rooms}），已忽略该预设")
                                t.preset_room = None
                            else:
                                t.preset_room = val
                        else:
                            # 未提供房间数，仅保留为正整数
                            t.preset_room = val if val >= 1 else None
                    except Exception:
                        warnings.append(f"教师 {t.name} 的预设监考考场不是有效数字：{raw_val}，已忽略该预设")
                        t.preset_room = None
                else:
                    warnings.append(f"教师 {t.name} 的预设监考考场包含无法识别的值：{raw_val}，已忽略该预设")
                    t.preset_room = None
        
        # 2) 最大监考段数校验与默认值
        if subject_count is not None and subject_count > 0:
            for t in teachers:
                raw_val = None
                if t.name in name_to_row:
                    raw_val = name_to_row[t.name].get('最大监考段数', None)
                # 判定空值
                is_empty = raw_val is None or (str(raw_val).strip() == '' or str(raw_val).lower() == 'nan')
                if is_empty:
                    # 允许为空：设为科目数
                    t.max_sessions = int(subject_count)
                else:
                    # 必须是数字
                    try:
                        val = int(float(str(raw_val).strip()))
                    except Exception:
                        errors.append(f"教师 {t.name} 的最大监考段数不是数字：{raw_val}")
                        continue
                    if val < 0:
                        errors.append(f"教师 {t.name} 的最大监考段数不能为负数：{val}")
                        continue
                    if val > subject_count:
                        errors.append(f"教师 {t.name} 的最大监考段数({val})超过科目数({subject_count})")
                        continue
                    t.max_sessions = val
        else:
            # 无科目数时，至少保证>0
            no_max_sessions = [t.name for t in teachers if (t.max_sessions is None or t.max_sessions <= 0)]
            if no_max_sessions:
                errors.append(f"以下教师未设置最大监考段数或设置为0: {no_max_sessions}")
        
        # 3) 不监考科目解析与校验（支持数字范围与科目名称映射）
        if subject_count is not None and subject_names is not None and df is not None:
            # 构建名称到编号的映射（1..科目数）
            clean_subject_names = [str(s).strip() if s is not None else '' for s in subject_names]
            name_to_id = {name: idx+1 for idx, name in enumerate(clean_subject_names) if name}
            import re
            for t in teachers:
                raw_cell = None
                if t.name in name_to_row:
                    raw_cell = name_to_row[t.name].get('不监考科目', None)
                s = '' if raw_cell is None else str(raw_cell).strip()
                if not s or s.lower() == 'nan':
                    t.unavailable_subjects = []
                    continue
                parts = re.split(r'[,,，,;|；|、|\s]+', s)
                parsed_ids = []
                invalid_tokens = []
                out_of_range = []
                for p in parts:
                    token = p.strip()
                    if not token:
                        continue
                    # 去除前缀
                    token = re.sub(r'^科目', '', token)
                    # 数字：允许浮点->整数
                    if re.match(r'^\d+(\.\d+)?$', token):
                        try:
                            sid = int(float(token))
                            if sid < 1 or sid > subject_count:
                                out_of_range.append(token)
                            else:
                                parsed_ids.append(sid)
                        except Exception:
                            invalid_tokens.append(token)
                    else:
                        # 作为科目名称匹配
                        name_match = token
                        if name_match in name_to_id:
                            parsed_ids.append(name_to_id[name_match])
                        else:
                            invalid_tokens.append(token)
                if invalid_tokens:
                    errors.append(f"教师 {t.name} 的不监考科目中存在无法识别的项: {invalid_tokens}。请使用[1..{subject_count}]的编号或已导入的科目名称")
                if out_of_range:
                    errors.append(f"教师 {t.name} 的不监考科目中存在越界编号: {out_of_range}（有效范围1..{subject_count}）")
                # 去重并覆盖解析结果
                t.unavailable_subjects = sorted(set(parsed_ids))
        
        # 4) 历次监考时长：只能为>=0整数或留空
        if df is not None:
            for t in teachers:
                raw_prev = None
                if t.name in name_to_row:
                    raw_prev = name_to_row[t.name].get('历次监考时长', None)
                is_empty = raw_prev is None or (str(raw_prev).strip() == '' or str(raw_prev).lower() == 'nan')
                if is_empty:
                    t.previous_supervision_duration = 0
                    continue
                try:
                    val = int(float(str(raw_prev).strip()))
                    if val < 0:
                        errors.append(f"教师 {t.name} 的历次监考时长不能为负数：{val}")
                    else:
                        t.previous_supervision_duration = val
                except Exception:
                    errors.append(f"教师 {t.name} 的历次监考时长不是有效整数：{raw_prev}")
        
        return errors, warnings
