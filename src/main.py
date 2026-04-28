# main.py (test bàn cờ)
# main.py (test bàn cờ)
from core.board import Board
from core.board_renderer import BoardRenderer
from core.move_generator import MoveGenerator
from core.move import uci_to_move, move_to_uci
from core.rules import *
from colorama import init
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
                    winner = "ĐỎ" if status == 1 else "ĐEN"
                    print(f"\n{'='*25}\n!!! TRẬN ĐẤU KẾT THÚC: {winner} THẮNG !!!\n{'='*25}\n")
                break
                
            # 4. Cảnh báo nếu đang bị chiếu
            if is_in_check(board, board.side_to_move):
                print("\033[93m[ CẢNH BÁO: ĐANG BỊ CHIẾU TƯỚNG! ]\033[0m")

            # 5. Gợi ý nước đi (Chỉ hiện 10 nước đầu cho gọn)
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
    except KeyboardInterrupt:
        print("\nĐã thoát game.")

if __name__ == "__main__":
    main()
