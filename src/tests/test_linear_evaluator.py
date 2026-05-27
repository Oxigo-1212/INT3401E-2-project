# test_linear_evaluator.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.board import Board
from core.pieces import Color
from bots.engine.linear_evaluator import (
    heuristic,
    _evaluate_material,
    _evaluate_pst,
    _evaluate_mobility,
    _evaluate_king_safety,
    _count_defenders,
    _find_king,
    _evaluate_rook_open,
    _game_phase,
)

def _king_safety_for_side(board: Board, color: Color, king_sq: int) -> int:
    """Helper to simulate the old _king_safety_for_side function using the new _king_danger function."""
    from bots.engine.linear_evaluator import _king_danger
    return _king_danger(board, color, king_sq, _game_phase(board))


# ── Các bài kiểm tra hiện có (đã sửa import _evaluate_position → _evaluate_pawn_structure) ──

def test_initial_board_neutral():
    """Bàn cờ ban đầu nên ở trạng thái cân bằng (0)."""
    board = Board()
    score = heuristic(board)
    assert score == 0


def test_material_advantage():
    """Việc loại bỏ một quân cờ sẽ làm thay đổi điểm vật chất."""
    board = Board()
    board.state[0] = '.'  # loại bỏ quân xe đen tại ô 0

    m_score = _evaluate_material(board)
    assert m_score > 0  # Ưu thế cho Đỏ

    h_score = heuristic(board)
    assert h_score > 0


def test_pawn_position_bonus():
    """Quân tốt qua sông sẽ nhận được điểm thưởng vị trí."""
    board = Board()
    # Di chuyển tốt đỏ từ vị trí bắt đầu (ô 63) qua sông (ô 36)
    board.state[63] = '.'
    board.state[36] = 'P'

    p_score = _evaluate_pst(board)
    assert p_score > 0


def test_mobility():
    """Bàn cờ trống (ngoại trừ Tướng) nên có tính cơ động cụ thể."""
    board = Board()
    for i in range(90):
        if board.state[i] not in {'K', 'k'}:
            board.state[i] = '.'

    mob = _evaluate_mobility(board)
    assert mob == 0


# ── Các bài kiểm tra An toàn Tướng ─────────────────────────────────────────────────────

def test_king_safety_symmetric_at_start():
    """Vị trí bắt đầu: an toàn tướng nên đối xứng (điểm == 0)."""
    board = Board()
    ks = _evaluate_king_safety(board, _game_phase(board))
    assert ks == 0, f"Mong đợi 0 lúc bắt đầu, nhưng nhận được {ks}"


def test_defender_count():
    """Loại bỏ Sĩ/Tượng sẽ làm giảm số lượng quân phòng thủ."""
    board = Board()
    assert _count_defenders(board, Color.RED) == 4   # 2 Sĩ + 2 Tượng
    assert _count_defenders(board, Color.BLACK) == 4

    # Loại bỏ một sĩ đỏ (ô 76 = hàng 8, cột 4 là Tướng; sĩ tại 66, 68 trên hàng 7)
    # Thực tế, từ FEN: hàng 9 = RNBAKABNR → ô 84=R, 85=N, 86=B, 87=A, 88=K, 89=A,...
    # Hãy loại bỏ quân sĩ đỏ đầu tiên tìm thấy
    for i, p in enumerate(board.state):
        if p == 'A':
            board.state[i] = '.'
            break
    assert _count_defenders(board, Color.RED) == 3


def test_shield_penalty_missing_defenders():
    """Mất tất cả quân phòng thủ sẽ làm tăng đáng kể mức độ nguy hiểm."""
    board = Board()

    base_red = _king_safety_for_side(board, Color.RED,
                                      _find_king(board, Color.RED))
    # Loại bỏ tất cả sĩ và tượng đỏ
    for i in range(90):
        if board.state[i] in ('A', 'B'):
            board.state[i] = '.'

    exposed_red = _king_safety_for_side(board, Color.RED,
                                         _find_king(board, Color.RED))
    # Nguy hiểm hơn (điểm cao hơn) khi quân phòng thủ không còn
    assert exposed_red > base_red


def test_rook_open_file_bonus():
    """Quân xe trên cột/hàng mở nhận điểm thưởng."""
    board = Board()
    base = _evaluate_rook_open(board)

    # Xóa các quân cản đường cột của quân xe đỏ ở ô 81 (hàng 9, cột 0)
    for r in range(9):
        board.state[r * 9 + 0] = '.'

    after = _evaluate_rook_open(board)
    assert after > base, "Điểm số cột mở của Xe đỏ sẽ tăng lên"


def test_tropism_closer_piece_more_danger():
    """Di chuyển một quân xe đối phương lại gần tướng sẽ làm tăng mức độ nguy hiểm."""
    # Bàn cờ trống + Tướng + một xe đen ở xa
    board = Board()
    for i in range(90):
        if board.state[i] not in {'K', 'k'}:
            board.state[i] = '.'

    # Xe đen cách xa tướng đỏ (góc trên bên trái)
    board.state[0] = 'r'
    far_danger = _king_safety_for_side(board, Color.RED,
                                        _find_king(board, Color.RED))

    # Di chuyển xe đen lại gần tướng đỏ (hàng 7, cột 4 = ô 67)
    board.state[0] = '.'
    board.state[67] = 'r'
    close_danger = _king_safety_for_side(board, Color.RED,
                                          _find_king(board, Color.RED))
    assert close_danger > far_danger, "Quân đối phương càng gần thì càng nguy hiểm"


def test_zone_attack_multiple_attackers():
    """Nhiều quân tấn công vào vùng tướng sẽ kích hoạt bảng an toàn."""
    board = Board()
    for i in range(90):
        if board.state[i] not in {'K', 'k'}:
            board.state[i] = '.'

    # Đặt hai quân xe đen có thể tấn công vùng tướng đỏ
    # Tướng đỏ ở ô 76 (hàng 8, cột 4) theo mặc định nhưng chúng ta đã xóa —
    # tướng vẫn ở vị trí FEN mặc định: K tại ô 76, k tại ô 4
    # Thực tế sau khi xóa, tướng ở bất cứ nơi nào nó vốn có trong FEN mặc định.
    red_king_sq = _find_king(board, Color.RED)

    # Đặt các xe đen trên cùng một cột với tướng đỏ (chúng trượt thẳng xuống)
    _, king_col = divmod(red_king_sq, 9)
    rook1_sq = 0 * 9 + king_col  # phía trên cùng của bàn cờ, cùng cột
    rook2_sq = 5 * 9 + king_col  # giữa bàn cờ, cùng cột
    # Đảm bảo không ghi đè lên tướng
    if board.state[rook1_sq] in ('K', 'k'):
        rook1_sq += 1
    if board.state[rook2_sq] in ('K', 'k'):
        rook2_sq += 1
    board.state[rook1_sq] = 'r'
    board.state[rook2_sq] = 'r'

    danger = _king_safety_for_side(board, Color.RED, red_king_sq)
    assert danger > 0, "Hai xe nhắm vào tướng sẽ tạo ra mức nguy hiểm khác không"


def test_king_safety_favors_side_with_stronger_shield():
    """Nếu Đỏ mất tất cả quân phòng thủ nhưng Đen vẫn giữ được, đánh giá nên ưu tiên Đen."""
    board = Board()
    for i in range(90):
        if board.state[i] in ('A', 'B'):
            board.state[i] = '.'
    # Đen vẫn còn sĩ và tượng
    ks = _evaluate_king_safety(board, _game_phase(board))
    # Dương = nguy hiểm của đen − nguy hiểm của đỏ. Đỏ mất quân phòng thủ → nguy hiểm của đỏ > nguy hiểm của đen.
    assert ks < 0, f"Đỏ mất quân phòng thủ, điểm số nên là âm (nhận được {ks})"


def test_scaling_less_material_less_danger():
    """Khi hầu hết các quân đối phương đã mất, nguy hiểm tấn công vùng nên ở mức thấp."""
    board = Board()
    # Loại bỏ tất cả quân đen ngoại trừ tướng và một xe
    for i in range(90):
        p = board.state[i]
        if p.islower() and p not in ('k',):
            board.state[i] = '.'
    # Đặt lại một quân xe
    board.state[0] = 'r'

    red_king_sq = _find_king(board, Color.RED)
    danger = _king_safety_for_side(board, Color.RED, red_king_sq)

    # So sánh với quân đội đầy đủ
    board2 = Board()
    danger_full = _king_safety_for_side(board2, Color.RED,
                                         _find_king(board2, Color.RED))
    # Với hầu như không còn quân, mức nguy hiểm nên ≤ mức nguy hiểm khi đầy đủ quân
    assert danger <= danger_full
