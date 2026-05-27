from typing import Callable, Optional

from bots.engine.iterative_deepening import SearchStopped
from bots.engine.linear_evaluator import heuristic
from bots.engine.move_ordering import MoveSorter
from core.board import Board
from core.move import get_to_sq
from core.move_generator import MoveGenerator
from core.rules import get_legal_moves

_MAX_QUIESCENCE_DEPTH = 4  # Giới hạn độ sâu quiescence để tránh đệ quy vô hạn


def is_capture(board: Board, move: int) -> bool:
    return board.state[get_to_sq(move)] != '.'


def quiescence_search(
    board: Board,
    alpha: float,
    beta: float,
    move_sorter: Optional[MoveSorter] = None,
    qdepth: int = 0,
    *,
    stats: Optional[dict[str, int]] = None,
    stop_flag: Callable[[], bool] | None = None,
    ply: int = 0,
) -> float:
    if stop_flag is not None and stop_flag():
        raise SearchStopped()
    if stats is not None:
        stats["nodes"] = stats.get("nodes", 0) + 1
        stats["seldepth"] = max(stats.get("seldepth", 0), ply + qdepth)

    stand_pat = float(heuristic(board))

    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    # Dừng khi đạt độ sâu tối đa — tránh đệ quy vô hạn
    if qdepth >= _MAX_QUIESCENCE_DEPTH:
        return alpha

    if move_sorter is None:
        move_sorter = MoveSorter()

    # Dùng get_legal_moves (fully legal) để đảm bảo không ăn Tướng trái phép
    # và không tạo trạng thái bàn cờ thiếu Tướng gây crash _find_king()
    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)

    capture_moves = [m for m in legal_moves if is_capture(board, m)]

    if not capture_moves:
        return alpha

    capture_moves = move_sorter.move_sort(capture_moves, board, 0)

    for move in capture_moves:
        board.make_move(move)
        try:
            score = -quiescence_search(
                board,
                -beta,
                -alpha,
                move_sorter,
                qdepth + 1,
                stats=stats,
                stop_flag=stop_flag,
                ply=ply,
            )
        finally:
            board.undo_move()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha