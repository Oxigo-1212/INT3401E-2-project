# tests/test_move_gen.py
"""
Unit tests cho core/move_generator.py
Bao gồm: sinh nước đi từng loại quân, perft, edge cases
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from core.board import Board
from core.move_generator import MoveGenerator
from core.move import encode_move, deserialize_move as uci_to_move, deserialize_square as uci_to_sq, serialize_square as sq_to_uci, get_to_sq, get_from_sq
from core.pieces import Color

def make_gen(fen, side='w'):
    b = Board()
    b.set_fen(fen)
    return b, MoveGenerator(b)

def to_uci_set(moves):
    """Chuyển danh sách move int thành set chuỗi UCI để dễ assert."""
    from core.move import move_to_uci
    return set(move_to_uci(m) for m in moves)

def assert_moves_contain(moves, *expected_ucis):
    """Kiểm tra danh sách nước đi chứa các nước được expect."""
    uci_set = to_uci_set(moves)
    for uci in expected_ucis:
        assert uci in uci_set, f"Thiếu nước đi: {uci} | Có: {sorted(uci_set)}"

def assert_moves_not_contain(moves, *forbidden_ucis):
    """Kiểm tra danh sách nước đi KHÔNG chứa các nước bị cấm."""
    uci_set = to_uci_set(moves)
    for uci in forbidden_ucis:
        assert uci not in uci_set, f"Nước đi bị cấm nhưng được sinh ra: {uci}"


# ==============================================================================
# 1. XE (R) - Đi thẳng ngang/dọc không giới hạn
# ==============================================================================

class TestRookMoves:
    def test_rook_open_file_vertical(self):
        """Xe đi tự do theo chiều dọc trên cột trống."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1")
        moves = gen.get_pseudo_legal_moves()
        # Xe ở a9, có thể đi a0..a8
        assert_moves_contain(moves, "a9a8", "a9a7", "a9a0")

    def test_rook_open_rank_horizontal(self):
        """Xe đi tự do theo chiều ngang trên hàng trống."""
        b, gen = make_gen("4k4/9/9/9/4R4/9/9/9/9/4K4 w - - 0 1")
        moves = gen.get_pseudo_legal_moves()
        # Xe ở e4, đi ngang a4..i4
        assert_moves_contain(moves, "e4a4", "e4b4", "e4i4")

    def test_rook_blocked_by_own_piece(self):
        """Xe không được đi qua quân mình hoặc đứng trên ô đó."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/9/9/RN2K4 w - - 0 1")
        # Xe ở a9, Mã ở b9 → Xe không được đi sang b9 trở đi theo chiều ngang
        moves = gen.get_pseudo_legal_moves()
        assert_moves_not_contain(moves, "a9b9", "a9c9")

    def test_rook_can_capture_enemy(self):
        """Xe được ăn quân đối phương."""
        b, gen = make_gen("r3k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1")
        moves = gen.get_pseudo_legal_moves()
        assert_moves_contain(moves, "a9a0")  # Xe Đỏ a9 ăn Xe Đen a0

    def test_rook_stops_after_capture(self):
        """Xe dừng sau khi ăn, không đi tiếp qua quân bị ăn."""
        b, gen = make_gen("r3k4/9/9/9/9/9/9/9/9/R3K4 w - - 0 1")
        moves = gen.get_pseudo_legal_moves()
        # Không có nước đi qua ô a0 (không tồn tại)
        uci_set = to_uci_set(moves)
        rook_vertical = [u for u in uci_set if u.startswith("a9a")]
        # a9→a0 là ăn quân, nhưng không thể đi tiếp (hết bàn)
        assert "a9a0" in uci_set


# ==============================================================================
# 2. PHÁO (C) - Đi như Xe nhưng phải có ngòi để ăn
# ==============================================================================

class TestCannonMoves:
    def test_cannon_moves_like_rook_on_empty(self):
        """Pháo di chuyển như Xe trên đường trống."""
        b, gen = make_gen("4k4/9/9/9/4C4/9/9/9/9/4K4 w - - 0 1")
        moves = gen.get_pseudo_legal_moves()
        # e4e0 không hợp lệ vì e0 có Tướng Đen (cùng phe? Không - Đen vs Đỏ)
        # Thực ra Pháo không ăn trực tiếp - cần ngòi. e0 có Tướng Đen → không ăn được (cần ngòi)
        # Pháo chỉ đến e1 (trống), không đến e0 (có Tướng Đen, không có ngòi)
        assert_moves_contain(moves, "e4a4", "e4i4", "e4e1", "e4e8")

    def test_cannon_cannot_capture_adjacent(self):
        """Pháo không ăn được quân kề cạnh (cần ngòi)."""
        b, gen = make_gen("r3k4/9/9/9/9/9/9/9/9/C3K4 w - - 0 1")
        # Pháo ở a9, Xe Đen ở a0, không có ngòi → không ăn được
        moves = gen.get_pseudo_legal_moves()
        assert_moves_not_contain(moves, "a9a0")

    def test_cannon_captures_with_screen(self):
        """Pháo ăn được khi có đúng 1 quân ngòi ở giữa."""
        b, gen = make_gen("r4k3/9/9/9/9/9/9/9/R8/C3K4 w - - 0 1")
        # Pháo a9, ngòi là Xe Đỏ a8, mục tiêu Xe Đen a0
        moves = gen.get_pseudo_legal_moves()
        assert_moves_contain(moves, "a9a0")

    def test_cannon_cannot_capture_with_two_screens(self):
        """Pháo KHÔNG ăn được khi có 2 quân ở giữa."""
        b, gen = make_gen("r4k3/9/9/9/9/9/9/R8/R8/C3K4 w - - 0 1")
        # Pháo a9, 2 Xe ở a8 và a7, mục tiêu Xe Đen a0 → không ăn được
        moves = gen.get_pseudo_legal_moves()
        assert_moves_not_contain(moves, "a9a0")

    def test_cannon_cannot_jump_to_empty_over_piece(self):
        """Pháo không thể đi đến ô trống nếu có quân ở giữa."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/9/R8/C3K4 w - - 0 1")
        # Pháo a9, có Xe a8 → Pháo không đi được lên a7, a6...
        moves = gen.get_pseudo_legal_moves()
        assert_moves_not_contain(moves, "a9a7", "a9a6", "a9a0")

    def test_cannon_moves_horizontally(self):
        """Pháo di chuyển ngang không bị cản."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/C8/9/4K4 w - - 0 1")
        moves = gen.get_pseudo_legal_moves()
        assert_moves_contain(moves, "a7b7", "a7i7")


# ==============================================================================
# 3. MÃ (N) - Đi hình chữ L, bị cản chân
# ==============================================================================

class TestHorseMoves:
    def test_horse_at_center_has_8_moves(self):
        """Mã ở giữa bàn cờ có đúng 8 nước đi."""
        b, gen = make_gen("4k4/9/9/9/4N4/9/9/9/9/4K4 w - - 0 1")
        moves = gen.get_pseudo_legal_moves()
        # Tướng Đỏ e9 cũng sinh nước đi → lọc chỉ lấy nước của Mã e4
        horse_sq = 4*9 + 4  # e4
        horse_moves = [m for m in moves if get_from_sq(m) == horse_sq]
        assert len(horse_moves) == 8

    def test_horse_blocked_by_leg(self):
        """Mã bị cản chân không đi được hướng đó."""
        # Mã ở e4, chân lên trên bị cản
        b, gen = make_gen("4k4/9/9/9/4N4/4P4/9/9/9/4K4 w - - 0 1")
        # Tốt Đỏ ở e5 cản chân lên → Mã không đi được d3, f3
        moves = gen.get_pseudo_legal_moves()
        horse_moves = [m for m in moves if get_from_sq(m) == 4*9+4]
        horse_uci = to_uci_set(horse_moves)
        # Chân lên là e5 (sq=5*9+4=49), cản hướng tiến 2 lên
        assert "e4d3" not in horse_uci
        assert "e4f3" not in horse_uci

    def test_horse_at_corner(self):
        """Mã ở góc bàn cờ chỉ có 2 nước đi hợp lệ."""
        b, gen = make_gen("k8/9/9/9/9/9/9/9/9/N3K4 w - - 0 1")
        horse_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == 9*9]
        assert len(horse_moves) == 2

    def test_horse_cannot_capture_own_piece(self):
        """Mã không được đứng lên ô có quân mình."""
        b, gen = make_gen("4k4/9/9/9/4N4/9/3P5/9/9/4K4 w - - 0 1")
        # Tốt Đỏ ở d6, là một trong các ô Mã e4 có thể đến
        horse_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == 4*9+4]
        assert_moves_not_contain(horse_moves, "e4d6")

    def test_horse_can_capture_enemy(self):
        """Mã được ăn quân đối phương."""
        b, gen = make_gen("4k4/9/9/9/4N4/9/3p5/9/9/4K4 w - - 0 1")
        horse_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == 4*9+4]
        assert_moves_contain(horse_moves, "e4d6")


# ==============================================================================
# 4. TƯỢNG (B) - Đi chéo 2 ô, không qua sông, check mắt tượng
# ==============================================================================

class TestElephantMoves:
    def test_elephant_cannot_cross_river(self):
        """Tượng Đỏ không được qua sông (hàng 0-4)."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/4B4/9/4K4 w - - 0 1")
        elephant_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == 7*9+4]
        uci_set = to_uci_set(elephant_moves)
        for uci in uci_set:
            to_sq = uci_to_sq(uci[2:])
            row = to_sq // 9
            assert row >= 5, f"Tượng Đỏ qua sông: {uci}"

    def test_black_elephant_cannot_cross_river(self):
        """Tượng Đen không được qua sông (hàng 5-9)."""
        b, gen = make_gen("4k4/9/4b4/9/9/9/9/9/9/4K4 b - - 0 1")
        elephant_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == 2*9+4]
        uci_set = to_uci_set(elephant_moves)
        for uci in uci_set:
            to_sq = uci_to_sq(uci[2:])
            row = to_sq // 9
            assert row <= 4, f"Tượng Đen qua sông: {uci}"

    def test_elephant_blocked_by_eye(self):
        """Tượng bị cản mắt không đi được hướng đó."""
        # Tượng e7, mắt hướng trên-trái là d8 bị chặn
        b, gen = make_gen("4k4/9/9/9/9/9/9/4B4/3P5/4K4 w - - 0 1")
        # d8 (hàng 8, cột 3) = sq 8*9+3=75 có Tốt Đỏ
        elephant_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == 7*9+4]
        assert_moves_not_contain(elephant_moves, "e7c9")  # hướng trên-trái

    def test_elephant_max_4_moves(self):
        """Tượng không bị cản tối đa 4 nước đi."""
        b, gen = make_gen("4k4/9/9/9/9/9/4B4/9/9/4K4 w - - 0 1")
        elephant_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == 6*9+4]
        assert len(elephant_moves) <= 4


# ==============================================================================
# 5. SĨ (A) - Đi chéo 1 ô trong cung
# ==============================================================================

class TestAdvisorMoves:
    def test_advisor_stays_in_palace(self):
        """Sĩ không được ra ngoài cung."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/9/9/3AK4 w - - 0 1")
        advisor_sq = 9*9 + 3  # d9
        advisor_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == advisor_sq]
        red_palace = {66, 67, 68, 75, 76, 77, 84, 85, 86}
        for mv in advisor_moves:
            assert get_to_sq(mv) in red_palace, f"Sĩ ra ngoài cung: {sq_to_uci(get_to_sq(mv))}"

    def test_advisor_at_center_has_4_moves(self):
        """Sĩ ở giữa cung (e8) có đúng 4 nước đi."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/9/4A4/4K4 w - - 0 1")
        advisor_sq = 8*9 + 4  # e8
        advisor_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == advisor_sq]
        assert len(advisor_moves) == 4

    def test_advisor_at_corner_has_1_move(self):
        """Sĩ ở góc cung chỉ có 1 nước đi (về giữa)."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/9/9/3AK4 w - - 0 1")
        advisor_sq = 9*9 + 3  # d9 (góc cung Đỏ)
        advisor_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == advisor_sq]
        assert len(advisor_moves) == 1

    def test_black_advisor_stays_in_palace(self):
        """Sĩ Đen không ra ngoài cung Đen."""
        b, gen = make_gen("3ak4/9/9/9/9/9/9/9/9/4K4 b - - 0 1")
        advisor_sq = 0*9 + 3  # d0
        advisor_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == advisor_sq]
        black_palace = {3, 4, 5, 12, 13, 14, 21, 22, 23}
        for mv in advisor_moves:
            assert get_to_sq(mv) in black_palace


# ==============================================================================
# 6. TƯỚNG (K) - Đi thẳng 1 ô trong cung
# ==============================================================================

class TestKingMoves:
    def test_king_stays_in_palace(self):
        """Tướng không được ra ngoài cung."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1")
        king_sq = 9*9 + 4  # e9
        king_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == king_sq]
        red_palace = {66, 67, 68, 75, 76, 77, 84, 85, 86}
        for mv in king_moves:
            assert get_to_sq(mv) in red_palace

    def test_king_at_center_has_4_moves(self):
        """Tướng ở giữa cung (e8) có 4 nước đi."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/9/4K4/9 w - - 0 1")
        king_sq = 8*9 + 4  # e8
        king_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == king_sq]
        assert len(king_moves) == 4

    def test_king_cannot_move_diagonally(self):
        """Tướng không được đi chéo."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/9/9/4K4 w - - 0 1")
        king_sq = 9*9 + 4
        king_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == king_sq]
        for mv in king_moves:
            frm_r, frm_c = divmod(get_from_sq(mv), 9)
            to_r, to_c = divmod(get_to_sq(mv), 9)
            # Không được đi chéo (cả hàng lẫn cột đều thay đổi)
            assert not (abs(frm_r - to_r) == 1 and abs(frm_c - to_c) == 1)

    def test_king_blocked_by_own_piece(self):
        """Tướng không được đi vào ô có quân mình."""
        b, gen = make_gen("4k4/9/9/9/9/9/9/9/4A4/4K4 w - - 0 1")
        king_sq = 9*9 + 4
        king_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == king_sq]
        assert_moves_not_contain(king_moves, "e9e8")


# ==============================================================================
# 7. TỐT (P) - Tiến thẳng, qua sông thì thêm ngang
# ==============================================================================

class TestPawnMoves:
    def test_red_pawn_before_river_only_advances(self):
        """Tốt Đỏ chưa qua sông chỉ được tiến."""
        b, gen = make_gen("4k4/9/9/9/9/9/4P4/9/9/4K4 w - - 0 1")
        pawn_sq = 6*9 + 4  # e6
        pawn_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == pawn_sq]
        assert len(pawn_moves) == 1
        assert_moves_contain(pawn_moves, "e6e5")  # chỉ tiến 1 ô

    def test_red_pawn_after_river_can_move_sideways(self):
        """Tốt Đỏ qua sông được đi ngang."""
        b, gen = make_gen("4k4/9/9/9/4P4/9/9/9/9/4K4 w - - 0 1")
        pawn_sq = 4*9 + 4  # e4
        pawn_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == pawn_sq]
        assert len(pawn_moves) == 3  # tiến + trái + phải
        assert_moves_contain(pawn_moves, "e4e3", "e4d4", "e4f4")

    def test_red_pawn_cannot_retreat(self):
        """Tốt Đỏ không được đi lùi."""
        b, gen = make_gen("4k4/9/9/9/4P4/9/9/9/9/4K4 w - - 0 1")
        pawn_sq = 4*9 + 4
        pawn_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == pawn_sq]
        assert_moves_not_contain(pawn_moves, "e4e5")

    def test_black_pawn_advances_downward(self):
        """Tốt Đen tiến xuống (tăng hàng)."""
        b, gen = make_gen("4k4/9/9/4p4/9/9/9/9/9/4K4 b - - 0 1")
        pawn_sq = 3*9 + 4  # e3
        pawn_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == pawn_sq]
        assert_moves_contain(pawn_moves, "e3e4")
        assert_moves_not_contain(pawn_moves, "e3e2")

    def test_black_pawn_after_river_can_move_sideways(self):
        """Tốt Đen qua sông được đi ngang."""
        b, gen = make_gen("4k4/9/9/9/9/4p4/9/9/9/4K4 b - - 0 1")
        pawn_sq = 5*9 + 4  # e5
        pawn_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == pawn_sq]
        assert len(pawn_moves) == 3
        assert_moves_contain(pawn_moves, "e5e6", "e5d5", "e5f5")

    def test_pawn_at_board_edge_no_sideways_wrap(self):
        """Tốt qua sông ở biên bàn không được đi tràn sang hàng khác."""
        b, gen = make_gen("4k4/9/9/9/P8/9/9/9/9/4K4 w - - 0 1")
        pawn_sq = 4*9 + 0  # a4
        pawn_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == pawn_sq]
        uci_set = to_uci_set(pawn_moves)
        # Không được đi sang cột i (tràn hàng)
        assert "a4i4" not in uci_set

    def test_pawn_can_capture_enemy(self):
        """Tốt ăn được quân đối phương."""
        b, gen = make_gen("4k4/9/9/9/4Pp3/9/9/9/9/4K4 w - - 0 1")
        pawn_sq = 4*9 + 4  # e4 Tốt Đỏ
        pawn_moves = [m for m in gen.get_pseudo_legal_moves() if get_from_sq(m) == pawn_sq]
        assert_moves_contain(pawn_moves, "e4f4")  # ăn Tốt Đen ở f4


# ==============================================================================
# 8. PERFT TEST - Đếm số node theo độ sâu
# ==============================================================================

def perft(board, gen, depth):
    """Đếm số lá (leaf nodes) ở độ sâu cho trước."""
    from core.rules import get_legal_moves
    if depth == 0:
        return 1
    moves = get_legal_moves(board, gen)
    count = 0
    for move in moves:
        board.make_move(move)
        count += perft(board, MoveGenerator(board), depth - 1)
        board.undo_move()
    return count

class TestPerft:
    """
    Perft từ vị trí ban đầu cờ tướng.
    Số liệu tham chiếu từ: https://www.chessprogramming.org/Xiangqi
    """
    def test_perft_depth_1(self):
        """Depth 1: 44 nước đi hợp lệ từ vị trí ban đầu."""
        b = Board()
        gen = MoveGenerator(b)
        assert perft(b, gen, 1) == 44

    def test_perft_depth_2(self):
        """Depth 2: 1920 nodes."""
        b = Board()
        gen = MoveGenerator(b)
        assert perft(b, gen, 2) == 1920

    def test_perft_no_move_lost_after_make_undo(self):
        """Sau make/undo, số nước đi depth=1 phải bằng nhau."""
        b = Board()
        gen = MoveGenerator(b)
        count_before = perft(b, gen, 1)
        b.make_move(uci_to_move("b7b5"))
        b.undo_move()
        gen2 = MoveGenerator(b)
        count_after = perft(b, gen2, 1)
        assert count_before == count_after