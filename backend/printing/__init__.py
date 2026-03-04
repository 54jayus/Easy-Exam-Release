from __future__ import annotations

from .core.config import BaseConfig
from .core.config import (
    AdmissionTicketConfig,
    CornerPaperConfig,
    DeskLabelConfig,
    StudentInfoTableConfig,
)
from .core.factory import GeneratorFactory
from .core.utils.data_loader import DataLoader

__all__ = [
    "AdmissionTicketConfig",
    "BaseConfig",
    "CornerPaperConfig",
    "DeskLabelConfig",
    "GeneratorFactory",
    "DataLoader",
    "StudentInfoTableConfig",
]
