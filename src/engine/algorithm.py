import math
from core.pieces import Color
from core.move_generator import MoveGenerator
from core.rules import get_legal_moves, check_game_status
from engine.evaluator import heuristic

def minimax(board, depth, alpha, beta, is_maximizing_player):
    """
    Thuật toán Minimax kết hợp cắt tỉa Alpha-Beta.
    """
    generator = MoveGenerator(board)
    # Lấy danh sách nước đi hợp lệ dựa trên luật chơi
    legal_moves = get_legal_moves(board, generator)
    status = check_game_status(board, legal_moves)

    # Điều kiện dừng: đạt độ sâu tối đa hoặc trận đấu kết thúc
    if depth == 0 or status != 0:
        if status == 1: return 99999  # Đỏ thắng
        if status == 2: return -99999 # Đen thắng
        if status == 3: return 0      # Hòa
        return heuristic(board) # Đánh giá thế cờ hiện tại

    if is_maximizing_player:
        max_eval = -math.inf
        for move in legal_moves:
            board.make_move(move)
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board.undo_move()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break # Cắt tỉa
        return max_eval
    else:
        min_eval = math.inf
        for move in legal_moves:
            board.make_move(move)
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board.undo_move()
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break # Cắt tỉa
        return min_eval

def get_best_move(board, depth=3):
    """
    Tìm nước đi tốt nhất cho phe hiện tại.
    """
    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)
    
    if not legal_moves:
        return None

    best_move = None
    is_red_turn = (board.side_to_move == Color.RED)
    
    if is_red_turn:
        best_val = -math.inf
        for move in legal_moves:
            board.make_move(move)
            value = minimax(board, depth - 1, -math.inf, math.inf, False)
            board.undo_move()
            if value > best_val:
                best_val = value
                best_move = move
    else:
        best_val = math.inf
        for move in legal_moves:
            board.make_move(move)
            value = minimax(board, depth - 1, -math.inf, math.inf, True)
            board.undo_move()
            if value < best_val:
                best_val = value
                best_move = move
                
    return best_move