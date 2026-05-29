from __future__ import annotations

import importlib
import sys

from ucci import run_ucci, run_uci, run

for _name in ("adapter", "commands", "engine", "handler", "utils"):
    sys.modules.setdefault(f"{__name__}.{_name}", importlib.import_module(f"ucci.{_name}"))

__all__ = ["run_ucci", "run_uci", "run"]
