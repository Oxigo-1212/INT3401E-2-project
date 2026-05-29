# rules.py
from core.pieces import Color
from enum import Enum


class GameStatus(Enum):
    Playing = 0
    RedWin = 1
    BlueWin = 2
    Draw = 3

def flying_general_check(board):
    """Trả về True nếu hai Tướng đang 'nhìn mặt' nhau (Lỗi luật)."""
    k_pos = -1
    K_pos = -1
    for sq, p in enumerate(board.state):
        if p == 'k':
            k_pos = sq
        if p == 'K':
            K_pos = sq
    
    if k_pos == -1 or K_pos == -1:
        return False
    rk, ck = divmod(k_pos, 9)
    rK, cK = divmod(K_pos, 9)
    
    if ck == cK: # Cùng cột
        # Kiểm tra xem có quân nào ở giữa không
        start = min(rk, rK) + 1
        end = max(rk, rK)
        for r in range(start, end):
            if board.state[r * 9 + ck] != '.':
                return False # Có quân cản, ổn!
        return True # Không có quân cản, phạm luật!
    return False

def is_in_check(board, color):
    """Kiểm tra Tướng phe color có đang bị chiếu hay không."""
    # Tìm vị trí Tướng
    target_king = 'K' if color == Color.RED else 'k'
    king_sq = board.state.index(target_king)
    
    # Đổi lượt giả định để xem phe kia có thể ăn Tướng không
    # Cách đơn giản: Sinh tất cả nước đi pseudo của đối phương
    from core.move_generator import MoveGenerator
    from core.move import get_to_sq
    
    opp_gen = MoveGenerator(board)
    # Lưu lượt đi cũ và đổi lượt để check
    original_side = board.side_to_move
    board.side_to_move = Color.BLACK if color == Color.RED else Color.RED
    
    opp_moves = opp_gen.get_pseudo_legal_moves()
    board.side_to_move = original_side # Trả lại lượt
    
    for m in opp_moves:
        if get_to_sq(m) == king_sq:
            return True
    return False

def get_legal_moves(board, generator):
    """Bộ lọc cuối cùng: Luật chiếu và Lộ mặt tướng."""
    pseudo_moves = generator.get_pseudo_legal_moves()
    legal_moves = []
    
    current_side = board.side_to_move
    for move in pseudo_moves:
        board.make_move(move)

        # Một nước đi chỉ hợp lệ nếu:
        # 1. Không làm Tướng mình bị chiếu
        # 2. Không làm lộ mặt Tướng (Flying General)
        if not is_in_check(board, current_side) and not flying_general_check(board):
            legal_moves.append(move)
        board.undo_move()
    return legal_moves

# rules.py

def check_game_status(board, legal_moves) -> GameStatus:
    """
    Trả về: 
    - 0: Đang chơi
    - 1: Đỏ thắng
    - 2: Đen thắng
    """
    if len(legal_moves) == 0:
        # Nếu bên đến lượt (side_to_move) không còn nước đi
        # thì bên đó thua, bên kia thắng.
        return GameStatus.RedWin if board.side_to_move == Color.BLACK else GameStatus.BlueWin
    if is_draw(board):
        return GameStatus.Draw

    return GameStatus.Playing

def is_draw(board):
    """Kiểm tra hòa cờ."""
    # 1. Luật 60 nước (120 half-moves không có quân nào bị ăn)
    if board.half_move_clock >= 120:
        return True
        
    # 2. Luật lặp cờ 3 lần (3-fold repetition)
    # Nếu mã zobrist hiện tại đã xuất hiện 2 lần trong lịch sử -> đây là lần thứ 3
    repetition_count = 0
    for key in reversed(board.zobrist_history):
        if key == board.zobrist_key:
            repetition_count += 1
            if repetition_count >= 2:
                return True
                
    return False
