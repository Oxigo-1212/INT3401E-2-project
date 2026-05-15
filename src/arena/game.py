# arena/game.py

import datetime
import os
import sys
import logging
from enum import Enum
from typing import Optional, List, Tuple

# Handle relative imports for both package and direct execution
try:
    from ..core.board import Board
    from ..core.move_generator import MoveGenerator
    from ..core.rules import check_game_status, GameStatus, get_legal_moves
    from ..core.move import move_to_uci
    from ..core.pieces import Color
except ImportError:
    # Fallback for direct execution
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from core.board import Board
    from core.move_generator import MoveGenerator
    from core.rules import check_game_status, GameStatus, get_legal_moves
    from core.move import move_to_uci
    from core.pieces import Color


class Winner(Enum):
    """Enum để xác định người thắng (dùng màu quân, không phải tên bot)."""
    RED = "Red"
    BLACK = "Black"
    DRAW = "Draw"


class Game:
    """
    Lớp quản lý một ván cờ tướng giữa hai bot/người chơi.
    
    Attributes:
        player1: Bot/Player thứ nhất (phe Đỏ/RED)
        player2: Bot/Player thứ hai (phe Đen/BLACK)
        board: Bàn cờ (Board object)
        moves: Danh sách các nước đi đã thực hiện
        game_status: Trạng thái ván cờ (Playing, RedWin, BlueWin, Draw)
        winner: Người thắng (Winner.RED, Winner.BLACK, Winner.DRAW)
        pgn: Ngoại lệ cờ (PGN format)
        game_id: ID duy nhất của ván cờ
        logger: Logger instance cho game này
        game_result_status: Trạng thái chi tiết (checkmate, timeout, resign, etc.)
    """
    
    def __init__(
        self,
        player1,
        player2,
        board: Board,
        game_id: Optional[str] = None,
        log_path: Optional[str] = None
    ):
        """
        Khởi tạo một ván cờ.
        
        Args:
            player1: Bot/Player thứ nhất (phe Đỏ/RED - sở hữu Tướng K)
            player2: Bot/Player thứ hai (phe Đen/BLACK - sở hữu Tướng k)
            board: Board object
            game_id: ID ván cờ (tự sinh nếu không có)
            log_path: Đường dẫn thư mục lưu log/PGN (mặc định: logs/)
        """
        self.player1 = player1
        self.player2 = player2
        self.board = board
        self.moves: List[Tuple[str, int, str]] = []  # (player_name, move_int, move_uci)
        self.game_status = GameStatus.Playing
        self.winner: Optional[Winner] = None
        self.game_result_status: str = "playing"  # checkmate, resign, timeout, draw, playing
        self.pgn = ""
        self.game_id = game_id or datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        self.log_path = log_path or "logs"
        
        # Khởi tạo logger
        self.logger = self._init_logger()

    def play(self) -> str:
        """
        Chạy ván cờ đến khi kết thúc.
        
        Returns:
            game_id của ván cờ
        """
        current_player = self.player1
        other_player = self.player2
        current_color = Color.RED
        move_count = 0
        max_moves = 1000  # Giới hạn nước đi tối đa để tránh vòng lặp vô hạn

        self.logger.info(f"Game started: {self.player1.name} (RED) vs {self.player2.name} (BLACK)")

        while self.game_status == GameStatus.Playing and move_count < max_moves:
            # Sinh nước đi hợp lệ
            move_generator = MoveGenerator(self.board)
            legal_moves = get_legal_moves(self.board, move_generator)

            # Kiểm tra trạng thái game
            self.game_status = check_game_status(self.board, legal_moves)
            if self.game_status != GameStatus.Playing:
                # Xác định người thắng dựa trên game_status
                self._determine_winner_from_status(current_color)
                self.game_result_status = "checkmate"
                break

            # Lấy nước đi từ bot
            try:
                move = current_player.get_move(self.board)
            except Exception as e:
                self.logger.error(f"Error getting move from {current_player.name}: {e}")
                # Nếu bot gặp lỗi, coi như nó thua
                self._set_winner(Winner.BLACK if current_color == Color.RED else Winner.RED)
                self.game_result_status = "error"
                break

            # Kiểm tra nước đi có hợp lệ không
            if move not in legal_moves:
                self.logger.error(f"Illegal move from {current_player.name}: {move}")
                # Nước đi không hợp lệ = thua
                self._set_winner(Winner.BLACK if current_color == Color.RED else Winner.RED)
                self.game_result_status = "illegal_move"
                break

            # Thực thi nước đi
            move_uci = move_to_uci(move)
            self.board.make_move(move)
            self.moves.append((current_player.name, move, move_uci))
            self.logger.info(f"Move {move_count + 1}: {current_player.name} ({current_color.name}) -> {move_uci}")

            # Đổi lượt
            current_player, other_player = other_player, current_player
            current_color = Color.BLACK if current_color == Color.RED else Color.RED
            move_count += 1

        # Nếu chưa có người thắng (e.g., hòa cờ)
        if self.winner is None:
            self.winner = Winner.DRAW
            self.game_result_status = "draw"

        self.logger.info(f"Game ended: {self.winner.value} wins. Status: {self.game_result_status}")
        
        # Xuất PGN
        self.pgn = self.export_pgn()
        self._save_pgn()
        
        return self.game_id

    def _determine_winner_from_status(self, last_move_color: Color) -> None:
        """
        Xác định người thắng dựa trên game_status và màu của nước đi cuối cùng.
        
        Logic: Nếu game_status là RedWin, tức là quân Đen bị checkmate,
        vậy quân Đỏ thắng (người chơi trước đó, opposite của last_move_color).
        
        Args:
            last_move_color: Màu của quân vừa di chuyển (gây ra checkmate/stalemate)
        """
        if self.game_status == GameStatus.RedWin:
            # Quân Đỏ thắng = quân Đen bị checkmate (người chơi vừa di chuyển là Đỏ)
            self.winner = Winner.RED
        elif self.game_status == GameStatus.BlueWin:
            # Quân Đen thắng = quân Đỏ bị checkmate (người chơi vừa di chuyển là Đen)
            self.winner = Winner.BLACK
        else:
            self.winner = Winner.DRAW

    def _set_winner(self, winner: Winner) -> None:
        """
        Thiết lập người thắng.
        
        Args:
            winner: Winner enum (RED, BLACK, hoặc DRAW)
        """
        self.winner = winner
        if winner == Winner.RED:
            self.game_status = GameStatus.RedWin
        elif winner == Winner.BLACK:
            self.game_status = GameStatus.BlueWin
        else:
            self.game_status = GameStatus.Draw

    def resign(self, player_name: str) -> None:
        """
        Xử lý khi một người chơi bỏ cuộc.
        
        Args:
            player_name: Tên của người chơi bỏ cuộc
        """
        if player_name == self.player1.name:
            self.winner = Winner.BLACK
        else:
            self.winner = Winner.RED
        
        self.game_status = GameStatus.BlueWin if self.winner == Winner.BLACK else GameStatus.RedWin
        self.game_result_status = "resign"
        self.logger.info(f"{player_name} resigned. {self.winner.value} wins.")

    def timeout(self, player_name: str) -> None:
        """
        Xử lý khi một người chơi hết thời gian.
        
        Args:
            player_name: Tên của người chơi hết giờ
        """
        if player_name == self.player1.name:
            self.winner = Winner.BLACK
        else:
            self.winner = Winner.RED
        
        self.game_status = GameStatus.BlueWin if self.winner == Winner.BLACK else GameStatus.RedWin
        self.game_result_status = "timeout"
        self.logger.info(f"{player_name} timeout. {self.winner.value} wins.")

    def _init_logger(self) -> logging.Logger:
        """
        Khởi tạo logger cho game này.
        
        Returns:
            Logger instance
        """
        # Tạo thư mục logs nếu chưa tồn tại
        os.makedirs(self.log_path, exist_ok=True)
        
        logger = logging.getLogger(f"Game_{self.game_id}")
        logger.setLevel(logging.DEBUG)
        
        # Handler cho file log
        log_file = os.path.join(self.log_path, f"{self.game_id}.log")
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        
        # Handler cho console
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Thêm handlers
        if not logger.handlers:  # Tránh thêm duplicate handlers
            logger.addHandler(fh)
            logger.addHandler(ch)
        
        return logger

    def _determine_winner(self):
        """
        [DEPRECATED] Xác định người thắng dựa trên game_status.
        Phương pháp này không chính xác, sử dụng _determine_winner_from_status thay thế.
        """
        # Giữ lại cho backward compatibility, nhưng không dùng nữa
        if self.winner is None:
            self.winner = Winner.DRAW

    def export_pgn(self) -> str:
        """
        Xuất ván cờ dưới định dạng PGN (Portable Game Notation).
        Định dạng được mở rộng cho cờ tướng với các tags bổ sung.
        
        Returns:
            Chuỗi PGN
        """
        pgn_lines = []
        
        # Thêm các tags PGN (Header)
        pgn_lines.append('[Event "AI Arena Game"]')
        pgn_lines.append(f'[Date "{datetime.date.today()}"]')
        pgn_lines.append(f'[Player1 "{self.player1.name}"]')
        pgn_lines.append(f'[Player2 "{self.player2.name}"]')
        pgn_lines.append(f'[Result "{self._get_pgn_result()}"]')
        pgn_lines.append(f'[GameID "{self.game_id}"]')
        pgn_lines.append(f'[Termination "{self.game_result_status}"]')
        pgn_lines.append(f'[Moves "{len(self.moves)}"]')
        pgn_lines.append(f'[Winner "{self.winner.value if self.winner else "Unknown"}"]')
        pgn_lines.append("")
        
        # Thêm các nước đi
        move_lines = []
        for move_num, (name, move_int, move_uci) in enumerate(self.moves, 1):
            if move_num % 2 == 1:  # Nước lẻ (Red)
                move_lines.append(f"{(move_num + 1) // 2}. {move_uci}")
            else:  # Nước chẵn (Black)
                move_lines[-1] += f" {move_uci}"
        
        pgn_lines.extend(move_lines)
        pgn_lines.append("")
        
        # Thêm kết quả
        pgn_lines.append(self._get_pgn_result())
        
        return "\n".join(pgn_lines)

    def _get_pgn_result(self) -> str:
        """
        Lấy kết quả ván cờ dưới dạng PGN.
        - "1-0": Đỏ/Player1 thắng
        - "0-1": Đen/Player2 thắng
        - "1/2-1/2": Hòa
        """
        if self.winner == Winner.RED:
            return "1-0"
        elif self.winner == Winner.BLACK:
            return "0-1"
        elif self.winner == Winner.DRAW:
            return "1/2-1/2"
        else:
            return "*"  # Chưa kết thúc

    def _save_pgn(self, log_path: Optional[str] = None) -> None:
        """
        Lưu PGN vào file.
        
        Args:
            log_path: Đường dẫn thư mục lưu (mặc định: self.log_path)
        """
        save_dir = log_path or self.log_path
        os.makedirs(save_dir, exist_ok=True)
        
        pgn_filename = os.path.join(save_dir, f"{self.game_id}.pgn")
        
        try:
            with open(pgn_filename, "w", encoding="utf-8") as f:
                f.write(self.pgn)
            self.logger.info(f"PGN saved to {pgn_filename}")
        except Exception as e:
            self.logger.error(f"Failed to save PGN: {e}")

    @staticmethod
    def _log(message: str) -> None:
        """[DEPRECATED] Ghi log thông thường. Sử dụng logger.info thay thế."""
        print(f"[GAME] {message}")

    @staticmethod
    def _log_move(player_name: str, move_uci: str) -> None:
        """[DEPRECATED] Ghi log nước đi. Sử dụng logger.info thay thế."""
        print(f"[MOVE] {player_name}: {move_uci}")

    @staticmethod
    def _log_error(message: str) -> None:
        """[DEPRECATED] Ghi log lỗi. Sử dụng logger.error thay thế."""
        print(f"[ERROR] {message}")


# Demo test
if __name__ == "__main__":
    # Note: Khi chạy trực tiếp file này, hãy chạy bằng:
    # python -m arena.game  (từ thư mục src)
    # Hoặc thêm đường dẫn project vào PYTHONPATH
    
    from bots.bot import NegmaxBot, RandomBot
    from core.board import Board

    # Tạo hai bot
    bot1 = NegmaxBot(depth=3)
    bot2 = RandomBot()
    
    # Tùy chọn: Đặt tên tùy chỉnh cho bot
    # bot1.name = "NegmaxBot-D3"
    # bot2.name = "RandomBot"
    
    # Khởi tạo bàn cờ
    board = Board()
    
    # Tạo ván cờ với custom log path
    game = Game(bot1, bot2, board, log_path="logs")
    
    # Chạy ván cờ
    game_id = game.play()
    print(f"\n{'='*50}")
    print(f"Game {game_id} finished!")
    print(f"Winner: {game.winner.value}")
    print(f"Result Status: {game.game_result_status}")
    print(f"Game Status: {game.game_status.name}")
    print(f"Total Moves: {len(game.moves)}")
    print(f"{'='*50}\n")
    print("PGN:")
    print(game.pgn)