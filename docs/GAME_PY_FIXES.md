# game.py - Fixes and Improvements

## Issues Fixed

### 1. **Relative Import Issue** ✅
**Problem:** Using `from ..core.board import Board` causes error when running directly as `python arena/game.py`

**Solution:** 
- Added try/except block for import handling
- Fallback to absolute imports by adjusting `sys.path` if relative import fails
- Now supports both package execution (`python -m arena.game`) and direct execution

```python
try:
    from ..core.board import Board
    # ... other relative imports
except ImportError:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from core.board import Board
    # ... absolute imports
```

### 2. **Winner Logic Fixed** ✅
**Problem:** The old `_determine_winner()` method incorrectly checked `self.board.side_to_move` which might not reflect actual winner

**Solution:**
- Created new `Winner` enum with values: `RED`, `BLACK`, `DRAW`
- Winner is now determined by color, NOT bot name (avoids confusion when bots are swapped)
- New method `_determine_winner_from_status()` properly determines winner based on last move color
- Added `_set_winner()` for explicit winner setting in error/resignation cases

```python
class Winner(Enum):
    RED = "Red"
    BLACK = "Black"
    DRAW = "Draw"
```

### 3. **Logging System Upgraded** ✅
**Problem:** Used basic print statements, not suitable for detailed logging

**Solution:**
- Integrated Python's `logging` module
- Each game has its own logger with file + console handlers
- Logs saved to: `logs/{game_id}.log`
- Supports DEBUG level in file, INFO level in console
- Proper timestamp and formatting

### 4. **Enhanced PGN Export** ✅
**Problem:** PGN format was minimal, missing game metadata

**Solution:**
- Added Chinese chess-specific tags:
  - `[Termination]`: Game ending type (checkmate, resign, timeout, draw, etc.)
  - `[Moves]`: Total number of moves
  - `[Winner]`: Winner color
- Better formatting with proper move numbering
- Supports standard PGN result format: "1-0" (Red wins), "0-1" (Black wins), "1/2-1/2" (Draw)

### 5. **New Features Added** ✅

#### Timeout Handling
```python
def timeout(self, player_name: str) -> None:
    """Handle when a player runs out of time"""
```

#### Resignation Support
```python
def resign(self, player_name: str) -> None:
    """Handle when a player resigns"""
```

#### Customizable Log Path
```python
def __init__(self, player1, player2, board, game_id=None, log_path=None):
    self.log_path = log_path or "logs"
```

#### Game Result Status Tracking
```python
self.game_result_status: str  # 'checkmate', 'resign', 'timeout', 'draw', 'illegal_move', 'error'
```

## Summary of Changes

| Aspect | Before | After |
|--------|--------|-------|
| **Imports** | Simple relative imports (fails directly) | Try/except with fallback to absolute |
| **Winner** | Bot name string (confusing) | Winner enum (RED/BLACK/DRAW) |
| **Logger** | Print statements | Python logging module |
| **PGN** | Minimal format | Extended with metadata |
| **Game Status** | Basic GameStatus enum | + game_result_status field |
| **Error Handling** | Simple exception handling | Proper winner determination on errors |
| **Features** | None | Timeout, Resign, custom log path |

## Usage Examples

```python
from arena.game import Game
from core.board import Board
from bots.bot import NegmaxBot, RandomBot

# Create bots
bot1 = NegmaxBot(depth=4, name="NegmaxBot-D4")
bot2 = RandomBot(name="RandomBot")

# Create game with custom log path
board = Board()
game = Game(bot1, bot2, board, log_path="custom_logs")

# Play the game
game_id = game.play()

# Access results
print(game.winner)  # Winner.RED, Winner.BLACK, or Winner.DRAW
print(game.game_result_status)  # 'checkmate', 'resign', 'timeout', etc.
print(game.pgn)  # Full PGN with metadata

# Handle resignation/timeout during game
game.resign("RandomBot")  # BlackBot wins
game.timeout("NegmaxBot-D4")  # BlackBot wins due to timeout
```

## Backward Compatibility

- Old `_log()`, `_log_move()`, `_log_error()` methods kept (deprecated) for backward compatibility
- Old `_determine_winner()` method kept (deprecated)
- New logger methods are primary interface

## Future Enhancements

- [ ] Add FEN export alongside PGN
- [ ] Add move timing information to logs
- [ ] Add tournament mode with multiple games
- [ ] Add performance statistics (nodes/sec, evaluation depth, etc.)
- [ ] Export to different formats (JSON, SQLite, etc.)
