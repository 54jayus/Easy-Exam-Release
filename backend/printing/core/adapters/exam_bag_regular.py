from backend.printing.core.adapters.exam_bag_common import (
    _count_students_for_subject,
    _get_exam_bag_room_entries,
)


def _build_exam_bag_rows_from_arranged_students(exam_arrangement, subjects):
    df = getattr(exam_arrangement, "arranged_students", None)
    if df is None or df.empty:
        return []

    if "考场号" not in df.columns and "考场" not in df.columns:
        return []

    result = []
    for _, room_name, room_df in _get_exam_bag_room_entries(df, exam_arrangement):
        for subject_name in subjects:
            count = _count_students_for_subject(room_df, subject_name)
            if count > 0:
                result.append({
                    "room": room_name,
                    "subject": subject_name,
                    "count": int(count),
                })
    return result
