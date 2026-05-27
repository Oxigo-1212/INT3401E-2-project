from __future__ import annotations

import sys

from .handler import UCCIHandler


def run_ucci() -> None:
    handler = UCCIHandler()
    try:
        for raw_line in sys.stdin:
            if not handler.handle_line(raw_line.strip()):
                break
    except KeyboardInterrupt:
        return


run = run_ucci
run_uci = run_ucci


if __name__ == "__main__":
    run_ucci()
