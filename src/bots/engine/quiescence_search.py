from typing import Optional
from core.board import Board
from core.move_generator import MoveGenerator
from core.rules import get_legal_moves
from bots.engine.linear_evaluator import heuristic
from bots.engine.move_ordering import MoveSorter
from core.move import get_to_sq

_MAX_QUIESCENCE_DEPTH = 4  # Giới hạn độ sâu quiescence để tránh đệ quy vô hạn


def is_capture(board: Board, move: int) -> bool:
    return board.state[get_to_sq(move)] != '.'


def quiescence_search(
    board: Board,
    alpha: float,
    beta: float,
    move_sorter: Optional[MoveSorter] = None,
    qdepth: int = 0
) -> float:
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
        score = -quiescence_search(board, -beta, -alpha, move_sorter, qdepth + 1)
        board.undo_move()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha