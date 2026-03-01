from __future__ import annotations

from typing import Sequence

import pandas as pd

from .core.models import Schedule


def export_schedule_to_excel(
    file_path: str,
    *,
    schedule: Schedule,
    subject_names: Sequence[str] | None,
    exam_times: Sequence[str] | None,
) -> None:
    subject_names = list(subject_names or [])
    exam_times = list(exam_times or [])

    rows = []
    for room in range(1, schedule.num_rooms + 1):
        row: dict[str, str] = {"考场": f"考场{room}"}
        rows.append(row)

    df = pd.DataFrame(rows)

    if schedule.mode == "double":
        for subject_id in range(1, schedule.num_subjects + 1):
            subject_name = (
                subject_names[subject_id - 1]
                if (subject_id - 1) < len(subject_names) and subject_names[subject_id - 1]
                else f"科目{subject_id}"
            )
            exam_time = (
                exam_times[subject_id - 1]
                if (subject_id - 1) < len(exam_times) and exam_times[subject_id - 1]
                else ""
            )
            col1 = f"{subject_name}-监考员1\n{exam_time}"
            col2 = f"{subject_name}-监考员2\n{exam_time}"
            df[col1] = ""
            df[col2] = ""

            exam = next((e for e in schedule.exams if e.subject_id == subject_id), None)
            if not exam:
                continue
            for idx, room in enumerate(range(1, schedule.num_rooms + 1)):
                teachers = exam.schedule.get(room, [])
                t1 = teachers[0].name if len(teachers) > 0 and teachers[0] else ""
                t2 = teachers[1].name if len(teachers) > 1 and teachers[1] else ""
                df.at[idx, col1] = t1
                df.at[idx, col2] = t2
    else:
        for subject_id in range(1, schedule.num_subjects + 1):
            subject_name = (
                subject_names[subject_id - 1]
                if (subject_id - 1) < len(subject_names) and subject_names[subject_id - 1]
                else f"科目{subject_id}"
            )
            exam_time = (
                exam_times[subject_id - 1]
                if (subject_id - 1) < len(exam_times) and exam_times[subject_id - 1]
                else ""
            )
            col = f"{subject_name}\n{exam_time}"
            df[col] = ""

            exam = next((e for e in schedule.exams if e.subject_id == subject_id), None)
            if not exam:
                continue
            for idx, room in enumerate(range(1, schedule.num_rooms + 1)):
                teachers = exam.schedule.get(room, [])
                name = teachers[0].name if teachers and teachers[0] else ""
                df.at[idx, col] = name

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="监考总览表", index=False)


def export_schedule_workbook_to_excel(
    file_path: str,
    *,
    schedule: Schedule,
    subject_names: Sequence[str] | None,
    exam_times: Sequence[str] | None,
) -> None:
    subject_names = list(subject_names or [])
    exam_times = list(exam_times or [])

    exams = schedule.exams or []
    if exams:
        num_subjects = max((exam.subject_id for exam in exams), default=schedule.num_subjects)
    else:
        num_subjects = schedule.num_subjects

    all_rooms = sorted({room for exam in exams for room in exam.rooms}) if exams else list(range(1, schedule.num_rooms + 1))

    overview_rows: list[dict[str, str]] = []
    for room in all_rooms:
        row_data: dict[str, str] = {"考场": f"考场{room}"}
        if schedule.mode == "double":
            for subject_id in range(1, num_subjects + 1):
                sname = (
                    subject_names[subject_id - 1]
                    if (subject_id - 1) < len(subject_names) and subject_names[subject_id - 1]
                    else f"科目{subject_id}"
                )
                etime = (
                    exam_times[subject_id - 1]
                    if (subject_id - 1) < len(exam_times) and exam_times[subject_id - 1]
                    else ""
                )
                row_data[f"{sname}-监考员1\n{etime}"] = ""
                row_data[f"{sname}-监考员2\n{etime}"] = ""
        else:
            for subject_id in range(1, num_subjects + 1):
                sname = (
                    subject_names[subject_id - 1]
                    if (subject_id - 1) < len(subject_names) and subject_names[subject_id - 1]
                    else f"科目{subject_id}"
                )
                etime = (
                    exam_times[subject_id - 1]
                    if (subject_id - 1) < len(exam_times) and exam_times[subject_id - 1]
                    else ""
                )
                row_data[f"{sname}\n{etime}"] = ""
        overview_rows.append(row_data)

    room_index_map = {room: idx for idx, room in enumerate(all_rooms)}
    for exam in exams:
        for room in exam.rooms:
            if room not in room_index_map:
                continue
            teachers = exam.schedule.get(room, [])
            idx = room_index_map[room]
            sname = (
                subject_names[exam.subject_id - 1]
                if (exam.subject_id - 1) < len(subject_names) and subject_names[exam.subject_id - 1]
                else f"科目{exam.subject_id}"
            )
            etime = (
                exam_times[exam.subject_id - 1]
                if (exam.subject_id - 1) < len(exam_times) and exam_times[exam.subject_id - 1]
                else ""
            )
            if schedule.mode == "double":
                col1_name = f"{sname}-监考员1\n{etime}"
                col2_name = f"{sname}-监考员2\n{etime}"
                if len(teachers) >= 1 and teachers[0] is not None:
                    overview_rows[idx][col1_name] = teachers[0].name
                if len(teachers) >= 2 and teachers[1] is not None:
                    overview_rows[idx][col2_name] = teachers[1].name
            else:
                col = f"{sname}\n{etime}"
                teacher_names = ", ".join([t.name for t in teachers if t is not None])
                overview_rows[idx][col] = teacher_names

    df_overview = pd.DataFrame(overview_rows) if overview_rows else pd.DataFrame()

    stats_data: list[dict[str, str]] = []
    max_subject_id = num_subjects
    stats = schedule.get_statistics()
    for stat in stats:
        teacher = next((t for t in schedule.teachers if t.name == stat["name"]), None)
        if not teacher:
            continue
        stat_row: dict[str, str] = {
            "教师姓名": teacher.name,
            "性别": "男" if teacher.gender == "M" else ("女" if teacher.gender == "F" else ""),
            "是否本校": "是" if teacher.is_internal is True else ("否" if teacher.is_internal is False else ""),
            "最大监考段数": str(teacher.max_sessions),
            "剩余监考次数": str((teacher.max_sessions or 0) - stat["count"]),
            "不监考科目": ",".join(map(str, teacher.unavailable_subjects)),
        }

        for j in range(1, max_subject_id + 1):
            sname = subject_names[j - 1] if j - 1 < len(subject_names) and subject_names[j - 1] else f"科目{j}"
            stat_row[sname] = str(1 if teacher.is_assigned_to_subject(j) else 0)

        stat_row["监考次数"] = str(stat["count"])
        stat_row["监考时长(分钟)"] = str(teacher.supervision_duration)
        stat_row["历次监考时长（分钟）"] = str(teacher.previous_supervision_duration)
        total_duration = (teacher.supervision_duration or 0) + (teacher.previous_supervision_duration or 0)
        stat_row["总监考时长(分钟)"] = str(total_duration)
        stats_data.append(stat_row)

    df_stats = pd.DataFrame(stats_data) if stats_data else pd.DataFrame()

    subject_sheets: dict[str, pd.DataFrame] = {}
    for exam in exams:
        subject_key = (
            subject_names[exam.subject_id - 1]
            if (exam.subject_id - 1) < len(subject_names) and subject_names[exam.subject_id - 1]
            else f"科目{exam.subject_id}"
        )
        rows: list[dict[str, str]] = []
        if schedule.mode == "double":
            headers = [
                "考场",
                "监考员1（姓名）",
                "监考员1性别",
                "监考员1来源",
                "监考员2（姓名）",
                "监考员2性别",
                "监考员2来源",
            ]
        else:
            headers = ["考场", "监考教师（姓名）", "性别", "来源"]

        for room in sorted(exam.rooms):
            if room not in exam.schedule:
                continue
            teachers = exam.schedule.get(room, [])
            row = dict.fromkeys(headers, "")
            row["考场"] = str(room)
            if schedule.mode == "double":
                if len(teachers) >= 1 and teachers[0] is not None:
                    t1 = teachers[0]
                    row["监考员1（姓名）"] = t1.name
                    row["监考员1性别"] = "男" if t1.gender == "M" else ("女" if t1.gender == "F" else "")
                    row["监考员1来源"] = "本校" if t1.is_internal is True else ("外校" if t1.is_internal is False else "")
                if len(teachers) >= 2 and teachers[1] is not None:
                    t2 = teachers[1]
                    row["监考员2（姓名）"] = t2.name
                    row["监考员2性别"] = "男" if t2.gender == "M" else ("女" if t2.gender == "F" else "")
                    row["监考员2来源"] = "本校" if t2.is_internal is True else ("外校" if t2.is_internal is False else "")
            else:
                teacher_names = ", ".join([t.name for t in teachers if t is not None])
                row["监考教师（姓名）"] = teacher_names
                if teachers and teachers[0] is not None:
                    t = teachers[0]
                    row["性别"] = "男" if t.gender == "M" else ("女" if t.gender == "F" else "")
                    row["来源"] = "本校" if t.is_internal is True else ("外校" if t.is_internal is False else "")
            rows.append(row)  # type: ignore[arg-type]

        if rows:
            df_subject = pd.DataFrame(rows)
            subject_sheets[subject_key] = df_subject

    with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
        if not df_overview.empty:
            df_overview.to_excel(writer, sheet_name="监考总览表", index=False)
        if not df_stats.empty:
            df_stats.to_excel(writer, sheet_name="监考统计", index=False)
        for subject_key, df_subject in subject_sheets.items():
            safe_name = subject_key[:31] if subject_key else "科目"
            df_subject.to_excel(writer, sheet_name=safe_name, index=False)

        workbook = writer.book
        if not df_overview.empty and "监考总览表" in workbook.sheetnames:
            worksheet = workbook["监考总览表"]
            try:
                from openpyxl.styles import Alignment

                worksheet.row_dimensions[1].height = 60
                for cell in worksheet[1]:
                    cell.alignment = Alignment(wrap_text=True, horizontal="center", vertical="center")
            except Exception:
                pass
            for column in worksheet.columns:
                worksheet.column_dimensions[column[0].column_letter].width = 10

        if not df_stats.empty and "监考统计" in workbook.sheetnames:
            ws = workbook["监考统计"]
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        max_length = max(max_length, len(str(cell.value)))
                    except Exception:
                        pass
                ws.column_dimensions[column_letter].width = min(max_length * 3, 50)

        for sheet_name in list(subject_sheets.keys()):
            safe_name = sheet_name[:31] if sheet_name else "科目"
            if safe_name not in workbook.sheetnames:
                continue
            ws = workbook[safe_name]
            for column in ws.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        max_length = max(max_length, len(str(cell.value)))
                    except Exception:
                        pass
                ws.column_dimensions[column_letter].width = min(max_length * 3, 50)
