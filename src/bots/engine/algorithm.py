import math
from typing import Callable, Optional
from core.board import Board
from core.move_generator import MoveGenerator
from core.rules import check_game_status, get_legal_moves, is_in_check, GameStatus
from core.pieces import Color
from bots.engine.linear_evaluator import heuristic
from bots.engine.move_ordering import MoveSorter
from core.utils import move_to_str
from bots.engine.transposition_table import TT_TABLE, store, probe, TT_FLAG
from bots.engine.quiescence_search import quiescence_search
from core.move import get_to_sq
from core.zobrist import ZOBRIST_SIDE
from core.logger import get_logger
from bots.engine.iterative_deepening import SearchStopped

type AlgorithmFunction = Callable[[Board, int, float, float, Optional[MoveSorter]], float]

_log = get_logger("algorithm")

_NULL_MOVE_R         = 2    
_NULL_MOVE_MIN_DEPTH = 3    


def _is_null_move_ok(board: Board) -> bool:
    if is_in_check(board, board.side_to_move):
        return False
    attackers = sum(1 for p in board.state if p in ('R', 'N', 'C', 'r', 'n', 'c'))
    return attackers >= 2


def _do_null_move(board: Board) -> None:
    board.history.append({
        'move': 0,
        'captured': '.',
        'half_move_clock': board.half_move_clock,
        'zobrist_key': board.zobrist_key,
    })
    board.zobrist_history.append(board.zobrist_key)
    board.side_to_move = Color.BLACK if board.side_to_move == Color.RED else Color.RED
    board.zobrist_key ^= ZOBRIST_SIDE
    board.half_move_clock += 1


def _undo_null_move(board: Board) -> None:
    if not board.history:
        return
    old = board.history.pop()
    board.side_to_move = Color.BLACK if board.side_to_move == Color.RED else Color.RED
    board.half_move_clock = old['half_move_clock']
    board.zobrist_key = old['zobrist_key']
    if board.zobrist_history:
        board.zobrist_history.pop()

def negmax(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    move_sorter: Optional[MoveSorter] = None,
    is_null_move: bool = False,
    *,
    stats: Optional[dict[str, int]] = None,
    stop_flag: Optional[Callable[[], bool]] = None,
    ply: int = 0,
) -> float:

    if stop_flag is not None and stop_flag():
        raise SearchStopped()
    if stats is not None:
        stats["nodes"] = stats.get("nodes", 0) + 1
        stats["search_nodes"] = stats.get("search_nodes", 0) + 1
        stats["seldepth"] = max(stats.get("seldepth", 0), ply)

    entry, useful = probe(board.zobrist_key, depth, alpha, beta, TT_TABLE)
    if entry is not None and useful:
        if entry.flag == TT_FLAG.EXACT:
            return entry.score
        if entry.flag == TT_FLAG.LOWERBOUND:
            alpha = max(alpha, entry.score)
        elif entry.flag == TT_FLAG.UPPERBOUND:
            beta = min(beta, entry.score)
        if alpha >= beta:
            return entry.score

    if move_sorter is None:
        move_sorter = MoveSorter()

    generator = MoveGenerator(board)
    legal_moves: list[int] = get_legal_moves(board, generator)
    tt_move = entry.best_move if entry is not None else 0
    legal_moves = move_sorter.move_sort(legal_moves, board, depth, tt_move)
    status = check_game_status(board, legal_moves)

    if status != GameStatus.Playing:
        if status == GameStatus.RedWin or status == GameStatus.BlueWin:
            return -90000.0 - depth
        return 0.0

    if depth == 0:
        return quiescence_search(
            board,
            alpha,
            beta,
            move_sorter,
            qdepth=0,
            stats=stats,
            stop_flag=stop_flag,
            ply=ply,
        )

    in_check = is_in_check(board, board.side_to_move)

    if (
        depth >= _NULL_MOVE_MIN_DEPTH
        and not is_null_move
        and not in_check
        and _is_null_move_ok(board)
    ):
        _do_null_move(board)
        try:
            null_score = -negmax(
                board,
                depth - 1 - _NULL_MOVE_R,
                -beta,
                -beta + 1,
                move_sorter,
                is_null_move=True,
                stats=stats,
                stop_flag=stop_flag,
                ply=ply,
            )
        finally:
            _undo_null_move(board)

        if null_score >= beta:
            store(board.zobrist_key, depth, beta, TT_FLAG.LOWERBOUND, 0, TT_TABLE)
            return beta

    original_alpha = alpha
    best_move: int = 0
    max_score: float = -math.inf

    for move in legal_moves:
        board.make_move(move)
        try:
            score = -negmax(
                board,
                depth - 1,
                -beta,
                -alpha,
                move_sorter,
                stats=stats,
                stop_flag=stop_flag,
                ply=ply + 1,
            )
        finally:
            board.undo_move()

        if score > max_score:
            max_score = score
            best_move = move
        if score > alpha:
            alpha = score

        if alpha >= beta:
            move_sorter.store_killer_move(depth, move, beta, score)
            move_sorter.store_history(move, depth)
            break

    flag = TT_FLAG.EXACT
    if max_score <= original_alpha:
        flag = TT_FLAG.UPPERBOUND
    elif max_score >= beta:
        flag = TT_FLAG.LOWERBOUND
    store(board.zobrist_key, depth, max_score, flag, best_move, TT_TABLE)
    return max_score

def get_best_move(board: Board, algorithm: AlgorithmFunction, depth: int = 3) -> int | None:
    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)
    if not legal_moves:
        return None

    move_sorter = MoveSorter()
    entry, _ = probe(board.zobrist_key, depth, -math.inf, math.inf, TT_TABLE)
    tt_move = entry.best_move if entry is not None else 0
    legal_moves = move_sorter.move_sort(legal_moves, board, depth, tt_move)

    best_move = None
    best_val = -math.inf
    for move in legal_moves:
        board.make_move(move)
        value = -algorithm(board, depth - 1, -math.inf, math.inf, move_sorter)
        board.undo_move()
        _log.debug("Nước %s có điểm: %s", move_to_str(move), value)
        if value > best_val:
            best_val = value
            best_move = move
    return best_move