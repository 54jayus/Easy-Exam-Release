from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

from backend.application.dashboard_service import DashboardService
from backend.domain.state import AppState


def test_dashboard_stats_show_empty_workflow_defaults() -> None:
    result = DashboardService(AppState()).get_stats({})

    stats = result["stats"]
    workflow = result["workflow"]

    assert stats[0]["value"] == "0"
    assert stats[0]["trend"] == "未设置"
    assert stats[1]["trend"] == "未导入"
    assert stats[2]["trend"] == "未设置"
    assert stats[3]["value"] == "未开始"
    assert [item["status"] for item in workflow] == ["current", "pending", "pending", "pending"]


def test_dashboard_stats_detect_complete_schedule_and_rooms() -> None:
    state = AppState()
    state.subjects = [{"name": "语文"}]
    state.proctoring.teachers = [{"name": "张老师"}, {"name": "李老师"}]
    state.proctoring.config = {"mode": "double"}
    state.proctoring.schedule = [
        {
            "rooms": [
                {"teachers": [{"name": "张老师"}, {"name": "李老师"}]},
            ]
        }
    ]
    state.exam_arrangement = SimpleNamespace(total_rooms=2, arranged_students=pd.DataFrame([{"姓名": "张三"}, {"姓名": "李四"}]))

    result = DashboardService(state).get_stats({})

    stats = result["stats"]
    workflow = result["workflow"]

    assert stats[1]["value"] == "2"
    assert stats[1]["trend"] == "充足"
    assert stats[2]["value"] == "2"
    assert stats[2]["trend"] == "已编排"
    assert stats[3]["value"] == "进行中"
    assert [item["status"] for item in workflow] == ["completed", "completed", "completed", "current"]
