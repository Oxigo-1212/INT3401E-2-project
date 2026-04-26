# zobrist.py
import random
from core.pieces import Color

# Cố định seed để các lần chạy đều sinh ra cùng một bảng băm (dễ debug)
random.seed(42)

# Bảng băm cho 14 loại quân cờ trên 90 ô
ZOBRIST_TABLE = {}
PIECES = ['K', 'A', 'E', 'H', 'R', 'C', 'P', 'k', 'a', 'e', 'h', 'r', 'c', 'p']

for p in PIECES:
    ZOBRIST_TABLE[p] = [random.getrandbits(64) for _ in range(90)]

# Khóa băm cho Lượt đi (Chỉ XOR khi đến lượt Đen)
ZOBRIST_SIDE = random.getrandbits(64)

def compute_initial_hash(board_state, side_to_move):
    """Tính toán mã băm Zobrist từ đầu cho một mảng bàn cờ (Chỉ dùng khi init)."""
    h = 0
    for sq, piece in enumerate(board_state):
        if piece != '.':
            h ^= ZOBRIST_TABLE[piece][sq]
    
    if side_to_move == Color.BLACK:
        h ^= ZOBRIST_SIDE
    return h