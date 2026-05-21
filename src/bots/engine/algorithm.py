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

type AlgorithmFunction = Callable[[Board, int, float, float, bool, Optional[MoveSorter]], float]

_log = get_logger("algorithm")

# ---------------------------------------------------------------------------
# Hằng số tuning
# ---------------------------------------------------------------------------
_NULL_MOVE_R         = 2    # Null Move: giảm depth đi R tầng
_NULL_MOVE_MIN_DEPTH = 3    # Chỉ thử Null Move khi depth >= N

_LMR_MIN_MOVE_INDEX  = 3    # LMR bắt đầu từ nước thứ N trong danh sách (0-indexed)
_LMR_MIN_DEPTH       = 3    # Chỉ áp dụng LMR khi depth >= N
_LMR_REDUCTION       = 1    # Giảm depth đi bao nhiêu tầng

# Futility margin theo depth (index = depth còn lại)
# depth 1 ≈ margin 1 quân Tốt, depth 2 ≈ margin 1 Mã
_FUTILITY_MARGIN = [0, 200, 450]


# ---------------------------------------------------------------------------
# Null Move helpers
# ---------------------------------------------------------------------------

def _is_null_move_ok(board: Board) -> bool:
    """
    Null Move không an toàn khi:
    - Đang bị chiếu
    - Endgame cạn quân (nguy cơ zugzwang): tổng Xe/Mã/Pháo < 2
    """
    if is_in_check(board, board.side_to_move):
        return False
    attackers = sum(1 for p in board.state if p in ('R', 'H', 'C', 'r', 'h', 'c'))
    return attackers >= 2


def _do_null_move(board: Board) -> None:
    """Bỏ qua lượt: chỉ đổi side_to_move và XOR zobrist."""
    # Lưu snapshot vào history để _undo_null_move khôi phục đúng
    board.history.append({
        'move': 0,
        'captured': '.',
        'half_move_clock': board.half_move_clock,
        'zobrist_key': board.zobrist_key,   # key TRƯỚC khi null move
    })
    board.zobrist_history.append(board.zobrist_key)
    board.side_to_move = Color.BLACK if board.side_to_move == Color.RED else Color.RED
    board.zobrist_key ^= ZOBRIST_SIDE
    board.half_move_clock += 1


def _undo_null_move(board: Board) -> None:
    """Hoàn tác null move."""
    if not board.history:
        return
    old = board.history.pop()
    board.side_to_move = Color.BLACK if board.side_to_move == Color.RED else Color.RED
    board.half_move_clock = old['half_move_clock']
    board.zobrist_key = old['zobrist_key']
    if board.zobrist_history:
        board.zobrist_history.pop()


# ---------------------------------------------------------------------------
# negmax với Null Move Pruning + LMR + Futility Pruning
# ---------------------------------------------------------------------------

def negmax(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    _is_maximizing_player: bool = True,
    move_sorter: Optional[MoveSorter] = None,
    is_null_move: bool = False,   # True nếu nước trước là null move → không null-null
) -> float:

    # ------------------------------------------------------------------
    # 1. Transposition Table lookup
    # ------------------------------------------------------------------
    entry, useful = probe(board.zobrist_key, depth, alpha, beta, TT_TABLE)
    if entry is not None and useful:
        if entry.flag == TT_FLAG.EXACT:
            return entry.score
        elif entry.flag == TT_FLAG.LOWERBOUND:
            alpha = max(alpha, entry.score)
        elif entry.flag == TT_FLAG.UPPERBOUND:
            beta = min(beta, entry.score)
        if alpha >= beta:
            return entry.score

    if move_sorter is None:
        move_sorter = MoveSorter()

    # ------------------------------------------------------------------
    # 2. Sinh nước đi + kiểm tra kết thúc
    # ------------------------------------------------------------------
    generator = MoveGenerator(board)
    legal_moves: list[int] = get_legal_moves(board, generator)
    tt_move = entry.best_move if entry is not None else 0
    legal_moves = move_sorter.move_sort(legal_moves, board, depth, tt_move)
    status = check_game_status(board, legal_moves)

    if status != GameStatus.Playing:
        if status == GameStatus.RedWin:
            return 90000.0 + depth
        if status == GameStatus.BlueWin:
            return -90000.0 - depth
        return 0.0  # Draw

    if depth == 0:
        return quiescence_search(board, alpha, beta, move_sorter, qdepth=0)

    in_check = is_in_check(board, board.side_to_move)

    # ------------------------------------------------------------------
    # 3. Null Move Pruning
    # Nếu bỏ qua lượt mà score vẫn >= beta → đây là nhánh "quá tốt",
    # đối thủ sẽ tránh từ trước → cắt sớm.
    # ------------------------------------------------------------------
    if (
        depth >= _NULL_MOVE_MIN_DEPTH
        and not is_null_move
        and not in_check
        and _is_null_move_ok(board)
    ):
        _do_null_move(board)
        null_score = -negmax(
            board,
            depth - 1 - _NULL_MOVE_R,
            -beta, -beta + 1,           # null window
            True, move_sorter,
            is_null_move=True
        )
        _undo_null_move(board)

        if null_score >= beta:
            store(board.zobrist_key, depth, beta, TT_FLAG.LOWERBOUND, 0, TT_TABLE)
            return beta

    # ------------------------------------------------------------------
    # 4. Futility Pruning setup (depth 1–2)
    # Nếu static eval + margin <= alpha → hầu hết nước non-capture vô ích.
    # ------------------------------------------------------------------
    futility_pruning = (
        not in_check
        and depth < len(_FUTILITY_MARGIN)
        and depth >= 1
    )
    futility_threshold = -math.inf
    if futility_pruning:
        static_eval = float(heuristic(board))
        futility_threshold = static_eval + _FUTILITY_MARGIN[depth]

    # ------------------------------------------------------------------
    # 5. Main search loop
    # ------------------------------------------------------------------
    original_alpha = alpha
    best_move: int = 0
    max_score: float = -math.inf

    for move_idx, move in enumerate(legal_moves):
        to_sq = get_to_sq(move)
        is_capture = board.state[to_sq] != '.'

        # --- Futility Pruning: bỏ qua non-capture không thể vượt alpha ---
        if (
            futility_pruning
            and not is_capture
            and move_idx > 0            # luôn search ít nhất nước đầu tiên
            and futility_threshold <= alpha
        ):
            continue

        # --- Late Move Reduction (LMR) ---
        # Nước đi cuối danh sách (sau sort tốt) thường kém hơn → search depth thấp hơn.
        # Nếu kết quả vượt alpha thì re-search full depth.
        reduction = 0
        if (
            depth >= _LMR_MIN_DEPTH
            and move_idx >= _LMR_MIN_MOVE_INDEX
            and not is_capture
            and not in_check
        ):
            reduction = _LMR_REDUCTION

        board.make_move(move)

        if reduction > 0:
            # Search thử với depth thấp hơn, null window
            score = -negmax(
                board, depth - 1 - reduction,
                -alpha - 1, -alpha,
                True, move_sorter
            )
            # Nếu có triển vọng (vượt alpha), re-search full
            if score > alpha:
                score = -negmax(board, depth - 1, -beta, -alpha, True, move_sorter)
        else:
            score = -negmax(board, depth - 1, -beta, -alpha, True, move_sorter)

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

    # ------------------------------------------------------------------
    # 6. Lưu vào TT
    # ------------------------------------------------------------------
    flag = TT_FLAG.EXACT
    if max_score <= original_alpha:
        flag = TT_FLAG.UPPERBOUND
    elif max_score >= beta:
        flag = TT_FLAG.LOWERBOUND
    store(board.zobrist_key, depth, max_score, flag, best_move, TT_TABLE)
    return max_score


# ---------------------------------------------------------------------------
# Minimax (giữ nguyên cho tương thích với MinimaxBot)
# ---------------------------------------------------------------------------

def minimax(
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    is_maximizing_player: bool,
    move_sorter: Optional[MoveSorter] = None
) -> float:
    generator = MoveGenerator(board)
    if move_sorter is None:
        move_sorter = MoveSorter()

    legal_moves = get_legal_moves(board, generator)
    legal_moves = move_sorter.move_sort(legal_moves, board, depth)
    status = check_game_status(board, legal_moves)

    if status != GameStatus.Playing:
        if status == GameStatus.RedWin:
            return 99999.0
        if status == GameStatus.BlueWin:
            return -99999.0
        return 0.0

    if depth == 0:
        return float(heuristic(board))

    if is_maximizing_player:
        max_eval = -math.inf
        for move in legal_moves:
            board.make_move(move)
            eval_score = minimax(board, depth - 1, alpha, beta, False, move_sorter)
            board.undo_move()
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if alpha >= beta:
                move_sorter.store_killer_move(depth, move, beta, eval_score)
                move_sorter.store_history(move, depth)
                break
        return max_eval

    min_eval = math.inf
    for move in legal_moves:
        board.make_move(move)
        eval_score = minimax(board, depth - 1, alpha, beta, True, move_sorter)
        board.undo_move()
        min_eval = min(min_eval, eval_score)
        beta = min(beta, eval_score)
        if alpha >= beta:
            move_sorter.store_killer_move(depth, move, beta, eval_score)
            move_sorter.store_history(move, depth)
            break
    return min_eval


# ---------------------------------------------------------------------------
# get_best_move (debug helper)
# ---------------------------------------------------------------------------

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
        value = -algorithm(board, depth - 1, -math.inf, math.inf, True, move_sorter)
        board.undo_move()
        _log.debug("Nước %s có điểm: %s", move_to_str(move), value)
        if value > best_val:
            best_val = value
            best_move = move
    return best_move