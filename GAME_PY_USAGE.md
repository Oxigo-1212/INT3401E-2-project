# game.py Usage Guide

## Basic Setup

### 1. Simple Game Between Two Bots

```python
from src.arena.game import Game, Winner
from src.core.board import Board
from src.bots.bot import NegmaxBot, RandomBot

# Create bots (assuming they have a 'name' attribute)
red_bot = NegmaxBot(depth=4, name="NegmaxBot-D4")
black_bot = RandomBot(name="RandomBot")

# Create board and game
board = Board()
game = Game(red_bot, black_bot, board)

# Play the game
game_id = game.play()

# Access results
print(f"Winner: {game.winner.value}")  # 'Red', 'Black', or 'Draw'
print(f"Total moves: {len(game.moves)}")
```

### 2. Custom Log Path

```python
game = Game(
    red_bot, 
    black_bot, 
    board, 
    log_path="my_games"  # Logs saved to my_games/{game_id}.log and my_games/{game_id}.pgn
)
```

### 3. Custom Game ID

```python
game = Game(
    red_bot, 
    black_bot, 
    board, 
    game_id="friendly_match_001"  # Custom identifier
)
```

## Advanced Usage

### 4. Handling Resignation

```python
game = Game(red_bot, black_bot, board)

# During game, if a bot wants to resign:
game.resign(red_bot.name)  # Black wins

# After resignation, game.winner == Winner.BLACK
# game.game_result_status == 'resign'
```

### 5. Handling Timeout

```python
# If a bot exceeds its time limit:
game.timeout(black_bot.name)  # Red wins

# After timeout:
# game.winner == Winner.RED
# game.game_result_status == 'timeout'
```

### 6. Accessing Game Logs

```python
game = Game(red_bot, black_bot, board, log_path="logs")
game.play()

# Logger instance
print(game.logger.handlers)  # Shows file and console handlers
# File logs saved to: logs/{game_id}.log
# PGN saved to: logs/{game_id}.pgn
```

## Understanding Results

### Game Status vs Winner

```python
# game.game_status: GameStatus enum
# - Playing: Game still ongoing
# - RedWin: Red (player1) won
# - BlueWin: Black (player2) won  [Note: BlueWin in enum, but Winner.BLACK]
# - Draw: Game ended in draw

# game.winner: Winner enum
# - Winner.RED
# - Winner.BLACK
# - Winner.DRAW

# game.game_result_status: String describing how game ended
# - 'checkmate': Normal checkmate
# - 'resign': Player resigned
# - 'timeout': Player ran out of time
# - 'draw': Draw by agreement/rules
# - 'illegal_move': Invalid move attempted
# - 'error': Exception during move generation
```

### Examining Moves

```python
# game.moves is a list of tuples: (player_name, move_int, move_uci)
for i, (name, move_int, move_uci) in enumerate(game.moves):
    print(f"Move {i+1}: {name} played {move_uci}")

# Total moves
print(f"Game lasted {len(game.moves)} moves")
```

## PGN Format

The exported PGN includes:

```
[Event "AI Arena Game"]
[Date "2024-05-15"]
[Player1 "NegmaxBot-D4"]
[Player2 "RandomBot"]
[Result "1-0"]                    # 1-0 = Red wins, 0-1 = Black wins, 1/2-1/2 = Draw
[GameID "20240515143022123456"]
[Termination "checkmate"]         # How game ended
[Moves "47"]                       # Total number of moves
[Winner "Red"]                     # Winner color

1. e3e5 e7e6
2. a4a5 h10h9
...
1-0
```

## Testing & Debugging

### 1. Direct Execution (for testing)

```bash
# From the INT3401E-2-project directory:
cd src
python -m arena.game
```

Note: Don't run `python arena/game.py` directly due to import issues.

### 2. Checking Logs

After running a game, check the log files:

```bash
# View game log
cat logs/{game_id}.log

# View PGN
cat logs/{game_id}.pgn
```

### 3. Game Flow Debugging

The logger provides detailed information:
- Each move with move number, player name, and color
- Error messages if invalid moves occur
- Game start and end status
- Final winner and game result status

## Common Issues & Solutions

### Issue 1: ImportError when running directly
**Solution:** Use `python -m arena.game` instead of `python arena/game.py`
The code now has a fallback for direct execution, but package execution is recommended.

### Issue 2: Winner is different than expected
**Solution:** Check `game.game_result_status`
- If 'error' or 'illegal_move', the current player lost
- If 'resign' or 'timeout', the named player lost
- If 'checkmate', the last player to move won

### Issue 3: PGN not saving
**Solution:** Check that the log_path directory exists and is writable
```python
game = Game(red_bot, black_bot, board, log_path="./output_logs")
```

## Best Practices

1. **Always provide bot names**
   ```python
   bot1 = NegmaxBot(depth=4, name="Negamax-4")  # ✓ Good
   bot2 = RandomBot(name="Random")
   ```

2. **Use Winner enum, not game_status**
   ```python
   if game.winner == Winner.RED:  # ✓ Good
       print("Red wins")
   
   if game.game_status == GameStatus.RedWin:  # ✗ Confusing
       print("Red wins")
   ```

3. **Check game_result_status for details**
   ```python
   print(game.game_result_status)  # Better insight than just winner
   ```

4. **Use custom log paths for organization**
   ```python
   game = Game(bot1, bot2, board, log_path="tournament_logs")
   ```

5. **Save game history**
   ```python
   # PGN is automatically saved
   # Access it anytime
   with open(f"archive/{game.game_id}.pgn", "w") as f:
       f.write(game.pgn)
   ```

## Example: Tournament

```python
from src.arena.game import Game, Winner
from src.core.board import Board
from src.bots.bot import NegmaxBot, RandomBot

results = []

for match_num in range(5):
    bot1 = NegmaxBot(depth=3, name="Negamax-3")
    bot2 = RandomBot(name="Random")
    
    game = Game(
        bot1, bot2, board,
        game_id=f"tournament_match_{match_num:02d}",
        log_path="tournament_logs"
    )
    
    game.play()
    
    results.append({
        'match': match_num,
        'winner': game.winner.value,
        'moves': len(game.moves),
        'status': game.game_result_status
    })

# Print tournament results
for r in results:
    print(f"Match {r['match']}: {r['winner']} wins in {r['moves']} moves ({r['status']})")
```
