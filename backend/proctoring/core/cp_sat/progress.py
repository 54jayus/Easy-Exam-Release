from __future__ import annotations

import time
from typing import Any, Callable

from .common import _normalize_report_number, cp_model, logger


_CallbackBase = cp_model.CpSolverSolutionCallback if cp_model is not None else object


class _StageProgressTracker(_CallbackBase):
    def __init__(
        self,
        *,
        stage_name: str,
        stage_index: int,
        stage_count: int,
        maximize: bool,
        sample_interval_seconds: float,
        progress_observer: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        if cp_model is not None:
            super().__init__()
        self.stage_name = stage_name
        self.stage_index = stage_index
        self.stage_count = stage_count
        self.maximize = bool(maximize)
        self.sample_interval_seconds = max(0.0, float(sample_interval_seconds))
        self.progress_observer = progress_observer
        self.samples: list[dict[str, Any]] = []
        self.solution_count = 0
        self.improvement_count = 0
        self.first_solution_seconds: float | None = None
        self.last_solution_seconds: float | None = None
        self.last_improvement_seconds: float | None = None
        self.last_objective_value: float | None = None
        self.best_bound_value: float | None = None
        self._stage_start_monotonic = time.monotonic()
        self._next_sample_seconds = (
            self.sample_interval_seconds if self.sample_interval_seconds > 0 else None
        )

    def _elapsed_since_stage_start(self) -> float:
        return max(0.0, time.monotonic() - self._stage_start_monotonic)

    def _is_improvement(self, objective_value: float) -> bool:
        if self.last_objective_value is None:
            return True
        if self.maximize:
            return objective_value > self.last_objective_value + 1e-9
        return objective_value < self.last_objective_value - 1e-9

    def _current_gap(self) -> float | None:
        if self.last_objective_value is None or self.best_bound_value is None:
            return None
        if self.maximize:
            gap = self.best_bound_value - self.last_objective_value
        else:
            gap = self.last_objective_value - self.best_bound_value
        return max(0.0, float(gap))

    def _append_sample(self, elapsed_seconds: float, reason: str) -> None:
        if self.last_objective_value is None:
            return
        sample = {
            "stage": self.stage_name,
            "elapsedSeconds": round(max(0.0, float(elapsed_seconds)), 3),
            "objectiveValue": _normalize_report_number(self.last_objective_value),
            "bestBound": _normalize_report_number(self.best_bound_value),
            "objectiveGap": _normalize_report_number(self._current_gap()),
            "reason": reason,
        }
        if self.samples and self.samples[-1] == sample:
            return
        self.samples.append(sample)
        self._notify_progress(status="RUNNING", reason=reason)

    def _emit_interval_samples(self, elapsed_seconds: float) -> None:
        if self._next_sample_seconds is None:
            return
        current = max(0.0, float(elapsed_seconds))
        while self._next_sample_seconds <= current + 1e-9:
            self._append_sample(self._next_sample_seconds, "interval")
            self._next_sample_seconds += self.sample_interval_seconds

    def OnSolutionCallback(self) -> None:
        elapsed_seconds = self._elapsed_since_stage_start()
        objective_value = float(self.ObjectiveValue())
        best_bound = float(self.BestObjectiveBound())
        self.solution_count += 1
        if self.first_solution_seconds is None:
            self.first_solution_seconds = elapsed_seconds
        self.last_solution_seconds = elapsed_seconds
        improved = self._is_improvement(objective_value)
        self.last_objective_value = objective_value
        self.best_bound_value = best_bound
        self._emit_interval_samples(elapsed_seconds)
        if improved:
            self.improvement_count += 1
            self.last_improvement_seconds = elapsed_seconds
            self._append_sample(elapsed_seconds, "improvement")

    def record_best_bound(self, best_bound: float) -> None:
        self.best_bound_value = float(best_bound)
        self._emit_interval_samples(self._elapsed_since_stage_start())

    def current_progress_snapshot(
        self,
        *,
        status: str = "RUNNING",
        reason: str | None = None,
    ) -> dict[str, Any]:
        elapsed_seconds = self._elapsed_since_stage_start()
        idle_after_last_improvement = None
        if self.last_improvement_seconds is not None:
            idle_after_last_improvement = max(0.0, elapsed_seconds - self.last_improvement_seconds)
        latest_sample = self.samples[-1] if self.samples else None
        snapshot = {
            "type": "stage_progress",
            "name": self.stage_name,
            "stage_index": self.stage_index,
            "stage_count": self.stage_count,
            "status": status,
            "reason": reason,
            "solve_seconds": round(elapsed_seconds, 3),
            "solution_count": self.solution_count,
            "improvement_count": self.improvement_count,
            "first_solution_seconds": _normalize_report_number(self.first_solution_seconds),
            "last_solution_seconds": _normalize_report_number(self.last_solution_seconds),
            "last_improvement_seconds": _normalize_report_number(self.last_improvement_seconds),
            "idle_after_last_improvement_seconds": _normalize_report_number(idle_after_last_improvement),
            "best_objective_value": _normalize_report_number(self.last_objective_value),
            "best_bound": _normalize_report_number(self.best_bound_value),
            "objective_gap": _normalize_report_number(self._current_gap()),
            "latest_sample": latest_sample,
        }
        return snapshot

    def _notify_progress(self, *, status: str = "RUNNING", reason: str | None = None) -> None:
        if self.progress_observer is None:
            return
        try:
            self.progress_observer(self.current_progress_snapshot(status=status, reason=reason))
        except Exception:
            logger.debug("Failed to publish CP-SAT stage progress.", exc_info=True)

    def finalize(
        self,
        best_bound: float | None = None,
    ) -> dict[str, Any]:
        elapsed_seconds = self._elapsed_since_stage_start()
        if best_bound is not None:
            self.best_bound_value = float(best_bound)
        self._emit_interval_samples(elapsed_seconds)
        self._append_sample(elapsed_seconds, "final")
        idle_after_last_improvement = None
        if self.last_improvement_seconds is not None:
            idle_after_last_improvement = max(0.0, elapsed_seconds - self.last_improvement_seconds)
        return {
            "solve_seconds": round(elapsed_seconds, 3),
            "solution_count": self.solution_count,
            "improvement_count": self.improvement_count,
            "first_solution_seconds": _normalize_report_number(self.first_solution_seconds),
            "last_solution_seconds": _normalize_report_number(self.last_solution_seconds),
            "last_improvement_seconds": _normalize_report_number(self.last_improvement_seconds),
            "idle_after_last_improvement_seconds": _normalize_report_number(idle_after_last_improvement),
            "best_bound": _normalize_report_number(self.best_bound_value),
            "objective_gap": _normalize_report_number(self._current_gap()),
            "progress_samples": self.samples,
        }
