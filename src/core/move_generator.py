# move_generator.py
from core.pieces import is_red, is_black, Color
from core.move import encode_move

class MoveGenerator:
    def __init__(self, board):
        self.board = board
        # Cung Đỏ (hàng 7, 8, 9; cột 3, 4, 5)
        self.red_palace = [66, 67, 68, 75, 76, 77, 84, 85, 86]
        # Cung Đen (hàng 0, 1, 2; cột 3, 4, 5)
        self.black_palace = [3, 4, 5, 12, 13, 14, 21, 22, 23]

    def get_pseudo_legal_moves(self):
        moves = []
        for sq, piece in enumerate(self.board.state):
            if piece == '.': continue
            
            # Chỉ sinh nước đi cho phe đang đến lượt
            if self.board.side_to_move == Color.RED and is_red(piece):
                moves.extend(self._generate_piece_moves(sq, piece))
            elif self.board.side_to_move == Color.BLACK and is_black(piece):
                moves.extend(self._generate_piece_moves(sq, piece))
        return moves

    def _generate_piece_moves(self, sq, piece):
        p = piece.upper()
        moves = []
        r, c = divmod(sq, 9)
        is_red_piece = piece.isupper()

        # 1. MÃ (H): Hình chữ L, check chân mã
        if p == 'H':
            # (offset_đi, offset_chân_mã)
            horse_logic = [
                (-18 - 1, -9), (-18 + 1, -9), # Tiến 2 trái/phải 1 - Chân: trên
                (18 - 1, 9),   (18 + 1, 9),   # Lùi 2 trái/phải 1 - Chân: dưới
                (-9 - 2, -1),  (9 - 2, -1),   # Trái 2 trên/dưới 1 - Chân: trái
                (-9 + 2, 1),   (9 + 2, 1)     # Phải 2 trên/dưới 1 - Chân: phải
            ]
            for m_off, b_off in horse_logic:
                target_sq = sq + m_off
                block_sq = sq + b_off
                if 0 <= target_sq < 90:
                    tr, tc = divmod(target_sq, 9)
                    # Kiểm tra không nhảy ra ngoài biên cột (tránh tràn hàng) và không bị cản
                    if abs(tc - c) <= 2 and self.board.state[block_sq] == '.':
                        target_piece = self.board.state[target_sq]
                        if target_piece == '.' or (is_red_piece != target_piece.isupper()):
                            moves.append(encode_move(sq, target_sq))

        # 2. TƯỢNG (E): Đi chéo 2 ô, không qua sông, check mắt tượng
        elif p == 'E':
            elephant_logic = [-20, -16, 16, 20] # 4 hướng chéo
            for off in elephant_logic:
                target_sq = sq + off
                eye_sq = sq + off // 2
                if 0 <= target_sq < 90:
                    tr, tc = divmod(target_sq, 9)
                    # Check mắt tượng, biên cột và SÔNG
                    if abs(tc - c) == 2 and self.board.state[eye_sq] == '.':
                        if (is_red_piece and tr >= 5) or (not is_red_piece and tr <= 4):
                            target_piece = self.board.state[target_sq]
                            if target_piece == '.' or (is_red_piece != target_piece.isupper()):
                                moves.append(encode_move(sq, target_sq))

        # 3. SĨ (A): Đi chéo 1 ô, trong cung
        elif p == 'A':
            for off in [-10, -8, 8, 10]:
                target_sq = sq + off
                if 0 <= target_sq < 90:
                    tr, tc = divmod(target_sq, 9)
                    palace = self.red_palace if is_red_piece else self.black_palace
                    if abs(tc - c) == 1 and target_sq in palace:
                        target_piece = self.board.state[target_sq]
                        if target_piece == '.' or (is_red_piece != target_piece.isupper()):
                            moves.append(encode_move(sq, target_sq))

        # 4. TƯỚNG (K): Đi thẳng 1 ô, trong cung
        elif p == 'K':
            for off in [-9, 9, -1, 1]:
                target_sq = sq + off
                if 0 <= target_sq < 90:
                    tr, tc = divmod(target_sq, 9)
                    palace = self.red_palace if is_red_piece else self.black_palace
                    if abs(tc - c) + abs(tr - r) == 1 and target_sq in palace:
                        target_piece = self.board.state[target_sq]
                        if target_piece == '.' or (is_red_piece != target_piece.isupper()):
                            moves.append(encode_move(sq, target_sq))

        # 5. TỐT (P): Tiến, qua sông thì được đi ngang
        elif p == 'P':
            step = -9 if is_red_piece else 9
            # Luôn được tiến
            target_sq = sq + step
            if 0 <= target_sq < 90:
                target_piece = self.board.state[target_sq]
                if target_piece == '.' or (is_red_piece != target_piece.isupper()):
                    moves.append(encode_move(sq, target_sq))
            # Qua sông được đi ngang
            is_over_river = (is_red_piece and r <= 4) or (not is_red_piece and r >= 5)
            if is_over_river:
                for side_step in [-1, 1]:
                    target_sq = sq + side_step
                    tr, tc = divmod(target_sq, 9)
                    if tr == r: # Cùng hàng
                        target_piece = self.board.state[target_sq]
                        if target_piece == '.' or (is_red_piece != target_piece.isupper()):
                            moves.append(encode_move(sq, target_sq))

        
    
        # Logic cho Xe (R) và Pháo (C) - Cùng kiểu trượt dọc/ngang
        if p in ['R', 'C']:
            for direction in [-1, 1, -9, 9]: # Trái, Phải, Trên, Dưới
                count_block = 0
                for step in range(1, 10):
                    target_sq = sq + direction * step
                    tr, tc = divmod(target_sq, 9)
                    if not (0 <= target_sq < 90) or (direction in [-1, 1] and tr != r): break
                    
                    target_piece = self.board.state[target_sq]
                    if target_piece == '.':
                        if p == 'R' and count_block == 0:
                            moves.append(encode_move(sq, target_sq))
                        elif p == 'C' and count_block == 0:
                            moves.append(encode_move(sq, target_sq))
                    else:
                        count_block += 1
                        if p == 'R':
                            if (is_red(piece) and is_black(target_piece)) or (is_black(piece) and is_red(target_piece)):
                                moves.append(encode_move(sq, target_sq))
                            break
                        elif p == 'C':
                            if count_block == 2: # Có ngòi mới được ăn
                                if (is_red(piece) and is_black(target_piece)) or (is_black(piece) and is_red(target_piece)):
                                    moves.append(encode_move(sq, target_sq))
                                break
                if count_block > 2: break
        
        return moves
