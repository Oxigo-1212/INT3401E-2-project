"""Entry point: cấu hình trận đấu trên Terminal và chạy GUI Pygame song song."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from arena.game import Game, GameResultStatus, Winner
from bots.bot import BotManager
from bots.engine.transposition_table import TT_TABLE, init_tt
from core.board import Board
from core.board_renderer import BoardRenderer
from core.logger import get_logger, init_logging
from core.pieces import Color
from gui.pygame_viewer import HumanPlayer, PygameXiangqiController

_log = get_logger("main")


@dataclass
class MatchConfig:
    mode: str  # "human_vs_bot" | "bot_vs_bot"
    human_color: Optional[Color]
    red_bot_type: Optional[str]
    black_bot_type: Optional[str]
    red_depth: Optional[int]
    black_depth: Optional[int]


def safe_input(prompt: str) -> Optional[str]:
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        return None


def log_time(player_name: str, time_taken: float) -> None:
    with open("time_log.txt", "a", encoding="utf-8") as f:
        f.write(f"[{player_name}] Thoi gian suy nghi: {time_taken:.2f}s\\n")


def ask_depth(bot_type: str, default_depth: int = 3) -> Optional[int]:
    if bot_type != "negamax":
        return None

    value = safe_input(f"Nhap depth cho {bot_type} (Enter={default_depth}): ")
    if value is None or value == "":
        return default_depth

    if value.isdigit() and int(value) > 0:
        return int(value)

    print("Depth khong hop le, dung gia tri mac dinh.")
    return default_depth


def choose_bot(label: str) -> tuple[str, Optional[int]]:
    bot_options = ["negamax", "random", "greedy"]
    print(f"\nChon bot cho {label}:")
    for idx, name in enumerate(bot_options, start=1):
        print(f"{idx}. {name}")

    raw = safe_input("Lua chon (1-3, Enter=negamax): ")
    if raw is None or raw == "":
        bot_type = "negamax"
    elif raw.isdigit() and 1 <= int(raw) <= len(bot_options):
        bot_type = bot_options[int(raw) - 1]
    elif raw.lower() in bot_options:
        bot_type = raw.lower()
    else:
        print("Lua chon khong hop le, mac dinh negamax.")
        bot_type = "negamax"

    depth = ask_depth(bot_type, default_depth=3)
    return bot_type, depth


def configure_match() -> Optional[MatchConfig]:
    print("=== CO TUONG ENGINE + PYGAME GUI ===")
    print("1. Nguoi vs Bot")
    print("2. Bot vs Bot")

    mode_choice = safe_input("Chon che do (1-2): ")
    if mode_choice is None:
        return None

    if mode_choice == "1":
        bot_type, bot_depth = choose_bot("phe Bot")
        side_choice = safe_input("Ban muon choi phe nao? (1=Do, 2=Den): ")
        if side_choice is None:
            return None
        human_color = Color.RED if side_choice != "2" else Color.BLACK

        if human_color == Color.RED:
            return MatchConfig(
                mode="human_vs_bot",
                human_color=human_color,
                red_bot_type=None,
                black_bot_type=bot_type,
                red_depth=None,
                black_depth=bot_depth,
            )

        return MatchConfig(
            mode="human_vs_bot",
            human_color=human_color,
            red_bot_type=bot_type,
            black_bot_type=None,
            red_depth=bot_depth,
            black_depth=None,
        )

    if mode_choice == "2":
        red_bot_type, red_depth = choose_bot("Do")
        black_bot_type, black_depth = choose_bot("Den")
        return MatchConfig(
            mode="bot_vs_bot",
            human_color=None,
            red_bot_type=red_bot_type,
            black_bot_type=black_bot_type,
            red_depth=red_depth,
            black_depth=black_depth,
        )

    print("Lua chon khong hop le.")
    return None


def _create_bot(bot_type: str, depth: Optional[int]):
    kwargs = {}
    if depth is not None:
        kwargs["depth"] = depth
    bot = BotManager.create_bot(bot_type, **kwargs)
    bot.name = bot.get_name()
    return bot


def run_match_gui(config: MatchConfig) -> None:
    board = Board()
    renderer = BoardRenderer(board)

    if config.mode == "human_vs_bot":
        human = HumanPlayer("Human_RED" if config.human_color == Color.RED else "Human_BLACK")

        if config.human_color == Color.RED:
            bot = _create_bot(config.black_bot_type or "negamax", config.black_depth)
            red_entity = human
            black_entity = bot
        else:
            bot = _create_bot(config.red_bot_type or "negamax", config.red_depth)
            red_entity = bot
            black_entity = human
    else:
        red_entity = _create_bot(config.red_bot_type or "negamax", config.red_depth)
        black_entity = _create_bot(config.black_bot_type or "greedy", config.black_depth)
        red_entity.name = f"{red_entity.name}_Red"
        black_entity.name = f"{black_entity.name}_Black"

    game = Game(red_entity, black_entity, board)
    game.logger._configure_handlers(console=True)
    game.logger.log_game_start(game.game_id, red_entity.name, black_entity.name)

    try:
        renderer.print_board()
        controller = PygameXiangqiController(
            board=board,
            game=game,
            renderer=renderer,
            red_entity=red_entity,
            black_entity=black_entity,
            human_color=config.human_color,
            fps=60,
        )
        controller.run()
    except KeyboardInterrupt:
        game.game_result_status = GameResultStatus.ERROR
        game._set_winner(Winner.DRAW)
    finally:
        # Nếu đóng GUI khi ván chưa kết thúc, đánh dấu hòa kỹ thuật.
        if game.game_result_status == GameResultStatus.PLAYING:
            game.game_result_status = GameResultStatus.DRAW
            if game.winner is None:
                game._set_winner(Winner.DRAW)
            game.logger.log_game_end(game.game_id, winner=game.winner.value if game.winner else "None", reason=game.game_result_status.value)

        game.pgn = game.export_pgn()
        game._save_pgn()

        _log.info("--- TONG KET VAN CO (%s) ---", game.game_id)
        _log.info("Tong so nuoc di: %d", len(game.moves))
        _log.info("Nguoi thang: %s", game.winner.value if game.winner else "Unknown")
        _log.info("Ket thuc: %s", game.game_result_status.value)


def main() -> None:
    with open("time_log.txt", "w", encoding="utf-8") as f:
        f.write("")

    init_logging()
    init_tt(1 << 20, TT_TABLE)

    config = configure_match()
    if config is None:
        print("Thoat.")
        return

    run_match_gui(config)


if __name__ == "__main__":
    main()
