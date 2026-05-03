import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.board import Board
from engine.algorithm import get_best_move, negmax
from core.utils import print_board, move_to_str, load_fen

# test move sorted
def test_move_quality():
    board = Board()
    # Thế cờ: Xe Đỏ có thể chiếu Tướng Đen
    mate_fen = "5k3/9/9/9/9/9/9/9/4R4/4K4 w"
    load_fen(board, mate_fen)
    
    print("--- THẾ CỜ TEST: KIỂM TRA NƯỚC ĐI ƯU THẾ ---")
    
    # 1. Lấy nước đi tốt nhất
    best_move = get_best_move(board, negmax, depth=3)
    move_str = move_to_str(best_move)
    
    # 2. Kiểm tra điểm số của nước đi đó (Optional)
    board.make_move(best_move)
    score = -negmax(board, 2, -100000, 100000, True) # Xem Bot đánh giá nước này bao nhiêu
    board.undo_move()

    print(f"Bot chọn: {move_str} với điểm đánh giá: {score}")

    # Thay đổi điều kiện assert: 
    # Nếu nước đi là 'e1f1' (chiếu Tướng) thì coi như thành công
    assert move_str == "e1f1", f"Lẽ ra phải đi e1f1 để chiếu, nhưng Bot đi {move_str}"
    print("=> KẾT QUẢ: THÀNH CÔNG!")

if __name__ == "__main__":
    test_move_quality()