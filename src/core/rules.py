# rules.py
from core.pieces import Color

def flying_general_check(board):
    """Trả về True nếu hai Tướng đang 'nhìn mặt' nhau (Lỗi luật)."""
    k_pos = -1
    K_pos = -1
    for sq, p in enumerate(board.state):
        if p == 'k': k_pos = sq
        if p == 'K': K_pos = sq
    
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

def check_game_status(board, legal_moves):
    """
    Trả về: 
    - 0: Đang chơi
    - 1: Đỏ thắng
    - 2: Đen thắng
    """
    if len(legal_moves) == 0:
        # Nếu bên đến lượt (side_to_move) không còn nước đi
        # thì bên đó thua, bên kia thắng.
        return 2 if board.side_to_move == Color.RED else 1
    
    return 0