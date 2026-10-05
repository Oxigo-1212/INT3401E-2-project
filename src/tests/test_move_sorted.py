import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bots.engine.algorithm import get_best_move, negmax
from bots.engine.transposition_table import TT_TABLE, init_tt
from core.board import Board
from core.move_generator import MoveGenerator
from core.rules import get_legal_moves
from core.utils import load_fen, move_to_str

# test move sorted


def test_move_quality():
    init_tt(1 << 16, TT_TABLE)
    board = Board()
    # Thế cờ: Xe Đỏ có thể chiếu Tướng Đen
    mate_fen = "5k3/9/9/9/9/9/9/9/4R4/4K4 w"
    load_fen(board, mate_fen)

    print("--- THẾ CỜ TEST: KIỂM TRA NƯỚC ĐI ƯU THẾ ---")

    # 1. Lấy nước đi tốt nhất
    best_move = get_best_move(board, negmax, depth=3)
    assert best_move is not None
    move_str = move_to_str(best_move)

    # 2. So sánh với toàn bộ nước hợp lệ để đảm bảo bot chọn một trong các nước tốt nhất
    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)
    scored_moves: list[tuple[float, str]] = []

    for move in legal_moves:
        board.make_move(move)
        score = -negmax(board, 2, -100000, 100000)
        board.undo_move()
        scored_moves.append((score, move_to_str(move)))

    best_score = max(score for score, _ in scored_moves)
    best_move_strings = {move for score, move in scored_moves if score == best_score}

    print(f"Bot chọn: {move_str} với điểm đánh giá: {best_score}")

    assert move_str in best_move_strings, (
        f"Bot đi {move_str}, nhưng các nước tốt nhất là {sorted(best_move_strings)}"
    )
    print("=> KẾT QUẢ: THÀNH CÔNG!")


if __name__ == "__main__":
    test_move_quality()
