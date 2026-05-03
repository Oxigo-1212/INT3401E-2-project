from core.board import Board
from core.move import get_from_sq, get_to_sq
from core.pieces import PIECE_VALUES


class MoveSorter:
    def __init__(self) -> None:
        # 90×90 integer matrix for the history heuristic
        self._history: list[list[int]] = [[0] * 90 for _ in range(90)]
        # killer moves: list of [first, second] per ply; grows on demand
        self._killers: list[list[int]] = []

    def _ensure_killer_slot(self, depth: int) -> None:
        while len(self._killers) <= depth:
            self._killers.append([0, 0])

    def store_killer_move(self, depth: int, move: int, beta: float, score: float) -> None:
        """
        Append or replace the move in a depth in the killers array
        """
        if score < beta:
            return
        self._ensure_killer_slot(depth)
        slot: list[int] = self._killers[depth]
        if move == slot[0] or move == slot[1]:
            return
        slot[1] = slot[0]
        slot[0] = move

    def store_history(self, move: int, depth: int) -> None:
        """
        Increment the history counter for a move.
        `depth` is the remaining depth at which the move was evaluated.
        A common bonus is depth*depth, but any positive value works.
        """
        f = get_from_sq(move)
        t = get_to_sq(move)
        self._history[f][t] += depth * depth


    def get_killers(self, depth: int) -> list[int]:
        """Return the two killers for ply (0 if empty)."""
        # Trả về nhiều hơn 2 nước killers.
        self._ensure_killer_slot(depth)
        return self._killers[depth]

    # most valuable victim - least valuable attackers
    def _mvv_lva(self, board: Board, move: int) -> int:
        """Return capture value minus attacker value, scaled for ordering."""
        frm = get_from_sq(move)
        to = get_to_sq(move)
        attacker = board.state[frm]
        captured = board.state[to]
        return PIECE_VALUES[captured] * 1000 - PIECE_VALUES[attacker]

    def move_sort(self, moves: list[int], board: Board, depth: int, tt_move: int = 0) -> list[int]:
        killers = self.get_killers(depth)
        state = board.state
        history = self._history

        def score(move: int) -> tuple[int, int]:
            if move == tt_move:
                return 4, 0
            frm = get_from_sq(move)
            to = get_to_sq(move)
            if state[to] != '.':
                return 3, self._mvv_lva(board, move)
            if move == killers[0]:
                return 2, 0
            if move == killers[1]:
                return 1, 0
            return 0, history[frm][to]

        moves.sort(key=score, reverse=True)
        return moves

