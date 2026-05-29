import os
import sys
import threading
import time


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.board import Board
from core.move import uci_to_move
from core.pieces import Color
from ucci.adapter import SearchResult
from ucci.commands import UCCICommand, parse_line
from ucci.handler import UCCIHandler
from ucci.utils import move_to_protocol, protocol_to_move, protocol_to_sq, sq_to_protocol


def test_parse_line_parses_uci_position_go_and_setoption():
    setoption = parse_line("setoption name Hash value 128")
    assert setoption is not None
    assert setoption.command == UCCICommand.SETOPTION
    assert setoption.setoption is not None
    assert setoption.setoption.name == "Hash"
    assert setoption.setoption.value == "128"

    position = parse_line("position fen r8/9/9/9/9/9/9/9/9/R3K3k w - - 0 1 moves a0a9 b2b4")
    assert position is not None
    assert position.command == UCCICommand.POSITION
    assert position.position is not None
    assert position.position.fen == "r8/9/9/9/9/9/9/9/9/R3K3k w - - 0 1"
    assert position.position.moves == ["a0a9", "b2b4"]

    go = parse_line(
        "go wtime 1000 btime 2000 winc 10 binc 20 movestogo 30 depth 4 nodes 123 movetime 50 infinite ponder"
    )
    assert go is not None
    assert go.command == UCCICommand.GO
    assert go.go is not None
    assert go.go.wtime == 1000
    assert go.go.btime == 2000
    assert go.go.winc == 10
    assert go.go.binc == 20
    assert go.go.movestogo == 30
    assert go.go.depth == 4
    assert go.go.nodes == 123
    assert go.go.movetime == 50
    assert go.go.infinite is True
    assert go.go.ponder is True


def test_parse_line_ucci():
    parsed = parse_line("ucci")
    assert parsed is not None
    assert parsed.command == UCCICommand.UCCI


def test_protocol_coordinate_roundtrip():
    for sq in range(90):
        coord = sq_to_protocol(sq)
        assert protocol_to_sq(coord) == sq

    move = uci_to_move("b7b5")
    assert move_to_protocol(move) == "b2b4"
    assert protocol_to_move("b2b4") == move


def test_handler_position_ignores_invalid_moves():
    handler = UCCIHandler()

    assert handler.handle_line("position startpos moves e2e4 e7e5") is True
    assert handler.board.side_to_move == Color.RED
    assert handler.board.state == Board().state


def test_handler_position_applies_moves():
    handler = UCCIHandler()

    assert handler.handle_line("position startpos moves b2b4 b7b5") is True
    assert handler.board.side_to_move == Color.RED
    assert handler.board.state[7 * 9 + 1] == "."
    assert handler.board.state[5 * 9 + 1] == "C"
    assert handler.board.state[2 * 9 + 1] == "."
    assert handler.board.state[4 * 9 + 1] == "c"


class _ImmediateSearchFacade:
    def search(self, board, params, stop_flag=None, info_cb=None):
        result = SearchResult(
            best_move=uci_to_move("b7b5"),
            score=42,
            depth=2,
            seldepth=3,
            nodes=12,
            time_ms=5,
            pv=[uci_to_move("b7b5")],
            mate=None,
        )
        if info_cb is not None:
            info_cb(result)
        time.sleep(0.01)
        return result


class _BlockingSearchFacade:
    def __init__(self):
        self.started = threading.Event()

    def search(self, board, params, stop_flag=None, info_cb=None):
        result = SearchResult(
            best_move=0,
            score=0,
            depth=1,
            seldepth=1,
            nodes=1,
            time_ms=1,
            pv=[],
            mate=None,
        )
        if info_cb is not None:
            info_cb(result)
        self.started.set()
        while stop_flag is not None and not stop_flag():
            time.sleep(0.01)
        return result


def test_handler_go_emits_info_and_bestmove(capsys):
    handler = UCCIHandler()
    handler._search_facade = _ImmediateSearchFacade()

    assert handler.handle_line("go depth 2") is True
    thread = handler._search_thread
    assert thread is not None
    thread.join(timeout=1)

    output = capsys.readouterr().out
    assert "info depth 2 seldepth 3 score cp 42 nodes 12 time 5" in output
    assert "pv b2b4" in output
    assert "bestmove b2b4" in output


def test_handler_uci_handshake(capsys):
    handler = UCCIHandler()

    assert handler.handle_line("uci") is True

    output = capsys.readouterr().out
    assert "id name BTL Xiangqi" in output
    assert "option name UCI_Variant type combo default xiangqi var xiangqi" in output
    assert "uciok" in output


def test_handler_ucci_handshake(capsys):
    handler = UCCIHandler()

    assert handler.handle_line("ucci") is True

    output = capsys.readouterr().out
    assert "id name BTL Xiangqi" in output
    assert "option name UCI_Variant type combo default xiangqi var xiangqi" not in output
    assert "ucciok" in output



def test_legacy_uci_shim_exports_protocol_modules():
    from ucci.engine import run_ucci
    from uci.engine import run_uci as legacy_run
    from uci.handler import UCIHandler as legacy_handler

    assert legacy_run is run_ucci
    assert legacy_handler is UCCIHandler

def test_handler_stop_aborts_running_search(capsys):
    handler = UCCIHandler()
    facade = _BlockingSearchFacade()
    handler._search_facade = facade

    assert handler.handle_line("go infinite") is True
    assert facade.started.wait(timeout=1)

    thread = handler._search_thread
    assert thread is not None

    assert handler.handle_line("stop") is True
    thread.join(timeout=1)

    output = capsys.readouterr().out
    assert "bestmove 0000" in output
    assert handler._stop_requested.is_set() is False


def test_parse_line_debug():
    parsed = parse_line("debug on")
    assert parsed is not None
    assert parsed.command == UCCICommand.DEBUG
    assert parsed.debug_value is True

    parsed = parse_line("debug off")
    assert parsed is not None
    assert parsed.command == UCCICommand.DEBUG
    assert parsed.debug_value is False

    parsed = parse_line("debug")
    assert parsed is not None
    assert parsed.command == UCCICommand.DEBUG
    assert parsed.debug_value is True


def test_handler_debug_handling():
    import logging

    handler = UCCIHandler()

    # Test command `debug on` / `debug off`
    handler.handle_line("debug on")
    assert logging.root.level == logging.DEBUG

    handler.handle_line("debug off")
    assert logging.root.level == logging.INFO

    # Test option `setoption name debug value true`
    handler.handle_line("setoption name debug value true")
    assert logging.root.level == logging.DEBUG

    handler.handle_line("setoption name debug value false")
    assert logging.root.level == logging.INFO


def test_uci_run_ignores_keyboard_interrupt(monkeypatch, capsys):
    from ucci.engine import run_ucci

    class _InterruptingStdin:
        def __iter__(self):
            return self

        def __next__(self):
            raise KeyboardInterrupt

    monkeypatch.setattr(sys, "stdin", _InterruptingStdin())

    run_ucci()

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
