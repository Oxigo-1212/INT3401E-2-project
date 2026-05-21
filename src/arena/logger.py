"""Tiện ích ghi log cho AI Arena.

Module này giữ nguyên API `Logger` cũ nhưng hiện thực bằng package
`logging` của Python để đồng bộ với phần còn lại của project.
"""

from __future__ import annotations

import datetime
import logging
from pathlib import Path
from typing import Optional


class Logger:
    """Logger ghi vào file cho các sự kiện game, nước đi, lỗi và thống kê.

    Lớp này được giữ nhẹ, đơn giản và tương thích ngược với API ghi text
    trước đây đang dùng trong project.
    """

    def __init__(
        self,
        log_dir: str | Path = "logs",
        game_id: Optional[str] = None,
        log_file: Optional[str | Path] = None,
        level: int = logging.DEBUG,
        console: bool = False,
    ):
        self.log_dir = Path(log_dir)
        self.game_id = game_id
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.level = level

        if log_file is not None:
            self.log_file = Path(log_file)
        elif game_id:
            self.log_file = self.log_dir / f"{game_id}.log"
        else:
            self.log_file = self.log_dir / f"log_{datetime.datetime.now().strftime('%Y%m%d')}.log"

        self.log_file = self.log_file.expanduser().resolve()

        logger_name = f"arena.logger.{self.log_file.as_posix()}"
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(self.level)
        self._logger.propagate = False

        self._configure_handlers(console=console)

    def log_game_start(self, game_id, player1, player2):
        self._logger.info(
            "=== Game %s start === | Red: %s | Black: %s",
            game_id,
            player1,
            player2,
        )

    def log_move(self, game_id, move_num, player_name, move_uci):
        self._logger.info(
            "[GAME %s] Move %s: %s -> %s",
            game_id,
            move_num,
            player_name,
            move_uci,
        )

    def log_game_end(self, game_id, winner, reason=None):
        if reason:
            self._logger.info(
                "=== Game %s end === | Winner: %s | Reason: %s",
                game_id,
                winner,
                reason,
            )
        else:
            self._logger.info("=== Game %s end === | Winner: %s", game_id, winner)

    def log_error(self, game_id, player_name, error):
        self._logger.error("[GAME %s] %s: %s", game_id, player_name, error)

    def log_statistic(self, stat_content):
        self._logger.info("[STAT] %s", stat_content)

    def info(self, message: str, *args) -> None:
        self._logger.info(message, *args)

    def warning(self, message: str, *args) -> None:
        self._logger.warning(message, *args)

    def error(self, message: str, *args) -> None:
        self._logger.error(message, *args)

    def debug(self, message: str, *args) -> None:
        self._logger.debug(message, *args)

    def _configure_handlers(self, console: bool) -> None:
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        file_handler = self._find_file_handler()
        if file_handler is None:
            file_handler = logging.FileHandler(self.log_file, encoding="utf-8")
            file_handler._arena_log_path = self.log_file  # type: ignore[attr-defined]
            self._logger.addHandler(file_handler)

        file_handler.setLevel(self.level)
        file_handler.setFormatter(formatter)

        if console:
            stream_handler = self._find_stream_handler()
            if stream_handler is None:
                stream_handler = logging.StreamHandler()
                stream_handler._arena_console_handler = True  # type: ignore[attr-defined]
                self._logger.addHandler(stream_handler)

            stream_handler.setLevel(max(logging.INFO, self.level))
            stream_handler.setFormatter(formatter)

    def _find_file_handler(self) -> Optional[logging.FileHandler]:
        for handler in self._logger.handlers:
            if isinstance(handler, logging.FileHandler) and getattr(handler, "_arena_log_path", None) == self.log_file:
                return handler
        return None

    def _find_stream_handler(self) -> Optional[logging.StreamHandler]:
        for handler in self._logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                if getattr(handler, "_arena_console_handler", False):
                    return handler
        return None


# Alias tương thích ngược.
ArenaLogger = Logger


if __name__ == "__main__":
    logger = Logger(game_id="202605152301", console=True)
    logger.log_game_start("202605152301", "BotA", "BotB")
    logger.log_move("202605152301", 1, "BotA", "e2e4")
    logger.log_move("202605152301", 2, "BotB", "e7e5")
    logger.log_error("202605152301", "BotB", "Timeout")
    logger.log_game_end("202605152301", "BotA", reason="Opponent timeout")
    logger.log_statistic("Total games: 10, Win rate: 60% BotA / 40% BotB")
