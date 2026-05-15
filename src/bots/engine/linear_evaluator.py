from core.board import Board
from core.move_generator import MoveGenerator
from core.pieces import Color, PIECE_VALUES, is_black, is_red

# ===========================================================================
# PIECE-SQUARE TABLES  —  góc nhìn phe ĐỎ, hàng 9 = sân Đỏ
# Phe Đen dùng bảng lật (89 - sq).
# ===========================================================================

# --- Xe (R) ---
# Nguyên tắc:
#   + Thưởng hàng 7 (hàng trống sau tốt, chuẩn bị tấn công)
#   + Thưởng cột trung tâm d-f ở PHÍA ĐỊCh (hàng 0-4)
#   + PHẠT nặng khi vào cung mình (hàng 7-9 cột d-f = sq 66-68,75-77,84-86)
#   + Vị trí góc ban đầu (a9=81, i9=89) để nguyên, đừng phạt (chờ khai cuộc)
_PST_R = [
#   a    b    c    d    e    f    g    h    i
   206, 208, 207, 210, 208, 210, 207, 208, 206,  # row 0 (địch)
   208, 212, 209, 212, 212, 212, 209, 212, 208,  # row 1
   206, 208, 207, 210, 210, 210, 207, 208, 206,  # row 2
   206, 210, 210, 212, 212, 212, 210, 210, 206,  # row 3
   208, 211, 211, 213, 214, 213, 211, 211, 208,  # row 4 (giữa bàn)
   210, 212, 212, 214, 215, 214, 212, 212, 210,  # row 5 (giữa bàn)
   212, 214, 214, 216, 218, 216, 214, 214, 212,  # row 6 (hàng tốt Đỏ)
   214, 216, 214, 214, 214, 214, 214, 216, 214,  # row 7 (hàng trống — vị trí tốt nhất)
   206, 208, 207, 198, 196, 198, 207, 208, 206,  # row 8 (phạt cột d-f = gần cung)
   206, 208, 207, 196, 194, 196, 207, 208, 206,  # row 9 (phạt cột d-f = trong cung)
]

# --- Mã (H) ---
# Triển khai lên hàng 7 (g7/c7), sau đó tiến sang sông
_PST_H = [
#   a    b    c    d    e    f    g    h    i
    84,  87,  90,  93,  87,  93,  90,  87,  84,  # row 0
    87,  93, 100,  95,  91,  95, 100,  93,  87,  # row 1
    89,  96,  97, 101,  96, 101,  97,  96,  89,  # row 2
    90, 106,  98, 105,  98, 105,  98, 106,  90,  # row 3
    87,  98,  97, 101, 102, 101,  97,  98,  87,  # row 4
    87,  96,  99, 100, 101, 100,  99,  96,  87,  # row 5
    89,  96,  97, 101,  96, 101,  97,  96,  89,  # row 6
    92, 108,  99, 106,  99, 106,  99, 108,  92,  # row 7 (vị trí triển khai tốt nhất)
    84,  93, 100,  93,  88,  93, 100,  93,  84,  # row 8
    80,  83,  83,  88,  83,  88,  83,  83,  80,  # row 9 (ban đầu, nên di chuyển)
]

# --- Pháo (C) ---
# Nguyên tắc:
#   + Nên ở hàng 7 ban đầu (b7/h7) — đây là vị trí khai cuộc chuẩn
#   + Tiến lên hàng 4-5 để tấn công (thưởng cột e)
#   + PHẠT khi lùi về hàng 9 a/i (mất tác dụng tấn công)
#   + Không thưởng hàng 9 góc nữa
_PST_C = [
#   a    b    c    d    e    f    g    h    i
   100, 100,  97,  91,  92,  91,  97, 100, 100,  # row 0 (địch)
    99,  99,  97,  93,  90,  93,  97,  99,  99,  # row 1
    98,  98,  97,  92,  93,  92,  97,  98,  98,  # row 2
    97, 100, 100,  99, 101,  99, 100, 100,  97,  # row 3
    97,  97,  97,  97, 102,  97,  97,  97,  97,  # row 4
    96,  97, 100,  97, 102,  97, 100,  97,  96,  # row 5 (giữa bàn)
    97,  97,  97,  97, 100,  97,  97,  97,  97,  # row 6
    99,  99,  98,  92,  93,  92,  98,  99,  99,  # row 7 (vị trí khai cuộc)
    95,  95,  94,  90,  88,  90,  94,  95,  95,  # row 8
    93,  91,  93,  89,  88,  89,  93,  91,  93,  # row 9 (phạt góc a9/i9)
]

# --- Tốt (P) ---
# Hàng 6 của Đỏ = chưa qua sông → 0 điểm vị trí, chỉ tiến
# Hàng 0-4 (đã qua sông) → thưởng mạnh, đặc biệt cột giữa
_PST_P = [
#   a    b    c    d    e    f    g    h    i
     9,   9,   9,  11,  13,  11,   9,   9,   9,  # row 0 (sát sân địch)
    13,  13,  13,  15,  15,  15,  13,  13,  13,  # row 1
    14,  14,  14,  16,  17,  16,  14,  14,  14,  # row 2
    14,  16,  16,  20,  22,  20,  16,  16,  14,  # row 3
    14,  16,  16,  20,  22,  20,  16,  16,  14,  # row 4
     0,   0,   5,   0,   5,   0,   5,   0,   0,  # row 5 (chưa qua sông)
     0,   0,   5,   0,   5,   0,   5,   0,   0,  # row 6 (vị trí ban đầu tốt Đỏ)
     0,   0,   0,   0,   0,   0,   0,   0,   0,  # row 7
     0,   0,   0,   0,   0,   0,   0,   0,   0,  # row 8
     0,   0,   0,   0,   0,   0,   0,   0,   0,  # row 9
]

# --- Sĩ (A) ---
_PST_A = [
    0, 0, 0,  0,  0,  0,  0, 0, 0,
    0, 0, 0,  0,  0,  0,  0, 0, 0,
    0, 0, 0,  0,  0,  0,  0, 0, 0,
    0, 0, 0, 20,  0, 20,  0, 0, 0,
    0, 0, 0,  0, 23,  0,  0, 0, 0,
    0, 0, 0, 20,  0, 20,  0, 0, 0,
    0, 0, 0,  0,  0,  0,  0, 0, 0,
    0, 0, 0, 20,  0, 20,  0, 0, 0,
    0, 0, 0,  0, 23,  0,  0, 0, 0,
    0, 0, 0, 20,  0, 20,  0, 0, 0,
]

# --- Tượng (E) ---
_PST_E = [
    0,  0, 20,  0,  0,  0, 20,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,
   18,  0,  0,  0, 23,  0,  0,  0, 18,
    0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0, 20,  0,  0,  0, 20,  0,  0,
    0,  0, 20,  0,  0,  0, 20,  0,  0,
    0,  0,  0,  0,  0,  0,  0,  0,  0,
   18,  0,  0,  0, 23,  0,  0,  0, 18,
    0,  0,  0,  0,  0,  0,  0,  0,  0,
    0,  0, 20,  0,  0,  0, 20,  0,  0,
]

# --- Tướng (K): ở giữa cung, tránh sát biên ---
_PST_K = [
    0, 0, 0,  1,  1,  1,  0, 0, 0,
    0, 0, 0,  2,  2,  2,  0, 0, 0,
    0, 0, 0,  3,  3,  3,  0, 0, 0,
    0, 0, 0,  0,  0,  0,  0, 0, 0,
    0, 0, 0,  0,  0,  0,  0, 0, 0,
    0, 0, 0,  0,  0,  0,  0, 0, 0,
    0, 0, 0,  0,  0,  0,  0, 0, 0,
    0, 0, 0,  3,  3,  3,  0, 0, 0,
    0, 0, 0,  2,  2,  2,  0, 0, 0,
    0, 0, 0,  1,  1,  1,  0, 0, 0,
]

_PST_MAP = {
    'R': _PST_R, 'H': _PST_H, 'C': _PST_C,
    'P': _PST_P, 'A': _PST_A, 'E': _PST_E, 'K': _PST_K,
}

# Trọng số — giảm king_safety để bot bớt thụ động
WEIGHT_VECTOR = {
    "material":   1.0,
    "position":   1.2,  
    "king_safety": 0.5,  
    "mobility":   0.1,
    "rook_open":  0.6,
}

# ===========================================================================
# GAME PHASE
# ===========================================================================
_PHASE_OPENING = 2400
_PHASE_ENDGAME = 1200


def _game_phase(board: Board) -> float:
    """0.0 = endgame, 1.0 = opening."""
    total = sum(
        PIECE_VALUES.get(p, 0)
        for p in board.state
        if p != '.' and p.upper() != 'K'
    )
    return min(1.0, max(0.0, (total - _PHASE_ENDGAME) / (_PHASE_OPENING - _PHASE_ENDGAME)))


# ===========================================================================
# PST evaluation
# ===========================================================================

def _evaluate_pst(board: Board) -> int:
    score = 0
    for sq, piece in enumerate(board.state):
        if piece == '.':
            continue
        table = _PST_MAP.get(piece.upper())
        if table is None:
            continue
        if is_red(piece):
            score += table[sq]
        else:
            score -= table[89 - sq]
    return score


# ===========================================================================
# Material
# ===========================================================================

def _evaluate_material(board: Board) -> int:
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


# ===========================================================================
# Mobility (pseudo-legal — nhanh)
# ===========================================================================

def _evaluate_mobility(board: Board) -> int:
    gen = MoveGenerator(board)
    orig = board.side_to_move
    board.side_to_move = Color.RED
    red_moves = len(gen.get_pseudo_legal_moves())
    board.side_to_move = Color.BLACK
    black_moves = len(gen.get_pseudo_legal_moves())
    board.side_to_move = orig
    return red_moves - black_moves


# ===========================================================================
# Rook open file/rank bonus
# ===========================================================================

def _evaluate_rook_open(board: Board) -> int:
    score = 0
    for sq, piece in enumerate(board.state):
        if piece not in ('R', 'r'):
            continue
        row, col = divmod(sq, 9)
        red = piece == 'R'

        # Cột mở: không có quân cùng phe trên cùng cột
        col_open = all(
            board.state[r * 9 + col] == '.' or
            (red and is_black(board.state[r * 9 + col])) or
            (not red and is_red(board.state[r * 9 + col]))
            for r in range(10) if r != row
        )
        if col_open:
            score += 15 if red else -15

        # Hàng mở
        row_open = all(
            board.state[row * 9 + c] == '.' or
            (red and is_black(board.state[row * 9 + c])) or
            (not red and is_red(board.state[row * 9 + c]))
            for c in range(9) if c != col
        )
        if row_open:
            score += 10 if red else -10

    return score


# ===========================================================================
# King Safety
# ===========================================================================

_TROPISM_WEIGHT = {'R': 4, 'r': 4, 'C': 3, 'c': 3, 'H': 3, 'h': 3, 'P': 1, 'p': 1}


def _chebyshev(sq1: int, sq2: int) -> int:
    r1, c1 = divmod(sq1, 9)
    r2, c2 = divmod(sq2, 9)
    return max(abs(r1 - r2), abs(c1 - c2))


def _find_king(board: Board, color: Color) -> int:
    target = 'K' if color == Color.RED else 'k'
    return board.state.index(target)


def _count_defenders(board: Board, color: Color) -> int:
    if color == Color.RED:
        return sum(1 for p in board.state if p in ('A', 'E'))
    return sum(1 for p in board.state if p in ('a', 'e'))


def _king_danger(board: Board, color: Color, king_sq: int, phase: float) -> int:
    defenders = _count_defenders(board, color)
    shield_penalty = (4 - defenders) * 20

    tropism = 0
    for sq, piece in enumerate(board.state):
        if piece == '.':
            continue
        if (color == Color.RED and is_black(piece)) or \
           (color == Color.BLACK and is_red(piece)):
            w = _TROPISM_WEIGHT.get(piece, 0)
            if w:
                dist = max(_chebyshev(sq, king_sq), 1)
                tropism += w * 10 // dist

    # Tropism mạnh hơn trong opening, yếu hơn endgame
    tropism = int(tropism * (0.4 + 0.6 * phase))
    return shield_penalty + tropism


def _evaluate_king_safety(board: Board, phase: float) -> int:
    red_king_sq   = _find_king(board, Color.RED)
    black_king_sq = _find_king(board, Color.BLACK)
    red_danger    = _king_danger(board, Color.RED,   red_king_sq,   phase)
    black_danger  = _king_danger(board, Color.BLACK, black_king_sq, phase)
    return black_danger - red_danger


# ===========================================================================
# Tổng hợp
# ===========================================================================

def _evaluate_absolute_score(board: Board) -> int:
    phase = _game_phase(board)
    mat      = _evaluate_material(board)
    pst      = _evaluate_pst(board)
    ksafety  = _evaluate_king_safety(board, phase)
    mob      = _evaluate_mobility(board)
    rook_op  = _evaluate_rook_open(board)
    return int(
        mat     * WEIGHT_VECTOR["material"]    +
        pst     * WEIGHT_VECTOR["position"]    +
        ksafety * WEIGHT_VECTOR["king_safety"] +
        mob     * WEIGHT_VECTOR["mobility"]    +
        rook_op * WEIGHT_VECTOR["rook_open"]
    )


def heuristic(board: Board) -> int:
    s = _evaluate_absolute_score(board)
    return s if board.side_to_move == Color.RED else -s


def get_heuristic_breakdown(board: Board) -> dict:
    phase    = _game_phase(board)
    mat      = _evaluate_material(board)
    pst      = _evaluate_pst(board)
    ksafety  = _evaluate_king_safety(board, phase)
    mob      = _evaluate_mobility(board)
    rook_op  = _evaluate_rook_open(board)
    total    = int(
        mat     * WEIGHT_VECTOR["material"]    +
        pst     * WEIGHT_VECTOR["position"]    +
        ksafety * WEIGHT_VECTOR["king_safety"] +
        mob     * WEIGHT_VECTOR["mobility"]    +
        rook_op * WEIGHT_VECTOR["rook_open"]
    )
    return {
        "total": total,
        "phase": f"{'opening' if phase > 0.7 else 'middlegame' if phase > 0.3 else 'endgame'} ({phase:.2f})",
        "components": {
            "material":    {"raw": mat,     "weighted": mat     * WEIGHT_VECTOR["material"]},
            "position":    {"raw": pst,     "weighted": pst     * WEIGHT_VECTOR["position"]},
            "king_safety": {"raw": ksafety, "weighted": ksafety * WEIGHT_VECTOR["king_safety"]},
            "mobility":    {"raw": mob,     "weighted": mob     * WEIGHT_VECTOR["mobility"]},
            "rook_open":   {"raw": rook_op, "weighted": rook_op * WEIGHT_VECTOR["rook_open"]},
        },
        "metadata": {
            "side_to_move": "Đỏ" if board.side_to_move == Color.RED else "Đen",
            "weights_used": WEIGHT_VECTOR,
        }
    }