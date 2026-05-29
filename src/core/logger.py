"""Logging wrapper cho cờ tướng engine."""

from __future__ import annotations

import logging
import sys

_INITIALIZED = False


def init_logging(*, debug: bool = False) -> None:
    """Khởi tạo logging một lần. Gọi lại cập nhật level."""
    global _INITIALIZED
    level = logging.DEBUG if debug else logging.INFO
    if _INITIALIZED:
        logging.root.setLevel(level)
        return
    _INITIALIZED = True

    level = logging.DEBUG if debug else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(name)s | %(message)s"))
    logging.root.addHandler(handler)
    logging.root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Trả về logger cho module."""
    return logging.getLogger(name)
