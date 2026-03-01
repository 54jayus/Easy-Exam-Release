from __future__ import annotations

import logging
import os
import sys


def setup_logging(level: str | None = None) -> None:
    lv = (level or os.getenv("EXAMFLOW_LOG_LEVEL") or os.getenv("EXAMDESK_LOG_LEVEL") or "INFO").strip().upper()
    if lv not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        lv = "INFO"

    root = logging.getLogger()
    root.setLevel(getattr(logging, lv, logging.INFO))

    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setLevel(getattr(logging, lv, logging.INFO))
    fmt = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    handler.setFormatter(fmt)
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
