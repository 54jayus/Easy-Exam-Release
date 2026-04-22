from backend.printing.core.adapters.exam_bag_common import (
    _count_students_for_subject,
    _get_exam_bag_room_entries,
)


def _build_exam_bag_rows_grouped_by_subject(exam_arrangement, subjects):
    df = getattr(exam_arrangement, "arranged_students", None)
    if df is None or df.empty:
        return []

    if "考场号" not in df.columns and "考场" not in df.columns:
        return []

    room_entries = _get_exam_bag_room_entries(df, exam_arrangement)
    result = []
    for subject_name in subjects:
        for _, room_name, room_df in room_entries:
            count = _count_students_for_subject(room_df, subject_name)
            if count > 0:
                result.append({
                    "room": room_name,
                    "subject": subject_name,
                    "count": int(count),
                })
    return result
