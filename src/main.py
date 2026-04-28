# main.py (test bàn cờ)
import time 
from core.board import Board
from core.board_renderer import BoardRenderer
from core.move_generator import MoveGenerator
from core.move import uci_to_move, move_to_uci
from core.rules import *
from colorama import init
from engine.algorithm import get_best_move
init() # Tự động xử lý mã màu trên Windows

def main():
    board = Board()
    gen = MoveGenerator(board)
    renderer = BoardRenderer(board)
    
    print("--- CHINESE CHESS ENGINE CORE ---")
    
    try:
        while True:
            # 1. Hiển thị bàn cờ
            renderer.print_board()
            
            # 2. Tính toán nước đi hợp lệ (CHỈ LÀM 1 LẦN duy nhất ở đầu lượt)
            legal_moves = get_legal_moves(board, gen)
            
            # 3. Kiểm tra trạng thái kết thúc (Chiếu bí / Hết nước)
            status = check_game_status(board, legal_moves)
            if status != 0:
                if status == 3:
                    print(f"\n{'='*25}\n!!! TRẬN ĐẤU KẾT THÚC: HÒA CỜ !!!\n{'='*25}\n")
                else:
                    winner = "ĐỎ (Player)" if status == 1 else "ĐEN (AI)"
                    print(f"\n{'='*25}\n!!! TRẬN ĐẤU KẾT THÚC: {winner} THẮNG !!!\n{'='*25}\n")
                break
                
            # 4. Cảnh báo nếu đang bị chiếu
            if is_in_check(board, board.side_to_move):
                print("\033[93m[ CẢNH BÁO: ĐANG BỊ CHIẾU TƯỚNG! ]\033[0m")

            # 5. Gợi ý nước đi (Chỉ hiện 10 nước đầu cho gọn)
            if board.side_to_move == Color.RED:
                moves_hint = [move_to_uci(m) for m in legal_moves[:10]]
                print(f"Lượt của {'ĐỎ' if board.side_to_move == Color.RED else 'ĐEN'}")
                print(f"Các nước hợp lệ ({len(legal_moves)}): {moves_hint}...")
            
                # 6. Nhận Input từ người dùng
                try:
                    move_str = input("Nhập nước đi (vd: h2e2) hoặc 'q' để thoát: ").strip().lower()
                except KeyboardInterrupt:
                    print("\nĐã thoát game.")
                    break
                
                if move_str == 'q': 
                    print("Đã thoát game.")
                    break

            # 7. Xử lý nước đi
                try:
                    user_move = uci_to_move(move_str)
                    if user_move in legal_moves:
                        board.make_move(user_move)
                    else:
                        print(f"\033[91m!!! Nước đi {move_str} không đúng luật. Hãy thử lại.\033[0m")
                except Exception:
                    print("\033[91m!!! Định dạng sai. Vui lòng nhập theo kiểu 'h2e2'.\033[0m")

            else: # !!! Lượt của AI (Đen)
                print("\n\033[96mAI đang suy nghĩ...\033[0m")
                start_time = time.time() # !!! Bắt đầu đo thời gian
                
                # Gọi thuật toán tìm nước đi tốt nhất
                # depth=3 là độ sâu vừa phải cho môi trường console
                ai_move = get_best_move(board, depth=3) # !!! AI tính toán
                
                end_time = time.time() # !!! Kết thúc đo thời gian
                
                if ai_move is not None:
                    # Chuyển đổi nước đi sang dạng uci để người chơi dễ quan sát
                    ai_move_str = move_to_uci(ai_move) # !!!
                    print(f"\033[92m=> AI đi: {ai_move_str} (Mất {round(end_time - start_time, 2)} giây)\033[0m")
                    board.make_move(ai_move) # !!! Thực thi nước đi của AI
                else:
                    print("AI không tìm thấy nước đi và xin chịu thua!")
                    break
    except KeyboardInterrupt:
        print("\nĐã thoát game.")

if __name__ == "__main__":
    main()