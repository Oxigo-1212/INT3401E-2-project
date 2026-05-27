from __future__ import annotations

import sys

from .handler import UCIHandler


def run() -> None:
    handler = UCIHandler()
    try:
        for raw_line in sys.stdin:
            if not handler.handle_line(raw_line.strip()):
                break
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    run()
