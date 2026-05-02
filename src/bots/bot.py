"""
Bot chơi cờ tướng sử dụng Iterative Deepening Search.
Hỗ trợ cả time control và depth limit.
"""

from typing import Optional, Dict
from core.board import Board
from core.move_generator import MoveGenerator
from core.rules import get_legal_moves
from engine.algorithm import negmax
from engine.iterative_deepening import (
    search_with_time_limit,
    search_with_depth_limit
)
import random
from core.move import get_to_sq
from core.pieces import PIECE_VALUES
from engine.algorithm import minimax

class Bot:
    """Lớp cơ sở cho Bot chơi cờ tướng."""
    
    def __init__(self):
        self.name = "Bot"
        self.depth = 4
        self.time_limit_ms = 1000
        self.use_time_limit = False
    
    def get_move(self, board: Board) -> Optional[int]:
        """
        Trả về nước đi tốt nhất cho bàn cờ hiện tại.

        Args:
            board: Bàn cờ hiện tại

        Returns:
            Nước đi (encoded integer), hoặc None nếu không có nước đi
        """
        raise NotImplementedError("Subclass phải cài đặt get_move()")
    
    def get_name(self) -> str:
        """Trả về tên bot (dùng cho log tournament)."""
        return self.name
    
    def get_config(self) -> Dict[str, object]:
        """Trả về cấu hình bot (depth, algorithm, ...)."""
        return {
            "name": self.name,
            "depth": self.depth,
            "time_limit_ms": self.time_limit_ms,
            "use_time_limit": self.use_time_limit
        }


class NegmaxBot(Bot):
    """
    Bot sử dụng Negamax + Alpha-Beta Pruning.
    Tìm kiếm với Iterative Deepening.
    """
    
    def __init__(self, depth: int = 4, time_limit_ms: Optional[int] = None):
        super().__init__()
        self.name = f"Negamax Bot (depth={depth})"
        self.depth = depth
        
        if time_limit_ms is not None:
            self.time_limit_ms = time_limit_ms
            self.use_time_limit = True
            self.name = f"Negamax Bot (time={time_limit_ms}ms)"
        else:
            self.use_time_limit = False
    
    def get_move(self, board: Board) -> Optional[int]:
        """Tìm nước đi tốt nhất bằng Negamax với IDS."""
        
        if self.use_time_limit:
            return search_with_time_limit(
                board,
                negmax,
                time_limit_ms=self.time_limit_ms,
                debug=False
            )
        else:
            return search_with_depth_limit(
                board,
                negmax,
                max_depth=self.depth,
                debug=False
            )


class RandomBot(Bot):
    """
    Bot chọn nước đi ngẫu nhiên.
    Dùng để test.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Random Bot"
    
    def get_move(self, board: Board) -> Optional[int]:
        """Chọn nước đi ngẫu nhiên."""
        generator = MoveGenerator(board)
        legal_moves = get_legal_moves(board, generator)

        if not legal_moves:
            return None

        return random.choice(legal_moves)


class GreedyBot(Bot):
    """
    Bot chọn nước đi ăn quân có giá trị lớn nhất.
    Nếu không có nước ăn quân, chọn nước đầu tiên.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "Greedy Bot"
    
    def get_move(self, board: Board) -> Optional[int]:
        """Chọn nước đi ăn quân tốt nhất."""
        generator = MoveGenerator(board)
        legal_moves = get_legal_moves(board, generator)

        if not legal_moves:
            return None

        best_move = legal_moves[0]
        best_capture_value = 0

        for move in legal_moves:
            to_sq = get_to_sq(move)
            captured_piece = board.state[to_sq]

            if captured_piece != '.':
                capture_value = PIECE_VALUES.get(captured_piece, 0)
                if capture_value > best_capture_value:
                    best_capture_value = capture_value
                    best_move = move

        return best_move


class MinimaxBot(Bot):
    """Bot sử dụng Minimax + Alpha-Beta Pruning."""
    
    def __init__(self, depth: int = 3):
        super().__init__()
        self.name = f"Minimax Bot (depth={depth})"
        self.depth = depth
        self.algorithm = minimax
    
    def get_move(self, board: Board) -> Optional[int]:
        """Tìm nước đi tốt nhất bằng Minimax."""
        return search_with_depth_limit(
            board,
            self.algorithm,
            max_depth=self.depth,
            debug=False
        )


class BotManager:
    """
    Quản lý các Bot khác nhau.
    Dùng để tạo và chọn Bot cho các trận đấu.
    """
    
    @staticmethod
    def create_bot(bot_type: str, **kwargs) -> Bot:
        """
        Tạo Bot theo loại.
        
        Args:
            bot_type: "negamax", "random", "greedy", "minimax"
            **kwargs: Các tham số cấu hình
        
        Returns:
            Instance của Bot
        """
        if bot_type.lower() == "negamax":
            depth = kwargs.get("depth", 4)
            time_limit = kwargs.get("time_limit_ms")
            return NegmaxBot(depth=depth, time_limit_ms=time_limit)
        
        elif bot_type.lower() == "minimax":
            depth = kwargs.get("depth", 3)
            return MinimaxBot(depth=depth)
        
        elif bot_type.lower() == "random":
            return RandomBot()
        
        elif bot_type.lower() == "greedy":
            return GreedyBot()
        
        else:
            raise ValueError(f"Unknown bot type: {bot_type}")
    
    @staticmethod
    def list_bots() -> list:
        """Danh sách các loại Bot có sẵn."""
        return ["negamax", "minimax", "random", "greedy"]
