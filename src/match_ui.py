"""Menu cấu hình và phần dựng GUI cho trận đấu."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from arena.game import Game
from bots.bot import BotManager
from core.board import Board
from core.board_renderer import BoardRenderer
from core.pieces import Color
from gui.pygame_viewer import HumanPlayer, PygameXiangqiController


@dataclass
class MatchConfig:
    display_mode: str  # "gui" | "cli"
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


def choose_display_mode() -> Optional[str]:
    print("\nChon kieu hien thi:")
    print("1. GUI")
    print("2. CLI")

    raw = safe_input("Lua chon (1-2, Enter=GUI): ")
    if raw is None or raw == "" or raw == "1":
        return "gui"
    if raw == "2":
        return "cli"

    print("Lua chon khong hop le, mac dinh GUI.")
    return "gui"


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
    display_mode = choose_display_mode()
    if display_mode is None:
        return None

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
            return MatchConfig(display_mode, "human_vs_bot", human_color, None, bot_type, None, bot_depth)

        return MatchConfig(display_mode, "human_vs_bot", human_color, bot_type, None, bot_depth, None)

    if mode_choice == "2":
        red_bot_type, red_depth = choose_bot("Do")
        black_bot_type, black_depth = choose_bot("Den")
        return MatchConfig(display_mode, "bot_vs_bot", None, red_bot_type, black_bot_type, red_depth, black_depth)

    print("Lua chon khong hop le.")
    return None


def create_bot(bot_type: str, depth: Optional[int]):
    kwargs = {}
    if depth is not None:
        kwargs["depth"] = depth
    bot = BotManager.create_bot(bot_type, **kwargs)
    bot.name = bot.get_name()
    return bot


def build_entities(config: MatchConfig):
    if config.mode == "human_vs_bot":
        human = HumanPlayer("Human_RED" if config.human_color == Color.RED else "Human_BLACK")

        if config.human_color == Color.RED:
            bot = create_bot(config.black_bot_type or "negamax", config.black_depth)
            return human, bot

        bot = create_bot(config.red_bot_type or "negamax", config.red_depth)
        return bot, human

    red_entity = create_bot(config.red_bot_type or "negamax", config.red_depth)
    black_entity = create_bot(config.black_bot_type or "greedy", config.black_depth)
    red_entity.name = f"{red_entity.name}_Red"
    black_entity.name = f"{black_entity.name}_Black"
    return red_entity, black_entity


def run_gui_game(config: MatchConfig, game: Game, board: Board, renderer: BoardRenderer, red_entity, black_entity) -> None:
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
