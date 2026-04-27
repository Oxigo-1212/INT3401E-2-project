# evaluator.py
from core.board import Board
from core.pieces import PIECE_VALUES, is_red
from core.move_generator import MoveGenerator
from core.pieces import Color

# Positional weights (simplified 90-cell tables for red)
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
    "position": 0.5,
    "mobility": 0.1
}

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

def _evaluate_position(board: Board) -> int:
    score = 0
    for sq, piece in enumerate(board.state):
        if piece == 'P':
            score += _RED_P_TABLE[sq]
        elif piece == 'p':
            score -= _RED_P_TABLE[89 - sq]
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

def heuristic(board: Board) -> int:
    m = _evaluate_material(board) * WEIGHT_VECTOR["material"]
    p = _evaluate_position(board) * WEIGHT_VECTOR["position"]
    mob = _evaluate_mobility(board) * WEIGHT_VECTOR["mobility"]
    
    return int(m + p + mob)
