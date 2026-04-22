from backend.printing.core.adapters.exam_bag_common import (
    _ELECTIVE_SUBJECTS,
    _EXAM_BAG_FIXED_SUBJECT_ORDER,
    _FIRST_CHOICE_SUBJECTS,
    safe_int_sort_key,
)


def _build_gaokao_exam_bag_rows(exam_arrangement):
    gaokao_results = exam_arrangement.gaokao_results or {}
    unified_df = gaokao_results.get("unified")
    electives_dict = gaokao_results.get("electives") or {}

    if unified_df is None or unified_df.empty:
        return []

    used_rooms = {
        str(room).strip()
        for room in unified_df["考场号"].dropna().astype(str).tolist()
        if str(room).strip()
    }
    for subject in _ELECTIVE_SUBJECTS:
        elective_df = electives_dict.get(subject)
        if elective_df is None or elective_df.empty:
            continue
        exam_rows = elective_df[elective_df["科目类型"] == subject]
        used_rooms.update(
            str(room).strip()
            for room in exam_rows["考场号"].dropna().astype(str).tolist()
            if str(room).strip()
        )

    room_list = []
    if hasattr(exam_arrangement, "_get_room_list"):
        room_list = [str(room).strip() for room in exam_arrangement._get_room_list() if str(room).strip()]
    room_list = [room for room in room_list if room in used_rooms]
    extra_rooms = sorted((room for room in used_rooms if room not in room_list), key=safe_int_sort_key)
    room_list.extend(extra_rooms)

    subject_column = str(getattr(exam_arrangement, "subject_column", "选科") or "选科")
    result = []

    for subject in _EXAM_BAG_FIXED_SUBJECT_ORDER:
        for room_num in room_list:
            room_name = exam_arrangement._get_room_name(room_num) if hasattr(exam_arrangement, "_get_room_name") else str(room_num)
            room_students = unified_df[unified_df["考场号"].astype(str) == str(room_num)]
            count = 0

            if subject in {"语文", "数学", "英语"}:
                count = len(room_students.index)
            elif subject in _FIRST_CHOICE_SUBJECTS:
                prefix = "物" if subject == "物理" else "史"
                count = int(
                    room_students[subject_column]
                    .fillna("")
                    .astype(str)
                    .apply(lambda x: str(x).strip().startswith(prefix))
                    .sum()
                )
            else:
                elective_df = electives_dict.get(subject)
                if elective_df is not None and not elective_df.empty:
                    exam_rows = elective_df[
                        (elective_df["考场号"].astype(str) == str(room_num))
                        & (elective_df["科目类型"] == subject)
                    ]
                    count = len(exam_rows.index)

            if count > 0:
                result.append({
                    "room": room_name,
                    "subject": subject,
                    "count": int(count),
                })

    return result
