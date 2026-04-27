# board.py
from core.pieces import Color
from core.move import get_from_sq, get_to_sq
from core.zobrist import ZOBRIST_TABLE, ZOBRIST_SIDE, compute_initial_hash

# Chuỗi FEN mặc định khi bắt đầu game
# FEN: mô tả toàn bộ trạng thái ván cờ bằng 1 string
START_FEN = "rheakaehr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RHEAKAEHR w - - 0 1"

class Board:
    def __init__(self):
        # Mảng 1D đại diện cho 90 ô (Hàng 0 là sân Đen, Hàng 9 là sân Đỏ)
        self.state = ['.'] * 90 
        
        # Ngăn xếp (Stack) lưu lịch sử nước đi để Undo: List[Tuple(move_int, captured_piece)]
        self.history = []
        
        self.side_to_move = Color.RED
        self.zobrist_key = 0
        self.half_move_clock = 0 # đếm số nước đi không bắt quân
        self.zobrist_history = [] # Lưu danh sách các mã băm để check lặp cờ
        
        self.set_fen(START_FEN)

    def set_fen(self, fen: str):
        """Khởi tạo bàn cờ từ chuỗi FEN."""
        self.state = ['.'] * 90
        self.history.clear()
        self.zobrist_history.clear()
        self.half_move_clock = 0

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

        self.zobrist_key = compute_initial_hash(self.state, self.side_to_move)

    def make_move(self, move: int):
        """Thực thi một nước đi và đổi lượt O(1)."""
        frm = get_from_sq(move)
        to = get_to_sq(move)
        
        # Lưu lại quân cờ tại ô đích (nếu có ăn quân)
        moving_piece = self.state[frm]
        captured = self.state[to]
        
        # 1. Lưu lại trạng thái CŨ vào lịch sử để Undo
        self.history.append({
            'move': move,
            'captured': captured,
            'half_move_clock': self.half_move_clock,
            'zobrist_key': self.zobrist_key
        })
        self.zobrist_history.append(self.zobrist_key)

        # 2. Cập nhật Zobrist Key 
        # Bỏ quân cờ ở ô cũ
        self.zobrist_key ^= ZOBRIST_TABLE[moving_piece][frm]
        # Bỏ quân bị ăn (nếu có)
        if captured != '.':
            self.zobrist_key ^= ZOBRIST_TABLE[captured][to]
        # Thêm quân cờ vào ô mới
        self.zobrist_key ^= ZOBRIST_TABLE[moving_piece][to]
        # Đổi lượt
        self.zobrist_key ^= ZOBRIST_SIDE

        # Cập nhật mảng
        self.state[to] = self.state[frm]
        self.state[frm] = '.'
        # Đổi lượt
        self.side_to_move = Color.BLACK if self.side_to_move == Color.RED else Color.RED
        
        # 4. Cập nhật đếm nước đi (Reset nếu có ăn quân)
        if captured != '.':
            self.half_move_clock = 0
            # Khi có ăn quân, các thế cờ trước đó không thể lặp lại nữa, ta có thể xóa bớt lịch sử
            # self.zobrist_history.clear()
        else:
            self.half_move_clock += 1
        
        
    def undo_move(self):
        """Hoàn tác nước đi cuối O(1)."""
        if not self.history:
            return
            
        # 1. Lấy lại trạng thái cũ
        old_state = self.history.pop()
        frm = get_from_sq(old_state['move'])
        to = get_to_sq(old_state['move'])
        captured = old_state['captured']
        
        # 2. Phục hồi bàn cờ
        self.state[frm] = self.state[to]
        self.state[to] = captured
        self.side_to_move = Color.BLACK if self.side_to_move == Color.RED else Color.RED
        
        # 3. Phục hồi đồng hồ và Zobrist
        self.half_move_clock = old_state['half_move_clock']
        self.zobrist_key = old_state['zobrist_key']
        
        # Xóa khỏi danh sách lặp cờ
        if self.zobrist_history:
            self.zobrist_history.pop()

