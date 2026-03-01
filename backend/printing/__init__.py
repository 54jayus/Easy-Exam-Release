from __future__ import annotations

try:
    from .core.config import BaseConfig
    from .core.config import (
        AdmissionTicketConfig,
        CornerPaperConfig,
        DeskLabelConfig,
        StudentInfoTableConfig,
    )
    from .core.factory import GeneratorFactory
    from .core.utils.data_loader import DataLoader
except Exception:  # pragma: no cover
    from ui.page.print_page.core.config import BaseConfig  # type: ignore
    from ui.page.print_page.core.config import (  # type: ignore
        AdmissionTicketConfig,
        CornerPaperConfig,
        DeskLabelConfig,
        StudentInfoTableConfig,
    )
    from ui.page.print_page.core.factory import GeneratorFactory  # type: ignore
    from ui.page.print_page.core.utils.data_loader import DataLoader  # type: ignore

__all__ = [
    "AdmissionTicketConfig",
    "BaseConfig",
    "CornerPaperConfig",
    "DeskLabelConfig",
    "GeneratorFactory",
    "DataLoader",
    "StudentInfoTableConfig",
]
