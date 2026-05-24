"""Protocol definition for perft-compatible Xiangqi boards."""

from __future__ import annotations

from typing import List, Literal, Protocol

Color = Literal["white", "black"]


class _PerftBoard(Protocol):
    """Structural interface required by benchmark perft."""

    state: List[str]
    side_to_move: Color

    def make_move(self, move: int) -> None:
        """Apply move and flip side_to_move."""
        ...

    def undo_move(self) -> None:
        """Undo last move."""
        ...


    def generate_legal_moves(self) -> List[int]:
        """Return legal moves for side_to_move."""
        ...
