import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.board import Board
from core.move import uci_to_move, uci_to_sq
from engine.move_ordering import MoveSorter


def sq(uci: str) -> int:
    return uci_to_sq(uci)


def make_empty_board() -> Board:
    board = Board()
    board.state = ["."] * 90
    return board


def test_store_killer_move_keeps_two_most_recent_unique_moves() -> None:
    sorter = MoveSorter()
    first = uci_to_move("c9c8")
    second = uci_to_move("e9e8")
    third = uci_to_move("g9g8")

    sorter.store_killer_move(depth=3, move=first, beta=0, score=-1)
    assert sorter.get_killers(3) == [0, 0]

    sorter.store_killer_move(depth=3, move=first, beta=0, score=0)
    sorter.store_killer_move(depth=3, move=second, beta=0, score=0)
    sorter.store_killer_move(depth=3, move=second, beta=0, score=0)
    sorter.store_killer_move(depth=3, move=third, beta=0, score=0)

    assert sorter.get_killers(3) == [third, second]


def test_store_history_accumulates_quadratically() -> None:
    sorter = MoveSorter()
    move_a = uci_to_move("f9f8")
    move_b = uci_to_move("g9g8")

    sorter.store_history(move_a, depth=3)
    sorter.store_history(move_a, depth=1)
    sorter.store_history(move_b, depth=2)

    assert sorter._history[sq("f9")][sq("f8")] == 10
    assert sorter._history[sq("g9")][sq("g8")] == 4


def test_move_sort_prioritizes_captures_killers_then_history() -> None:
    sorter = MoveSorter()
    board = make_empty_board()

    capture_low = uci_to_move("a9a8")
    capture_high = uci_to_move("b9b8")
    killer_older = uci_to_move("c9c8")
    killer_recent = uci_to_move("e9e8")
    history_high = uci_to_move("f9f8")
    history_low = uci_to_move("g9g8")

    board.state[sq("a9")] = "R"
    board.state[sq("b9")] = "R"
    board.state[sq("a8")] = "p"
    board.state[sq("b8")] = "r"
    board.state[sq("c9")] = "R"
    board.state[sq("e9")] = "R"
    board.state[sq("f9")] = "R"
    board.state[sq("g9")] = "R"

    sorter.store_killer_move(depth=2, move=killer_older, beta=0, score=0)
    sorter.store_killer_move(depth=2, move=killer_recent, beta=0, score=0)
    sorter.store_history(history_high, depth=3)
    sorter.store_history(history_low, depth=1)

    moves = [history_low, killer_older, capture_low, history_high, killer_recent, capture_high]

    sorted_moves = sorter.move_sort(moves, board, depth=2)

    assert sorted_moves is moves
    assert sorted_moves == [capture_high, capture_low, killer_recent, killer_older, history_high, history_low]
