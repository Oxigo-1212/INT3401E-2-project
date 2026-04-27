# test_evaluator.py
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from core.board import Board
from engine.evaluator import (
    heuristic, 
    _evaluate_material, 
    _evaluate_position, 
    _evaluate_mobility
)

def test_initial_board_neutral():
    """Initial board should be roughly balanced (0)."""
    board = Board()
    # At start, material is equal, position is mirrored, mobility is equal
    score = heuristic(board)
    assert score == 0

def test_material_advantage():
    """Removing a piece should change material score."""
    board = Board()
    # Remove black rook (r) at sq 0
    board.state[0] = '.'
    
    m_score = _evaluate_material(board)
    assert m_score > 0 # Red advantage
    
    h_score = heuristic(board)
    assert h_score > 0

def test_pawn_position_bonus():
    """Pawn crossing river should gain positional bonus."""
    board = Board()
    # Red pawn (P) at sq 63 (row 7, col 0) - starting pos
    # Move it to sq 36 (row 4, col 0) - crossed river
    board.state[63] = '.'
    board.state[36] = 'P'
    
    p_score = _evaluate_position(board)
    assert p_score > 0

def test_mobility():
    """Empty board (except kings) should have specific mobility."""
    board = Board()
    # Clear most pieces to make mobility obvious
    for i in range(90):
        if board.state[i] not in {'K', 'k'}:
            board.state[i] = '.'
            
    mob = _evaluate_mobility(board)
    # Both kings in palaces should have same mobility (4 moves if center, less if corner)
    # But symmetric, so diff should be 0
    assert mob == 0
