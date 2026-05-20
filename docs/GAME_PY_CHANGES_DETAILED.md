# game.py - Detailed Change Summary

## File Location
`src/arena/game.py`

## Changes Overview

### 1. Import Section (Lines 1-26)

**BEFORE:**
```python
# arena/game.py

import datetime
import os
from typing import Optional, List, Tuple
from ..core.board import Board
from ..core.move_generator import MoveGenerator
from ..core.rules import check_game_status, GameStatus, get_legal_moves
from ..core.move import move_to_uci
from ..core.pieces import Color
```

**AFTER:**
```python
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
```

**Changes:**
- ✅ Added `sys` and `logging` imports for better import handling and logging
- ✅ Added `try/except` block for import handling
- ✅ Fallback to absolute imports if relative imports fail

---

### 2. New Winner Enum (Lines 27-32)

**NEW:**
```python
class Winner(Enum):
    """Enum để xác định người thắng (dùng màu quân, không phải tên bot)."""
    RED = "Red"
    BLACK = "Black"
    DRAW = "Draw"
```

**Changes:**
- ✅ Created `Winner` enum to replace string-based winner tracking
- ✅ Uses color names (RED/BLACK) instead of bot names for consistency
- ✅ Separate from `GameStatus` enum for clarity

---

### 3. Game Class Docstring (Lines 34-50)

**BEFORE:**
```python
class Game:
    """
    Lớp quản lý một ván cờ tướng giữa hai bot/người chơi.
    
    Attributes:
        player1: Bot/Player thứ nhất (phe Đỏ)
        player2: Bot/Player thứ hai (phe Đen)
        board: Bàn cờ (Board object)
        moves: Danh sách các nước đi đã thực hiện
        game_status: Trạng thái ván cờ
        game_id: ID duy nhất của ván cờ
        pgn: Ngoại lệ cờ (PGN format)
    """
```

**AFTER:**
```python
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
```

**Changes:**
- ✅ Updated to reflect new `Winner` enum and `logger`
- ✅ Added `game_result_status` documentation
- ✅ Clarified RED/BLACK terminology

---

### 4. __init__ Method (Lines 52-80)

**BEFORE:**
```python
def __init__(self, player1, player2, board: Board, game_id: Optional[str] = None):
    """
    Khởi tạo một ván cờ.
    
    Args:
        player1: Bot/Player thứ nhất (phe Đỏ - sở hữu Tướng K)
        player2: Bot/Player thứ hai (phe Đen - sở hữu Tướng k)
        board: Board object
        game_id: ID ván cờ (tự sinh nếu không có)
    """
    self.player1 = player1
    self.player2 = player2
    self.board = board
    self.moves: List[Tuple[str, int, str]] = []  # (player_name, move_int, move_uci)
    self.game_status = GameStatus.Playing
    self.winner: Optional[str] = None
    self.pgn = ""
    self.game_id = game_id or datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
```

**AFTER:**
```python
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
```

**Changes:**
- ✅ Added `log_path` parameter for customizable logging directory
- ✅ Changed `winner` type from `Optional[str]` to `Optional[Winner]`
- ✅ Added `game_result_status` field to track how game ended
- ✅ Initialize logger in `__init__`

---

### 5. play() Method (Lines 82-149)

**MAJOR CHANGES:**

**BEFORE:**
```python
def play(self) -> str:
    """
    Chạy ván cờ đến khi kết thúc.
    
    Returns:
        game_id của ván cờ
    """
    current_player = self.player1
    other_player = self.player2
    move_count = 0
    max_moves = 1000

    while self.game_status == GameStatus.Playing and move_count < max_moves:
        # ... game loop ...
        
        # Kiểm tra trạng thái game
        self.game_status = check_game_status(self.board, legal_moves)
        if self.game_status != GameStatus.Playing:
            break

        # ... move getting and validation ...
        
        # Thực thi nước đi
        move_uci = move_to_uci(move)
        self.board.make_move(move)
        self.moves.append((current_player.name, move, move_uci))
        self._log_move(current_player.name, move_uci)

        # Đổi lượt
        current_player, other_player = other_player, current_player
        move_count += 1

    # Xác định người thắng cuối cùng
    self._determine_winner()
    
    # Xuất PGN
    self.pgn = self.export_pgn()
    self._save_pgn()
    
    return self.game_id
```

**AFTER:**
```python
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
    max_moves = 1000

    self.logger.info(f"Game started: {self.player1.name} (RED) vs {self.player2.name} (BLACK)")

    while self.game_status == GameStatus.Playing and move_count < max_moves:
        # ... game loop ...
        
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

        # ... move execution ...
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
```

**Changes:**
- ✅ Track `current_color` to properly determine winner
- ✅ Use logger instead of `_log_move()`
- ✅ Call `_determine_winner_from_status()` with correct logic
- ✅ Add `game_result_status` tracking for different end conditions
- ✅ Use `_set_winner()` for error handling
- ✅ Set `game_result_status = "draw"` for draws
- ✅ Log game start and end with clear messages

---

### 6. New Methods: _determine_winner_from_status() and _set_winner()

**NEW:**
```python
def _determine_winner_from_status(self, last_move_color: Color) -> None:
    """
    Xác định người thắng dựa trên game_status và màu của nước đi cuối cùng.
    ...
    """
    if self.game_status == GameStatus.RedWin:
        self.winner = Winner.RED
    elif self.game_status == GameStatus.BlueWin:
        self.winner = Winner.BLACK
    else:
        self.winner = Winner.DRAW

def _set_winner(self, winner: Winner) -> None:
    """
    Thiết lập người thắng.
    ...
    """
    self.winner = winner
    if winner == Winner.RED:
        self.game_status = GameStatus.RedWin
    elif winner == Winner.BLACK:
        self.game_status = GameStatus.BlueWin
    else:
        self.game_status = GameStatus.Draw
```

**Changes:**
- ✅ Properly determine winner from game status
- ✅ Explicit winner setting method for error cases

---

### 7. New Methods: resign() and timeout()

**NEW:**
```python
def resign(self, player_name: str) -> None:
    """
    Xử lý khi một người chơi bỏ cuộc.
    ...
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
    ...
    """
    if player_name == self.player1.name:
        self.winner = Winner.BLACK
    else:
        self.winner = Winner.RED
    
    self.game_status = GameStatus.BlueWin if self.winner == Winner.BLACK else GameStatus.RedWin
    self.game_result_status = "timeout"
    self.logger.info(f"{player_name} timeout. {self.winner.value} wins.")
```

**Changes:**
- ✅ Handle resignation and timeout scenarios
- ✅ Properly set winner and game_result_status
- ✅ Log the events

---

### 8. New Method: _init_logger()

**NEW:**
```python
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
    if not logger.handlers:
        logger.addHandler(fh)
        logger.addHandler(ch)
    
    return logger
```

**Changes:**
- ✅ Create logger with file and console handlers
- ✅ File logs saved to `log_path/{game_id}.log`
- ✅ Proper timestamp and format

---

### 9. Updated export_pgn() Method

**BEFORE:**
```python
def export_pgn(self) -> str:
    """
    Xuất ván cờ dưới định dạng PGN (Portable Game Notation).
    
    Returns:
        Chuỗi PGN
    """
    pgn_str = f"[Event \"AI Arena Game\"]\n"
    pgn_str += f"[Date \"{datetime.date.today()}\"]\n"
    pgn_str += f"[Player1 \"{self.player1.name}\"]\n"
    pgn_str += f"[Player2 \"{self.player2.name}\"]\n"
    pgn_str += f"[Result \"{self._get_pgn_result()}\"]\n"
    pgn_str += f"[GameID \"{self.game_id}\"]\n"
    pgn_str += "\n"

    # Thêm các nước đi
    for move_num, (name, move_int, move_uci) in enumerate(self.moves, 1):
        if move_num % 2 == 1:  # Nước lẻ
            pgn_str += f"{(move_num + 1) // 2}. {move_uci} "
        else:  # Nước chẵn
            pgn_str += f"{move_uci} "

    # Thêm kết quả
    pgn_str += f"\n{self._get_pgn_result()}\n"
    
    return pgn_str
```

**AFTER:**
```python
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
```

**Changes:**
- ✅ Added `[Termination]` tag to show how game ended
- ✅ Added `[Moves]` tag for total move count
- ✅ Added `[Winner]` tag to show winner
- ✅ Better formatting with newlines
- ✅ Extended comments for Chinese chess

---

### 10. Updated _get_pgn_result() Method

**BEFORE:**
```python
def _get_pgn_result(self) -> str:
    """Lấy kết quả ván cờ dưới dạng PGN."""
    if self.game_status == GameStatus.RedWin:
        return "1-0" if self.winner == self.player1.name else "0-1"
    elif self.game_status == GameStatus.BlueWin:
        return "0-1" if self.winner == self.player1.name else "1-0"
    else:
        return "1/2-1/2"
```

**AFTER:**
```python
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
```

**Changes:**
- ✅ Use `Winner` enum instead of game_status
- ✅ Simpler and clearer logic
- ✅ Return "*" for incomplete games

---

### 11. Updated _save_pgn() Method

**BEFORE:**
```python
def _save_pgn(self, path: Optional[str] = None) -> None:
    """
    Lưu PGN vào file.
    
    Args:
        path: Đường dẫn file (mặc định: logs/{game_id}.pgn)
    """
    filename = path or f"logs/{self.game_id}.pgn"
    
    # Tạo thư mục nếu chưa tồn tại
    os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else ".", exist_ok=True)
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self.pgn)
        self._log(f"PGN saved to {filename}")
    except Exception as e:
        self._log_error(f"Failed to save PGN: {e}")
```

**AFTER:**
```python
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
```

**Changes:**
- ✅ Use `log_path` parameter (defaults to `self.log_path`)
- ✅ Use logger instead of `_log()` and `_log_error()`
- ✅ Cleaner directory creation logic

---

### 12. Deprecated Methods (kept for backward compatibility)

**_determine_winner()** - Now deprecated, use `_determine_winner_from_status()` instead
**_log()** - Now deprecated, use `logger.info()` instead
**_log_move()** - Now deprecated, use `logger.info()` instead
**_log_error()** - Now deprecated, use `logger.error()` instead

---

### 13. Updated Demo Test (Lines 350-376)

**BEFORE:**
```python
if __name__ == "__main__":
    from ..bots.bot import NegmaxBot, RandomBot
    from ..core.board import Board

    # Tạo hai bot
    bot1 = NegmaxBot(depth=3)
    bot2 = RandomBot()
    
    # Khởi tạo bàn cờ
    board = Board()
    
    # Tạo ván cờ
    game = Game(bot1, bot2, board)
    
    # Chạy ván cờ
    game_id = game.play()
    print(f"Game {game_id} finished!")
    print(f"Winner: {game.winner}")
    print(f"Status: {game.game_status}")
```

**AFTER:**
```python
if __name__ == "__main__":
    # Note: Khi chạy trực tiếp file này, hãy chạy bằng:
    # python -m arena.game  (từ thư mục src)
    # Hoặc thêm đường dẫn project vào PYTHONPATH
    
    from bots.bot import NegmaxBot, RandomBot
    from core.board import Board

    # Tạo hai bot
    bot1 = NegmaxBot(depth=3, name="NegmaxBot-D3")
    bot2 = RandomBot(name="RandomBot")
    
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
```

**Changes:**
- ✅ Changed from relative to absolute imports
- ✅ Added bot names
- ✅ Added log_path parameter
- ✅ Added note about proper execution method
- ✅ Better output formatting
- ✅ Show `game_result_status`
- ✅ Show `winner.value` instead of just winner

---

## Summary Statistics

- **Total lines added:** ~250
- **Total lines removed:** ~50
- **New methods:** 4 (resign, timeout, _determine_winner_from_status, _set_winner, _init_logger)
- **Modified methods:** 5 (play, export_pgn, _get_pgn_result, _save_pgn, __init__)
- **New enums:** 1 (Winner)
- **Deprecated methods:** 4 (kept for compatibility)
- **New features:** Logging, timeout handling, resignation, custom log paths
- **Bug fixes:** Winner determination logic, import issues
