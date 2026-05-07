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
    



