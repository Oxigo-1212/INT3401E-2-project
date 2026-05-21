# Game Refactor Requirements

## Overview

Refactor the bot-vs-bot game flow into a clearer separation between game state, game outcome, and game execution. Logging should be file-based only when debugging is enabled or when a failure occurs.

## Scope

- Game flow in `arena/game.py`
- Logging behavior in `arena/logger.py`
- Bot-vs-bot entry point in `main.py`

## Requirements

### 1. Logging behavior

- Normal play should not create a log file unless debugging is enabled.
- Failures should always produce a log file with error details.
- Existing logging behavior should remain available during gameplay.

### 2. Separate game state from execution

- Game state should be represented independently from the loop that runs the game.
- State should include the board, move history, turn information, move count, and current status.
- This state should not perform logging, file I/O, or game-loop decisions.

### 3. Represent game outcomes explicitly

- Game execution should return a clear final result.
- The result should capture the winner or draw, the final status, the move count, the full move history, the exported record of the game, and any error details when applicable.

### 4. Centralize game execution

- The bot-vs-bot loop should live in one place.
- Each turn should: check game status, request a move, validate it, apply it, and advance play.
- The game should stop for normal completion, illegal moves, bot failures, or when the maximum move limit is reached.
- Failures should trigger logging even when debugging is off.

### 5. Simplify the entry point

- The bot-vs-bot should be hide in within a class or a method.
- Human-vs-bot play is out of scope.

### 6. Remove replaced behavior

- Once the new flow is verified, remove the old game implementation and unused references to it.

## Build Order

| Step | What | Depends On |
|------|------|------------|
| 1 | Extract pure game state | None |
| 2 | Define a structured game result | Step 1 |
| 3 | Make logging file output conditional | None |
| 4 | Centralize game execution | Steps 1, 2, 3 |
| 5 | Connect execution to logging rules | Step 4 |
| 6 | Redirect the bot-vs-bot entry point | Steps 4, 5 |
| 7 | Remove the old game flow | Step 6 |

## Key Contracts

```
Game state: board, moves, turn, move count, status
Game result: winner/draw, status, move count, moves, export, error details
Game execution returns a game result
Logging stays silent in normal mode and records failures when needed
```

## Tests Required

| # | Component | Scenario | Expected |
|---|-----------|----------|----------|
| 1 | Logging | Debug is off and play is normal | No log file |
| 2 | Logging | Debug is off and a failure occurs | Log file with error details |
| 3 | Logging | Debug is on and play is normal | Log file with full game record |
| 4 | Game execution | Two bots complete a normal game | Final result includes a winner and moves |
| 5 | Game execution | A bot makes an illegal move | Final result reports an illegal move and the opponent wins |
| 6 | Game execution | A bot fails while choosing a move | Final result reports an error and includes the error message |
| 7 | Game execution | The move limit is reached | Final result is a draw |

## Existing Code References

- `arena/game.py` — current game flow
- `arena/logger.py` — current logging behavior
- `main.py` — bot-vs-bot entry point
- `bots/bot.py` — bot interface
- `core/board.py` — board model
- `core/rules.py` — status and legal-move logic
- `core/move_generator.py` — move generation
- `core/move.py` — move formatting
- `core/pieces.py` — color definitions
