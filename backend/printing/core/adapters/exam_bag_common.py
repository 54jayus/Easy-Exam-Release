import re


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


_SUBJECT_ALIAS_MAP = {
    "语": "语文",
    "语文": "语文",
    "数": "数学",
    "数学": "数学",
    "英": "英语",
    "英语": "英语",
    "物": "物理",
    "物理": "物理",
    "史": "历史",
    "历史": "历史",
    "化": "化学",
    "化学": "化学",
    "生": "生物",
    "生物": "生物",
    "政": "政治",
    "政治": "政治",
    "地": "地理",
    "地理": "地理",
}

_FIRST_CHOICE_SUBJECTS = {"物理", "历史"}
_ELECTIVE_SUBJECTS = {"化学", "生物", "政治", "地理"}
_EXAM_BAG_FIXED_SUBJECT_ORDER = ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "政治", "地理"]


def _normalize_subject_name(value):
    text = str(value or "").strip()
    if not text:
        return ""
    return _SUBJECT_ALIAS_MAP.get(text, text)


def _extract_subject_names(subjects_data):
    subject_names = []
    seen = set()
    for item in subjects_data or []:
        if isinstance(item, dict):
            name = _normalize_subject_name(item.get("name") or item.get("subjectName") or item.get("id"))
        else:
            name = _normalize_subject_name(item)
        if name and name not in seen:
            subject_names.append(name)
            seen.add(name)
    return subject_names


def _expand_exam_bag_subject_name(value):
    text = str(value or "").strip()
    compact = text.replace("/", "").replace("、", "").replace(" ", "")
    if compact in {"物理历史", "历史物理", "物史", "史物"}:
        return ["物理", "历史"]

    normalized = _normalize_subject_name(text)
    if not normalized:
        return []
    return [normalized]


def _extract_exam_bag_subject_names(subjects_data, default_subjects=None):
    subject_names = []
    seen = set()
    source = subjects_data if subjects_data is not None else default_subjects

    for item in source or []:
        if isinstance(item, dict):
            raw_value = item.get("name") or item.get("subjectName") or item.get("id")
        else:
            raw_value = item

        for name in _expand_exam_bag_subject_name(raw_value):
            if name and name not in seen:
                subject_names.append(name)
                seen.add(name)

    return subject_names


def _get_room_identifier(row):
    room_no = str(row.get("考场号", "")).strip()
    room_name = str(row.get("考场", "")).strip()
    return room_no or room_name


def _matches_subject_combination(subject_combo, subject_name):
    combo = str(subject_combo or "").strip()
    normalized_subject = _normalize_subject_name(subject_name)
    if not combo or not normalized_subject:
        return False
    if normalized_subject in _FIRST_CHOICE_SUBJECTS:
        alias = "物" if normalized_subject == "物理" else "史"
        return combo.startswith(alias) or normalized_subject in combo
    alias_lookup = {"化学": "化", "生物": "生", "政治": "政", "地理": "地"}
    alias = alias_lookup.get(normalized_subject, "")
    return normalized_subject in combo or (alias and alias in combo)


def _count_students_for_subject(room_df, subject_name):
    normalized_subject = _normalize_subject_name(subject_name)
    if not normalized_subject:
        return 0

    if normalized_subject in _FIRST_CHOICE_SUBJECTS:
        if "首选" in room_df.columns:
            return int(room_df["首选"].fillna("").astype(str).map(_normalize_subject_name).eq(normalized_subject).sum())
        if "选科" in room_df.columns:
            return int(room_df["选科"].fillna("").astype(str).apply(lambda x: _matches_subject_combination(x, normalized_subject)).sum())

    if normalized_subject in _ELECTIVE_SUBJECTS:
        if "选科1" in room_df.columns or "选科2" in room_df.columns:
            count = 0
            if "选科1" in room_df.columns:
                count += int(room_df["选科1"].fillna("").astype(str).map(_normalize_subject_name).eq(normalized_subject).sum())
            if "选科2" in room_df.columns:
                count += int(room_df["选科2"].fillna("").astype(str).map(_normalize_subject_name).eq(normalized_subject).sum())
            return count
        if "选科" in room_df.columns:
            return int(room_df["选科"].fillna("").astype(str).apply(lambda x: _matches_subject_combination(x, normalized_subject)).sum())

    return len(room_df.index)


def _get_arrangement_mode(exam_arrangement):
    return str(getattr(exam_arrangement, "arrangement_mode", "") or "").strip()


def _get_exam_bag_room_entries(df, exam_arrangement):
    room_order = []
    if hasattr(exam_arrangement, "_get_room_list"):
        try:
            room_order.extend(str(room).strip() for room in exam_arrangement._get_room_list() if str(room).strip())
        except Exception:
            pass

    room_keys_in_data = []
    for _, row in df.iterrows():
        room_key = _get_room_identifier(row)
        if room_key and room_key not in room_keys_in_data:
            room_keys_in_data.append(room_key)

    for room_key in room_keys_in_data:
        if room_key not in room_order:
            room_order.append(room_key)

    room_entries = []
    for room_key in room_order:
        room_df = df[df.apply(lambda row: _get_room_identifier(row) == room_key, axis=1)]
        if room_df.empty:
            continue

        first_row = room_df.iloc[0]
        room_name = str(first_row.get("考场", "")).strip()
        if not room_name and hasattr(exam_arrangement, "_get_room_name"):
            try:
                room_name = str(exam_arrangement._get_room_name(room_key)).strip()
            except Exception:
                room_name = ""
        if not room_name:
            room_name = str(room_key)

        room_entries.append((room_key, room_name, room_df))

    return room_entries
