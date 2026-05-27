# tests/test_board.py
"""
Unit tests cho core/board.py
Bao gồm: FEN parse, make_move, undo_move, Zobrist hash
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from core.board import Board, START_FEN
from core.pieces import Color
from core.move import encode_move, deserialize_move as uci_to_move, serialize_move as move_to_uci


@pytest.fixture
def board():
    """Bàn cờ mới ở vị trí ban đầu."""
    return Board()

@pytest.fixture
def empty_board():
    """Bàn cờ trống hoàn toàn - chỉ có 2 Tướng."""
    b = Board()
    b.set_fen("4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1")
    return b


# ==============================================================================
# 1. FEN PARSING
# ==============================================================================

class TestFenParsing:
    def test_start_fen_side_to_move(self, board):
        """Lượt đầu tiên phải là phe Đỏ."""
        assert board.side_to_move == Color.RED

    def test_start_fen_black_side(self):
        """Parse FEN với lượt của Đen."""
        b = Board()
        b.set_fen("rheakaehr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RHEAKAEHR b - - 0 1")
        assert b.side_to_move == Color.BLACK

    def test_start_fen_piece_positions(self, board):
        """Kiểm tra vị trí các quân cờ ban đầu (theo FEN chuẩn)."""
        # Hàng 0 (Đen): r h e a k a e h r
        assert board.state[0]  == 'r'  # a0: Xe Đen trái
        assert board.state[1]  == 'h'  # b0: Mã Đen trái
        assert board.state[2]  == 'e'  # c0: Tượng Đen trái
        assert board.state[3]  == 'a'  # d0: Sĩ Đen trái
        assert board.state[4]  == 'k'  # e0: Tướng Đen
        assert board.state[5]  == 'a'  # f0: Sĩ Đen phải
        assert board.state[6]  == 'e'  # g0: Tượng Đen phải
        assert board.state[7]  == 'h'  # h0: Mã Đen phải
        assert board.state[8]  == 'r'  # i0: Xe Đen phải
        # Hàng 9 (Đỏ): R H E A K A E H R
        assert board.state[81] == 'R'  # a9
        assert board.state[82] == 'H'  # b9
        assert board.state[85] == 'K'  # e9: Tướng Đỏ
        assert board.state[89] == 'R'  # i9

    def test_start_fen_empty_squares(self, board):
        """Các ô trống đúng vị trí."""
        # Hàng 1 toàn trống
        for sq in range(9, 18):
            assert board.state[sq] == '.'
        # Hàng 8 toàn trống
        for sq in range(72, 81):
            assert board.state[sq] == '.'

    def test_start_fen_cannons(self, board):
        """Pháo đặt đúng vị trí b2, h2 (Đen) và b7, h7 (Đỏ)."""
        assert board.state[2*9 + 1] == 'c'   # b2
        assert board.state[2*9 + 7] == 'c'   # h2
        assert board.state[7*9 + 1] == 'C'   # b7
        assert board.state[7*9 + 7] == 'C'   # h7

    def test_set_fen_resets_history(self, board):
        """set_fen phải xóa lịch sử nước đi cũ."""
        mv = uci_to_move("b7b5")
        board.make_move(mv)
        assert len(board.history) == 1

        board.set_fen(START_FEN)
        assert len(board.history) == 0
        assert len(board.zobrist_history) == 0

    def test_set_fen_resets_half_move_clock(self, board):
        """set_fen phải reset đồng hồ 60 nước."""
        board.half_move_clock = 50
        board.set_fen(START_FEN)
        assert board.half_move_clock == 0

    def test_custom_fen_piece_placement(self):
        """FEN tùy chỉnh đặt quân đúng vị trí."""
        b = Board()
        # Chỉ có Xe Đỏ ở e5 và 2 Tướng
        b.set_fen("4k4/9/9/9/4R4/9/9/9/9/4K4 w - - 0 1")
        assert b.state[4*9 + 4] == 'R'   # e4: Xe Đỏ
        assert b.state[0*9 + 4] == 'k'   # e0: Tướng Đen
        assert b.state[9*9 + 4] == 'K'   # e9: Tướng Đỏ

    def test_total_pieces_at_start(self, board):
        """Số lượng quân cờ mỗi loại đúng ở vị trí ban đầu."""
        from collections import Counter
        counts = Counter(p for p in board.state if p != '.')
        assert counts['R'] == 2  # 2 Xe Đỏ
        assert counts['r'] == 2  # 2 Xe Đen
        assert counts['P'] == 5  # 5 Tốt Đỏ
        assert counts['p'] == 5  # 5 Tốt Đen
        assert counts['K'] == 1  # 1 Tướng Đỏ
        assert counts['k'] == 1  # 1 Tướng Đen


# ==============================================================================
# 2. MAKE_MOVE
# ==============================================================================

class TestMakeMove:
    def test_move_updates_piece_position(self, board):
        """Quân cờ phải di chuyển từ ô đi sang ô đến."""
        # Pháo Đỏ b7 đi lên b5
        mv = uci_to_move("b7b5")
        board.make_move(mv)
        assert board.state[7*9 + 1] == '.'   # b7 trống
        assert board.state[5*9 + 1] == 'C'   # b5 có Pháo Đỏ

    def test_move_switches_side(self, board):
        """Sau mỗi nước đi, lượt phải đổi phe."""
        assert board.side_to_move == Color.RED
        board.make_move(uci_to_move("b7b5"))
        assert board.side_to_move == Color.BLACK
        board.make_move(uci_to_move("b2b4"))
        assert board.side_to_move == Color.RED

    def test_capture_removes_piece(self, board):
        """Ăn quân: quân bị ăn phải biến mất."""
        # Xe Đỏ a9 lên a0 - thực ra không thể đi thẳng, dùng FEN setup
        b = Board()
        b.set_fen("r8/9/9/9/9/9/9/9/9/R3K3k w - - 0 1")
        # Xe Đỏ a9 ăn Xe Đen a0
        mv = uci_to_move("a9a0")
        b.make_move(mv)
        assert b.state[0] == 'R'    # a0 bây giờ là Xe Đỏ
        assert b.state[9*9] == '.'  # a9 trống

    def test_capture_recorded_in_history(self, board):
        """Quân bị ăn phải được lưu trong history để undo."""
        b = Board()
        b.set_fen("r8/9/9/9/9/9/9/9/9/R3K3k w - - 0 1")
        mv = uci_to_move("a9a0")
        b.make_move(mv)
        assert b.history[-1]['captured'] == 'r'

    def test_quiet_move_recorded_in_history(self, board):
        """Nước đi không ăn quân lưu captured = '.'."""
        mv = uci_to_move("b7b5")
        board.make_move(mv)
        assert board.history[-1]['captured'] == '.'

    def test_half_move_clock_increments_on_quiet(self, board):
        """Đồng hồ tăng khi không ăn quân."""
        board.make_move(uci_to_move("b7b5"))
        assert board.half_move_clock == 1
        board.make_move(uci_to_move("b2b4"))
        assert board.half_move_clock == 2

    def test_half_move_clock_resets_on_capture(self):
        """Đồng hồ reset về 0 khi ăn quân."""
        b = Board()
        b.set_fen("r8/9/9/9/9/9/9/9/9/R3K3k w - - 0 1")
        b.half_move_clock = 30
        b.make_move(uci_to_move("a9a0"))
        assert b.half_move_clock == 0

    def test_zobrist_history_grows(self, board):
        """Zobrist history phải được ghi lại sau mỗi nước."""
        assert len(board.zobrist_history) == 0
        board.make_move(uci_to_move("b7b5"))
        assert len(board.zobrist_history) == 1
        board.make_move(uci_to_move("b2b4"))
        assert len(board.zobrist_history) == 2

    def test_consecutive_moves(self, board):
        """Nhiều nước đi liên tiếp không làm hỏng state."""
        moves = ["b7b5", "b2b4", "h7h5", "h2h4"]
        for uci in moves:
            board.make_move(uci_to_move(uci))
        assert len(board.history) == 4
        assert board.side_to_move == Color.RED


# ==============================================================================
# 3. UNDO_MOVE
# ==============================================================================

class TestUndoMove:
    def test_undo_restores_piece_position(self, board):
        """Undo phải đưa quân về vị trí cũ."""
        original_state = board.state[:]
        board.make_move(uci_to_move("b7b5"))
        board.undo_move()
        assert board.state == original_state

    def test_undo_restores_side_to_move(self, board):
        """Undo phải trả lại đúng lượt đi."""
        board.make_move(uci_to_move("b7b5"))
        board.undo_move()
        assert board.side_to_move == Color.RED

    def test_undo_restores_captured_piece(self):
        """Undo nước ăn quân phải đặt lại quân bị ăn."""
        b = Board()
        b.set_fen("r8/9/9/9/9/9/9/9/9/R3K3k w - - 0 1")
        b.make_move(uci_to_move("a9a0"))
        b.undo_move()
        assert b.state[0] == 'r'       # Xe Đen phải còn ở a0
        assert b.state[9*9] == 'R'     # Xe Đỏ phải về a9

    def test_undo_restores_half_move_clock(self, board):
        """Undo phải phục hồi đồng hồ về giá trị trước."""
        board.make_move(uci_to_move("b7b5"))  # clock = 1
        board.make_move(uci_to_move("b2b4"))  # clock = 2
        board.undo_move()
        assert board.half_move_clock == 1
        board.undo_move()
        assert board.half_move_clock == 0

    def test_undo_restores_zobrist_key(self, board):
        """Undo phải phục hồi đúng Zobrist key."""
        initial_key = board.zobrist_key
        board.make_move(uci_to_move("b7b5"))
        board.undo_move()
        assert board.zobrist_key == initial_key

    def test_undo_shrinks_zobrist_history(self, board):
        """Zobrist history phải giảm sau undo."""
        board.make_move(uci_to_move("b7b5"))
        board.make_move(uci_to_move("b2b4"))
        board.undo_move()
        assert len(board.zobrist_history) == 1

    def test_undo_on_empty_history_is_safe(self, board):
        """Undo khi không có lịch sử không được crash."""
        board.undo_move()  # Không nên raise exception
        assert board.side_to_move == Color.RED

    def test_multiple_undo_restores_full_state(self, board):
        """Undo nhiều lần liên tiếp phải khôi phục đúng."""
        original_state = board.state[:]
        original_key = board.zobrist_key
        moves = ["b7b5", "b2b4", "h7h5", "h2h4"]
        for uci in moves:
            board.make_move(uci_to_move(uci))
        for _ in moves:
            board.undo_move()
        assert board.state == original_state
        assert board.zobrist_key == original_key
        assert board.side_to_move == Color.RED


# ==============================================================================
# 4. ZOBRIST HASHING
# ==============================================================================

class TestZobristHashing:
    def test_same_position_same_hash(self):
        """Hai bàn cờ cùng vị trí phải có cùng hash."""
        b1 = Board()
        b2 = Board()
        assert b1.zobrist_key == b2.zobrist_key

    def test_different_positions_different_hash(self, board):
        """Sau khi đi 1 nước, hash phải thay đổi."""
        key_before = board.zobrist_key
        board.make_move(uci_to_move("b7b5"))
        assert board.zobrist_key != key_before

    def test_hash_consistent_after_make_undo(self, board):
        """Hash phải giống nhau sau make + undo."""
        key_before = board.zobrist_key
        board.make_move(uci_to_move("b7b5"))
        board.undo_move()
        assert board.zobrist_key == key_before

    def test_hash_side_to_move_affects_key(self):
        """Cùng vị trí quân nhưng khác lượt đi → hash khác."""
        b1 = Board()
        b2 = Board()
        b2.set_fen(START_FEN.replace(" w ", " b "))
        assert b1.zobrist_key != b2.zobrist_key

    def test_transposition_same_hash(self):
        """Hai đường đi khác nhau đến cùng vị trí → hash bằng nhau."""
        b1 = Board()
        b2 = Board()
        # b1: Pháo b7→b5, rồi b2: Pháo h7→h5
        b1.make_move(uci_to_move("b7b5"))
        b1.make_move(uci_to_move("b2b4"))  # Black
        b1.make_move(uci_to_move("h7h5"))
        b1.make_move(uci_to_move("h2h4"))  # Black
        # b2: đi ngược thứ tự
        b2.make_move(uci_to_move("h7h5"))
        b2.make_move(uci_to_move("h2h4"))  # Black
        b2.make_move(uci_to_move("b7b5"))
        b2.make_move(uci_to_move("b2b4"))  # Black
        assert b1.zobrist_key == b2.zobrist_key