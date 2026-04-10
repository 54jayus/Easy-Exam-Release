#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.application.proctoring_service import ProctoringService
from backend.application.subjects_service import SubjectsService
from backend.domain.state import AppState


SUBJECT_NAME = "\u79d1\u76ee\u540d\u79f0"
EXAM_DATE = "\u8003\u8bd5\u65e5\u671f"
EXAM_TIME = "\u8003\u8bd5\u65f6\u95f4"
DURATION = "\u8003\u8bd5\u65f6\u957f\uff08\u5206\u949f\uff09-\u53ef\u7559\u7a7a"
ROOM_COUNT = "\u8003\u573a\u6570\u91cf\uff08\u53ef\u7559\u7a7a\uff09"
REMARK = "\u5907\u6ce8"

TEACHER_NAME = "\u59d3\u540d"
GENDER = "\u6027\u522b"
IS_INTERNAL = "\u662f\u5426\u672c\u6821"
MAX_SESSIONS = "\u6700\u5927\u76d1\u8003\u6bb5\u6570"
UNAVAILABLE = "\u4e0d\u76d1\u8003\u79d1\u76ee"
PREVIOUS_DURATION = "\u5386\u6b21\u76d1\u8003\u65f6\u957f"
PRESET_ROOM = "\u9884\u8bbe\u76d1\u8003\u8003\u573a"

OVERVIEW_SHEET = "\u76d1\u8003\u603b\u89c8\u8868"
ROOM_COLUMN = "\u8003\u573a"


class NoopRepository:
    def save(self, _state: AppState) -> None:
        return None

    def load(self, _state: AppState) -> None:
        return None

    def delete(self) -> None:
        return None


def subject_row(
    name: str,
    exam_date: str,
    exam_time: str,
    *,
    duration: int | str,
    room_count: int | str = "",
    remark: str = "",
) -> dict[str, Any]:
    return {
        SUBJECT_NAME: name,
        EXAM_DATE: exam_date,
        EXAM_TIME: exam_time,
        DURATION: duration,
        ROOM_COUNT: room_count,
        REMARK: remark,
    }


def teacher_row(
    name: str,
    *,
    gender: str = "",
    is_internal: bool | None = None,
    max_sessions: int | str = "",
    unavailable: str = "",
    previous_duration: int | str = 0,
    preset_room: int | str = "",
) -> dict[str, Any]:
    return {
        TEACHER_NAME: name,
        GENDER: {"M": "\u7537", "F": "\u5973"}.get(gender, ""),
        IS_INTERNAL: "" if is_internal is None else ("\u662f" if is_internal else "\u5426"),
        MAX_SESSIONS: max_sessions,
        UNAVAILABLE: unavailable,
        PREVIOUS_DURATION: previous_duration,
        PRESET_ROOM: preset_room,
    }


def room_count_of(subject: dict[str, Any], default_room_count: int) -> int:
    raw = subject.get(ROOM_COUNT, "")
    if raw in ("", None):
        return default_room_count
    return int(raw)


def build_subject_payloads(state_subjects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for index, subject in enumerate(state_subjects, start=1):
        payloads.append(
            {
                "id": str(index),
                "name": subject.get("name", ""),
                "exam_date": subject.get("exam_date", ""),
                "exam_time": subject.get("exam_time", ""),
                "time": subject.get("exam_time", ""),
                "durationMinutes": subject.get("duration_minutes", 0),
                "roomCount": subject.get("room_count", 0),
            }
        )
    return payloads


def build_preset_dataframe(
    *,
    subjects: list[dict[str, Any]],
    mode: str,
    default_room_count: int,
    assignments: dict[tuple[int, int], list[str]],
) -> pd.DataFrame:
    max_rooms = max(room_count_of(subject, default_room_count) for subject in subjects)
    rows: list[dict[str, Any]] = []
    for room in range(1, max_rooms + 1):
        row: dict[str, Any] = {ROOM_COLUMN: f"\u8003\u573a{room}"}
        for subject_index, subject in enumerate(subjects, start=1):
            name = str(subject[SUBJECT_NAME])
            exam_time = str(subject[EXAM_TIME])
            usable_rooms = room_count_of(subject, default_room_count)
            key = (subject_index, room)
            teacher_names = assignments.get(key, [])
            if mode == "double":
                col1 = f"{name}-\u76d1\u8003\u54581\n{exam_time}"
                col2 = f"{name}-\u76d1\u8003\u54582\n{exam_time}"
                if room <= usable_rooms:
                    row[col1] = teacher_names[0] if len(teacher_names) >= 1 else ""
                    row[col2] = teacher_names[1] if len(teacher_names) >= 2 else ""
                else:
                    row[col1] = ""
                    row[col2] = ""
            else:
                col = f"{name}\n{exam_time}"
                row[col] = teacher_names[0] if room <= usable_rooms and teacher_names else ""
        rows.append(row)
    return pd.DataFrame(rows)


def write_excel(path: Path, rows: list[dict[str, Any]], *, sheet_name: str = "Sheet1") -> None:
    df = pd.DataFrame(rows)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False)


def write_scenario_files(output_dir: Path, scenario: dict[str, Any]) -> None:
    case_dir = output_dir / scenario["slug"]
    case_dir.mkdir(parents=True, exist_ok=True)
    write_excel(case_dir / "subjects.xlsx", scenario["subjects"])
    write_excel(case_dir / "teachers.xlsx", scenario["teachers"])
    if scenario.get("preset_assignments") is not None:
        preset_df = build_preset_dataframe(
            subjects=scenario["subjects"],
            mode=scenario["config"]["mode"],
            default_room_count=int(scenario["config"].get("roomCount", 0) or 0),
            assignments=scenario["preset_assignments"],
        )
        with pd.ExcelWriter(case_dir / "preset.xlsx", engine="openpyxl") as writer:
            preset_df.to_excel(writer, sheet_name=OVERVIEW_SHEET, index=False)

    scenario_meta = {
        "slug": scenario["slug"],
        "description": scenario["description"],
        "operation": scenario["operation"],
        "expected": scenario["expected"],
        "config": scenario["config"],
        "subject_count": len(scenario["subjects"]),
        "teacher_count": len(scenario["teachers"]),
    }
    (case_dir / "scenario.json").write_text(json.dumps(scenario_meta, indent=2, ensure_ascii=False), encoding="utf-8")


def write_readme(output_dir: Path, scenarios: list[dict[str, Any]]) -> None:
    lines = [
        "# Proctoring Stress Cases",
        "",
        "Generated by `python tools/proctoring_stress_cases.py generate`.",
        "",
        "## Cases",
        "",
    ]
    for scenario in scenarios:
        lines.append(f"- `{scenario['slug']}`: {scenario['description']}")
    lines.extend(
        [
            "",
            "## Commands",
            "",
            "- Generate cases: `python tools/proctoring_stress_cases.py generate`",
            "- Run cases: `python tools/proctoring_stress_cases.py run`",
        ]
    )
    (output_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize_assignments(schedule_result: dict[str, Any], *, mode: str = "single") -> dict[str, int]:
    required_slots = 2 if str(mode).strip().lower() == "double" else 1
    total_slots = 0
    assigned_slots = 0
    for subject in schedule_result.get("schedule", []) or []:
        for room in subject.get("rooms", []) or []:
            teachers = list(room.get("teachers", []) or [])[:required_slots]
            total_slots += required_slots
            assigned_slots += sum(1 for teacher in teachers if teacher)
    return {
        "total_slots": total_slots,
        "assigned_slots": assigned_slots,
        "unassigned_slots": max(0, total_slots - assigned_slots),
    }


def get_teacher_name_at(
    schedule_data: list[dict[str, Any]],
    *,
    subject_id: str,
    room_num: int,
    teacher_index: int,
) -> str | None:
    for subject in schedule_data or []:
        if str(subject.get("subjectId")) != str(subject_id):
            continue
        for room in subject.get("rooms", []) or []:
            if int(room.get("roomNum", 0)) != int(room_num):
                continue
            teachers = room.get("teachers", []) or []
            if 0 <= teacher_index < len(teachers):
                teacher = teachers[teacher_index]
                if isinstance(teacher, dict):
                    return str(teacher.get("name") or "")
                return None
    return None


def validate_expected_error(observed: str, expected_parts: list[str]) -> bool:
    return all(part in observed for part in expected_parts)


def evaluate_case(scenario: dict[str, Any], run_summary: dict[str, Any]) -> bool:
    expected = scenario["expected"]
    observed_status = run_summary.get("observed_status", "")
    observed_error = run_summary.get("error", "") or ""
    if expected["kind"] == "success":
        passed = (
            observed_status == "success"
            and run_summary.get("unassigned_slots", 1) == 0
            and not observed_error
        )
        warning_min = int(expected.get("warning_min", 0) or 0)
        if warning_min > 0:
            passed = passed and len(run_summary.get("teacher_import_warnings", [])) >= warning_min
        expected_positions = expected.get("positions", {})
        if expected_positions:
            snapshots = run_summary.get("position_snapshot", {})
            for key, value in expected_positions.items():
                if snapshots.get(key) != value:
                    return False
        return passed
    if expected["kind"] == "error":
        return observed_status == "error" and validate_expected_error(
            observed_error, expected.get("error_contains", [])
        )
    if expected["kind"] == "teacher_import_error":
        teacher_errors = run_summary.get("teacher_import_errors", [])
        warning_parts = expected.get("warning_contains", [])
        warnings = run_summary.get("teacher_import_warnings", [])
        return (
            observed_status == "teacher_import_error"
            and all(part in "\n".join(teacher_errors) for part in expected.get("error_contains", []))
            and all(part in "\n".join(warnings) for part in warning_parts)
        )
    return False


def export_solution(
    case_dir: Path,
    service: ProctoringService,
    result: dict[str, Any],
    subjects: list[dict[str, Any]],
    config: dict[str, Any],
) -> None:
    service.export(
        {
            "path": str(case_dir / "output_schedule.xlsx"),
            "teachers": result.get("teachers", []),
            "subjects": subjects,
            "schedule": result.get("schedule", []),
            "config": config,
        }
    )


def run_case(case_dir: Path, scenario: dict[str, Any]) -> dict[str, Any]:
    state = AppState()
    repo = NoopRepository()
    subjects_service = SubjectsService(state, repo)
    proctoring_service = ProctoringService(state, repo)

    summary: dict[str, Any] = {
        "slug": scenario["slug"],
        "description": scenario["description"],
        "operation": scenario["operation"],
        "expected_kind": scenario["expected"]["kind"],
        "subject_file": str(case_dir / "subjects.xlsx"),
        "teacher_file": str(case_dir / "teachers.xlsx"),
    }

    subject_import = subjects_service.import_from_excel({"path": str(case_dir / "subjects.xlsx")})
    summary["subject_import_errors"] = subject_import.get("errors", [])
    if summary["subject_import_errors"]:
        summary["observed_status"] = "subject_import_error"
        summary["error"] = "\n".join(summary["subject_import_errors"])
        return summary

    subjects = build_subject_payloads(state.subjects)
    config = dict(scenario["config"])
    teacher_import = proctoring_service.import_teachers(
        {
            "path": str(case_dir / "teachers.xlsx"),
            "config": config,
            "subjects": subjects,
        }
    )
    summary["teacher_import_errors"] = teacher_import.get("errors", [])
    summary["teacher_import_warnings"] = teacher_import.get("warnings", [])
    if summary["teacher_import_errors"]:
        summary["observed_status"] = "teacher_import_error"
        summary["error"] = "\n".join(summary["teacher_import_errors"])
        return summary

    teachers = teacher_import.get("teachers", [])

    result: dict[str, Any]
    solve_started = time.perf_counter()
    if scenario["operation"] == "generate":
        result = proctoring_service.generate_schedule(
            {
                "teachers": teachers,
                "subjects": subjects,
                "config": config,
            }
        )
    elif scenario["operation"] == "continue":
        preset_path = case_dir / "preset.xlsx"
        summary["preset_file"] = str(preset_path)
        preset_result = proctoring_service.import_preset(
            {
                "path": str(preset_path),
                "teachers": teachers,
                "subjects": subjects,
                "config": config,
            }
        )
        summary["preset_error"] = preset_result.get("error", "")
        if preset_result.get("error"):
            summary["observed_status"] = "error"
            summary["error"] = str(preset_result["error"])
            summary["solve_seconds"] = 0.0
            return summary
        result = proctoring_service.continue_schedule(
            {
                "teachers": preset_result.get("teachers", teachers),
                "subjects": subjects,
                "schedule": preset_result.get("schedule", []),
                "config": {**config, "lockImported": True},
            }
        )
    elif scenario["operation"] == "import_schedule":
        schedule_path = case_dir / "preset.xlsx"
        summary["preset_file"] = str(schedule_path)
        result = proctoring_service.import_schedule(
            {
                "path": str(schedule_path),
                "teachers": teachers,
                "subjects": subjects,
                "config": config,
            }
        )
    elif scenario["operation"] == "swap":
        schedule_path = case_dir / "preset.xlsx"
        summary["preset_file"] = str(schedule_path)
        imported = proctoring_service.import_schedule(
            {
                "path": str(schedule_path),
                "teachers": teachers,
                "subjects": subjects,
                "config": config,
            }
        )
        if imported.get("error"):
            summary["observed_status"] = "error"
            summary["error"] = str(imported["error"])
            summary["solve_seconds"] = 0.0
            return summary
        swap_result = proctoring_service.swap(
            {
                "p1": scenario["swap_points"]["p1"],
                "p2": scenario["swap_points"]["p2"],
                "teachers": imported.get("teachers", teachers),
                "subjects": subjects,
                "schedule": imported.get("schedule", []),
                "config": config,
            }
        )
        if not swap_result.get("success", False):
            summary["solve_seconds"] = round(time.perf_counter() - solve_started, 3)
            summary["observed_status"] = "error"
            summary["error"] = str(swap_result.get("message") or "swap failed")
            return summary
        result = swap_result
    else:
        raise ValueError(f"Unsupported operation: {scenario['operation']}")
    summary["solve_seconds"] = round(time.perf_counter() - solve_started, 3)

    if result.get("error"):
        summary["observed_status"] = "error"
        summary["error"] = str(result["error"])
        return summary

    counts = summarize_assignments(result, mode=str(config.get("mode", "single")))
    summary["observed_status"] = "success"
    summary.update(counts)
    summary["solver"] = result.get("meta", {}).get("solver")
    summary["solver_status"] = result.get("meta", {}).get("solverStatus")
    summary["optimal"] = bool(result.get("meta", {}).get("optimal", False))
    summary["teacher_count_after"] = len(result.get("teachers", []))
    if scenario.get("position_snapshot"):
        snapshot: dict[str, str | None] = {}
        for key, spec in scenario["position_snapshot"].items():
            snapshot[key] = get_teacher_name_at(
                result.get("schedule", []),
                subject_id=str(spec["subjectId"]),
                room_num=int(spec["room"]),
                teacher_index=int(spec.get("teacherIndex", 0)),
            )
        summary["position_snapshot"] = snapshot
    export_solution(case_dir, proctoring_service, result, subjects, config)
    return summary


def write_run_artifacts(output_dir: Path, results: list[dict[str, Any]]) -> None:
    (output_dir / "report.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# Proctoring Stress Report",
        "",
        "| Case | Expected | Observed | Time(s) | Notes |",
        "| --- | --- | --- | ---: | --- |",
    ]
    for result in results:
        notes: list[str] = []
        if result.get("teacher_import_errors"):
            notes.append(f"errors={len(result['teacher_import_errors'])}")
        if result.get("teacher_import_warnings"):
            notes.append(f"warnings={len(result['teacher_import_warnings'])}")
        if result.get("observed_status") == "success":
            notes.append(f"unassigned={result.get('unassigned_slots', 0)}")
            notes.append(f"solver={result.get('solver_status', '-')}")
        if result.get("error"):
            notes.append(result["error"].replace("\n", " / "))
        lines.append(
            f"| `{result['slug']}` | {result['expected_kind']} | {result.get('observed_status', '-')} | "
            f"{result.get('solve_seconds', 0.0):.3f} | {'; '.join(notes)} |"
        )
    (output_dir / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_single_dense_case() -> dict[str, Any]:
    subjects = [
        subject_row(f"\u79d1\u76ee{index:02d}", date_text, time_text, duration=duration, room_count="")
        for index, (date_text, time_text, duration) in enumerate(
            [
                ("2026-06-20", "09:00-11:00", 120),
                ("2026-06-20", "10:30-12:30", 120),
                ("2026-06-20", "14:00-16:00", 120),
                ("2026-06-21", "09:00-11:30", 150),
                ("2026-06-21", "14:00-15:30", 90),
                ("2026-06-22", "08:30-10:00", 90),
                ("2026-06-22", "10:15-12:15", 120),
                ("2026-06-22", "15:00-17:00", 120),
            ],
            start=1,
        )
    ]
    teachers: list[dict[str, Any]] = []
    for index in range(1, 57):
        unavailable = ""
        if index % 11 == 0:
            unavailable = "1,4"
        elif index % 7 == 0:
            unavailable = "2"
        teachers.append(
            teacher_row(
                f"Teacher-{index:02d}",
                gender="M" if index % 2 else "F",
                is_internal=index % 3 != 0,
                max_sessions=4 if index % 5 else 3,
                unavailable=unavailable,
                previous_duration=(index % 6) * 30,
                preset_room=((index - 1) % 20) + 1 if index <= 6 else "",
            )
        )
    return {
        "slug": "case01_single_dense_default_rooms",
        "description": "Single-monitor dense schedule with default room count and mild restrictions.",
        "operation": "generate",
        "config": {
            "roomCount": 20,
            "mode": "single",
            "balanceMode": "duration",
            "cpSatTimeLimitSeconds": 20,
            "cpSatNumWorkers": 4,
            "cpSatNoImprovementSeconds": 3,
            "cpSatProgressIntervalSeconds": 0.5,
        },
        "subjects": subjects,
        "teachers": teachers,
        "expected": {"kind": "success"},
    }


def build_double_mixed_case() -> dict[str, Any]:
    subjects = [
        subject_row(f"\u79d1\u76ee{index:02d}", date_text, time_text, duration=duration, room_count=16)
        for index, (date_text, time_text, duration) in enumerate(
            [
                ("2026-06-25", "09:00-11:00", 120),
                ("2026-06-25", "14:00-16:00", 120),
                ("2026-06-26", "09:00-10:30", 90),
                ("2026-06-26", "10:45-12:15", 90),
                ("2026-06-27", "09:00-11:30", 150),
                ("2026-06-27", "14:00-16:30", 150),
            ],
            start=1,
        )
    ]
    teachers: list[dict[str, Any]] = []
    groups = [
        ("MI", "M", True),
        ("FE", "F", False),
        ("FI", "F", True),
        ("ME", "M", False),
    ]
    counter = 1
    for _label, gender, is_internal in groups:
        for _ in range(12):
            unavailable = ""
            if counter % 10 == 0:
                unavailable = "2"
            elif counter % 13 == 0:
                unavailable = "5"
            teachers.append(
                teacher_row(
                    f"Teacher-{counter:02d}",
                    gender=gender,
                    is_internal=is_internal,
                    max_sessions=5,
                    unavailable=unavailable,
                    previous_duration=(counter % 5) * 20,
                )
            )
            counter += 1
    return {
        "slug": "case02_double_mixed_constraints",
        "description": "Double-monitor case with gender and internal/external pairing constraints.",
        "operation": "generate",
        "config": {
            "roomCount": 0,
            "mode": "double",
            "balanceMode": "session",
            "genderMix": True,
            "internalMix": True,
            "cpSatTimeLimitSeconds": 25,
            "cpSatNumWorkers": 4,
            "cpSatNoImprovementSeconds": 3,
            "cpSatProgressIntervalSeconds": 0.5,
        },
        "subjects": subjects,
        "teachers": teachers,
        "expected": {"kind": "success"},
    }


def build_variable_room_case() -> dict[str, Any]:
    subjects = [
        subject_row(
            f"\u79d1\u76ee{index:02d}",
            date_text,
            time_text,
            duration=duration,
            room_count=room_count,
        )
        for index, (date_text, time_text, duration, room_count) in enumerate(
            [
                ("2026-07-01", "09:00-10:30", 90, 6),
                ("2026-07-01", "10:00-11:30", 90, 12),
                ("2026-07-01", "14:00-16:00", 120, 8),
                ("2026-07-02", "09:00-11:30", 150, 14),
                ("2026-07-02", "10:15-12:00", 105, 10),
                ("2026-07-02", "15:00-16:00", 60, 7),
                ("2026-07-03", "09:00-11:00", 120, 9),
            ],
            start=1,
        )
    ]
    teachers: list[dict[str, Any]] = []
    for index in range(1, 31):
        unavailable = ""
        if index % 9 == 0:
            unavailable = "2,4"
        elif index % 8 == 0:
            unavailable = "5"
        teachers.append(
            teacher_row(
                f"Teacher-{index:02d}",
                gender="M" if index % 2 else "F",
                is_internal=index % 4 != 0,
                max_sessions=4,
                unavailable=unavailable,
                previous_duration=(index % 4) * 15,
                preset_room=((index - 1) % 14) + 1 if index <= 4 else "",
            )
        )
    return {
        "slug": "case03_variable_rooms_overlap",
        "description": "Single-monitor case with per-subject room counts, overlaps, and anti-consecutive preference.",
        "operation": "generate",
        "config": {
            "roomCount": 0,
            "mode": "single",
            "balanceMode": "duration",
            "avoidConsecutiveSessions": True,
            "cpSatTimeLimitSeconds": 20,
            "cpSatNumWorkers": 4,
            "cpSatNoImprovementSeconds": 3,
            "cpSatProgressIntervalSeconds": 0.5,
        },
        "subjects": subjects,
        "teachers": teachers,
        "expected": {"kind": "success"},
    }


def build_capacity_shortfall_case() -> dict[str, Any]:
    subjects = [
        subject_row(f"\u79d1\u76ee{index:02d}", date_text, time_text, duration=120, room_count="")
        for index, (date_text, time_text) in enumerate(
            [
                ("2026-07-10", "09:00-11:00"),
                ("2026-07-10", "14:00-16:00"),
                ("2026-07-11", "09:00-11:00"),
                ("2026-07-11", "14:00-16:00"),
            ],
            start=1,
        )
    ]
    teachers = [
        teacher_row(
            f"Teacher-{index:02d}",
            gender="M" if index % 2 else "F",
            is_internal=True,
            max_sessions=2,
            previous_duration=0,
        )
        for index in range(1, 11)
    ]
    return {
        "slug": "case04_capacity_shortfall",
        "description": "Single-monitor case that should fail fast because total capacity is insufficient.",
        "operation": "generate",
        "config": {
            "roomCount": 12,
            "mode": "single",
            "balanceMode": "duration",
            "cpSatTimeLimitSeconds": 10,
            "cpSatNumWorkers": 2,
        },
        "subjects": subjects,
        "teachers": teachers,
        "expected": {"kind": "error", "error_contains": ["\u5168\u5c40\u76d1\u8003\u540d\u989d\u4e0d\u8db3"]},
    }


def build_pairing_impossible_case() -> dict[str, Any]:
    subjects = [
        subject_row(f"\u79d1\u76ee{index:02d}", date_text, time_text, duration=120, room_count=10)
        for index, (date_text, time_text) in enumerate(
            [
                ("2026-07-15", "09:00-11:00"),
                ("2026-07-15", "14:00-16:00"),
                ("2026-07-16", "09:00-11:00"),
            ],
            start=1,
        )
    ]
    teachers: list[dict[str, Any]] = []
    for index in range(1, 21):
        gender = "M" if index <= 18 else "F"
        is_internal = True if index <= 18 else False
        teachers.append(
            teacher_row(
                f"Teacher-{index:02d}",
                gender=gender,
                is_internal=is_internal,
                max_sessions=3,
                previous_duration=0,
            )
        )
    return {
        "slug": "case05_pairing_impossible",
        "description": "Double-monitor case that is infeasible under gender plus internal/external pairing rules.",
        "operation": "generate",
        "config": {
            "roomCount": 0,
            "mode": "double",
            "balanceMode": "session",
            "genderMix": True,
            "internalMix": True,
            "cpSatTimeLimitSeconds": 10,
            "cpSatNumWorkers": 2,
        },
        "subjects": subjects,
        "teachers": teachers,
        "expected": {"kind": "error", "error_contains": ["\u6027\u522b+\u672c\u5916\u6821"]},
    }


def build_dirty_teacher_import_case() -> dict[str, Any]:
    subjects = [
        subject_row(f"\u79d1\u76ee{index:02d}", "2026-07-20", time_text, duration=120, room_count=6)
        for index, time_text in enumerate(["09:00-11:00", "14:00-16:00", "16:30-18:00", "19:00-20:30"], start=1)
    ]
    teachers = [
        teacher_row("Teacher-01", gender="M", is_internal=True, max_sessions=2, unavailable="", previous_duration=0),
        teacher_row("Teacher-01", gender="F", is_internal=False, max_sessions=2, unavailable="", previous_duration=10),
        teacher_row("Teacher-03", gender="M", is_internal=True, max_sessions="abc", unavailable="", previous_duration=15),
        teacher_row("Teacher-04", gender="F", is_internal=False, max_sessions=1, unavailable="999,UnknownSubject", previous_duration=-30, preset_room="room-x"),
    ]
    return {
        "slug": "case06_dirty_teacher_import",
        "description": "Teacher import robustness case with duplicate names and malformed cells.",
        "operation": "generate",
        "config": {
            "roomCount": 0,
            "mode": "single",
            "balanceMode": "duration",
        },
        "subjects": subjects,
        "teachers": teachers,
        "expected": {
            "kind": "teacher_import_error",
            "error_contains": [
                "\u6559\u5e08\u59d3\u540d\u5b58\u5728\u91cd\u590d",
                "\u6700\u5927\u76d1\u8003\u6bb5\u6570\u4e0d\u662f\u6570\u5b57",
                "\u65e0\u6cd5\u8bc6\u522b\u7684\u9879",
                "\u8d8a\u754c\u7f16\u53f7",
                "\u5386\u6b21\u76d1\u8003\u65f6\u957f\u4e0d\u80fd\u4e3a\u8d1f\u6570",
            ],
            "warning_contains": ["\u9884\u8bbe\u76d1\u8003\u8003\u573a"],
        },
    }


def build_locked_conflict_case() -> dict[str, Any]:
    subjects = [
        subject_row("\u79d1\u76ee01", "2026-07-25", "09:00-11:00", duration=120, room_count=3),
        subject_row("\u79d1\u76ee02", "2026-07-25", "10:00-12:00", duration=120, room_count=3),
    ]
    teachers = [
        teacher_row("Teacher-01", gender="M", is_internal=True, max_sessions=2),
        teacher_row("Teacher-02", gender="F", is_internal=False, max_sessions=2),
        teacher_row("Teacher-03", gender="M", is_internal=True, max_sessions=2),
        teacher_row("Teacher-04", gender="F", is_internal=False, max_sessions=2),
        teacher_row("Teacher-05", gender="M", is_internal=True, max_sessions=2),
    ]
    preset_assignments = {
        (1, 1): ["Teacher-01"],
        (2, 1): ["Teacher-01"],
    }
    return {
        "slug": "case07_locked_conflict_continue",
        "description": "Continue-scheduling case with overlapping locked assignments for the same teacher.",
        "operation": "continue",
        "config": {
            "roomCount": 0,
            "mode": "single",
            "balanceMode": "duration",
            "cpSatTimeLimitSeconds": 10,
            "cpSatNumWorkers": 2,
        },
        "subjects": subjects,
        "teachers": teachers,
        "preset_assignments": preset_assignments,
        "expected": {"kind": "error", "error_contains": ["\u5bfc\u5165\u7684\u9501\u5b9a\u5b89\u6392\u5b58\u5728\u51b2\u7a81"]},
    }


def build_feasible_continue_case() -> dict[str, Any]:
    subjects = [
        subject_row(f"\u79d1\u76ee{index:02d}", date_text, time_text, duration=duration, room_count="")
        for index, (date_text, time_text, duration) in enumerate(
            [
                ("2026-08-01", "09:00-11:00", 120),
                ("2026-08-01", "14:00-16:00", 120),
                ("2026-08-02", "09:00-10:30", 90),
                ("2026-08-02", "10:45-12:15", 90),
            ],
            start=1,
        )
    ]
    teachers: list[dict[str, Any]] = []
    groups = [
        ("M", True),
        ("F", False),
        ("F", True),
        ("M", False),
    ]
    counter = 1
    for gender, is_internal in groups:
        for _ in range(6):
            teachers.append(
                teacher_row(
                    f"Teacher-{counter:02d}",
                    gender=gender,
                    is_internal=is_internal,
                    max_sessions=4,
                    previous_duration=(counter % 3) * 30,
                )
            )
            counter += 1
    preset_assignments = {
        (1, 1): ["Teacher-01", "Teacher-07"],
        (1, 2): ["Teacher-13", "Teacher-19"],
        (2, 1): ["Teacher-02", "Teacher-08"],
        (3, 1): ["Teacher-03", "Teacher-09"],
    }
    return {
        "slug": "case08_feasible_continue_partial_preset",
        "description": "Feasible continue-scheduling case with partial double-monitor preset assignments.",
        "operation": "continue",
        "config": {
            "roomCount": 8,
            "mode": "double",
            "balanceMode": "duration",
            "genderMix": True,
            "internalMix": True,
            "cpSatTimeLimitSeconds": 20,
            "cpSatNumWorkers": 4,
            "cpSatNoImprovementSeconds": 3,
            "cpSatProgressIntervalSeconds": 0.5,
        },
        "subjects": subjects,
        "teachers": teachers,
        "preset_assignments": preset_assignments,
        "expected": {"kind": "success"},
    }


def build_gender_only_case() -> dict[str, Any]:
    subjects = [
        subject_row(f"\u79d1\u76ee{index:02d}", date_text, time_text, duration=120, room_count=6)
        for index, (date_text, time_text) in enumerate(
            [
                ("2026-08-05", "09:00-11:00"),
                ("2026-08-05", "14:00-16:00"),
                ("2026-08-06", "09:00-11:00"),
                ("2026-08-06", "14:00-16:00"),
            ],
            start=1,
        )
    ]
    teachers = [
        teacher_row(
            f"Teacher-{index:02d}",
            gender="M" if index <= 6 else "F",
            is_internal=True,
            max_sessions=4,
            previous_duration=(index % 3) * 20,
        )
        for index in range(1, 13)
    ]
    return {
        "slug": "case09_double_gender_only",
        "description": "Double-monitor case with only gender-mix enabled.",
        "operation": "generate",
        "config": {
            "roomCount": 0,
            "mode": "double",
            "balanceMode": "duration",
            "genderMix": True,
            "internalMix": False,
            "cpSatTimeLimitSeconds": 12,
            "cpSatNumWorkers": 4,
        },
        "subjects": subjects,
        "teachers": teachers,
        "expected": {"kind": "success"},
    }


def build_internal_only_case() -> dict[str, Any]:
    subjects = [
        subject_row(f"\u79d1\u76ee{index:02d}", date_text, time_text, duration=120, room_count=6)
        for index, (date_text, time_text) in enumerate(
            [
                ("2026-08-08", "09:00-11:00"),
                ("2026-08-08", "14:00-16:00"),
                ("2026-08-09", "09:00-11:00"),
                ("2026-08-09", "14:00-16:00"),
            ],
            start=1,
        )
    ]
    teachers = [
        teacher_row(
            f"Teacher-{index:02d}",
            gender="M" if index % 2 else "F",
            is_internal=index <= 6,
            max_sessions=4,
            previous_duration=(index % 4) * 15,
        )
        for index in range(1, 13)
    ]
    return {
        "slug": "case10_double_internal_only",
        "description": "Double-monitor case with only internal/external mix enabled.",
        "operation": "generate",
        "config": {
            "roomCount": 0,
            "mode": "double",
            "balanceMode": "session",
            "genderMix": False,
            "internalMix": True,
            "cpSatTimeLimitSeconds": 12,
            "cpSatNumWorkers": 4,
        },
        "subjects": subjects,
        "teachers": teachers,
        "expected": {"kind": "success"},
    }


def build_room_repeat_fixed_case() -> dict[str, Any]:
    subjects = [
        subject_row(f"\u79d1\u76ee{index:02d}", "2026-08-12", time_text, duration=90, room_count=6)
        for index, time_text in enumerate(
            ["08:30-10:00", "10:30-12:00", "14:00-15:30", "16:00-17:30"],
            start=1,
        )
    ]
    teachers = [
        teacher_row(
            f"Teacher-{index:02d}",
            gender="M" if index % 2 else "F",
            is_internal=index % 3 != 0,
            max_sessions=3,
            previous_duration=(index % 5) * 10,
        )
        for index in range(1, 13)
    ]
    return {
        "slug": "case11_room_repeat_fixed",
        "description": "Single-monitor case with fixed-room preference enabled.",
        "operation": "generate",
        "config": {
            "roomCount": 0,
            "mode": "single",
            "balanceMode": "duration",
            "roomRepeatPreference": "fixed",
            "cpSatTimeLimitSeconds": 12,
            "cpSatNumWorkers": 4,
        },
        "subjects": subjects,
        "teachers": teachers,
        "expected": {"kind": "success"},
    }


def build_room_repeat_different_case() -> dict[str, Any]:
    subjects = [
        subject_row(f"\u79d1\u76ee{index:02d}", "2026-08-13", time_text, duration=90, room_count=6)
        for index, time_text in enumerate(
            ["08:30-10:00", "10:30-12:00", "14:00-15:30", "16:00-17:30"],
            start=1,
        )
    ]
    teachers = [
        teacher_row(
            f"Teacher-{index:02d}",
            gender="M" if index % 2 else "F",
            is_internal=index % 4 != 0,
            max_sessions=3,
            previous_duration=(index % 5) * 10,
        )
        for index in range(1, 13)
    ]
    return {
        "slug": "case12_room_repeat_different",
        "description": "Single-monitor case with different-room preference enabled.",
        "operation": "generate",
        "config": {
            "roomCount": 0,
            "mode": "single",
            "balanceMode": "duration",
            "roomRepeatPreference": "different",
            "cpSatTimeLimitSeconds": 12,
            "cpSatNumWorkers": 4,
        },
        "subjects": subjects,
        "teachers": teachers,
        "expected": {"kind": "success"},
    }


def build_preset_warning_case() -> dict[str, Any]:
    subjects = [
        subject_row(f"\u79d1\u76ee{index:02d}", date_text, time_text, duration=120, room_count="")
        for index, (date_text, time_text) in enumerate(
            [
                ("2026-08-16", "09:00-11:00"),
                ("2026-08-16", "14:00-16:00"),
                ("2026-08-17", "09:00-11:00"),
            ],
            start=1,
        )
    ]
    teachers = [
        teacher_row("Teacher-01", gender="M", is_internal=True, max_sessions=2, preset_room=99),
        teacher_row("Teacher-02", gender="F", is_internal=False, max_sessions=2, preset_room="room-x"),
        teacher_row("Teacher-03", gender="M", is_internal=True, max_sessions=2, preset_room=1),
        teacher_row("Teacher-04", gender="F", is_internal=False, max_sessions=2),
        teacher_row("Teacher-05", gender="M", is_internal=True, max_sessions=2),
        teacher_row("Teacher-06", gender="F", is_internal=False, max_sessions=2),
    ]
    return {
        "slug": "case13_invalid_preset_warning_success",
        "description": "Teacher import warnings for invalid preset rooms should not block scheduling.",
        "operation": "generate",
        "config": {
            "roomCount": 2,
            "mode": "single",
            "balanceMode": "duration",
            "cpSatTimeLimitSeconds": 10,
            "cpSatNumWorkers": 2,
        },
        "subjects": subjects,
        "teachers": teachers,
        "expected": {"kind": "success", "warning_min": 2},
    }


def build_import_schedule_case() -> dict[str, Any]:
    subjects = [
        subject_row("\u79d1\u76ee01", "2026-08-20", "09:00-11:00", duration=120, room_count=3),
        subject_row("\u79d1\u76ee02", "2026-08-20", "14:00-16:00", duration=120, room_count=3),
    ]
    teachers = [
        teacher_row("Teacher-01", gender="M", is_internal=True, max_sessions=2),
        teacher_row("Teacher-02", gender="F", is_internal=False, max_sessions=2),
        teacher_row("Teacher-03", gender="M", is_internal=True, max_sessions=2),
        teacher_row("Teacher-04", gender="F", is_internal=False, max_sessions=2),
        teacher_row("Teacher-05", gender="M", is_internal=True, max_sessions=2),
        teacher_row("Teacher-06", gender="F", is_internal=False, max_sessions=2),
    ]
    preset_assignments = {
        (1, 1): ["Teacher-01"],
        (1, 2): ["Teacher-02"],
        (1, 3): ["Teacher-03"],
        (2, 1): ["Teacher-04"],
        (2, 2): ["Teacher-05"],
        (2, 3): ["Teacher-06"],
    }
    return {
        "slug": "case14_import_schedule_complete",
        "description": "Import a complete single-monitor schedule workbook.",
        "operation": "import_schedule",
        "config": {
            "roomCount": 0,
            "mode": "single",
            "balanceMode": "duration",
        },
        "subjects": subjects,
        "teachers": teachers,
        "preset_assignments": preset_assignments,
        "expected": {"kind": "success"},
    }


def build_swap_success_case() -> dict[str, Any]:
    subjects = [
        subject_row("\u79d1\u76ee01", "2026-08-22", "09:00-11:00", duration=120, room_count=2),
    ]
    teachers = [
        teacher_row("Teacher-01", gender="M", is_internal=True, max_sessions=1),
        teacher_row("Teacher-02", gender="F", is_internal=False, max_sessions=1),
    ]
    preset_assignments = {
        (1, 1): ["Teacher-01"],
        (1, 2): ["Teacher-02"],
    }
    return {
        "slug": "case15_swap_success",
        "description": "Manual swap succeeds on an imported complete schedule.",
        "operation": "swap",
        "config": {
            "roomCount": 0,
            "mode": "single",
            "balanceMode": "duration",
        },
        "subjects": subjects,
        "teachers": teachers,
        "preset_assignments": preset_assignments,
        "swap_points": {
            "p1": {"room": 1, "subId": "1", "tIdx": 0},
            "p2": {"room": 2, "subId": "1", "tIdx": 0},
        },
        "position_snapshot": {
            "subject1-room1-slot0": {"subjectId": "1", "room": 1, "teacherIndex": 0},
            "subject1-room2-slot0": {"subjectId": "1", "room": 2, "teacherIndex": 0},
        },
        "expected": {
            "kind": "success",
            "positions": {
                "subject1-room1-slot0": "Teacher-02",
                "subject1-room2-slot0": "Teacher-01",
            },
        },
    }


def build_swap_preset_block_case() -> dict[str, Any]:
    subjects = [
        subject_row("\u79d1\u76ee01", "2026-08-23", "09:00-11:00", duration=120, room_count=2),
    ]
    teachers = [
        teacher_row("Teacher-01", gender="M", is_internal=True, max_sessions=1, preset_room=1),
        teacher_row("Teacher-02", gender="F", is_internal=False, max_sessions=1),
    ]
    preset_assignments = {
        (1, 1): ["Teacher-01"],
        (1, 2): ["Teacher-02"],
    }
    return {
        "slug": "case16_swap_blocked_by_preset",
        "description": "Manual swap is rejected when a teacher has a fixed preset room.",
        "operation": "swap",
        "config": {
            "roomCount": 0,
            "mode": "single",
            "balanceMode": "duration",
        },
        "subjects": subjects,
        "teachers": teachers,
        "preset_assignments": preset_assignments,
        "swap_points": {
            "p1": {"room": 1, "subId": "1", "tIdx": 0},
            "p2": {"room": 2, "subId": "1", "tIdx": 0},
        },
        "expected": {"kind": "error", "error_contains": ["\u9884\u8bbe\u623f\u95f4\u4e3a"]},
    }


def build_scenarios() -> list[dict[str, Any]]:
    return [
        build_single_dense_case(),
        build_double_mixed_case(),
        build_variable_room_case(),
        build_capacity_shortfall_case(),
        build_pairing_impossible_case(),
        build_dirty_teacher_import_case(),
        build_locked_conflict_case(),
        build_feasible_continue_case(),
        build_gender_only_case(),
        build_internal_only_case(),
        build_room_repeat_fixed_case(),
        build_room_repeat_different_case(),
        build_preset_warning_case(),
        build_import_schedule_case(),
        build_swap_success_case(),
        build_swap_preset_block_case(),
    ]


def generate_cases(output_dir: Path, *, clean: bool) -> None:
    scenarios = build_scenarios()
    if clean and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for scenario in scenarios:
        write_scenario_files(output_dir, scenario)
    write_readme(output_dir, scenarios)
    print(f"Generated {len(scenarios)} cases in {output_dir}")


def run_cases(output_dir: Path) -> int:
    scenarios = build_scenarios()
    results: list[dict[str, Any]] = []
    failed = 0
    for scenario in scenarios:
        case_dir = output_dir / scenario["slug"]
        if not case_dir.exists():
            raise FileNotFoundError(f"Missing case directory: {case_dir}. Run generate first.")
        result = run_case(case_dir, scenario)
        result["passed"] = evaluate_case(scenario, result)
        if not result["passed"]:
            failed += 1
        (case_dir / "result.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        results.append(result)
        status_text = "PASS" if result["passed"] else "FAIL"
        print(
            f"[{status_text}] {scenario['slug']} -> {result.get('observed_status', '-')}"
            f" ({result.get('solve_seconds', 0.0):.3f}s)"
        )
        if result.get("error"):
            print(f"    {result['error']}")
    write_run_artifacts(output_dir, results)
    print(f"Wrote report to {output_dir / 'report.md'}")
    return 1 if failed else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and run proctoring stress cases.")
    parser.add_argument(
        "command",
        choices=["generate", "run"],
        help="`generate` creates files under testdata; `run` executes all scenarios and writes a report.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path("testdata") / "proctoring-stress-cases"),
        help="Directory used to store generated cases and reports.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove the output directory before generating cases.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if args.command == "generate":
        generate_cases(output_dir, clean=args.clean)
        return 0
    return run_cases(output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
