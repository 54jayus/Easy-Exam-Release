from __future__ import annotations

from backend.logging_config import setup_logging

setup_logging()
from backend.rpc_server import main
raise SystemExit(main())
