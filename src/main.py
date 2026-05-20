"""
Chế độ chơi: Con người vs Bot hoặc Bot vs Bot
"""

from typing import Optional
from core.board import Board
from bots.engine.transposition_table import init_tt, TT_TABLE
from core.board_renderer import BoardRenderer
from core.move_generator import MoveGenerator
from core.move import uci_to_move, move_to_uci
from core.rules import check_game_status, get_legal_moves, is_in_check, GameStatus, Color
from core.utils import move_to_str
from bots.bot import BotManager
from colorama import init
import time 

init()
def log_time(player_name: str, time_taken: float):
    # Mở (hoặc tạo nếu chưa có) file time_log.txt và ghi thêm vào cuối file  
    with open("time_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{player_name}] Thời gian suy nghĩ: {time_taken:.2f}s\n")

def safe_input(prompt: str) -> Optional[str]:
    try:
        string = input(prompt).strip()
        return string
    except KeyboardInterrupt:
        return None

def vs_bot():
    """Con người chơi với Bot."""
    board = Board()
    gen = MoveGenerator(board)
    renderer = BoardRenderer(board)
    
    # Tạo Bot
    print("Chọn Bot:")
    print("1. Negamax (depth=4)")
    print("2. Minimax (depth=3)")
    print("3. Random")
    print("4. Greedy")
    
    choice = input("Chọn Bot (1-4): ").strip()
    bot_map = {"1": "negamax", "2": "minimax", "3": "random", "4": "greedy"}
    bot_type = bot_map.get(choice, "negamax")
    
    bot = BotManager.create_bot(bot_type, depth=3)
    print(f"\nBot được chọn: {bot.get_name()}")
    
    player_color = input("Bạn muốn chơi với phe nào? (1=Đỏ, 2=Đen): ").strip()
    player_is_red = player_color == "1"
    
    try:
        while True:
            renderer.print_board()
            
            legal_moves = get_legal_moves(board, gen)
            status = check_game_status(board, legal_moves)
            
            if status != GameStatus.Playing:
                if status == GameStatus.Draw:
                    print(f"\n{'='*25}\nHÒA CỜ\n{'='*25}\n")
                else:
                    winner = "ĐỎ" if status == GameStatus.RedWin else "ĐEN"
                    print(f"\n{'='*25}\n{winner} THẮNG\n{'='*25}\n")
                break
            
            if is_in_check(board, board.side_to_move):
                print("\033[93m[CẢNH BÁO: ĐANG BỊ CHIẾU TƯỚNG!]\033[0m")
            
            is_red_turn = board.side_to_move == Color.RED
            
            if is_red_turn == player_is_red:
                # Lượt của người chơi
                moves_hint = [move_to_uci(m) for m in legal_moves[:10]]
                print(f"Các nước hợp lệ ({len(legal_moves)}): {moves_hint}...")
                
                # Bắt đầu bấm giờ
                start_time = time.time()

                try:
                    move_str = input("Nhập nước đi (vd: h2e2): ").strip().lower()
                except KeyboardInterrupt:
                    print("\nĐã thoát game.")
                    break

                # Kết thúc bấm giờ
                end_time = time.time()
                
                if move_str == 'q':
                    print("Đã thoát game.")
                    break
                
                try:
                    user_move = uci_to_move(move_str)
                    if user_move in legal_moves:
                        board.make_move(user_move)
                        log_time("Người chơi", end_time - start_time) # ghi thời gian ra file time_log.txt
                    else:
                        print(f"\033[91m!!! Nước đi {move_str} không hợp lệ.\033[0m")
                except ValueError:
                    print("\033[91m!!! Định dạng sai. Vui lòng nhập kiểu 'h2e2'.\033[0m")
            else:
                # Lượt của Bot
                print(f"Bot {bot.get_name()} đang suy nghĩ...")
                
                # bấm giờ cho bot
                start_time = time.time()
                move = bot.get_move(board)
                end_time = time.time()
                
                if move:
                    board.make_move(move)
                    log_time(bot.get_name(), end_time - start_time) # ghi thời gian ra file time_log.txt
                    print(f"Bot chơi: {move_to_str(move)}")
                else:
                    print("Bot không có nước đi hợp lệ!")
                    break
    
    except KeyboardInterrupt:
        print("\nĐã thoát game.")

def bot_vs_bot():
    """Bot chơi với Bot."""
    board = Board()
    gen = MoveGenerator(board)
    renderer = BoardRenderer(board)
    
    bot_red = BotManager.create_bot("negamax", depth=3)
    bot_black = BotManager.create_bot("negamax", depth=3)
    
    print(f"Đen: {bot_red.get_name()}")
    print(f"Đỏ: {bot_black.get_name()}\n")
    
    move_count = 0
    
    try:
        while move_count < 200:  # Tối đa 200 nước
            renderer.print_board()
            
            legal_moves = get_legal_moves(board, gen)
            status = check_game_status(board, legal_moves)
            
            if status != GameStatus.Playing:
                if status == GameStatus.Draw:
                    print("\nHÒA CỜ")
                else:
                    winner = "ĐỎ" if status == GameStatus.RedWin else "ĐEN"
                    print(f"\n{winner} THẮNG")
                break
            
            is_red_turn = board.side_to_move == Color.RED
            bot = bot_red if is_red_turn else bot_black
            
            print(f"Lượt {move_count + 1}: {bot.get_name()} đang suy nghĩ...")
            
            # bấm giờ cho bot
            start_time = time.time()
            move = bot.get_move(board)
            end_time = time.time()

            if move:
                board.make_move(move)
                log_time(bot.get_name(), end_time - start_time) # ghi thời gian ra file time_log.txt
                print(f"→ {move_to_str(move)}\n")
                move_count += 1
            else:
                print("Không có nước đi hợp lệ!")
                break
    
    except KeyboardInterrupt:
        print("\nĐã thoát game.")
def main() -> None:
    # Xóa file log cũ trước khi bắt đầu trận mới
    with open("time_log.txt", "w", encoding="utf-8") as f:
        f.write("")

    init_tt(1 << 20, TT_TABLE)
    print("=== CỜ TƯỚNG ENGINE ===")
    print("1. Con người vs Bot")
    print("2. Bot vs Bot")

    choice = safe_input("Chọn chế độ (1-2): ")

    if choice == "1":
        vs_bot()
    elif choice == "2":
        bot_vs_bot()
    else:
        print("Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main()
