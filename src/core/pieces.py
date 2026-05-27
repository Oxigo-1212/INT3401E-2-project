# pieces.py
from enum import Enum

class Color(Enum):
    RED = 0
    BLACK = 1

# Ký hiệu bàn cờ
# Đỏ (Upper case): K (Tướng), A (Sĩ), B (Tượng), N (Mã), R (Xe), C (Pháo), P (Tốt)
# Đen (Lower case): k, a, b, n, r, c, p
# Ô trống: '.'
PIECE_VALUES = {
        'K': 6000, 'A': 120, 'B': 120, 'N': 270, 'R': 600, 'C': 285, 'P': 30,
        'k': 6000, 'a': 120, 'b': 120, 'n': 270, 'r': 600, 'c': 285, 'p': 30,
        '.': 0
        }

# Ánh xạ ký tự để in ra màn hình Console (Debug View)
CHINESE_PIECES = {
    'R': '车', 'N': '马', 'B': '相', 'A': '仕', 'K': '帅', 'C': '炮', 'P': '兵',
    'r': '車', 'n': '馬', 'b': '象', 'a': '士', 'k': '将', 'c': '砲', 'p': '卒',
    '.': '＋' # Dấu thập đại diện cho điểm giao cắt trên bàn cờ
}

def is_red(piece: str) -> bool:
    """Kiểm tra xem quân cờ có phải phe Đỏ không."""
    return piece.isupper() and piece != '.'

def is_black(piece: str) -> bool:
    """Kiểm tra xem quân cờ có phải phe Đen không."""
    return piece.islower() and piece != '.' 
