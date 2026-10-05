"""Protocol definition for perft-compatible Xiangqi boards."""

from __future__ import annotations

from typing import Literal, Protocol

Color = Literal["white", "black"]


class _PerftBoard(Protocol):
    """Structural interface required by benchmark perft."""

    state: list[str]
    side_to_move: Color

    def make_move(self, move: int) -> None:
        """Apply move and flip side_to_move."""
        ...

    def undo_move(self) -> None:
        """Undo last move."""
        ...

    def generate_legal_moves(self) -> list[int]:
        """Return legal moves for side_to_move."""
        ...
