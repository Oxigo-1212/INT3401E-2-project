import math

from typing import Callable
from core.board import Board
from core.move_generator import MoveGenerator
from core.pieces import Color
from core.rules import check_game_status, get_legal_moves, GameStatus
from engine.linear_evaluator import heuristic
from engine.move_ordering import MoveSorter

type AlgorithmFunction = Callable[[Board, int, float, float, bool], float]

def negmax(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    _is_maximizing_player: bool = True,
) -> float:
    generator: MoveGenerator = MoveGenerator(board)
    move_sorter: MoveSorter = MoveSorter()
    # Lấy danh sách nước đi hợp lệ dựa trên luật chơi
    legal_moves: list[int] = get_legal_moves(board, generator)
    legal_moves = move_sorter.move_sort(legal_moves, board, depth)
    status: GameStatus = check_game_status(board, legal_moves)
    if status != GameStatus.Playing:
        if status == GameStatus.RedWin:
            return 99999.0  # Đỏ thắng
        if status == GameStatus.BlueWin:
            return -99999.0  # Đen thắng
        if status == GameStatus.Draw:
            return 0.0  # Hòa

    if depth == 0:
        return float(heuristic(board))  # Đánh giá thế cờ hiện tại
    max_score: float = -math.inf
    for move in legal_moves:
        board.make_move(move)
        score = -negmax(board, depth - 1, -beta, -alpha)
        board.undo_move()
        max_score = max(max_score, score)
        alpha = max(alpha, score)
        if alpha >=beta:
            move_sorter.store_killer_move(depth, move, beta, score)
            move_sorter.store_history(move, depth)
            break
    return max_score

def minimax(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    is_maximizing_player: bool,
) -> float:
    """
    Thuật toán Minimax kết hợp cắt tỉa Alpha-Beta.
    """
    generator: MoveGenerator = MoveGenerator(board)
    move_sorter: MoveSorter = MoveSorter()
    # Lấy danh sách nước đi hợp lệ dựa trên luật chơi
    legal_moves: list[int] = get_legal_moves(board, generator)
    legal_moves = move_sorter.move_sort(legal_moves, board, depth)
    status: GameStatus = check_game_status(board, legal_moves)
    eval_score: float = 0

    # Điều kiện dừng: đạt độ sâu tối đa hoặc trận đấu kết thúc
    if status != GameStatus.Playing:
        if status == GameStatus.RedWin:
            return 99999.0  # Đỏ thắng
        if status == GameStatus.BlueWin:
            return -99999.0  # Đen thắng
        if status == GameStatus.Draw:
            return 0.0  # Hòa

    if depth == 0:
        return float(heuristic(board))  # Đánh giá thế cờ hiện tại

    if is_maximizing_player:
        max_eval: float = -math.inf
        for move in legal_moves:
            board.make_move(move)
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board.undo_move()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if alpha >= beta:
                move_sorter.store_killer_move(depth, move, beta, eval_score)
                move_sorter.store_history(move, depth)
                break  # Cắt tỉa
        return max_eval

    min_eval: float = math.inf
    for move in legal_moves:
        board.make_move(move)
        eval_score = minimax(board, depth - 1, alpha, beta, True)
        board.undo_move()
        min_eval = min(min_eval, eval_score)
        beta = min(beta, eval_score)
        if alpha >= beta:
            move_sorter.store_killer_move(depth, move, beta, eval_score)
            move_sorter.store_history(move, depth)
            break  # Cắt tỉa
    return min_eval


def get_best_move(board: Board, algorithm: AlgorithmFunction, depth: int = 3 ) -> int | None:
    """
    Tìm nước đi tốt nhất cho phe hiện tại.
    """
    generator: MoveGenerator = MoveGenerator(board)
    legal_moves: list[int] = get_legal_moves(board, generator)

    if not legal_moves:
        return None

    best_move: int | None = None
    is_red_turn: bool = board.side_to_move == Color.RED
    best_val: float = 0
    value: float = 0

    if is_red_turn:
        best_val = -math.inf
        for move in legal_moves:
            board.make_move(move)
            value = algorithm(board, depth - 1, -math.inf, math.inf, True)
            board.undo_move()
            if value > best_val:
                best_val = value
                best_move = move
    else:
        best_val = math.inf
        for move in legal_moves:
            board.make_move(move)
            value = algorithm(board, depth - 1, -math.inf, math.inf, False)
            board.undo_move()
            if value < best_val:
                best_val = value
                best_move = move

    return best_move
