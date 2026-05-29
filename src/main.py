"""Entry point của game cờ tướng."""

from __future__ import annotations

from arena.game import Game, GameResultStatus, Winner
import sys
from bots.engine.transposition_table import TT_TABLE, init_tt
from core.board import Board
from typing import Optional
import argparse
from benchmark.cli import run_benchmark
from benchmark.xiangqi_perft_positions import POSITIONS

from core.board import Board
from bots.engine.transposition_table import init_tt, TT_TABLE, clear_tt
from ucci.adapter import GoParams, SearchFacade
from core.board_renderer import BoardRenderer
from core.logger import get_logger, init_logging
from core.move import move_to_uci
from core.move_generator import MoveGenerator
from core.pieces import Color
from core.rules import GameStatus, check_game_status, get_legal_moves
from match_ui import MatchConfig, build_entities, configure_match, run_gui_game
from core.move import deserialize_move as uci_to_move, serialize_move as move_to_uci
from core.rules import check_game_status, get_legal_moves, is_in_check, GameStatus, Color
from core.utils import move_to_str
from bots.bot import BotManager
from colorama import init
import time 
from core.logger import init_logging, get_logger

# Import thêm Game và các Enum liên quan từ arena.game
from arena.game import Game, Winner, GameResultStatus

init()

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


def run_search_benchmark() -> None:
    facade = SearchFacade()
    for fen, depth, expected in POSITIONS:
        board = Board()
        board.set_fen(fen)
        clear_tt(TT_TABLE)
        result = facade.search(board, GoParams(depth=depth))
        print(f"bench depth: {depth} nodes: {result.nodes} expected: {expected} time: {result.time_ms / 1000:.3f} sec")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cờ tướng engine")
    parser.add_argument(
        "-p",
        "--perft",
        action="store_true",
        help="Run perft benchmark",
    )
    parser.add_argument(
        "--bench",
        action="store_true",
        help="Run search benchmark",
    )
    parser.add_argument(
        "--uci",
        "--ucci",
        dest="ucci",
        action="store_true",
        help="Run UCCI front-end",
    )
    args, remaining = parser.parse_known_args()

    if args.ucci:
        from ucci import run_ucci

        # Check remaining arguments for debug flag
        debug_mode = False
        for arg in remaining:
            arg_lower = arg.lower()
            if arg_lower in ("--debug", "-d", "debug", "debug=true", "debug=on", "debug=1"):
                debug_mode = True
                break

        init_logging(debug=debug_mode)
        run_ucci()
        return

    if args.bench:
        try:
            run_search_benchmark()
        except KeyboardInterrupt:
            return
        return
    if args.perft:
        try:
            run_benchmark()
        except KeyboardInterrupt:
            return
        return

    # Xóa file log cũ trước khi bắt đầu trận mới
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
    main()
