from __future__ import annotations

import importlib
import threading
import time

from bots.engine.transposition_table import TT_TABLE, clear_tt
from benchmark.implementations.xiangqi_board import XiangqiBoardAdapter
from core.board import Board
from core.logger import init_logging
from core.move_generator import MoveGenerator
from core.rules import get_legal_moves
from .adapter import GoParams, SearchFacade, SearchResult
from .commands import (
    BenchParams,
    ParsedCommand,
    PerftParams,
    PositionParams,
    SetOptionParams,
    UCCICommand,
    parse_line,
)
from .utils import build_info, move_to_protocol, protocol_to_move, write_line


class UCCIHandler:
    def __init__(self) -> None:
        self.board = Board()
        self._search_thread: threading.Thread | None = None
        self._stop_requested = threading.Event()
        self._search_facade = SearchFacade()
        self._ucci_mode = False
        self.options: dict[str, str | None] = {}

    def handle_line(self, line: str) -> bool:
        parsed = parse_line(line)
        if parsed is None:
            return True

        command = parsed.command
        if command == UCCICommand.UCI:
            self._handle_uci()
        elif command == UCCICommand.UCCI:
            self._handle_ucci()
        elif command == UCCICommand.ISREADY:
            self._handle_isready()
        elif command == UCCICommand.SETOPTION and parsed.setoption is not None:
            self._handle_setoption(parsed.setoption)
        elif command == UCCICommand.UCINEWGAME:
            self._handle_ucinewgame()
        elif command == UCCICommand.POSITION and parsed.position is not None:
            self._handle_position(parsed.position)
        elif command == UCCICommand.GO and parsed.go is not None:
            self._handle_go(parsed.go)
        elif command == UCCICommand.BENCH and parsed.bench is not None:
            self._handle_bench(parsed.bench)
        elif command == UCCICommand.PERFT and parsed.perft is not None:
            self._handle_perft(parsed.perft)
        elif command == UCCICommand.STOP:
            self._handle_stop()
        elif command == UCCICommand.QUIT:
            return self._handle_quit()
        elif command == UCCICommand.PONDERHIT:
            self._handle_ponderhit()
        elif command == UCCICommand.DEBUG:
            self._handle_debug(parsed)
        return True

    def _handle_uci(self) -> None:
        self._ucci_mode = False
        write_line("id name BTL Xiangqi")
        write_line("id author group14")
        write_line("option name Hash type spin default 16 min 1 max 1024")
        write_line("option name Threads type spin default 1 min 1 max 64")
        write_line("option name OwnBook type check default false")
        write_line("option name UCI_Variant type combo default xiangqi var xiangqi")
        write_line("uciok")

    def _handle_ucci(self) -> None:
        self._ucci_mode = True
        write_line("id name BTL Xiangqi")
        write_line("id author group14")
        write_line("option name Hash type spin default 16 min 1 max 1024")
        write_line("option name Threads type spin default 1 min 1 max 64")
        write_line("option name OwnBook type check default false")
        write_line("ucciok")

    def _handle_isready(self) -> None:
        write_line("readyok")

    def _handle_setoption(self, params: SetOptionParams) -> None:
        name = params.name.lower()
        self.options[name] = params.value
        if name == "debug":
            debug_on = params.value is not None and params.value.lower() in ("true", "on", "1")
            init_logging(debug=debug_on)

    def _handle_debug(self, parsed: ParsedCommand) -> None:
        debug_on = parsed.debug_value if parsed.debug_value is not None else True
        init_logging(debug=debug_on)

    def _handle_ucinewgame(self) -> None:
        self._handle_stop()
        self.board = Board()
        clear_tt(TT_TABLE)

    def _handle_position(self, params: PositionParams) -> None:
        self._handle_stop()
        if params.fen is None:
            self.board = Board()
        else:
            self.board.set_fen(params.fen)

        for move_text in params.moves:
            try:
                move = protocol_to_move(move_text)
            except (IndexError, ValueError):
                break

            legal_moves = get_legal_moves(self.board, MoveGenerator(self.board))
            if move not in legal_moves:
                break

            self.board.make_move(move)

    def _handle_go(self, params: GoParams) -> None:
        self._handle_stop()
        self._stop_requested.clear()

        def emit_info(result: SearchResult) -> None:
            write_line(
                build_info(
                    depth=result.depth,
                    seldepth=result.seldepth,
                    score=result.score,
                    nodes=result.nodes,
                    time_ms=result.time_ms,
                    pv=result.pv,
                    mate=result.mate,
                )
            )

        def run_search() -> None:
            result = SearchResult(
                best_move=0,
                score=0,
                depth=0,
                seldepth=0,
                nodes=0,
                time_ms=0,
                pv=[],
                mate=None,
            )
            try:
                result = self._search_facade.search(
                    self.board,
                    params,
                    stop_flag=self._stop_requested.is_set,
                    info_cb=emit_info,
                )
            finally:
                move_text = move_to_protocol(result.best_move) if result.best_move else "0000"
                write_line(f"bestmove {move_text}")
                self._stop_requested.clear()
                self._search_thread = None

        thread = threading.Thread(target=run_search, daemon=True)
        self._search_thread = thread
        thread.start()

    def _handle_bench(self, bench: BenchParams) -> None:
        self._handle_stop()
        self._stop_requested.clear()
        clear_tt(TT_TABLE)
        params = GoParams(depth=bench.depth)
        def emit_info(result: SearchResult) -> None:
            write_line(
                build_info(
                    depth=result.depth,
                    seldepth=result.seldepth,
                    score=result.score,
                    nodes=result.nodes,
                    time_ms=result.time_ms,
                    pv=result.pv,
                    mate=result.mate,
                )
            )
        def run_search() -> None:
            result = SearchResult(
                best_move=0,
                score=0,
                depth=0,
                seldepth=0,
                nodes=0,
                time_ms=0,
                pv=[],
                mate=None,
            )
            try:
                result = self._search_facade.search(
                    self.board,
                    params,
                    stop_flag=self._stop_requested.is_set,
                    info_cb=emit_info,
                )
            finally:
                write_line(f"bench depth {result.depth} nodes {result.nodes} time {result.time_ms}")
                self._stop_requested.clear()
                self._search_thread = None
        thread = threading.Thread(target=run_search, daemon=True)
        self._search_thread = thread
        thread.start()

    def _handle_perft(self, perft: PerftParams) -> None:
        self._handle_stop()
        adapter = XiangqiBoardAdapter.from_board(self.board)
        started = time.perf_counter()
        nodes = importlib.import_module("benchmark.perft").perft(adapter, perft.depth)
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        write_line(f"perft depth {perft.depth} nodes {nodes} time {elapsed_ms}")

    def _handle_stop(self) -> None:
        thread = self._search_thread
        if thread is None:
            self._stop_requested.clear()
            return

        self._stop_requested.set()
        thread.join()
        self._search_thread = None
        self._stop_requested.clear()

    def _handle_quit(self) -> bool:
        self._handle_stop()
        return False

    def _handle_ponderhit(self) -> None:
        return


UCIHandler = UCCIHandler
