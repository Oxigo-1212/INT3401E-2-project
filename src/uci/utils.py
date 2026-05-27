from __future__ import annotations

import sys
from typing import Sequence

from core.move import encode_move, get_from_sq, get_to_sq


# ---------------------------------------------------------------------------
# Protocol ↔ internal coordinate conversion
#
# Internal: row 0 = Black's back rank (top), row 9 = Red's back rank (bottom)
# Protocol: rank 0 = Red's back rank (bottom), rank 9 = Black's back rank (top)
# ---------------------------------------------------------------------------

def sq_to_protocol(sq: int) -> str:
    """Convert internal square index to protocol coordinate string."""
    file_idx = sq % 9
    rank_idx = 9 - (sq // 9)
    return chr(ord('a') + file_idx) + str(rank_idx)


def protocol_to_sq(s: str) -> int:
    """Convert protocol coordinate string to internal square index."""
    file_idx = ord(s[0]) - ord('a')
    rank_idx = 9 - int(s[1])
    return rank_idx * 9 + file_idx


def move_to_protocol(move: int) -> str:
    """Convert internal move int to protocol move string."""
    return sq_to_protocol(get_from_sq(move)) + sq_to_protocol(get_to_sq(move))


def protocol_to_move(move_str: str) -> int:
    """Convert protocol move string to internal move int."""
    from_sq = protocol_to_sq(move_str[0:2])
    to_sq = protocol_to_sq(move_str[2:4])
    return encode_move(from_sq, to_sq)


def write_line(msg: str) -> None:
    sys.stdout.write(msg)
    sys.stdout.write("\n")
    sys.stdout.flush()


def format_score(score: int, mate: int | None = None) -> str:
    if mate is not None:
        return f"score mate {mate}"
    return f"score cp {score}"


def format_pv(pv: Sequence[int]) -> str:
    if not pv:
        return ""
    return "pv " + " ".join(move_to_protocol(move) for move in pv)


def build_info(
    *,
    depth: int,
    seldepth: int,
    score: int,
    nodes: int,
    time_ms: int,
    pv: Sequence[int] | None = None,
    mate: int | None = None,
) -> str:
    parts = [
        "info",
        f"depth {depth}",
        f"seldepth {seldepth}",
        format_score(score, mate),
        f"nodes {nodes}",
        f"time {time_ms}",
    ]

    if time_ms > 0:
        parts.append(f"nps {max(1, (nodes * 1000) // time_ms)}")

    pv_text = format_pv(pv or [])
    if pv_text:
        parts.append(pv_text)

    return " ".join(parts)
