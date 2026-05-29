import random
from core.board import Board
from core.move import deserialize_move as uci_to_move

OPENING_BOOK: dict[int, list[int]] = {}

def add_opening(move_sequence: list[str], response_moves: list[str]):
    board = Board()
    
    # Giả lập đi từng nước trong sequence để tái tạo bàn cờ
    for uci in move_sequence:
        move = uci_to_move(uci)
        board.make_move(move)
        
    # Mã hóa danh sách nước đi khuyên dùng
    encoded_responses = [uci_to_move(uci) for uci in response_moves]
    
    # Lưu vào Sổ bằng mã Zobrist
    if board.zobrist_key not in OPENING_BOOK:
        OPENING_BOOK[board.zobrist_key] = []
    OPENING_BOOK[board.zobrist_key].extend(encoded_responses)


# 1. THẾ CỜ BAN ĐẦU (Nước đầu tiên là của Bot chơi)
# Có 4 lựa chọn kinh điển nhất: Pháo đầu (h7e7), Tiên nhân chỉ lộ (g6g5), Khởi mã (h9g7), Phi tượng (g9e7)
add_opening([], ["h7e7", "b7e7", "g6g5", "c6c5", "h9g7", "b9c7", "g9e7", "c9e7"])


# PHÁO ĐẦU 

# Nếu Đỏ đánh Pháo đầu (h7e7), Đen phản hồi bằng Mã 8 tiến 7 (Bình phong mã) hoặc Pháo 8 bình 5 (Thuận pháo)
add_opening(["h7e7"], ["h0g2", "b0c2", "h2e2"])
add_opening(["b7e7"], ["h0g2", "b0c2", "b2e2"])

# Đỏ Pháo đầu, Đen lên Mã -> Đỏ thường lên Mã để giữ Pháo (h9g7)
add_opening(["h7e7", "h0g2"], ["h9g7", "b9c7"])

# Pháo đầu đối Bình Phong Mã (biến cơ bản)
add_opening(["h7e7", "h0g2", "h9g7"], ["b0c2", "i0h0"]) # Đen lên nốt Mã hoặc ra Xe


# TIÊN NHÂN CHỈ LỘ 
# Nếu Đỏ tiến Tốt 3 (g6g5), Đen phản hồi bằng Tốt đối (g3g4) hoặc Pháo đầu (h2e2)
add_opening(["g6g5"], ["g3g4", "h2e2", "c3c4"])
add_opening(["c6c5"], ["c3c4", "b2e2", "g3g4"])

# Đỏ Tiến Tốt 3, Đen đối Tốt 3 -> Đỏ thường lên Mã (h9g7)
add_opening(["g6g5", "g3g4"], ["h9g7"])


# KHỞI MÃ (EDGE HORSE)

# Đỏ lên Mã phải (h9g7), Đen có thể Tiến Tốt (g3g4) hoặc Pháo đầu (h2e2)
add_opening(["h9g7"], ["g3g4", "h2e2", "c3c4"])


# PHI TƯỢNG CUỘC 
# Đỏ lên Tượng phải (g9e7), Đen thường lên Mã (h0g2), Pháo Đầu (h2e2) hoặc Sĩ Giác Pháo (h2d2)
add_opening(["g9e7"], ["h0g2", "b0c2", "h2e2", "h2d2"])
add_opening(["g9e7", "h2e2"], ["h9g7"]) # Đen đánh Pháo đầu, Đỏ lên Mã giữ chốt giữa
add_opening(["g9e7", "h0g2"], ["h9g7", "b7d7"]) # Đen lên Mã, Đỏ lên Mã hoặc Quá Cung Pháo

# THUẬN PHÁO 
# Cả 2 bên đều vào Pháo Đầu cùng phía
add_opening(["h7e7", "h2e2"], ["h9g7", "i9h9"])
add_opening(["h7e7", "h2e2", "h9g7"], ["h0g2", "i0h0"])
add_opening(["h7e7", "h2e2", "h9g7", "h0g2"], ["i9h9"])
add_opening(["h7e7", "h2e2", "h9g7", "h0g2", "i9h9"], ["i0h0", "b0c2"])

# NGHỊCH PHÁO
# Đỏ vào Pháo h7e7, Đen vào Pháo nghịch b2e2
add_opening(["h7e7", "b2e2"], ["h9g7", "i9h9"])
add_opening(["h7e7", "b2e2", "h9g7"], ["b0c2", "a0b0"])

# SĨ GIÁC PHÁO (PALACE CORNER CANNON)
add_opening([], ["h7f7", "h7d7"]) # Đỏ có thể đánh Sĩ Giác Pháo hoặc Quá Cung Pháo từ nước đầu tiên
add_opening(["h7f7"], ["h0g2", "b0c2", "h2e2"])
add_opening(["h7f7", "h2e2"], ["h9g7"])

# QUÁ CUNG PHÁO 
# Pháo ném qua khỏi cung Tướng: h7d7
add_opening(["h7d7"], ["h0g2", "b0c2", "h2e2", "g3g4"])
add_opening(["h7d7", "h0g2"], ["h9g7"])
add_opening(["h7d7", "h2e2"], ["h9g7"])
