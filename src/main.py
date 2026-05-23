"""
Chế độ chơi: Con người vs Bot hoặc Bot vs Bot (Tích hợp Arena Game)
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
from core.logger import init_logging, get_logger

# Import thêm Game và các Enum liên quan từ arena.game
from arena.game import Game, Winner, GameResultStatus

init()

_log = get_logger("main")

class HumanPlayer:
    """Class bọc cho người chơi để tương thích với thuộc tính 'name' của Game"""
    def __init__(self, name="Human"):
        self.name = name

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
    print("1. Negamax (depth=3)")
    print("2. Random")
    print("3. Greedy")
    
    choice = input("Chọn Bot (1-3): ").strip()
    bot_map = {"1": "negamax", "2": "random", "3": "greedy"}
    bot_type = bot_map.get(choice, "negamax")
    
    bot = BotManager.create_bot(bot_type, depth=3)
    bot.name = bot.get_name() # Gán name cho bot để Game ghi log
    print(f"\nBot được chọn: {bot.name}")
    
    player_color = input("Bạn muốn chơi với phe nào? (1=Đỏ, 2=Đen): ").strip()
    player_is_red = player_color == "1"
    
    human = HumanPlayer("Player_Red" if player_is_red else "Player_Black")
    
    # Thiết lập Player 1 (Đỏ) và Player 2 (Đen)
    if player_is_red:
        player1, player2 = human, bot
    else:
        player1, player2 = bot, human
        
    # Khởi tạo Arena Game
    game = Game(player1, player2, board)
    game.logger.info(f"Game started: {player1.name} (RED) vs {player2.name} (BLACK)")
    
    try:
        while True:
            renderer.print_board()
            
            legal_moves = get_legal_moves(board, gen)
            status = check_game_status(board, legal_moves)
            
            # KIỂM TRA KẾT THÚC VÁN CỜ
            if status != GameStatus.Playing:
                if status == GameStatus.Draw:
                    print(f"\n{'='*25}\nHÒA CỜ\n{'='*25}\n")
                    game._set_winner(Winner.DRAW)
                    game.game_result_status = GameResultStatus.DRAW
                else:
                    winner = "ĐỎ" if status == GameStatus.RedWin else "ĐEN"
                    print(f"\n{'='*25}\n{winner} THẮNG\n{'='*25}\n")
                    game._set_winner(Winner.RED if status == GameStatus.RedWin else Winner.BLACK)
                    game.game_result_status = GameResultStatus.CHECKMATE
                
                game.logger.info(f"Game ended. Status: {game.game_result_status.value}")
                break
            
            if is_in_check(board, board.side_to_move):
                print("\033[93m[CẢNH BÁO: ĐANG BỊ CHIẾU TƯỚNG!]\033[0m")
            
            is_red_turn = board.side_to_move == Color.RED
            current_player_name = player1.name if is_red_turn else player2.name
            current_color_name = "RED" if is_red_turn else "BLACK"
            
            if is_red_turn == player_is_red:
                # Lượt của người chơi
                moves_hint = [move_to_uci(m) for m in legal_moves[:10]]
                print(f"Các nước hợp lệ ({len(legal_moves)}): {moves_hint}...")
                
                start_time = time.time()
                try:
                    move_str = input("Nhập nước đi (vd: h2e2, q để thoát): ").strip().lower()
                except KeyboardInterrupt:
                    print("\nĐã thoát game.")
                    game.resign(human.name)
                    break
                end_time = time.time()
                
                if move_str == 'q':
                    print("Đã thoát game (Bỏ cuộc).")
                    game.resign(human.name)
                    break
                
                try:
                    user_move = uci_to_move(move_str)
                    if user_move in legal_moves:
                        board.make_move(user_move)
                        log_time("Người chơi", end_time - start_time)
                        
                        # Ghi log vào arena game
                        game.moves.append((human.name, user_move, move_str))
                        game.logger.info(f"Move {len(game.moves)}: {human.name} ({current_color_name}) -> {move_str}")
                    else:
                        print(f"\033[91m!!! Nước đi {move_str} không hợp lệ.\033[0m")
                except ValueError:
                    print("\033[91m!!! Định dạng sai. Vui lòng nhập kiểu 'h2e2'.\033[0m")
            else:
                # Lượt của Bot
                _log.info("Bot %s đang suy nghĩ...", bot.name)
                start_time = time.time()
                move = bot.get_move(board)
                end_time = time.time()
                
                if move:
                    board.make_move(move)
                    log_time(bot.name, end_time - start_time)
                    move_uci = move_to_uci(move)
                    print(f"Bot chơi: {move_to_str(move)} ({move_uci})")
                    
                    # Ghi log vào arena game
                    game.moves.append((bot.name, move, move_uci))
                    game.logger.info(f"Move {len(game.moves)}: {bot.name} ({current_color_name}) -> {move_uci}")
                else:
                    _log.warning("Bot không có nước đi hợp lệ!")
                    _log.error("%s has no valid moves!", bot.name)
                    game.resign(bot.name)
                    break
                    
    except KeyboardInterrupt:
        _log.info("Đã thoát game đột ngột.")
        game.resign(human.name)
        
    finally:
        # Xuất PNG và thông báo tổng kết ở cuối ván
        game.pgn = game.export_pgn()
        game._save_pgn()
        _log.info("--- TỔNG KẾT VÁN CỜ (%s) ---", game.game_id)
        _log.info("Tổng số nước đi: %d", len(game.moves))
        _log.info("Người chiến thắng được ghi nhận: %s", game.winner.value if game.winner else 'Chưa rõ')
        _log.info("PGN:")
        _log.info("%s", game.pgn)


def bot_vs_bot():
    """Bot chơi với Bot."""
    board = Board()
    gen = MoveGenerator(board)
    renderer = BoardRenderer(board)
    # Cho phép người dùng chọn bot cho cả hai phe trước khi vào trận
    available = BotManager.list_bots()
    print("Các loại Bot khả dụng:")
    for i, b in enumerate(available, start=1):
        print(f"{i}. {b}")

    def choose_bot(prompt: str, default: str) -> str:
        # Lặp cho tới khi người dùng nhập hợp lệ. Enter chấp nhận giá trị mặc định.
        while True:
            choice = input(prompt).strip()
            if choice == "":
                return default
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(available):
                    return available[idx]
                else:
                    print("Lựa chọn không hợp lệ: không có bot với số này. Vui lòng thử lại.")
                    continue
            # allow typing name directly
            if choice.lower() in available:
                return choice.lower()
            print("Lựa chọn không tồn tại. Vui lòng nhập số (1-3) hoặc tên bot hợp lệ.")

    red_type = choose_bot("Chọn Bot cho Đỏ (số hoặc tên, enter=negamax): ", "negamax")
    black_type = choose_bot("Chọn Bot cho Đen (số hoặc tên, enter=greedy): ", "greedy")

    # Tùy chọn độ sâu mặc định cho các bot tìm kiếm
    def ask_depth(bot_type: str, default_depth: int) -> int:
        if bot_type in ("negamax",):
            d = input(f"Đặt depth cho {bot_type} (enter={default_depth}): ").strip()
            if d.isdigit() and int(d) > 0:
                return int(d)
        return default_depth

    red_depth = ask_depth(red_type, 3)
    black_depth = ask_depth(black_type, 3)

    bot_red = BotManager.create_bot(red_type, depth=red_depth)
    bot_black = BotManager.create_bot(black_type, depth=black_depth)

    bot_red.name = bot_red.get_name() + "_Red"
    bot_black.name = bot_black.get_name() + "_Black"

    print(f"\nĐỏ: {bot_red.name}")
    print(f"Đen: {bot_black.name}\n")
    
    # Khởi tạo Arena Game
    game = Game(bot_red, bot_black, board)
    game.logger.info(f"Game started: {bot_red.name} (RED) vs {bot_black.name} (BLACK)")
    
    move_count = 0
    
    try:
        while move_count < 200:  # Tối đa 200 nước
            renderer.print_board()
            
            legal_moves = get_legal_moves(board, gen)
            status = check_game_status(board, legal_moves)
            
            # KIỂM TRA KẾT THÚC VÁN CỜ
            if status != GameStatus.Playing:
                if status == GameStatus.Draw:
                    print("\nHÒA CỜ")
                    game._set_winner(Winner.DRAW)
                    game.game_result_status = GameResultStatus.DRAW
                else:
                    winner = "ĐỎ" if status == GameStatus.RedWin else "ĐEN"
                    print(f"\n{winner} THẮNG")
                    game._set_winner(Winner.RED if status == GameStatus.RedWin else Winner.BLACK)
                    game.game_result_status = GameResultStatus.CHECKMATE
                    
                game.logger.info(f"Game ended. Status: {game.game_result_status.value}")
                break
            
            is_red_turn = board.side_to_move == Color.RED
            bot = bot_red if is_red_turn else bot_black
            current_color_name = "RED" if is_red_turn else "BLACK"
            
            _log.info("Lượt %d: %s đang suy nghĩ...", move_count + 1, bot.name)
            
            start_time = time.time()
            move = bot.get_move(board)
            end_time = time.time()

            if move:
                board.make_move(move)
                log_time(bot.name, end_time - start_time)
                move_uci = move_to_uci(move)
                print(f"→ {move_to_str(move)} ({move_uci})\n")
                
                # Ghi log
                game.moves.append((bot.name, move, move_uci))
                game.logger.info(f"Move {len(game.moves)}: {bot.name} ({current_color_name}) -> {move_uci}")
                
                move_count += 1
            else:
                _log.warning("%s không có nước đi hợp lệ!", bot.name)
                game.resign(bot.name)
                break
                
        if move_count >= 200:
            _log.info("Đạt giới hạn 200 nước đi. Xử hòa.")
            game._set_winner(Winner.DRAW)
            game.game_result_status = GameResultStatus.DRAW
            
    except KeyboardInterrupt:
        _log.info("Đã can thiệp dừng game.")
        game.game_result_status = GameResultStatus.ERROR
        
    finally:
        # Xuất PNG và thông báo tổng kết ở cuối ván
        game.pgn = game.export_pgn()
        game._save_pgn()
        _log.info("--- TỔNG KẾT VÁN CỜ (%s) ---", game.game_id)
        _log.info("Tổng số nước đi: %d", len(game.moves))
        _log.info("Người chiến thắng được ghi nhận: %s", game.winner.value if game.winner else 'Chưa rõ')
        _log.info("PGN:")
        _log.info("%s", game.pgn)


if __name__ == "__main__":
    # Xóa file log cũ trước khi bắt đầu trận mới
    with open("time_log.txt", "w", encoding="utf-8") as f:
        f.write("")
        
    init_logging()
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
