# evaluator.py
from core.board import Board
from core.move_generator import MoveGenerator
from core.pieces import Color, PIECE_VALUES, is_black, is_red

# Trọng số vị trí (bảng 90 ô rút gọn cho bên đỏ)
_RED_P_TABLE = [
    0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0,
    2, 0, 2, 0, 2, 0, 2, 0, 2,
    4, 0, 4, 0, 4, 0, 4, 0, 4,
    5, 5, 5, 5, 5, 5, 5, 5, 5,
    5, 5, 5, 5, 5, 5, 5, 5, 5,
    2, 0, 2, 0, 2, 0, 2, 0, 2,
    0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0,
]

WEIGHT_VECTOR = {
    "material": 1.0,
    "pawn_structure": 0.5,
    "mobility": 0.1,
    "king_safety": 1.0,
}

# ---------------------------------------------------------------------------
# Các hằng số An toàn Tướng (dựa trên CPW / Stockfish / Glaurung cho Cờ Tướng)
# ---------------------------------------------------------------------------

# Các ô trong cung
_RED_PALACE = {66, 67, 68, 75, 76, 77, 84, 85, 86}
_BLACK_PALACE = {3, 4, 5, 12, 13, 14, 21, 22, 23}

# Vùng Tướng: các ô trong cung + một hàng tiến về phía đối phương.
# Đây là những ô mà quân tấn công gây đe dọa nguy hiểm nhất.
_RED_KING_ZONE = _RED_PALACE | {57, 58, 59}      # hàng 6 các cột trung tâm
_BLACK_KING_ZONE = _BLACK_PALACE | {30, 31, 32}   # hàng 3 các cột trung tâm

# Áp lực của quân cờ lên các ô vùng Tướng.
_ZONE_ATTACK_VALUE = {
    'H': 20, 'h': 20,
    'C': 25, 'c': 25,
    'R': 40, 'r': 40,
    'P': 10, 'p': 10,
}

# Tỉ lệ áp lực tấn công theo số lượng quân tấn công riêng biệt (bảng mẫu CPW).
_ATTACKER_WEIGHT_TABLE = [0, 0, 50, 75, 88, 94, 97, 99, 100]

# Số hàng phía trước Tướng được tính là lá chắn bảo vệ tại chỗ.
_SHELTER_DEPTH = 4

# Hướng Tướng (Tropism): trọng số khoảng cách Chebyshev mỗi quân cờ để tính điểm khoảng cách tới Tướng.
# Trọng số càng cao = quân cờ ở gần Tướng đối phương càng quan trọng.
_TROPISM_WEIGHT = {
    'R': 3, 'r': 3,
    'C': 2, 'c': 2,
    'H': 3, 'h': 3,
    'P': 1, 'p': 1,
}


# ---------------------------------------------------------------------------
# Hàm bổ trợ
# ---------------------------------------------------------------------------

def _chebyshev(sq1: int, sq2: int) -> int:
    """Khoảng cách Chebyshev (vua) trên bàn cờ 9x10."""
    r1, c1 = divmod(sq1, 9)
    r2, c2 = divmod(sq2, 9)
    return max(abs(r1 - r2), abs(c1 - c2))


def _find_king(board: Board, color: Color) -> int:
    """Trả về chỉ số ô của Tướng cho phe *color*."""
    target = 'K' if color == Color.RED else 'k'
    return board.state.index(target)


def _count_defenders(board: Board, color: Color) -> int:
    """Đếm số Sĩ và Tượng còn lại trên bàn cờ cho phe *color* (Lá chắn Tướng).

    Trong Cờ Tướng, Sĩ (A/a) và Tượng (E/e) đóng vai trò lá chắn bảo vệ Tướng
    bên trong hoặc gần cung, tương tự như lá chắn tốt trong cờ vua.
    """
    if color == Color.RED:
        return sum(1 for p in board.state if p in ('A', 'E'))
    return sum(1 for p in board.state if p in ('a', 'e'))


def _pieces_attacking_zone(board: Board, zone: set[int], attacker_color: Color) -> tuple[int, int]:
    """Trả về (số_quân_tấn_công, áp_lực_tấn_công) vào vùng Tướng đối phương."""
    from core.move import get_from_sq, get_to_sq

    gen = MoveGenerator(board)
    original_side = board.side_to_move
    board.side_to_move = attacker_color
    try:
        moves = gen.get_pseudo_legal_moves()
    finally:
        board.side_to_move = original_side

    attackers: set[int] = set()
    pressure = 0

    for mv in moves:
        to_sq = get_to_sq(mv)
        if to_sq not in zone:
            continue
        frm = get_from_sq(mv)
        piece = board.state[frm]
        if piece.upper() in ('A', 'E', 'K'):
            continue
        attackers.add(frm)
        pressure += _ZONE_ATTACK_VALUE.get(piece, 0)

    return len(attackers), pressure


def _open_file_near_king(board: Board, king_sq: int, defender_color: Color) -> int:
    """Hình phạt cho các cột không có quân tốt che chắn tại vùng Tướng."""
    king_row, king_col = divmod(king_sq, 9)
    pawn_char = 'P' if defender_color == Color.RED else 'p'
    penalty = 0

    if defender_color == Color.RED:
        shelter_rows = range(max(0, king_row - _SHELTER_DEPTH), king_row + 1)
    else:
        shelter_rows = range(king_row, min(10, king_row + _SHELTER_DEPTH + 1))

    for col in range(max(0, king_col - 1), min(9, king_col + 2)):
        has_shield = any(board.state[row * 9 + col] == pawn_char for row in shelter_rows)
        if not has_shield:
            penalty += 15

    return penalty


# ---------------------------------------------------------------------------
# Đánh giá An toàn Tướng
# ---------------------------------------------------------------------------

def _evaluate_king_safety(board: Board) -> int:
    """Điểm an toàn Tướng từ góc nhìn phe Đỏ (dương = Đỏ an toàn hơn)."""
    red_king_sq = _find_king(board, Color.RED)
    black_king_sq = _find_king(board, Color.BLACK)

    red_danger = _king_safety_for_side(board, Color.RED, red_king_sq)
    black_danger = _king_safety_for_side(board, Color.BLACK, black_king_sq)

    return black_danger - red_danger


def _king_safety_for_side(board: Board, color: Color, king_sq: int) -> int:
    """Tính toán điểm nguy hiểm cho Tướng phe *color* (càng cao càng nguy hiểm).

    Mối đe dọa được tính dựa trên khả năng tấn công của đối thủ lên vùng Tướng
    và các yếu tố phòng thủ hiện có của phe *color*.
    """
    opp_color = Color.BLACK if color == Color.RED else Color.RED
    zone = _RED_KING_ZONE if color == Color.RED else _BLACK_KING_ZONE

    # 1. Lá chắn phòng thủ (Sĩ + Tượng) — tối đa 4 quân.
    defenders = _count_defenders(board, color)
    # Phạt cho mỗi quân phòng thủ bị mất.
    shield_penalty = (4 - defenders) * 15

    # 2. Cột mở gần Tướng (thiếu tốt che chắn).
    open_file_penalty = _open_file_near_king(board, king_sq, color)

    # 3. Hướng Tướng (Tropism) — khoảng cách quân tấn công đối phương tới Tướng.
    tropism_score = 0
    for sq, piece in enumerate(board.state):
        if piece == '.':
            continue
        if (color == Color.RED and is_black(piece)) or \
           (color == Color.BLACK and is_red(piece)):
            weight = _TROPISM_WEIGHT.get(piece, 0)
            if weight:
                dist = max(_chebyshev(sq, king_sq), 1)
                tropism_score += weight * 10 // dist

    # 4. Áp lực tấn công vùng Tướng (bỏ qua nếu chỉ có 1 quân tấn công).
    num_attackers, attack_pressure = _pieces_attacking_zone(board, zone, opp_color)
    if num_attackers < 2:
        zone_attack_score = 0
    else:
        idx = min(num_attackers, len(_ATTACKER_WEIGHT_TABLE) - 1)
        zone_attack_score = attack_pressure * _ATTACKER_WEIGHT_TABLE[idx] // 100

    # 5. Tỉ lệ nguy hiểm theo vật chất còn lại của đối phương.
    #    Tổng giá trị phi-tướng: 2R + 2H + 2E + 2A + 2C + 5P = 2940
    opp_material = 0
    for piece in board.state:
        if piece == '.' or piece.upper() == 'K':
            continue
        if (opp_color == Color.RED and is_red(piece)) or \
           (opp_color == Color.BLACK and is_black(piece)):
            opp_material += PIECE_VALUES.get(piece, 0)
    material_scale = min(opp_material, 2940) / 2940

    # Kết hợp các yếu tố nguy hiểm.
    danger = (
        shield_penalty
        + open_file_penalty
        + tropism_score
        + int(zone_attack_score * material_scale)
    )
    return danger


# ---------------------------------------------------------------------------
# Các thành phần đánh giá cơ bản
# ---------------------------------------------------------------------------

def _evaluate_material(board: Board) -> int:
    """Tính toán chênh lệch giá trị quân cờ (Vật chất)."""
    score = 0
    for piece in board.state:
        if piece == '.':
            continue
        val = PIECE_VALUES.get(piece, 0)
        if is_red(piece):
            score += val
        else:
            score -= val
    return score


def _evaluate_pawn_structure(board: Board) -> int:
    """Tính toán điểm thưởng vị trí cho quân Tốt."""
    score = 0
    for sq, piece in enumerate(board.state):
        if piece == 'P':
            score += _RED_P_TABLE[sq]
        elif piece == 'p':
            score -= _RED_P_TABLE[89 - sq]
    return score


def _evaluate_mobility(board: Board) -> int:
    """Tính toán chênh lệch số lượng nước đi khả thi (Tính cơ động)."""
    gen = MoveGenerator(board)
    orig = board.side_to_move

    board.side_to_move = Color.RED
    red_moves = len(gen.get_pseudo_legal_moves())

    board.side_to_move = Color.BLACK
    black_moves = len(gen.get_pseudo_legal_moves())

    board.side_to_move = orig
    return red_moves - black_moves


# ---------------------------------------------------------------------------
# Hàm lượng giá tổng hợp (Heuristic)
# ---------------------------------------------------------------------------

def heuristic(board: Board) -> int:
    """Hàm đánh giá trạng thái bàn cờ tổng quát."""
    m   = _evaluate_material(board)       * WEIGHT_VECTOR["material"]
    p   = _evaluate_pawn_structure(board)  * WEIGHT_VECTOR["pawn_structure"]
    mob = _evaluate_mobility(board)        * WEIGHT_VECTOR["mobility"]
    ks  = _evaluate_king_safety(board)     * WEIGHT_VECTOR["king_safety"]

    return int(m + p + mob + ks)
