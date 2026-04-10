from __future__ import annotations

import copy
import threading
import time
import traceback
import uuid
from typing import Any, Callable

from .proctoring_support import _to_int


class ProctoringJobManager:
    def __init__(self, execute_operation: Callable[..., Any]):
        self._execute_operation = execute_operation
        self._job_lock = threading.Lock()
        self._jobs: dict[str, dict[str, Any]] = {}

    def _trim_jobs_locked(self, keep_last: int = 12) -> None:
        if len(self._jobs) <= keep_last:
            return
        finished_jobs = [
            (job.get("finished_monotonic", 0.0), job_id)
            for job_id, job in self._jobs.items()
            if job.get("status") in {"completed", "failed"}
        ]
        finished_jobs.sort()
        while len(self._jobs) > keep_last and finished_jobs:
            _, job_id = finished_jobs.pop(0)
            self._jobs.pop(job_id, None)

    def _active_job_id_locked(self) -> str | None:
        for job_id, job in self._jobs.items():
            if job.get("status") in {"queued", "running"}:
                return job_id
        return None

    def _append_progress_sample_locked(self, job: dict[str, Any], sample: dict[str, Any] | None) -> None:
        if not sample:
            return
        progress = job["progress"]
        samples = progress.setdefault("progressSamples", [])
        marker = (
            sample.get("stage"),
            sample.get("elapsedSeconds"),
            sample.get("reason"),
            sample.get("objectiveValue"),
            sample.get("bestBound"),
        )
        if samples:
            last = samples[-1]
            last_marker = (
                last.get("stage"),
                last.get("elapsedSeconds"),
                last.get("reason"),
                last.get("objectiveValue"),
                last.get("bestBound"),
            )
            if last_marker == marker:
                return
        samples.append(dict(sample))
        if len(samples) > 200:
            del samples[:-200]

    def _update_job_progress(self, job_id: str, event: dict[str, Any]) -> None:
        now = time.monotonic()
        with self._job_lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            progress = job["progress"]
            event_type = str(event.get("type") or "")
            progress["lastEventType"] = event_type
            progress["lastUpdatedMonotonic"] = now

            if event_type == "solve_started":
                progress["stageCount"] = _to_int(event.get("stage_count"), 0)
                progress["timeLimitSeconds"] = event.get("time_limit_seconds")
                progress["progressIntervalSeconds"] = event.get("progress_interval_seconds")
                progress["noImprovementLimitSeconds"] = event.get("no_improvement_limit_seconds")
                progress["previewResult"] = None
                progress["previewStageIndex"] = 0
                progress["previewStageName"] = ""
                return

            if event_type == "stage_started":
                progress["currentStageName"] = event.get("name")
                progress["currentStageIndex"] = _to_int(event.get("stage_index"), 0)
                progress["stageCount"] = _to_int(event.get("stage_count"), progress.get("stageCount", 0))
                progress["currentStageMaximize"] = bool(event.get("maximize", False))
                job["current_stage_started_monotonic"] = now
                return

            if event_type == "stage_progress":
                progress["currentStageName"] = event.get("name")
                progress["currentStageIndex"] = _to_int(event.get("stage_index"), progress.get("currentStageIndex", 0))
                progress["stageCount"] = _to_int(event.get("stage_count"), progress.get("stageCount", 0))
                progress["currentStageStatus"] = event.get("status")
                progress["currentStageReason"] = event.get("reason")
                progress["currentStageSolveSeconds"] = event.get("solve_seconds")
                progress["solutionCount"] = event.get("solution_count")
                progress["improvementCount"] = event.get("improvement_count")
                progress["firstSolutionSeconds"] = event.get("first_solution_seconds")
                progress["lastSolutionSeconds"] = event.get("last_solution_seconds")
                progress["lastImprovementSeconds"] = event.get("last_improvement_seconds")
                progress["idleAfterLastImprovementSeconds"] = event.get("idle_after_last_improvement_seconds")
                progress["bestObjectiveValue"] = event.get("best_objective_value")
                progress["bestBound"] = event.get("best_bound")
                progress["objectiveGap"] = event.get("objective_gap")
                self._append_progress_sample_locked(job, event.get("latest_sample"))
                return

            if event_type == "stage_finished":
                stages = progress.setdefault("stages", [])
                stage_index = _to_int(event.get("stage_index"), 0)
                stage_payload = {
                    k: v
                    for k, v in event.items()
                    if k not in {"type", "preview_result"}
                }
                replaced = False
                for idx, stage in enumerate(stages):
                    if _to_int(stage.get("stage_index"), 0) == stage_index:
                        stages[idx] = stage_payload
                        replaced = True
                        break
                if not replaced:
                    stages.append(stage_payload)
                    stages.sort(key=lambda item: _to_int(item.get("stage_index"), 10**9))
                for sample in event.get("progress_samples", []) or []:
                    self._append_progress_sample_locked(job, sample)
                progress["currentStageStatus"] = event.get("status")
                progress["solutionCount"] = event.get("solution_count")
                progress["improvementCount"] = event.get("improvement_count")
                progress["lastImprovementSeconds"] = event.get("last_improvement_seconds")
                progress["idleAfterLastImprovementSeconds"] = event.get("idle_after_last_improvement_seconds")
                progress["bestObjectiveValue"] = event.get("value")
                progress["bestBound"] = event.get("best_bound")
                progress["objectiveGap"] = event.get("objective_gap")
                preview_result = event.get("preview_result")
                if preview_result is not None:
                    progress["previewResult"] = copy.deepcopy(preview_result)
                    progress["previewStageIndex"] = stage_index
                    progress["previewStageName"] = event.get("name")
                    progress["previewStatus"] = event.get("status")

    def _build_job_status_payload(self, job: dict[str, Any]) -> dict[str, Any]:
        now = time.monotonic()
        status = str(job.get("status") or "unknown")
        progress = copy.deepcopy(job.get("progress") or {})
        started_monotonic = job.get("started_monotonic")
        current_stage_started_monotonic = job.get("current_stage_started_monotonic")
        finished_monotonic = job.get("finished_monotonic")

        elapsed_seconds = None
        if started_monotonic is not None:
            end_time = finished_monotonic if finished_monotonic is not None else now
            elapsed_seconds = round(max(0.0, end_time - started_monotonic), 3)

        current_stage_elapsed = progress.get("currentStageSolveSeconds")
        if status == "running" and current_stage_started_monotonic is not None:
            current_stage_elapsed = round(max(0.0, now - current_stage_started_monotonic), 3)
            progress["currentStageSolveSeconds"] = current_stage_elapsed
            last_improvement = progress.get("lastImprovementSeconds")
            if last_improvement is not None:
                progress["idleAfterLastImprovementSeconds"] = round(
                    max(0.0, float(current_stage_elapsed) - float(last_improvement)),
                    3,
                )

        stage_count = max(1, _to_int(progress.get("stageCount"), 0) or 1)
        current_stage_index = _to_int(progress.get("currentStageIndex"), 0)
        completed_stage_count = len(progress.get("stages") or [])
        no_improvement_limit = progress.get("noImprovementLimitSeconds")
        time_limit_seconds = progress.get("timeLimitSeconds")
        within_stage_window = no_improvement_limit or time_limit_seconds or 3
        try:
            within_stage_window = max(1.0, float(within_stage_window))
        except Exception:
            within_stage_window = 3.0
        if status == "completed":
            percent = 100
        elif status == "failed":
            percent = 100
        elif status == "queued":
            percent = 0
        else:
            stage_slot = max(completed_stage_count, current_stage_index - 1)
            current_stage_progress = 0.0
            if current_stage_elapsed is not None:
                current_stage_progress = min(1.0, float(current_stage_elapsed) / within_stage_window)
            percent = min(99, max(1, int(((stage_slot + current_stage_progress) / stage_count) * 100)))

        return {
            "jobId": job.get("id"),
            "operation": job.get("operation"),
            "status": status,
            "message": job.get("message", ""),
            "error": job.get("error"),
            "elapsedSeconds": elapsed_seconds,
            "progressPercent": percent,
            "progress": progress,
            "result": copy.deepcopy(job.get("result")) if status == "completed" else None,
        }

    def _run_background_job(self, job_id: str, operation: str, params: dict) -> None:
        with self._job_lock:
            job = self._jobs.get(job_id)
            if job is None:
                return
            job["status"] = "running"
            job["started_monotonic"] = time.monotonic()
            job["message"] = "Running CP-SAT solver."

        try:
            result = self._execute_operation(
                operation,
                params,
                progress_observer=lambda event: self._update_job_progress(job_id, event),
            )
            with self._job_lock:
                job = self._jobs.get(job_id)
                if job is None:
                    return
                if result.get("error"):
                    job["status"] = "failed"
                    job["error"] = result.get("error")
                    job["message"] = result.get("error", "")
                else:
                    job["status"] = "completed"
                    job["result"] = result
                    job["message"] = (
                        result.get("meta", {}).get("continueMessage")
                        or result.get("optimization", {}).get("earlyStopReason")
                        or "Completed."
                    )
                job["finished_monotonic"] = time.monotonic()
        except Exception as exc:
            with self._job_lock:
                job = self._jobs.get(job_id)
                if job is None:
                    return
                job["status"] = "failed"
                job["error"] = f"{type(exc).__name__}: {str(exc)}"
                job["message"] = job["error"]
                job["trace"] = traceback.format_exc()[-4000:]
                job["finished_monotonic"] = time.monotonic()

    def start_solver_job(self, params: dict) -> Any:
        operation = str(params.get("operation") or "generate").strip().lower()
        if operation not in {"generate", "continue"}:
            raise ValueError(f"Unsupported proctoring job operation: {operation}")

        with self._job_lock:
            active_job_id = self._active_job_id_locked()
            if active_job_id:
                return {
                    "error": f"Another proctoring job is already running: {active_job_id}",
                    "activeJobId": active_job_id,
                }
            job_id = uuid.uuid4().hex
            self._jobs[job_id] = {
                "id": job_id,
                "operation": operation,
                "status": "queued",
                "message": "Queued.",
                "error": None,
                "created_monotonic": time.monotonic(),
                "started_monotonic": None,
                "finished_monotonic": None,
                "current_stage_started_monotonic": None,
                "progress": {
                    "stageCount": 0,
                    "currentStageIndex": 0,
                    "currentStageName": "",
                    "stages": [],
                    "progressSamples": [],
                    "previewResult": None,
                    "previewStageIndex": 0,
                    "previewStageName": "",
                },
                "result": None,
            }
            self._trim_jobs_locked()

        worker = threading.Thread(
            target=self._run_background_job,
            args=(job_id, operation, copy.deepcopy(params)),
            daemon=True,
        )
        worker.start()
        return {"jobId": job_id, "status": "queued", "operation": operation}

    def get_job_status(self, params: dict) -> Any:
        job_id = str(params.get("jobId") or "").strip()
        if not job_id:
            raise ValueError("jobId is required.")
        with self._job_lock:
            job = self._jobs.get(job_id)
            if job is None:
                return {"jobId": job_id, "status": "missing", "error": "Job not found."}
            return self._build_job_status_payload(job)
