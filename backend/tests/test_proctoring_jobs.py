from __future__ import annotations

import time

from backend.application.proctoring_jobs import ProctoringJobManager


def test_job_manager_exposes_stage_preview_result_while_running() -> None:
    preview_result = {
        "schedule": [{"subjectId": "1", "subjectName": "语文", "rooms": []}],
        "teachers": [{"id": "张老师", "name": "张老师"}],
        "meta": {"complete": False, "isPreview": True},
    }
    final_result = {
        "schedule": [{"subjectId": "1", "subjectName": "语文", "rooms": []}],
        "teachers": [{"id": "张老师", "name": "张老师"}],
    }

    def execute_operation(operation: str, params: dict, *, progress_observer=None):
        assert operation == "generate"
        assert params == {"operation": "generate"}
        assert progress_observer is not None

        progress_observer({"type": "solve_started", "stage_count": 2})
        progress_observer(
            {
                "type": "stage_started",
                "name": "minimize_max_count",
                "stage_index": 1,
                "stage_count": 2,
                "maximize": False,
            }
        )
        progress_observer(
            {
                "type": "stage_finished",
                "name": "minimize_max_count",
                "stage_index": 1,
                "stage_count": 2,
                "status": "FEASIBLE",
                "value": 1,
                "preview_result": preview_result,
            }
        )
        time.sleep(0.2)
        return final_result

    manager = ProctoringJobManager(execute_operation)
    started = manager.start_solver_job({"operation": "generate"})
    job_id = started["jobId"]

    time.sleep(0.05)
    running = manager.get_job_status({"jobId": job_id})
    assert running["status"] == "running"
    assert running["progress"]["previewResult"] == preview_result
    assert running["progress"]["previewStageIndex"] == 1
    assert running["progress"]["previewStageName"] == "minimize_max_count"
    assert running["progress"]["stages"][0]["name"] == "minimize_max_count"
    assert "preview_result" not in running["progress"]["stages"][0]

    time.sleep(0.25)
    completed = manager.get_job_status({"jobId": job_id})
    assert completed["status"] == "completed"
    assert completed["result"] == final_result
