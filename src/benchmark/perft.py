"""Depth-first perft node counter for benchmark package."""

from __future__ import annotations

import sys
from typing import Callable

from .protocol import _PerftBoard

move_formatter: Callable[[int], str] = str


def perft(board: _PerftBoard, depth: int, *, verbose: bool = False) -> int:
    """Count leaf nodes at given depth."""
    if depth < 0:
        raise ValueError("Depth must be >= 0")

    max_depth = depth
    formatter = move_formatter

    def _search(b: _PerftBoard, d: int) -> int:
        if d == 0:
            return 1

        moves = b.generate_legal_moves()
        total = 0
        indent = "  " * (max_depth - d)

        if verbose:
            print(f"{indent}depth {d}")
            sys.stdout.flush()

        for move in moves:
            b.make_move(move)
            nodes = _search(b, d - 1)
            total += nodes
            b.undo_move()

            if verbose:
                print(f"{indent}  {formatter(move)}: {nodes}")
                sys.stdout.flush()

        if verbose:
            print(f"{indent}total: {total}")
            sys.stdout.flush()

        return total

    return _search(board, depth)
