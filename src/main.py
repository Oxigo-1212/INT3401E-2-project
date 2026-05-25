"""Entry point của game cờ tướng."""

from __future__ import annotations

from arena.game import Game, GameResultStatus, Winner
import sys
from bots.engine.transposition_table import TT_TABLE, init_tt
from core.board import Board
from core.board_renderer import BoardRenderer
from core.logger import get_logger, init_logging
from core.move import move_to_uci
from core.move_generator import MoveGenerator
from core.pieces import Color
from core.rules import GameStatus, check_game_status, get_legal_moves
from match_ui import MatchConfig, build_entities, configure_match, run_gui_game

_log = get_logger("main")


def _finalize_game(game: Game) -> None:
    if game.game_result_status == GameResultStatus.PLAYING:
        game.game_result_status = GameResultStatus.DRAW
        if game.winner is None:
            game._set_winner(Winner.DRAW)
        game.logger.log_game_end(
            game.game_id,
            winner=game.winner.value if game.winner else "None",
            reason=game.game_result_status.value,
        )

    game.pgn = game.export_pgn()
    game._save_pgn()

    _log.info("--- TONG KET VAN CO (%s) ---", game.game_id)
    _log.info("Tong so nuoc di: %d", len(game.moves))
    _log.info("Nguoi thang: %s", game.winner.value if game.winner else "Unknown")
    _log.info("Ket thuc: %s", game.game_result_status.value)


def run_match_cli(config: MatchConfig) -> None:
    board = Board()
    renderer = BoardRenderer(board)

    red_entity, black_entity = build_entities(config)

    game = Game(red_entity, black_entity, board)
    game.logger._configure_handlers(console=True)
    game.logger.log_game_start(game.game_id, red_entity.name, black_entity.name)

    try:
        while True:
            renderer.print_board()

            legal_moves = get_legal_moves(board, MoveGenerator(board))
            status = check_game_status(board, legal_moves)
            if status != GameStatus.Playing:
                if status == GameStatus.Draw:
                    game._set_winner(Winner.DRAW)
                    game.game_result_status = GameResultStatus.DRAW
                elif status == GameStatus.RedWin:
                    game._set_winner(Winner.RED)
                    game.game_result_status = GameResultStatus.CHECKMATE
                else:
                    game._set_winner(Winner.BLACK)
                    game.game_result_status = GameResultStatus.CHECKMATE

                game.logger.log_game_end(
                    game.game_id,
                    winner=game.winner.value if game.winner else "None",
                    reason=game.game_result_status.value,
                )
                break

            current_player = red_entity if board.side_to_move == Color.RED else black_entity
            move = current_player.get_move(board)
            if move is None:
                game.resign(current_player.name)
                break

            if move not in legal_moves:
                game.logger.log_error(game.game_id, current_player.name, f"Illegal move: {move_to_uci(move)}")
                game.resign(current_player.name)
                break

            board.make_move(move)
            move_uci = move_to_uci(move)
            game.moves.append((current_player.name, move, move_uci))
            game.logger.log_move(game.game_id, len(game.moves), current_player.name, move_uci)

    except KeyboardInterrupt:
        game.game_result_status = GameResultStatus.ERROR
        game._set_winner(Winner.DRAW)
    finally:
        _finalize_game(game)


def run_game_app() -> None:
    with open("time_log.txt", "w", encoding="utf-8") as f:
        f.write("")

    init_logging()
    # Ensure stdout/stderr can emit Unicode on Windows consoles that default
    # to a legacy encoding (prevents UnicodeEncodeError when printing Vietnamese/Unicode).
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        # reconfigure may not be available in some embeded IO wrappers; ignore if it fails
        pass
    init_tt(1 << 20, TT_TABLE)

    config = configure_match()
    if config is None:
        print("Thoat.")
        return

    if config.display_mode == "cli":
        run_match_cli(config)
    else:
        board = Board()
        renderer = BoardRenderer(board)
        red_entity, black_entity = build_entities(config)
        game = Game(red_entity, black_entity, board)
        game.logger._configure_handlers(console=True)
        game.logger.log_game_start(game.game_id, red_entity.name, black_entity.name)
        try:
            run_gui_game(config, game, board, renderer, red_entity, black_entity)
        except KeyboardInterrupt:
            game.game_result_status = GameResultStatus.ERROR
            game._set_winner(Winner.DRAW)
        finally:
            _finalize_game(game)


if __name__ == "__main__":
    run_game_app()
