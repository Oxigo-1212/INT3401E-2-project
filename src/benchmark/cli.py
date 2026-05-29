"""Benchmark runner for xiangqi perft."""

from __future__ import annotations
from typing import Any

import importlib
import time

from core.move import serialize_move as move_to_uci

from .implementations.xiangqi_board import XiangqiBoardAdapter
from .xiangqi_perft_positions import POSITIONS


def run_benchmark(verbose: bool = False) -> None:
    """Run benchmark positions and verify expected node counts."""
    perft_mod: Any = importlib.import_module(".perft", __package__)
    perft_mod.move_formatter = move_to_uci

    total = 0
    failed = 0

    for fen, depth, expected in POSITIONS:
        board = XiangqiBoardAdapter.from_fen(fen)
        start = time.perf_counter()
        nodes = perft_mod.perft(board, depth, verbose=verbose)
        elapsed = time.perf_counter() - start
        ok = nodes == expected
        status = "OK" if ok else "FAIL"
        print(f"{status} depth={depth} nodes={nodes} expected={expected} time={elapsed:.3f}s")
        total += 1
        if not ok:
            failed += 1

    print(f"Benchmark done: {total} cases, {failed} failed")
    if failed:
        raise AssertionError(f"Benchmark failed: {failed} case(s) mismatched")
