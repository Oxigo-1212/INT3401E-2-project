import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import main as engine_main
from benchmark.implementations.xiangqi_board import XiangqiBoardAdapter
from core.board import Board, START_FEN
from ucci import handler as engine_handler
from ucci.adapter import GoParams, SearchResult
from ucci.commands import UCCICommand, parse_line
from ucci.handler import UCCIHandler


def test_parse_line_bench():
    parsed = parse_line("bench depth 3")

    assert parsed is not None
    assert parsed.command == UCCICommand.BENCH
    assert parsed.bench is not None
    assert parsed.bench.depth == 3
    assert parsed.go is None
    assert parsed.perft is None


def test_parse_line_perft():
    parsed = parse_line("perft depth 4")

    assert parsed is not None
    assert parsed.command == UCCICommand.PERFT
    assert parsed.perft is not None
    assert parsed.perft.depth == 4
    assert parsed.go is None
    assert parsed.bench is None


def test_run_search_benchmark_formats_labels(monkeypatch, capsys):
    seen: dict[str, object] = {}

    class FakeSearchFacade:
        def __init__(self) -> None:
            seen["facade_inited"] = True

        def search(self, board, params):
            seen["depth"] = params.depth
            seen["board"] = board
            return SearchResult(
                best_move=0,
                score=0,
                depth=params.depth,
                seldepth=0,
                nodes=1234,
                time_ms=7,
                pv=[],
                mate=None,
            )

    monkeypatch.setattr(engine_main, "POSITIONS", [(START_FEN, 3, 56)])
    monkeypatch.setattr(engine_main, "SearchFacade", FakeSearchFacade)

    engine_main.run_search_benchmark()

    output = capsys.readouterr().out.splitlines()
    assert output == ["bench depth: 3 nodes: 1234 expected: 56 time: 0.007 sec"]
    assert seen["facade_inited"] is True
    assert seen["depth"] == 3
    assert isinstance(seen["board"], Board)
    assert seen["board"].state == Board().state


def test_handler_bench_output_on_startpos(monkeypatch, capsys):
    seen: dict[str, object] = {}

    class FakeSearchFacade:
        def __init__(self) -> None:
            seen["facade_inited"] = True

        def search(self, board, params, stop_flag=None, info_cb=None):
            seen["depth"] = params.depth
            seen["board"] = board
            res = SearchResult(
                best_move=0,
                score=0,
                depth=params.depth,
                seldepth=0,
                nodes=1234,
                time_ms=17,
                pv=[],
                mate=None,
            )
            if info_cb is not None:
                info_cb(res)
            return res
    monkeypatch.setattr(engine_handler, "SearchFacade", FakeSearchFacade)
    handler = UCCIHandler()
    assert handler.handle_line("position startpos") is True
    assert handler.handle_line("bench depth 3") is True
    thread = handler._search_thread
    if thread is not None:
        thread.join(timeout=1)
    output = capsys.readouterr().out.strip().splitlines()
    assert "info depth 3 seldepth 0 score cp 0 nodes 1234 time 17" in output[0]
    assert "bench depth 3 nodes 1234 time 17" in output[1]
    assert seen["facade_inited"] is True
    assert seen["depth"] == 3
    assert isinstance(seen["board"], Board)
    assert seen["board"].state == Board().state
    assert handler.board.state == Board().state


def test_handler_perft_output_on_startpos(monkeypatch, capsys):
    seen: dict[str, object] = {}

    class FakePerftModule:
        def perft(self, board, depth):
            seen["depth"] = depth
            seen["board"] = board
            return 44

    times = iter([10.0, 10.5])
    monkeypatch.setattr(engine_handler.time, "perf_counter", lambda: next(times))
    monkeypatch.setattr(engine_handler.importlib, "import_module", lambda name: FakePerftModule())

    handler = UCCIHandler()
    assert handler.handle_line("position startpos") is True
    assert handler.handle_line("perft depth 4") is True

    output = capsys.readouterr().out.strip().splitlines()
    assert output == ["perft depth 4 nodes 44 time 500"]
    assert seen["depth"] == 4
    assert isinstance(seen["board"], XiangqiBoardAdapter)
    assert seen["board"].state == Board().state
    assert handler.board.state == Board().state


def test_search_depth_1_counts_only_search_nodes():
    """Depth-1 search from startpos: 44 children (no root negmax call), 0 qsearch nodes."""
    from ucci.adapter import SearchFacade

    board = Board()
    board.set_fen(START_FEN)
    facade = SearchFacade()
    result = facade.search(board, GoParams(depth=1))

    assert result.nodes == 44, f"Expected 44 search nodes, got {result.nodes}"
