# board.py
from core.pieces import Color, CHINESE_PIECES
from core.move import get_from_sq, get_to_sq

# Chuỗi FEN mặc định khi bắt đầu game
# FEN: mô tả toàn bộ trạng thái ván cờ bằng 1 string
START_FEN = "rheakaehr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RHEAKAEHR w - - 0 1"
# ANSI Color Codes
RED_COLOR = "\033[91m"     # Đỏ sáng
BLACK_COLOR = "\033[94m"   # Xanh dương sáng (dễ nhìn hơn màu đen trên nền tối)
RESET_COLOR = "\033[0m"    # Reset về màu mặc định
BOARD_COLOR = "\033[90m"   # Màu xám cho tọa độ và ô trống

class Board:
    def __init__(self):
        # Mảng 1D đại diện cho 90 ô (Hàng 0 là sân Đen, Hàng 9 là sân Đỏ)
        self.state = ['.'] * 90 
        
        # Ngăn xếp (Stack) lưu lịch sử nước đi để Undo: List[Tuple(move_int, captured_piece)]
        self.history = []
        
        self.side_to_move = Color.RED
        self.set_fen(START_FEN)

    def set_fen(self, fen: str):
        """Khởi tạo bàn cờ từ chuỗi FEN."""
        self.state = ['.'] * 90
        self.history.clear()
        
        parts = fen.split()
        board_part = parts[0]
        
        # Parse phần bàn cờ
        row, col = 0, 0
        for char in board_part:
            if char == '/':
                row += 1
                col = 0
            elif char.isdigit():
                col += int(char)
            else:
                sq = row * 9 + col
                self.state[sq] = char
                col += 1
                
        # Parse lượt đi
        if len(parts) > 1:
            self.side_to_move = Color.RED if parts[1] == 'w' else Color.BLACK

    def make_move(self, move: int):
        """Thực thi một nước đi và đổi lượt O(1)."""
        frm = get_from_sq(move)
        to = get_to_sq(move)
        
        # Lưu lại quân cờ tại ô đích (nếu có ăn quân)
        captured = self.state[to]
        
        # Cập nhật mảng
        self.state[to] = self.state[frm]
        self.state[frm] = '.'
        
        # Đẩy vào lịch sử
        self.history.append((move, captured))
        
        # Đổi lượt
        self.side_to_move = Color.BLACK if self.side_to_move == Color.RED else Color.RED

    def undo_move(self):
        """Hoàn tác nước đi cuối O(1)."""
        if not self.history:
            return
            
        move, captured = self.history.pop()
        frm = get_from_sq(move)
        to = get_to_sq(move)
        
        # Trả quân về vị trí cũ
        self.state[frm] = self.state[to]
        
        # Khôi phục quân bị ăn (hoặc trả lại ô trống '.')
        self.state[to] = captured
        
        # Đổi lại lượt
        self.side_to_move = Color.BLACK if self.side_to_move == Color.RED else Color.RED

    def print_board(self):
        """Hàm Debug: Vẽ bàn cờ ra màn hình Terminal."""
        print(f"\nLượt đi: {'ĐỎ' if self.side_to_move == Color.RED else 'ĐEN'}")
        print("  " + "  ".join(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']))
        for row in range(10):
            row_str = [str(row)]
            for col in range(9):
                piece = self.state[row * 9 + col]
                row_str.append(CHINESE_PIECES[piece])
            print(" ".join(row_str) + f" {row}")
        print("  " + "  ".join(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i']) + "\n")

    def print_board(self):
        """Hàm Debug: Vẽ bàn cờ có màu sắc ra Terminal."""
        # Khai báo lại hoặc import các mã màu
        RED = "\033[91m"
        BLUE = "\033[94m" 
        RESET = "\033[0m"
        GRAY = "\033[90m"

        print(f"\nLượt đi: {RED + 'ĐỎ' if self.side_to_move == Color.RED else BLUE + 'ĐEN'}{RESET}")
        
        # In hàng tọa độ cột (a b c...)
        header = "   " + "  ".join(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'])
        print(GRAY + header + RESET)

        for row in range(10):
            # In tọa độ hàng (0...9)
            row_str = [GRAY + str(row) + RESET] 
            
            for col in range(9):
                piece = self.state[row * 9 + col]
                char = CHINESE_PIECES[piece]
                
                # Kiểm tra và tô màu
                if piece == '.':
                    row_str.append(GRAY + char + RESET)
                elif piece.isupper(): # Quân Đỏ
                    row_str.append(RED + char + RESET)
                else: # Quân Đen
                    row_str.append(BLUE + char + RESET)
            
            print(" ".join(row_str) + GRAY + f" {row}" + RESET)
        
        print(GRAY + header + RESET + "\n")
