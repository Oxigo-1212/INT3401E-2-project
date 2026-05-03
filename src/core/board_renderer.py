# board_renderer.py
from core.board import Board
from core.pieces import CHINESE_PIECES, Color


class BoardRenderer:
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    GRAY = "\033[90m"

    def __init__(self, board: Board):
        self.board = board

    def print_board(self):
        print(f"\nLượt đi: {self.RED + 'ĐỎ' if self.board.side_to_move == Color.RED else self.BLUE + 'ĐEN'}{self.RESET}")
        header = "   " + "  ".join(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i'])
        print(self.GRAY + header + self.RESET)
        for row in range(10):
            row_str = [self.GRAY + str(row) + self.RESET]
            for col in range(9):
                piece = self.board.state[row * 9 + col]
                char = CHINESE_PIECES[piece]
                if piece == '.':
                    row_str.append(self.GRAY + char + self.RESET)
                elif piece.isupper():
                    row_str.append(self.RED + char + self.RESET)
                else:
                    row_str.append(self.BLUE + char + self.RESET)
            print(" ".join(row_str) + self.GRAY + f" {row}" + self.RESET)
        print(self.GRAY + header + self.RESET + "\n")
