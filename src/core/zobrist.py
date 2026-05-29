# zobrist.py
import random
from core.pieces import Color
from core.move import get_from_sq, get_to_sq


type BoardState = list[str]  # Mảng 1D đại diện cho 90 ô, mỗi ô chứa '.' hoặc ký tự quân cờ

# Cố định seed để các lần chạy đều sinh ra cùng một bảng băm (dễ debug)
random.seed(42)

# Bảng băm cho 14 loại quân cờ trên 90 ô
ZOBRIST_TABLE: dict[str, list[int]] = {}
PIECES = ['K', 'A', 'B', 'N', 'R', 'C', 'P', 'k', 'a', 'b', 'n', 'r', 'c', 'p']

# Khởi tạo một tập giá trị random key trong 90 ô của một tập quân cờ
for p in PIECES:
    ZOBRIST_TABLE[p] = [random.getrandbits(64) for _ in range(90)]

# Khóa băm cho Lượt đi (Chỉ XOR khi đến lượt Đen)
ZOBRIST_SIDE = random.getrandbits(64)

def compute_initial_hash(board: BoardState, side_to_move: Color):
    """Tính toán mã băm Zobrist từ đầu cho một mảng bàn cờ (Chỉ dùng khi init)."""
    h = 0
    for sq, piece in enumerate(board):
        if piece != '.':
            h ^= ZOBRIST_TABLE[piece][sq]
    
    if side_to_move == Color.BLACK:
        h ^= ZOBRIST_SIDE
    return h


def make_move_hash(current_hash: int, current_board: BoardState, move: int) -> int:
    """Hashing giá trị sẵn có cho nước đi mới"""
    src = get_from_sq(move)
    dest = get_to_sq(move)
    current_hash ^= ZOBRIST_TABLE[current_board[src]][src] # Bỏ quân ở ô ban đầu
    if current_board[dest] != '.':
        current_hash ^= ZOBRIST_TABLE[current_board[dest]][dest] # Bỏ quân bị ăn
    current_hash ^= ZOBRIST_TABLE[current_board[src]][dest] # Thêm quân ở ô mới
    current_hash ^= ZOBRIST_SIDE
    return current_hash
