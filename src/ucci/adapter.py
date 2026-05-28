from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from time import perf_counter
from typing import Callable, Optional

from bots.engine.algorithm import negmax
from bots.engine.iterative_deepening import (
    search_with_depth_limit,
    search_with_time_limit,
)
from bots.engine.transposition_table import TT_TABLE, init_tt
from core.board import Board
from core.pieces import Color


@dataclass(slots=True)
class GoParams:
    wtime: Optional[int] = None
    btime: Optional[int] = None
    winc: Optional[int] = None
    binc: Optional[int] = None
    movestogo: Optional[int] = None
    depth: Optional[int] = None
    nodes: Optional[int] = None
    movetime: Optional[int] = None
    infinite: bool = False
    ponder: bool = False


@dataclass(slots=True)
class SearchResult:
    best_move: int
    score: int
    depth: int
    seldepth: int
    nodes: int
    time_ms: int
    pv: list[int] = field(default_factory=list)
    mate: Optional[int] = None


InfoCallback = Callable[[SearchResult], None]
StopFlag = Callable[[], bool]


def _time_from_clock(board: Board, params: GoParams) -> Optional[int]:
    remaining = params.wtime if board.side_to_move == Color.RED else params.btime
    if remaining is None:
        return None

    increment = params.winc if board.side_to_move == Color.RED else params.binc
    moves_to_go = params.movestogo or 30
    slice_ms = remaining // max(2, moves_to_go)
    bonus_ms = 0 if increment is None else (increment * 4) // 5
    budget = slice_ms + bonus_ms
    if remaining > 50:
        budget = min(budget, remaining - 50)
    return max(1, budget)


class SearchFacade:
    def __init__(self, algorithm: Callable[..., float] = negmax) -> None:
        self._algorithm = algorithm
        if not TT_TABLE:
            init_tt(1 << 20, TT_TABLE)

    def search(
        self,
        board: Board,
        params: GoParams,
        stop_flag: StopFlag | None = None,
        info_cb: InfoCallback | None = None,
    ) -> SearchResult:
        if params.depth is not None:
            return self._search_depth(board, params, stop_flag, info_cb)
        return self._search_time(board, params, stop_flag, info_cb)

    def _search_time(
        self,
        board: Board,
        params: GoParams,
        stop_flag: StopFlag | None = None,
        info_cb: InfoCallback | None = None,
    ) -> SearchResult:
        search_board = board.copy()
        started = perf_counter()
        stats: dict[str, int] = {"nodes": 0, "seldepth": 0}
        latest: SearchResult | None = None

        limit_ms = params.movetime
        if limit_ms is None and not (params.infinite or params.ponder):
            limit_ms = _time_from_clock(search_board, params)

        def should_stop() -> bool:
            if stop_flag is not None and stop_flag():
                return True
            if params.nodes is not None and stats["nodes"] >= params.nodes:
                return True
            return False

        def emit(snapshot: dict[str, object]) -> None:
            nonlocal latest
            latest = self._result_from_snapshot(snapshot)
            if info_cb is not None:
                info_cb(latest)

        best_move = search_with_time_limit(
            search_board,
            self._algorithm,
            time_limit_ms=limit_ms,
            stop_flag=should_stop,
            info_cb=emit,
            stats=stats,
        )
        elapsed_ms = max(0, int((perf_counter() - started) * 1000))
        return self._finalize_result(best_move, latest, elapsed_ms, stats, params.depth)

    def _search_depth(
        self,
        board: Board,
        params: GoParams,
        stop_flag: StopFlag | None = None,
        info_cb: InfoCallback | None = None,
    ) -> SearchResult:
        search_board = board.copy()
        started = perf_counter()
        stats: dict[str, int] = {"nodes": 0, "seldepth": 0}
        latest: SearchResult | None = None
        max_depth = params.depth or 0

        def should_stop() -> bool:
            if stop_flag is not None and stop_flag():
                return True
            if params.nodes is not None and stats["nodes"] >= params.nodes:
                return True
            return False

        def emit(snapshot: dict[str, object]) -> None:
            nonlocal latest
            latest = self._result_from_snapshot(snapshot)
            if info_cb is not None:
                info_cb(latest)

        best_move = search_with_depth_limit(
            search_board,
            self._algorithm,
            max_depth=max_depth,
            stop_flag=should_stop,
            info_cb=emit,
            stats=stats,
        )
        elapsed_ms = max(0, int((perf_counter() - started) * 1000))
        return self._finalize_result(best_move, latest, elapsed_ms, stats, max_depth)

    def _result_from_snapshot(self, snapshot: dict[str, object]) -> SearchResult:
        pv = snapshot.get("pv", [])
        if not isinstance(pv, list):
            pv = list(pv)
        score_obj = snapshot.get("score", 0)
        score = int(round(score_obj)) if isinstance(score_obj, (int, float)) and isfinite(score_obj) else 0
        mate_obj = snapshot.get("mate")
        mate = int(mate_obj) if isinstance(mate_obj, int) else None
        nodes_obj = snapshot.get("search_nodes", snapshot.get("nodes", 0))
        return SearchResult(
            best_move=int(snapshot.get("best_move", 0) or 0),
            score=score,
            depth=int(snapshot.get("depth", 0) or 0),
            seldepth=int(snapshot.get("seldepth", 0) or 0),
            nodes=int(nodes_obj or 0),
            time_ms=int(snapshot.get("time_ms", 0) or 0),
            pv=list(pv),
            mate=mate,
        )

    def _finalize_result(
        self,
        best_move: int | None,
        latest: SearchResult | None,
        elapsed_ms: int,
        stats: dict[str, int],
        depth: int,
    ) -> SearchResult:
        if latest is not None:
            return latest
        nodes = stats.get("search_nodes", stats.get("nodes", 0))
        return SearchResult(
            best_move=best_move or 0,
            score=0,
            depth=depth,
            seldepth=stats.get("seldepth", 0),
            nodes=nodes,
            time_ms=elapsed_ms,
            pv=[],
            mate=None,
        )
