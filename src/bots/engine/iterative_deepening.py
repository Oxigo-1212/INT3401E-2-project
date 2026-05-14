import time
import math
from typing import Optional, Callable
from core.board import Board
from core.move_generator import MoveGenerator
from core.rules import get_legal_moves
from core.utils import move_to_str
from bots.engine.move_ordering import MoveSorter
from bots.engine.transposition_table import probe, TT_TABLE

# Aspiration Window: cửa sổ alpha/beta hẹp ban đầu quanh score lần trước.
# Nếu fail-low hoặc fail-high thì mở rộng ra và search lại.
_ASPIRATION_DELTA    = 50    # Cửa sổ ban đầu: [prev - 50, prev + 50]
_ASPIRATION_MIN_DEPTH = 4   # Chỉ bật Aspiration từ depth này trở lên


def search_with_time_limit(
    board: Board,
    algorithm: Callable,
    time_limit_ms: int = 1000,
    debug: bool = False
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

    if debug:
        print(f"[IDS] Bắt đầu tìm kiếm: {time_limit_ms}ms | {len(legal_moves)} nước hợp lệ")

    while True:
        depth += 1
        elapsed = time.time() - start_time
        if elapsed > time_limit_sec * 0.9:
            if debug:
                print(f"[IDS] Dừng tại depth {depth - 1} ({elapsed*1000:.0f}ms)")
            break

        if debug:
            print(f"\n[IDS] Depth {depth} | {elapsed*1000:.0f}ms")

        current_best_move = best_move
        current_best_value = -math.inf
        moves_evaluated = 0

        entry, _ = probe(board.zobrist_key, depth, -math.inf, math.inf, TT_TABLE)
        tt_move = entry.best_move if entry is not None else 0
        sorted_moves = move_sorter.move_sort(legal_moves[:], board, depth, tt_move)

        for move_idx, move in enumerate(sorted_moves):
            if time.time() - start_time > time_limit_sec:
                if debug:
                    print(f"[IDS] Timeout tại nước {moves_evaluated}/{len(sorted_moves)}")
                break

            board.make_move(move)
            try:
                value = -algorithm(board, depth - 1, -math.inf, math.inf, True, move_sorter)
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
            if debug:
                print(f"[IDS] depth {depth}: {move_to_str(best_move)} ({current_best_value:.0f})")
        else:
            if debug:
                print(f"[IDS] Timeout — giữ kết quả depth {depth - 1}")
            break

    if debug:
        elapsed_total = (time.time() - start_time) * 1000
        print(f"[IDS] Kết thúc: {move_to_str(best_move)} | {elapsed_total:.0f}ms")
    return best_move


def search_with_depth_limit(
    board: Board,
    algorithm: Callable,
    max_depth: int = 4,
    debug: bool = False
) -> Optional[int]:
    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)
    if not legal_moves:
        return None

    best_move = legal_moves[0]
    move_sorter = MoveSorter()
    prev_score = 0.0

    if debug:
        print(f"[IDS] Độ sâu tối đa: {max_depth}")

    for depth in range(1, max_depth + 1):
        if debug:
            print(f"\n[IDS] Depth {depth}")

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
                value = -algorithm(board, depth - 1, -beta, -alpha, True, move_sorter)
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
                if debug:
                    print(f"  Fail-low ({iter_best_value:.0f}), mở rộng cửa sổ xuống")
            elif iter_best_value >= prev_score + _ASPIRATION_DELTA and depth >= _ASPIRATION_MIN_DEPTH:
                # Fail-high: mở rộng lên
                alpha = iter_best_value - 1
                beta = math.inf
                if debug:
                    print(f"  Fail-high ({iter_best_value:.0f}), mở rộng cửa sổ lên")
            else:
                aspiration_done = True

            depth_best_move = iter_best_move
            depth_best_value = iter_best_value

        best_move = depth_best_move
        prev_score = depth_best_value

        if debug:
            print(f"  → {move_to_str(best_move)} ({depth_best_value:.0f})")

    return best_move