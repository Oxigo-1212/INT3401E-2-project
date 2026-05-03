from core.move import get_from_sq, get_to_sq
from core.board import Board
from core.pieces import Color

def sq_to_str(sq: int) -> str:
    """Chuyển index (0-89) thành tọa độ bàn cờ (ví dụ: 0 -> a9, 89 -> i0)."""
    row, col = divmod(sq, 9)
    # Cột: a-i, Hàng: 9-0 (đảo ngược để trực quan với cờ tướng)
    col_str = chr(ord('a') + col)
    row_str = str(9 - row)
    return f"{col_str}{row_str}"

def move_to_str(move: int) -> str:
    """Chuyển move int thành chuỗi (ví dụ: 'h2e2')."""
    return f"{sq_to_str(get_from_sq(move))}{sq_to_str(get_to_sq(move))}"

def print_board(board: Board):
    """In bàn cờ ra màn hình console một cách đẹp mắt."""
    print("\n    a b c d e f g h i")
    print("  +-------------------+")
    for r in range(10):
        row_str = f"{9-r} | "
        for c in range(9):
            piece = board.state[r * 9 + c]
            row_str += (piece if piece != '.' else '·') + " "
        print(row_str + f"| {9-r}")
    print("  +-------------------+")
    side = "ĐỎ" if board.side_to_move == Color.RED else "ĐEN"
    print(f"  Lượt đi: {side}\n")

def load_fen(board: Board, fen: str):
    """
    Thiết lập bàn cờ từ chuỗi FEN đơn giản.
    Ví dụ: '3ak4/9/9/... w' (w: Đỏ đi, b: Đen đi)
    """
    parts = fen.split(' ')
    rows = parts[0].split('/')
    board.state = []
    for row in rows:
        for char in row:
            if char.isdigit():
                board.state.extend(['.'] * int(char))
            else:
                board.state.append(char)
    
    if len(parts) > 1:
        board.side_to_move = Color.RED if parts[1] == 'w' else Color.BLACK