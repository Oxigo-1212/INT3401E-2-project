import time
import math
from typing import Optional, Callable
from core.board import Board
from core.move_generator import MoveGenerator
from core.rules import get_legal_moves
from core.utils import move_to_str
from core.logger import get_logger
from bots.engine.move_ordering import MoveSorter
from bots.engine.transposition_table import probe, TT_TABLE

# Aspiration Window: cửa sổ alpha/beta hẹp ban đầu quanh score lần trước.
# Nếu fail-low hoặc fail-high thì mở rộng ra và search lại.
_ASPIRATION_DELTA    = 50    # Cửa sổ ban đầu: [prev - 50, prev + 50]
_ASPIRATION_MIN_DEPTH = 4    # Chỉ bật Aspiration từ depth này trở lên

_log = get_logger("IDS")


def search_with_time_limit(
    board: Board,
    algorithm: Callable,
    time_limit_ms: int = 1000,
) -> Optional[int]:
    start_time = time.time()
    time_limit_sec = time_limit_ms / 1000.0

    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)
    if not legal_moves:
        return None

    best_move = legal_moves[0]
    depth = 0
    prev_score = 0.0          # score từ iteration trước, dùng cho Aspiration
    move_sorter = MoveSorter()

    _log.debug("Bắt đầu tìm kiếm: %dms | %d nước hợp lệ", time_limit_ms, len(legal_moves))

    while True:
        depth += 1
        elapsed = time.time() - start_time
        if elapsed > time_limit_sec * 0.9:
            _log.debug("Dừng tại depth %d (%.0fms)", depth - 1, elapsed * 1000)
            break

        _log.debug("Depth %d | %.0fms", depth, elapsed * 1000)

        current_best_move = best_move
        current_best_value = -math.inf
        moves_evaluated = 0

        entry, _ = probe(board.zobrist_key, depth, -math.inf, math.inf, TT_TABLE)
        tt_move = entry.best_move if entry is not None else 0
        sorted_moves = move_sorter.move_sort(legal_moves[:], board, depth, tt_move)

        for move_idx, move in enumerate(sorted_moves):
            if time.time() - start_time > time_limit_sec:
                _log.debug("Timeout tại nước %d/%d", moves_evaluated, len(sorted_moves))
                break

            board.make_move(move)
            try:
                value = -algorithm(board, depth - 1, -math.inf, math.inf, move_sorter)
            except Exception:
                value = -math.inf
            board.undo_move()

            moves_evaluated += 1
            if value > current_best_value:
                current_best_value = value
                current_best_move = move

        if moves_evaluated == len(sorted_moves):
            best_move = current_best_move
            prev_score = current_best_value
            _log.debug("depth %d: %s (%.0f)", depth, move_to_str(best_move), current_best_value)
        else:
            _log.debug("Timeout — giữ kết quả depth %d", depth - 1)
            break

    elapsed_total = (time.time() - start_time) * 1000
    _log.debug("Kết thúc: %s | %.0fms", move_to_str(best_move), elapsed_total)
    return best_move


def search_with_depth_limit(
    board: Board,
    algorithm: Callable,
    max_depth: int = 4,
) -> Optional[int]:
    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)
    if not legal_moves:
        return None

    best_move = legal_moves[0]
    move_sorter = MoveSorter()
    prev_score = 0.0

    _log.debug("Độ sâu tối đa: %d", max_depth)

    for depth in range(1, max_depth + 1):
        _log.debug("Depth %d", depth)

        entry, _ = probe(board.zobrist_key, depth, -math.inf, math.inf, TT_TABLE)
        tt_move = entry.best_move if entry is not None else 0
        sorted_moves = move_sorter.move_sort(legal_moves[:], board, depth, tt_move)

        depth_best_move = best_move
        depth_best_value = -math.inf

        # Aspiration Windows
        # Dùng cửa sổ hẹp [prev - delta, prev + delta] thay vì [-inf, +inf].
        # Nếu kết quả nằm ngoài cửa sổ (fail-low hoặc fail-high),
        # mở rộng và search lại ngay trong cùng depth.
        if depth >= _ASPIRATION_MIN_DEPTH:
            alpha = prev_score - _ASPIRATION_DELTA
            beta  = prev_score + _ASPIRATION_DELTA
        else:
            alpha = -math.inf
            beta  = math.inf

        aspiration_done = False
        while not aspiration_done:
            iter_best_move = best_move
            iter_best_value = -math.inf

            for move_idx, move in enumerate(sorted_moves):
                board.make_move(move)
                value = -algorithm(board, depth - 1, -beta, -alpha, move_sorter)
                board.undo_move()

                if value > iter_best_value:
                    iter_best_value = value
                    iter_best_move = move

                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break

            # Kiểm tra fail-low / fail-high → mở rộng cửa sổ
            if iter_best_value <= prev_score - _ASPIRATION_DELTA and depth >= _ASPIRATION_MIN_DEPTH:
                # Fail-low: mở rộng xuống
                alpha = -math.inf
                beta = iter_best_value + 1
                _log.debug("  Fail-low (%.0f), mở rộng cửa sổ xuống", iter_best_value)
            elif iter_best_value >= prev_score + _ASPIRATION_DELTA and depth >= _ASPIRATION_MIN_DEPTH:
                # Fail-high: mở rộng lên
                alpha = iter_best_value - 1
                beta = math.inf
                _log.debug("  Fail-high (%.0f), mở rộng cửa sổ lên", iter_best_value)
            else:
                aspiration_done = True

            depth_best_move = iter_best_move
            depth_best_value = iter_best_value

        best_move = depth_best_move
        prev_score = depth_best_value

        _log.debug("  → %s (%.0f)", move_to_str(best_move), depth_best_value)

    return best_move
