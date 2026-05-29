from __future__ import annotations

import inspect
import math
import time
from typing import Callable, Optional

from bots.engine.move_ordering import MoveSorter
from bots.engine.transposition_table import TT_TABLE, probe
from core.pieces import Color
from core.board import Board
from core.move_generator import MoveGenerator
from core.rules import GameStatus, check_game_status, get_legal_moves
from core.utils import move_to_str
from core.logger import get_logger

# Aspiration Window: cửa sổ alpha/beta hẹp ban đầu quanh score lần trước.
# Nếu fail-low hoặc fail-high thì mở rộng ra và search lại.
_ASPIRATION_DELTA = 50    # Cửa sổ ban đầu: [prev - 50, prev + 50]
_ASPIRATION_MIN_DEPTH = 4  # Chỉ bật Aspiration từ depth này trở lên

_log = get_logger("IDS")


class SearchStopped(Exception):
    pass


def _algorithm_supports_control(algorithm: Callable) -> bool:
    try:
        signature = inspect.signature(algorithm)
    except (TypeError, ValueError):
        return False

    params = signature.parameters
    if any(param.kind == inspect.Parameter.VAR_KEYWORD for param in params.values()):
        return True
    return {"stats", "stop_flag", "ply"}.issubset(params)


def _call_algorithm(
    algorithm: Callable,
    board: Board,
    depth: int,
    alpha: float,
    beta: float,
    move_sorter: Optional[MoveSorter],
    *,
    stats: dict[str, int],
    stop_flag: Callable[[], bool] | None,
    ply: int,
    supports_control: bool,
) -> float:
    if supports_control:
        return algorithm(
            board,
            depth,
            alpha,
            beta,
            move_sorter,
            stats=stats,
            stop_flag=stop_flag,
            ply=ply,
        )
    return algorithm(board, depth, alpha, beta, move_sorter)


def _extract_pv(board: Board, max_depth: int) -> list[int]:
    pv: list[int] = []
    cursor = board.copy()

    for _ in range(max_depth):
        entry, _ = probe(cursor.zobrist_key, 0, -math.inf, math.inf, TT_TABLE)
        if entry is None or entry.best_move == 0:
            break
        pv.append(entry.best_move)
        cursor.make_move(entry.best_move)

    return pv


def _mate_from_pv(board: Board, pv: list[int]) -> Optional[int]:
    if not pv:
        return None

    root_side = board.side_to_move
    cursor = board.copy()
    for ply, move in enumerate(pv, start=1):
        cursor.make_move(move)
        generator = MoveGenerator(cursor)
        legal_moves = get_legal_moves(cursor, generator)
        status = check_game_status(cursor, legal_moves)
        if status != GameStatus.Playing:
            if status == GameStatus.RedWin:
                winner = Color.RED
            elif status == GameStatus.BlueWin:
                winner = Color.BLACK
            else:
                return None
            return ply if winner == root_side else -ply
    return None


def _snapshot(
    board: Board,
    best_move: int,
    score: float,
    depth: int,
    stats: dict[str, int],
    elapsed_ms: int,
) -> dict[str, object]:
    pv = _extract_pv(board, depth)
    mate = _mate_from_pv(board, pv)
    score_value = int(round(score)) if math.isfinite(score) else 0
    search_nodes = stats.get("search_nodes", stats.get("nodes", 0))
    return {
        "best_move": best_move,
        "score": score_value,
        "depth": depth,
        "seldepth": stats.get("seldepth", 0),
        "nodes": search_nodes,
        "time_ms": elapsed_ms,
        "pv": pv,
        "mate": mate,
    }


def search_with_time_limit(
    board: Board,
    algorithm: Callable,
    time_limit_ms: int | None = 1000,
    *,
    stop_flag: Callable[[], bool] | None = None,
    info_cb: Callable[[dict[str, object]], None] | None = None,
    stats: Optional[dict[str, int]] = None,
) -> Optional[int]:
    start_time = time.time()
    time_limit_sec = None if time_limit_ms is None else time_limit_ms / 1000.0

    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)
    if not legal_moves:
        return None

    best_move = legal_moves[0]
    depth = 0
    move_sorter = MoveSorter()
    supports_control = _algorithm_supports_control(algorithm)
    stats = {"nodes": 0, "search_nodes": 0, "seldepth": 0} if stats is None else stats

    _log.debug("Bắt đầu tìm kiếm: %sms | %d nước hợp lệ", time_limit_ms, len(legal_moves))

    while True:
        if stop_flag is not None and stop_flag():
            break

        depth += 1
        elapsed = time.time() - start_time
        if time_limit_sec is not None:
            remaining = time_limit_sec - elapsed
            alloc = max(remaining * 0.5, min(time_limit_sec * 0.1, 0.1))
            if remaining < alloc:
                _log.debug("Dừng tại depth %d (%.0fms)", depth - 1, elapsed * 1000)
                break

        _log.debug("Depth %d | %.0fms", depth, elapsed * 1000)

        entry, _ = probe(board.zobrist_key, depth, -math.inf, math.inf, TT_TABLE)
        tt_move = entry.best_move if entry is not None else 0
        sorted_moves = move_sorter.move_sort(legal_moves[:], board, depth, tt_move)

        current_best_move = best_move
        current_best_value = -math.inf
        moves_evaluated = 0
        completed = True

        for move in sorted_moves:
            if time_limit_sec is not None and time.time() - start_time > time_limit_sec:
                _log.debug("Timeout tại nước %d/%d", moves_evaluated, len(sorted_moves))
                completed = False
                break

            board.make_move(move)
            try:
                value = -_call_algorithm(
                    algorithm,
                    board,
                    depth - 1,
                    -math.inf,
                    math.inf,
                    move_sorter,
                    stats=stats,
                    stop_flag=stop_flag,
                    ply=1,
                    supports_control=supports_control,
                )
            except SearchStopped:
                completed = False
                break
            except Exception:
                value = -math.inf
            finally:
                board.undo_move()

            moves_evaluated += 1
            if value > current_best_value:
                current_best_value = value
                current_best_move = move

        if completed and moves_evaluated == len(sorted_moves):
            best_move = current_best_move
            elapsed_ms = int((time.time() - start_time) * 1000)
            snapshot = _snapshot(board, best_move, current_best_value, depth, stats, elapsed_ms)
            if info_cb is not None:
                info_cb(snapshot)
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
    *,
    stop_flag: Callable[[], bool] | None = None,
    info_cb: Callable[[dict[str, object]], None] | None = None,
    stats: Optional[dict[str, int]] = None,
) -> Optional[int]:
    start_time = time.time()
    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)
    if not legal_moves:
        return None

    best_move = legal_moves[0]
    move_sorter = MoveSorter()
    prev_score = 0.0
    supports_control = _algorithm_supports_control(algorithm)
    stats = {"nodes": 0, "search_nodes": 0, "seldepth": 0} if stats is None else stats

    _log.debug("Độ sâu tối đa: %d", max_depth)

    for depth in range(1, max_depth + 1):
        if stop_flag is not None and stop_flag():
            break

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
            beta = prev_score + _ASPIRATION_DELTA
        else:
            alpha = -math.inf
            beta = math.inf

        aspiration_done = False
        stopped = False
        while not aspiration_done:
            iter_best_move = best_move
            iter_best_value = -math.inf

            for move in sorted_moves:
                board.make_move(move)
                try:
                    value = -_call_algorithm(
                        algorithm,
                        board,
                        depth - 1,
                        -beta,
                        -alpha,
                        move_sorter,
                        stats=stats,
                        stop_flag=stop_flag,
                        ply=1,
                        supports_control=supports_control,
                    )
                except SearchStopped:
                    stopped = True
                    break
                except Exception:
                    value = -math.inf
                finally:
                    board.undo_move()

                if value > iter_best_value:
                    iter_best_value = value
                    iter_best_move = move

                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break

            if stopped:
                aspiration_done = True
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

        if stopped:
            break

        best_move = depth_best_move
        prev_score = depth_best_value

        elapsed_ms = int((time.time() - start_time) * 1000)
        snapshot = _snapshot(board, best_move, depth_best_value, depth, stats, elapsed_ms)
        if info_cb is not None:
            info_cb(snapshot)

        _log.debug("  → %s (%.0f)", move_to_str(best_move), depth_best_value)

    return best_move


def get_best_move(board: Board, algorithm: Callable, depth: int = 3) -> int | None:
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
