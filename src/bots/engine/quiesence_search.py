from typing import Optional
from core.board import Board
from core.move_generator import MoveGenerator
from core.rules import get_legal_moves
from bots.engine.linear_evaluator import heuristic
from bots.engine.move_ordering import MoveSorter
from core.move import get_to_sq

def is_capture(board: Board, move: int) -> bool:
    target_sq = get_to_sq(move)
    return board.state[target_sq] != '.'

def quiescene_search(board: Board, alpha: float, beta: float, move_sorter: Optional[MoveSorter] = None) -> float:
    stand_pat = float(heuristic(board)) # suppose that we don't do anything

    if stand_pat >= beta:
        return beta 
    if alpha < stand_pat:
        alpha = stand_pat

    if move_sorter is None:
        move_sorter = MoveSorter()

    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)

    capture_moves = [move for move in legal_moves if is_capture(board, move)]

    capture_moves = move_sorter.move_sort(capture_moves, board, 0)

    for move in capture_moves: # this is the stopping condition
        board.make_move(move)
        score = -quiescene_search(board, -beta, -alpha, move_sorter)
        board.undo_move()

        if score >= beta:
            return beta 
        if score > alpha:
            alpha = score 

    return alpha



