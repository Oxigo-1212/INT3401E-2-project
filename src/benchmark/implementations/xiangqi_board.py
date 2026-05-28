"""Adapter around core.Board for benchmark perft."""

from __future__ import annotations

from typing import List

from core.board import Board
from core.move_generator import MoveGenerator
from core.pieces import Color as XiangqiColor
from core.rules import get_legal_moves

from ..protocol import Color


class XiangqiBoardAdapter:
    """Wrap core.Board with benchmark perft protocol."""

    def __init__(self, fen: str | None = None) -> None:
        self._board = Board()
        if fen is not None:
            self._board.set_fen(fen)

    @classmethod
    def from_fen(cls, fen: str) -> XiangqiBoardAdapter:
        """Create adapter from FEN string."""
        return cls(fen)

    @classmethod
    def from_board(cls, board: Board) -> XiangqiBoardAdapter:
        """Wrap an existing Board instance."""
        adapter = object.__new__(cls)
        adapter._board = board
        return adapter

    @property
    def state(self) -> List[str]:
        """Expose board state as list of strings."""
        return self._board.state

    @property
    def side_to_move(self) -> Color:
        """Map core Color enum to benchmark protocol color."""
        return "white" if self._board.side_to_move == XiangqiColor.RED else "black"

    def make_move(self, move: int) -> None:
        """Apply move through wrapped board."""
        self._board.make_move(move)

    def undo_move(self) -> None:
        """Undo last move through wrapped board."""
        self._board.undo_move()

    def generate_legal_moves(self) -> List[int]:
        """Generate legal Xiangqi moves."""
        return get_legal_moves(self._board, MoveGenerator(self._board))
