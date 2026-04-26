# move.py

# ==============================================================================
# CẤU TRÚC BIT CỦA 1 NƯỚC ĐI (16-bit Integer):
# [ 0-6 bit ]: to_square   (Ô đến, giá trị 0-89)
# [ 7-13 bit]: from_square (Ô đi, giá trị 0-89)
# ==============================================================================

def encode_move(from_sq: int, to_sq: int) -> int:
    """Mã hóa ô đi và ô đến thành 1 số nguyên 16-bit."""
    return (from_sq << 7) | to_sq

def get_from_sq(move: int) -> int:
    """Giải mã lấy ô đi (dịch phải 7 bit và lấy 7 bit cuối)."""
    return (move >> 7) & 0x7F

def get_to_sq(move: int) -> int:
    """Giải mã lấy ô đến (lấy 7 bit cuối)."""
    return move & 0x7F

# Các hàm tiện ích (debug/giao tiếp với người chơi)
# uci: universal chess interface
def sq_to_uci(sq: int) -> str:
    """Chuyển index (0-89) sang tọa độ chuẩn (ví dụ: 0 -> a0, 89 -> i9)."""
    file_idx = sq % 9   # Cột từ 0-8 (a-i)
    rank_idx = sq // 9  # Hàng từ 0-9 (0-9)
    return chr(ord('a') + file_idx) + str(rank_idx)

def uci_to_sq(uci: str) -> int:
    """Chuyển tọa độ chuẩn (ví dụ: a0) sang index (0-89)."""
    file_idx = ord(uci[0]) - ord('a')
    rank_idx = int(uci[1])
    return rank_idx * 9 + file_idx

def move_to_uci(move: int) -> str:
    """Chuyển integer move thành chuỗi dễ đọc (VD: 1420 -> 'h2e2')."""
    return sq_to_uci(get_from_sq(move)) + sq_to_uci(get_to_sq(move))

def uci_to_move(uci: str) -> int:
    """Chuyển chuỗi (VD: 'h2e2') thành integer move."""
    from_sq = uci_to_sq(uci[0:2])
    to_sq = uci_to_sq(uci[2:4])
    return encode_move(from_sq, to_sq)