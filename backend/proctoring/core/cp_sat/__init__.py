from __future__ import annotations

from .assignment import _build_consecutive_pairs
from .common import SubjectContext, cp_model
from .diagnostics import (
    _build_infeasibility_diagnostic_message,
    _build_solution_summary,
    _diagnose_locked_assignment_conflicts,
)
from .metrics import compute_schedule_metrics
from .solver import solve_schedule_with_cp_sat

__all__ = [
    "SubjectContext",
    "cp_model",
    "compute_schedule_metrics",
    "solve_schedule_with_cp_sat",
    "_build_consecutive_pairs",
    "_build_infeasibility_diagnostic_message",
    "_build_solution_summary",
    "_diagnose_locked_assignment_conflicts",
]
