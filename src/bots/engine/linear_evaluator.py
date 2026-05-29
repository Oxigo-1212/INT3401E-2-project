from core.board import Board
from core.move_generator import MoveGenerator
from core.pieces import Color, PIECE_VALUES, is_black, is_red

# Xe
_PST_R = [
#   a    b    c    d    e    f    g    h    i
   206, 208, 207, 210, 208, 210, 207, 208, 206,  
   208, 212, 209, 212, 212, 212, 209, 212, 208, 
   206, 208, 207, 210, 210, 210, 207, 208, 206, 
   206, 210, 210, 212, 212, 212, 210, 210, 206,  
   208, 211, 211, 213, 214, 213, 211, 211, 208,  
   210, 212, 212, 214, 215, 214, 212, 212, 210, 
   212, 214, 214, 216, 218, 216, 214, 214, 212, 
   214, 216, 214, 214, 214, 214, 214, 216, 214,  
   206, 208, 207, 198, 196, 198, 207, 208, 206, 
   206, 208, 207, 196, 194, 196, 207, 208, 206,  
]

# Mã
_PST_N = [
#   a    b    c    d    e    f    g    h    i
    84,  87,  90,  93,  87,  93,  90,  87,  84,  
    87,  93, 100,  95,  91,  95, 100,  93,  87,  
    89,  96,  97, 101,  96, 101,  97,  96,  89,  
    90, 106,  98, 105,  98, 105,  98, 106,  90,  
    87,  98,  97, 101, 102, 101,  97,  98,  87,  
    87,  96,  99, 100, 101, 100,  99,  96,  87,  
    89,  96,  97, 101,  96, 101,  97,  96,  89, 
    92, 108,  99, 106,  99, 106,  99, 108,  92,  
    84,  93, 100,  93,  88,  93, 100,  93,  84,  
    80,  83,  83,  88,  83,  88,  83,  83,  80,  
]

# Pháo
_PST_C = [
#   a    b    c    d    e    f    g    h    i
   100, 100,  97,  91,  92,  91,  97, 100, 100,  
    99,  99,  97,  93,  90,  93,  97,  99,  99,  
    98,  98,  97,  92,  93,  92,  97,  98,  98,  
    97, 100, 100,  99, 101,  99, 100, 100,  97, 
    97,  97,  97,  97, 102,  97,  97,  97,  97,  
    96,  97, 100,  97, 102,  97, 100,  97,  96,  
    97,  97,  97,  97, 100,  97,  97,  97,  97, 
    99,  99,  98,  92,  93,  92,  98,  99,  99, 
    95,  95,  94,  90,  88,  90,  94,  95,  95,  
    93,  91,  93,  89,  88,  89,  93,  91,  93,  
]

# Tốt
_PST_P = [
#   a    b    c    d    e    f    g    h    i
     9,   9,   9,  11,  13,  11,   9,   9,   9, 
    13,  13,  13,  15,  15,  15,  13,  13,  13,  
    14,  14,  14,  16,  17,  16,  14,  14,  14,  
    14,  16,  16,  20,  22,  20,  16,  16,  14,  
    14,  16,  16,  20,  22,  20,  16,  16,  14, 
     0,   0,   5,   0,   5,   0,   5,   0,   0,  
     0,   0,   5,   0,   5,   0,   5,   0,   0,  
     0,   0,   0,   0,   0,   0,   0,   0,   0, 
     0,   0,   0,   0,   0,   0,   0,   0,   0,  
     0,   0,   0,   0,   0,   0,   0,   0,   0, 
]

# Sĩ
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

# Tượng
_PST_B = [
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


# Tướng
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
    'R': _PST_R, 'N': _PST_N, 'C': _PST_C,
    'P': _PST_P, 'A': _PST_A, 'B': _PST_B, 'K': _PST_K,
}

WEIGHT_VECTOR = {
    "material":   1.0,
    "position":   1.2,  
    "king_safety": 0.5,  
    "mobility":   0.1,
    "rook_open":  0.6,
}

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

def _evaluate_mobility(board: Board) -> int:
    gen = MoveGenerator(board)
    orig = board.side_to_move
    board.side_to_move = Color.RED
    red_moves = len(gen.get_pseudo_legal_moves())
    board.side_to_move = Color.BLACK
    black_moves = len(gen.get_pseudo_legal_moves())
    board.side_to_move = orig
    return red_moves - black_moves

def _evaluate_rook_open(board: Board) -> int:
    score = 0
    for sq, piece in enumerate(board.state):
        if piece not in ('R', 'r'):
            continue
        row, col = divmod(sq, 9)
        red = piece == 'R'

        # Cột mở
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


# King Safety
_TROPISM_WEIGHT = {'R': 4, 'r': 4, 'C': 3, 'c': 3, 'N': 3, 'n': 3, 'P': 1, 'p': 1}

def _chebyshev(sq1: int, sq2: int) -> int:
    r1, c1 = divmod(sq1, 9)
    r2, c2 = divmod(sq2, 9)
    return max(abs(r1 - r2), abs(c1 - c2))


def _find_king(board: Board, color: Color) -> int:
    target = 'K' if color == Color.RED else 'k'
    return board.state.index(target)


def _count_defenders(board: Board, color: Color) -> int:
    if color == Color.RED:
        return sum(1 for p in board.state if p in ('A', 'B'))
    return sum(1 for p in board.state if p in ('a', 'b'))


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

    tropism = int(tropism * (0.4 + 0.6 * phase))
    return shield_penalty + tropism

def _evaluate_king_safety(board: Board, phase: float) -> int:
    red_king_sq   = _find_king(board, Color.RED)
    black_king_sq = _find_king(board, Color.BLACK)
    red_danger    = _king_danger(board, Color.RED,   red_king_sq,   phase)
    black_danger  = _king_danger(board, Color.BLACK, black_king_sq, phase)
    return black_danger - red_danger

def _evaluate_absolute_score(board: Board, *, skip_mobility: bool = False) -> int:
    phase = _game_phase(board)
    mat      = _evaluate_material(board)
    pst      = _evaluate_pst(board)
    ksafety  = _evaluate_king_safety(board, phase)
    mob      = 0 if skip_mobility else _evaluate_mobility(board)
    rook_op  = _evaluate_rook_open(board)
    return int(
        mat     * WEIGHT_VECTOR["material"]    +
        pst     * WEIGHT_VECTOR["position"]    +
        ksafety * WEIGHT_VECTOR["king_safety"] +
        mob     * WEIGHT_VECTOR["mobility"]    +
        rook_op * WEIGHT_VECTOR["rook_open"]
    )

def heuristic(board: Board, *, skip_mobility: bool = False) -> int:
    s = _evaluate_absolute_score(board, skip_mobility=skip_mobility)
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