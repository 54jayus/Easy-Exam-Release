from __future__ import annotations

from backend.rpc_server import build_dispatch


def main() -> int:
    dispatch = build_dispatch()

    dispatch["subjects.update"](
        {
            "subjects": [
                {
                    "name": "语文",
                    "exam_date": "2026-01-01",
                    "exam_time": "09:00-11:00",
                    "duration_minutes": 120,
                    "remark": "",
                },
                {
                    "name": "数学",
                    "exam_date": "2026-01-01",
                    "exam_time": "14:00-16:00",
                    "duration_minutes": 120,
                    "remark": "",
                },
            ]
        }
    )
    subjects_full = dispatch["subjects.list"]({})["subjects"]
    subjects_minimal = [{"id": s["id"], "name": s["name"], "time": s.get("exam_time", "")} for s in subjects_full]

    teachers = [
        {
            "id": "张三",
            "name": "张三",
            "gender": "M",
            "isInternal": True,
            "maxSessions": 2,
            "unavailableSubjects": [],
            "presetRoom": None,
            "previousSupervisionDuration": 0,
        },
        {
            "id": "李四",
            "name": "李四",
            "gender": "F",
            "isInternal": True,
            "maxSessions": 2,
            "unavailableSubjects": [],
            "presetRoom": None,
            "previousSupervisionDuration": 0,
        },
        {
            "id": "王五",
            "name": "王五",
            "gender": "M",
            "isInternal": False,
            "maxSessions": 2,
            "unavailableSubjects": [],
            "presetRoom": None,
            "previousSupervisionDuration": 0,
        },
        {
            "id": "赵六",
            "name": "赵六",
            "gender": "F",
            "isInternal": False,
            "maxSessions": 2,
            "unavailableSubjects": [],
            "presetRoom": None,
            "previousSupervisionDuration": 0,
        },
    ]

    config = {
        "roomCount": 2,
        "mode": "double",
        "balanceMode": "session",
        "genderMix": False,
        "internalMix": False,
    }

    res = dispatch["proctoring.generateSchedule"]({"teachers": teachers, "subjects": subjects_minimal, "config": config})
    print("meta:", res.get("meta"))
    print("subjects:", [s.get("name") for s in subjects_minimal])
    print("schedule_subject_count:", len(res.get("schedule") or []))
    first_subject = (res.get("schedule") or [None])[0]
    if first_subject:
        rooms = first_subject.get("rooms") or []
        if rooms:
            print("first_room_teachers:", rooms[0].get("teachers"))

    teachers_after = res.get("teachers") or []
    if teachers_after:
        print("first_teacher_current_minutes:", teachers_after[0].get("supervisionDuration"))

    optimized = dispatch["proctoring.optimize"](
        {
            "teachers": teachers_after,
            "subjects": subjects_minimal,
            "schedule": res.get("schedule"),
            "config": config,
        }
    )
    print("optimize_schedule_subject_count:", len(optimized.get("schedule") or []))
    print("optimize_detail_swap_count:", len((optimized.get("optimizationDetails") or {}).get("swaps") or []))
    print("optimize_detail_preset_count:", len((optimized.get("optimizationDetails") or {}).get("presetDetails") or []))

    swapped = dispatch["proctoring.swap"](
        {
            "p1": {"room": 1, "subId": "1", "tIdx": 0},
            "p2": {"room": 2, "subId": "1", "tIdx": 0},
            "teachers": optimized.get("teachers"),
            "subjects": subjects_minimal,
            "schedule": optimized.get("schedule"),
            "config": config,
        }
    )
    print("swap_success:", swapped.get("success"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
