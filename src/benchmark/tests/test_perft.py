"""Unit tests for benchmark perft using mock boards."""

from __future__ import annotations

import os
import sys
from typing import List

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from benchmark.perft import perft
from benchmark.protocol import Color


class MockBoard:
    """Mock board that implements _PerftBoard for deterministic branching."""

    def __init__(self, branch_factors: List[int]) -> None:
        self.branch_factors = branch_factors
        self.state = ["mock"]
        self.side_to_move: Color = "white"
        self.made_moves: List[int] = []
        self.undone_moves: List[int] = []

        self.max_depth_reached = 0
        self.undo_calls = 0

    def make_move(self, move: int) -> None:
        self.made_moves.append(move)
        self.max_depth_reached = max(self.max_depth_reached, len(self.made_moves))

    def undo_move(self) -> None:
        self.undo_calls += 1
        if self.made_moves:
            self.undone_moves.append(self.made_moves.pop())


    def generate_legal_moves(self) -> List[int]:
        depth_index = len(self.made_moves)
        if depth_index < len(self.branch_factors):
            return list(range(self.branch_factors[depth_index]))
        return []


def test_perft_depth_zero() -> None:
    board = MockBoard([10, 5])
    assert perft(board, 0) == 1
    assert len(board.made_moves) == 0


def test_perft_depth_one() -> None:
    board = MockBoard([3, 5])
    assert perft(board, 1) == 3
    assert len(board.undone_moves) == 3
    assert board.undone_moves == [0, 1, 2]


def test_perft_depth_two() -> None:
    board = MockBoard([2, 3])
    assert perft(board, 2) == 6
    assert board.max_depth_reached == 2
    assert len(board.made_moves) == 0
    assert len(board.undone_moves) == 8


def test_perft_invalid_depth() -> None:
    board = MockBoard([3])
    with pytest.raises(ValueError, match="Depth must be >= 0"):
        perft(board, -1)

