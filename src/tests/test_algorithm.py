import math
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import bots.engine.algorithm as algorithm
from core.board import Board
from core.pieces import Color
from core.rules import GameStatus


class DummyMoveGenerator:
    def __init__(self, board):
        self.board = board


class RecordingBoard(Board):
    def __init__(self, side_to_move=Color.RED):
        self.side_to_move = side_to_move
        self.state = ["."] * 90
        self.moves: list[int] = []
    zobrist_key: int = 0

    def make_move(self, move: int):
        self.moves.append(move)
        self.side_to_move = Color.BLACK if self.side_to_move == Color.RED else Color.RED

    def undo_move(self):
        if self.moves:
            self.moves.pop()
        self.side_to_move = Color.BLACK if self.side_to_move == Color.RED else Color.RED


def install_search_stubs(monkeypatch, legal_moves, status=GameStatus.Playing):
    monkeypatch.setattr(algorithm, "MoveGenerator", DummyMoveGenerator)
    monkeypatch.setattr(algorithm, "get_legal_moves", lambda board, generator: list(legal_moves))
    monkeypatch.setattr(algorithm, "check_game_status", lambda board, moves: status)
    monkeypatch.setattr(algorithm, "probe", lambda key, depth, alpha, beta, tt: (None, False))
    monkeypatch.setattr(algorithm, "store", lambda key, depth, score, flag, best_move, tt: None)
    monkeypatch.setattr(algorithm, "is_in_check", lambda board, color: False)
    monkeypatch.setattr(
        algorithm,
        "quiescence_search",
        lambda board, alpha, beta, *args, **kwargs: float(algorithm.heuristic(board)),
    )


def test_negmax_searches_one_ply_and_returns_negated_best_score(monkeypatch):
    board = RecordingBoard()
    install_search_stubs(monkeypatch, legal_moves=[1, 2], status=GameStatus.Playing)

    scores = {
        (): 0.0,
        (1,): 2.0,
        (2,): 5.0,
    }

    def fake_heuristic(current_board):
        path = tuple(current_board.moves)
        return scores[path]

    monkeypatch.setattr(algorithm, "heuristic", fake_heuristic)

    score = algorithm.negmax(board, depth=1, alpha=-math.inf, beta=math.inf)

    # Negamax returns -min(child_scores) = -min(2.0, 5.0) = -2.0
    assert score == -2.0
    assert board.moves == []
    assert board.side_to_move == Color.RED


@pytest.mark.parametrize(
    "side_to_move, expected_move",
    [
        (Color.RED, 11),
        (Color.BLACK, 11),
    ],
)
def test_get_best_move_selects_best_move_for_each_side(monkeypatch, side_to_move, expected_move):
    board = RecordingBoard(side_to_move=side_to_move)
    install_search_stubs(monkeypatch, legal_moves=[11, 22], status=GameStatus.Playing)

    calls: list[tuple[tuple[int, ...], int, float, float]] = []
    scores = {
        (11,): 1.0,
        (22,): 3.0,
    }

    def fake_algorithm(current_board, depth, alpha, beta, move_sorter=None):
        path = tuple(current_board.moves)
        calls.append((path, depth, alpha, beta))
        return scores[path]

    best_move = algorithm.get_best_move(board, fake_algorithm, depth=4)

    assert best_move == expected_move
    assert calls == [
        ((11,), 3, -math.inf, math.inf),
        ((22,), 3, -math.inf, math.inf),
    ]
    assert board.moves == []
    assert board.side_to_move == side_to_move


def test_get_best_move_returns_none_when_no_legal_moves(monkeypatch):
    board = RecordingBoard()
    install_search_stubs(monkeypatch, legal_moves=[], status=GameStatus.Playing)

    algorithm_called = False

    def fake_algorithm(*args, **kwargs):
        nonlocal algorithm_called
        algorithm_called = True
        return 0.0

    best_move = algorithm.get_best_move(board, fake_algorithm, depth=4)

    assert best_move is None
    assert algorithm_called is False
    assert board.moves == []
    assert board.side_to_move == Color.RED
