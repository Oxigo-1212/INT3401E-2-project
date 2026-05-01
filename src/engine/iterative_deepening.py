
import time
import math
from typing import Optional, Callable
from core.board import Board
from core.move_generator import MoveGenerator
from core.rules import get_legal_moves, check_game_status
from core.utils import move_to_str
from engine.algorithm import negmax, minimax
from engine.move_ordering import MoveSorter
from core.move import get_to_sq, get_from_sq


def search_with_time_limit(
    board: Board,
    algorithm: Callable,
    time_limit_ms: int = 1000,
    debug: bool = False
) -> Optional[int]:
    """
    Tìm kiếm Iterative Deepening với giới hạn thời gian.
    
    Thuật toán tăng độ sâu cho đến khi hết thời gian.

    Args:
        board: Bàn cờ hiện tại
        algorithm: Hàm tìm kiếm (negmax)
        time_limit_ms
        debug: In thông tin debug
    
    Returns:
        Nước đi tốt nhất, hoặc None nếu không có nước đi nào
    """
    start_time = time.time()
    time_limit_sec = time_limit_ms / 1000.0
    
    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)
    
    if not legal_moves:
        return None
    
    best_move = legal_moves[0]
    best_value = -math.inf
    depth = 0
    
    move_sorter = MoveSorter()
    
    if debug:
        print(f"[IDS] Bắt đầu tìm kiếm với thời gian: {time_limit_ms}ms")
        print(f"[IDS] Số nước đi hợp lệ: {len(legal_moves)}")
    
    # Tăng độ sâu cho đến khi hết thời gian
    while True:
        depth += 1
        elapsed = time.time() - start_time
        
        if elapsed > time_limit_sec * 0.9:  # Dừng khi dùng hết 90% thời gian
            if debug:
                print(f"[IDS] Dừng tại độ sâu {depth - 1} (thời gian: {elapsed*1000:.0f}ms)")
            break
        
        if debug:
            print(f"\n[IDS] Depth {depth} | Thời gian: {elapsed*1000:.0f}ms")
        
        current_best_move = None
        current_best_value = -math.inf
        moves_evaluated = 0
        
        # Sắp xếp nước đi bằng kết quả lần trước
        sorted_moves = move_sorter.move_sort(legal_moves[:], board, 0)
        
        for move_idx, move in enumerate(sorted_moves):
            # Kiểm tra timeout sau mỗi nước đi
            if time.time() - start_time > time_limit_sec:
                if debug:
                    print(f"[IDS] Timeout - đã đánh giá {moves_evaluated}/{len(sorted_moves)} nước")
                break
            
            board.make_move(move)
            
            # Gọi hàm tìm kiếm (negmax)
            try:
                value = -algorithm(
                    board,
                    depth - 1,
                    -math.inf,
                    math.inf,
                    True,
                    move_sorter
                )
            except:
                value = -math.inf
            
            board.undo_move()
            
            moves_evaluated += 1
            
            if value > current_best_value:
                current_best_value = value
                current_best_move = move
            
            if debug and move_idx < min(5, len(sorted_moves)):
                print(f"  {move_to_str(move)}: {value}")
        
        # Nếu tìm được nước đi tốt hơn, cập nhật
        if current_best_move is not None and current_best_value > best_value:
            best_move = current_best_move
            best_value = current_best_value
            if debug:
                print(f"[IDS] Nước đi tốt nhất ở depth {depth}: {move_to_str(best_move)} ({best_value})")
        
        # Nếu đã duyệt hết tất cả nước ở depth này, tăng depth
        if moves_evaluated < len(sorted_moves):
            if debug:
                print(f"[IDS] Timeout trước khi hoàn thành depth {depth}")
            break
    
    elapsed_total = (time.time() - start_time) * 1000
    if debug:
        print(f"\n[IDS] Kết thúc: Nước đi {move_to_str(best_move)} ({best_value})")
        print(f"[IDS] Tổng thời gian: {elapsed_total:.0f}ms")
    
    return best_move


def search_with_depth_limit(
    board: Board,
    algorithm: Callable,
    max_depth: int = 4,
    debug: bool = False
) -> Optional[int]:
    """
    Iterative Deepening với giới hạn độ sâu cố định.
    Dùng khi không có giới hạn thời gian.
    
    Args:
        board: Bàn cờ hiện tại
        algorithm: Hàm tìm kiếm
        max_depth: Độ sâu tối đa
        debug: In thông tin debug
    
    Returns:
        Nước đi tốt nhất
    """
    generator = MoveGenerator(board)
    legal_moves = get_legal_moves(board, generator)
    
    if not legal_moves:
        return None
    
    best_move = legal_moves[0]
    best_value = -math.inf
    move_sorter = MoveSorter()
    
    if debug:
        print(f"[IDS] Tìm kiếm với độ sâu tối đa: {max_depth}")
    
    # Tăng độ sâu từ 1 đến max_depth
    for depth in range(1, max_depth + 1):
        if debug:
            print(f"\n[IDS] Depth {depth}")
        
        sorted_moves = move_sorter.move_sort(legal_moves[:], board, 0)
        
        for move_idx, move in enumerate(sorted_moves):
            board.make_move(move)
            
            value = -algorithm(
                board,
                depth - 1,
                -math.inf,
                math.inf,
                True,
                move_sorter
            )
            
            board.undo_move()
            
            if value > best_value:
                best_value = value
                best_move = move
                if debug and move_idx < 3:
                    print(f"  {move_to_str(move)}: {value}")
        
        if debug:
            print(f"  → Nước đi tốt nhất: {move_to_str(best_move)} ({best_value})")
    
    return best_move