from __future__ import annotations

import copy
import queue
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import pygame
except ModuleNotFoundError:
    import pygame_ce as pygame  # type: ignore

from arena.game import Game, GameResultStatus, Winner
from bots.bot import Bot
from core.board import Board
from core.board_renderer import BoardRenderer
from core.move import get_from_sq, get_to_sq, move_to_uci, uci_to_move
from core.move_generator import MoveGenerator
from core.pieces import CHINESE_PIECES, Color, is_black, is_red
from core.rules import GameStatus, check_game_status, get_legal_moves


@dataclass
class MatchParticipants:
    red_name: str
    black_name: str


class PygameXiangqiController:
    """GUI/controller phản chiếu trực tiếp trạng thái Board và điều phối bot worker thread."""

    GRID_COLS = 9
    GRID_ROWS = 10

    BG_COLOR = (186, 142, 92)
    BG_DARK = (130, 89, 50)
    BG_LIGHT = (214, 175, 121)
    PANEL_COLOR = (235, 211, 168)
    LINE_COLOR = (77, 51, 22)
    GRID_FADE = (120, 84, 48)
    RED_COLOR = (205, 52, 45)
    BLACK_COLOR = (54, 54, 54)
    PIECE_FILL = (247, 233, 202)
    PIECE_EDGE = (111, 72, 31)
    PIECE_SHADOW = (74, 48, 24, 90)
    HINT_WHITE = (255, 255, 255, 135)
    TAG_BG = (33, 33, 33)
    TAG_TEXT = (245, 245, 245)

    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    ASSET_BOARD = PROJECT_ROOT / "assets" / "table_chess.png"
    LOCAL_FONT_REGULAR = PROJECT_ROOT / "arial unicode ms.otf"
    LOCAL_FONT_BOLD = PROJECT_ROOT / "arial unicode ms bold.otf"

    def __init__(
        self,
        board: Board,
        game: Game,
        renderer: BoardRenderer,
        red_entity,
        black_entity,
        human_color: Optional[Color],
        fps: int = 60,
    ) -> None:
        self.board = board
        self.game = game
        self.renderer = renderer
        self.red_entity = red_entity
        self.black_entity = black_entity
        self.human_color = human_color
        self.participants = MatchParticipants(red_name=red_entity.name, black_name=black_entity.name)

        self.max_moves = 200
        self.move_count = 0
        self.fps = fps
        self.clock = pygame.time.Clock()

        self.selected_sq: Optional[int] = None
        self.selected_moves: list[int] = []

        self.bot_queue: queue.Queue[dict] = queue.Queue()
        self.bot_worker: Optional[threading.Thread] = None
        self.bot_worker_active = False

        pygame.init()
        pygame.display.set_caption("Xiangqi GUI Viewer")

        self.board_source_surface = pygame.image.load(str(self.ASSET_BOARD))
        self.board_grid_xs, self.board_grid_ys = self._detect_grid_lines(self.board_source_surface)
        source_board_w, source_board_h = self.board_source_surface.get_size()
        self.board_scale = 1.08
        self.board_w = int(round(source_board_w * self.board_scale))
        self.board_h = int(round(source_board_h * self.board_scale))
        self.grid_step_x = self._average_step(self.board_grid_xs)
        self.grid_step_y = self._average_step(self.board_grid_ys)
        self.cell = int(round(min(self.grid_step_x, self.grid_step_y) * self.board_scale))
        self.display_grid_xs = [int(round(x * self.board_scale)) for x in self.board_grid_xs]
        self.display_grid_ys = [int(round(y * self.board_scale)) for y in self.board_grid_ys]

        self.left = 12
        # Raise the board a bit so it's centered between the top/bottom player tags
        self.top = 92
        # Negative top gap places the top coordinate labels slightly inside the board
        self.coord_top_gap = -20
        self.coord_bottom_gap = 16
        self.window_w = self.left * 2 + self.board_w
        # Reduce extra bottom padding so window is shorter after removing coordinate strip
        self.window_h = self.top + self.board_h + self.coord_bottom_gap + 60

        self.screen = pygame.display.set_mode((self.window_w, self.window_h))
        self.board_source_surface = self.board_source_surface.convert_alpha()

        # Ưu tiên font Unicode có sẵn trong project để tránh ký tự quân cờ bị render thành '?'.
        self.tag_font = self._create_font(["segoe ui", "tahoma", "arial"], 24, bold=True)
        self.piece_font = self._create_piece_font(20)
        self.overlay_font = self._create_font(["segoe ui", "tahoma", "arial"], 34, bold=True)
        self.overlay_small_font = self._create_font(["segoe ui", "tahoma", "arial"], 18, bold=False)
        self.coord_font = self._create_font(["segoe ui", "tahoma", "arial"], 16, bold=True)

        self.background_surface = self._create_background_surface()
        self.board_panel_surface = self._create_board_panel_surface()
        self.board_texture_surface = self._load_board_texture_surface()

        self.running = True
        self.game_over = False
        self.game_over_text = ""
        self.game_over_detail = ""

    def run(self) -> None:
        """Main thread: event loop + render 60 FPS."""
        while self.running:
            self._process_events()
            self._poll_bot_result()
            self._maybe_start_bot_turn()
            self._draw_frame()
            self.clock.tick(self.fps)

        pygame.quit()

    def _process_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self._handle_left_click(event.pos)

    def _handle_left_click(self, pos: tuple[int, int]) -> None:
        if self._is_game_over() or self.bot_worker_active:
            return

        if self.human_color is None:
            return

        if self.board.side_to_move != self.human_color:
            return

        clicked_sq = self._pixel_to_square(pos)
        if clicked_sq is None:
            self._clear_selection()
            return

        if self.selected_sq is not None:
            target_move = self._find_selected_move(clicked_sq)
            if target_move is not None:
                # Chuẩn hóa qua UCI để đồng bộ đúng pipeline thao tác của Core.
                move_uci = move_to_uci(target_move)
                self._execute_move(uci_to_move(move_uci), self._current_side_name())
                self._clear_selection()
                return

        piece = self.board.state[clicked_sq]
        if piece == ".":
            self._clear_selection()
            return

        if self.board.side_to_move == Color.RED and not is_red(piece):
            self._clear_selection()
            return

        if self.board.side_to_move == Color.BLACK and not is_black(piece):
            self._clear_selection()
            return

        self.selected_sq = clicked_sq
        legal_moves = get_legal_moves(self.board, MoveGenerator(self.board))
        self.selected_moves = [m for m in legal_moves if get_from_sq(m) == clicked_sq]

    def _poll_bot_result(self) -> None:
        if not self.bot_worker_active:
            return

        try:
            result = self.bot_queue.get_nowait()
        except queue.Empty:
            return

        self.bot_worker_active = False

        if result.get("error"):
            self.game.logger.error("Worker bot error: %s", result["error"])
            loser = result.get("bot_name", "Unknown")
            self.game.resign(loser)
            self._show_game_over_overlay("GAME OVER", f"{loser} gặp lỗi khi tính nước đi")
            return

        move = result.get("move")
        bot_name = result.get("bot_name", self._current_side_name())
        if move is None:
            self.game.logger.warning("%s không có nước đi hợp lệ", bot_name)
            self.game.resign(bot_name)
            self._show_game_over_overlay("GAME OVER", f"{bot_name} không còn nước đi hợp lệ")
            return

        self._execute_move(move, bot_name)

    def _maybe_start_bot_turn(self) -> None:
        if self._is_game_over():
            return

        if self.bot_worker_active:
            return

        side_entity = self.red_entity if self.board.side_to_move == Color.RED else self.black_entity
        if self._is_human_turn():
            return

        if not isinstance(side_entity, Bot):
            return

        self._start_bot_worker(side_entity)

    def _start_bot_worker(self, bot: Bot) -> None:
        snapshot = copy.deepcopy(self.board)

        def worker() -> None:
            start = time.time()
            try:
                move = bot.get_move(snapshot)
                elapsed = time.time() - start
                self.bot_queue.put({"move": move, "bot_name": bot.name, "time": elapsed})
            except Exception as exc:
                self.bot_queue.put({"error": str(exc), "bot_name": bot.name})

        self.bot_worker_active = True
        self.bot_worker = threading.Thread(target=worker, name="bot-worker", daemon=True)
        self.bot_worker.start()

    def _execute_move(self, move: int, actor_name: str) -> None:
        legal_moves = get_legal_moves(self.board, MoveGenerator(self.board))
        if move not in legal_moves:
            self.game.logger.error("Illegal move from %s: %s", actor_name, move_to_uci(move))
            self.game.game_result_status = GameResultStatus.ILLEGAL_MOVE
            self.game.resign(actor_name)
            self._show_game_over_overlay("GAME OVER", f"Nước đi không hợp lệ từ {actor_name}")
            return

        move_uci = move_to_uci(move)
        self.board.make_move(move)
        self.move_count += 1

        self.game.moves.append((actor_name, move, move_uci))
        self.game.logger.log_move(self.game.game_id, len(self.game.moves), actor_name, move_uci)

        status = check_game_status(self.board, get_legal_moves(self.board, MoveGenerator(self.board)))
        if status != GameStatus.Playing:
            self._close_with_status(status)
            return

        if self.move_count >= self.max_moves:
            self.game._set_winner(Winner.DRAW)
            self.game.game_result_status = GameResultStatus.DRAW
            self._show_game_over_overlay("HÒA CỜ", "Ván cờ kết thúc sau khi đạt giới hạn nước đi")

    def _close_with_status(self, status: GameStatus) -> None:
        if status == GameStatus.Draw:
            self.game._set_winner(Winner.DRAW)
            self.game.game_result_status = GameResultStatus.DRAW
            title = "HÒA CỜ"
        elif status == GameStatus.RedWin:
            self.game._set_winner(Winner.RED)
            self.game.game_result_status = GameResultStatus.CHECKMATE
            title = "ĐỎ THẮNG"
        else:
            self.game._set_winner(Winner.BLACK)
            self.game.game_result_status = GameResultStatus.CHECKMATE
            title = "ĐEN THẮNG"

        self.game.logger.log_game_end(
            self.game.game_id,
            winner=self.game.winner.value if self.game.winner else "None",
            reason=self.game.game_result_status.value,
        )
        self._show_game_over_overlay(title, f"Kết quả: {self.game.game_result_status.value}")

    def _show_game_over_overlay(self, title: str, detail: str) -> None:
        self.game_over = True
        self.game_over_text = title
        self.game_over_detail = detail
        self._clear_selection()

    def _is_game_over(self) -> bool:
        return self.game.game_result_status != GameResultStatus.PLAYING

    def _is_human_turn(self) -> bool:
        return self.human_color is not None and self.board.side_to_move == self.human_color

    def _current_side_name(self) -> str:
        return self.red_entity.name if self.board.side_to_move == Color.RED else self.black_entity.name

    def _find_selected_move(self, clicked_sq: int) -> Optional[int]:
        for move in self.selected_moves:
            if get_to_sq(move) == clicked_sq:
                return move
        return None

    def _clear_selection(self) -> None:
        self.selected_sq = None
        self.selected_moves = []

    def _draw_frame(self) -> None:
        self.screen.blit(self.background_surface, (0, 0))
        self.screen.blit(self.board_panel_surface, (0, 0))
        self._draw_board_lines()
        # Draw player tags first so coordinate labels can be rendered on top
        self._draw_player_tags()
        self._draw_coordinates()
        self._draw_pieces()
        self._draw_move_hints()
        if self.game_over:
            self._draw_game_over_overlay()
        pygame.display.flip()

    def _draw_board_lines(self) -> None:
        self.screen.blit(self.board_texture_surface, (self.left, self.top))

    def _draw_palace(self, start: tuple[int, int], end: tuple[int, int]) -> None:
        c0, r0 = start
        c1, r1 = end
        x0 = self.left + c0 * self.cell
        y0 = self.top + r0 * self.cell
        x1 = self.left + c1 * self.cell
        y1 = self.top + r1 * self.cell
        pygame.draw.line(self.screen, self.LINE_COLOR, (x0, y0), (x1, y1), 2)
        pygame.draw.line(self.screen, self.LINE_COLOR, (x0, y1), (x1, y0), 2)

    def _draw_coordinates(self) -> None:
        # Coordinates removed per user request (no-op)
        return

    def _blit_label(self, text: str, pos: tuple[int, int], font, color, center: bool = False) -> None:
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        self.screen.blit(surf, rect)

    def _create_background_surface(self):
        surface = pygame.Surface((self.window_w, self.window_h))
        for y in range(self.window_h):
            ratio = y / max(1, self.window_h - 1)
            r = int(self.BG_LIGHT[0] * (1 - ratio) + self.BG_DARK[0] * ratio)
            g = int(self.BG_LIGHT[1] * (1 - ratio) + self.BG_DARK[1] * ratio)
            b = int(self.BG_LIGHT[2] * (1 - ratio) + self.BG_DARK[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.window_w, y))

        # Họa tiết gỗ nhẹ bằng các vệt ngang.
        for y in range(0, self.window_h, 18):
            alpha = 10 if (y // 18) % 2 == 0 else 6
            pygame.draw.line(surface, (255, 255, 255, alpha), (0, y), (self.window_w, y), 1)
        return surface

    def _create_board_panel_surface(self):
        surface = pygame.Surface((self.window_w, self.window_h), pygame.SRCALPHA)
        panel_rect = pygame.Rect(12, 12, self.window_w - 24, self.window_h - 24)
        pygame.draw.rect(surface, (70, 46, 24, 255), panel_rect.inflate(8, 8), border_radius=24)
        pygame.draw.rect(surface, (*self.PANEL_COLOR, 255), panel_rect, border_radius=20)
        pygame.draw.rect(surface, (111, 73, 36, 255), panel_rect, width=4, border_radius=20)
        # Nét lót bên trong để tạo chiều sâu.
        inner = panel_rect.inflate(-14, -14)
        pygame.draw.rect(surface, (255, 247, 228, 40), inner, width=1, border_radius=16)
        return surface

    def _draw_player_tags(self) -> None:
        red_turn = self.board.side_to_move == Color.RED
        black_turn = not red_turn

        self._draw_tag(self.participants.black_name, top=True, active=black_turn)
        self._draw_tag(self.participants.red_name, top=False, active=red_turn)

    def _draw_tag(self, text: str, top: bool, active: bool) -> None:
        width = self.window_w - 40
        height = 42
        x = 20
        y = 20 if top else self.window_h - 58

        tag_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        alpha = 255 if active else 102
        pygame.draw.rect(tag_surface, (*self.TAG_BG, alpha), (0, 0, width, height), border_radius=10)
        label = self.tag_font.render(text, True, self.TAG_TEXT)
        label_rect = label.get_rect(center=(width // 2, height // 2))
        tag_surface.blit(label, label_rect)
        self.screen.blit(tag_surface, (x, y))

    def _draw_pieces(self) -> None:
        for sq, piece in enumerate(self.board.state):
            if piece == ".":
                continue

            row, col = divmod(sq, 9)
            center = self._square_center(row, col)

            radius = int(self.cell * 0.30)
            shadow_surface = pygame.Surface((radius * 3, radius * 3), pygame.SRCALPHA)
            pygame.draw.circle(shadow_surface, self.PIECE_SHADOW, (radius + 3, radius + 5), radius)
            self.screen.blit(shadow_surface, (center[0] - radius - 3, center[1] - radius - 5))

            pygame.draw.circle(self.screen, self.PIECE_FILL, center, radius)
            pygame.draw.circle(self.screen, self.PIECE_EDGE, center, radius, 2)
            pygame.draw.circle(self.screen, (255, 248, 231), center, radius - 5, 1)

            text_color = self.RED_COLOR if piece.isupper() else self.BLACK_COLOR
            label = self.piece_font.render(CHINESE_PIECES[piece], True, text_color)
            label_rect = label.get_rect(center=center)
            self.screen.blit(label, label_rect)

    def _draw_move_hints(self) -> None:
        if self.selected_sq is None:
            return

        sel_row, sel_col = divmod(self.selected_sq, 9)
        center = self._square_center(sel_row, sel_col)
        pygame.draw.circle(self.screen, (255, 255, 255), center, int(self.cell * 0.42), 3)

        for move in self.selected_moves:
            to_sq = get_to_sq(move)
            row, col = divmod(to_sq, 9)
            to_center = self._square_center(row, col)
            target_piece = self.board.state[to_sq]

            if target_piece == ".":
                hint_surface = pygame.Surface((self.cell, self.cell), pygame.SRCALPHA)
                pygame.draw.circle(
                    hint_surface,
                    self.HINT_WHITE,
                    (self.cell // 2, self.cell // 2),
                    int(self.cell * 0.13),
                )
                self.screen.blit(hint_surface, (to_center[0] - self.cell // 2, to_center[1] - self.cell // 2))
            else:
                pygame.draw.circle(self.screen, (215, 50, 50), to_center, int(self.cell * 0.42), 3)

    def _draw_game_over_overlay(self) -> None:
        overlay = pygame.Surface((self.window_w, self.window_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))

        box_w = int(self.window_w * 0.78)
        box_h = 150
        box_x = (self.window_w - box_w) // 2
        box_y = (self.window_h - box_h) // 2

        box_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box_surface, (244, 236, 220, 235), (0, 0, box_w, box_h), border_radius=18)
        pygame.draw.rect(box_surface, (75, 45, 15, 255), (0, 0, box_w, box_h), width=3, border_radius=18)

        title_label = self.overlay_font.render(self.game_over_text, True, (65, 35, 20))
        title_rect = title_label.get_rect(center=(box_w // 2, 54))
        box_surface.blit(title_label, title_rect)

        detail_label = self.overlay_small_font.render(self.game_over_detail, True, (90, 60, 30))
        detail_rect = detail_label.get_rect(center=(box_w // 2, 98))
        box_surface.blit(detail_label, detail_rect)

        hint_label = self.overlay_small_font.render("Đóng cửa sổ bằng nút X để thoát", True, (90, 60, 30))
        hint_rect = hint_label.get_rect(center=(box_w // 2, 124))
        box_surface.blit(hint_label, hint_rect)

        self.screen.blit(box_surface, (box_x, box_y))

    def _square_center(self, row: int, col: int) -> tuple[int, int]:
        return (self.left + self.display_grid_xs[col], self.top + self.display_grid_ys[row])

    def _load_board_texture_surface(self):
        return pygame.transform.smoothscale(self.board_source_surface, (self.board_w, self.board_h))

    def _detect_grid_lines(self, surface) -> tuple[list[int], list[int]]:
        width, height = surface.get_size()

        def row_score(y: int) -> float:
            total = 0.0
            for x in range(width):
                if surface.get_at((x, y)).a > 0:
                    total += 1
            return total / width

        def col_score(x: int) -> float:
            total = 0.0
            for y in range(height):
                if surface.get_at((x, y)).a > 0:
                    total += 1
            return total / height

        x_positions = self._pick_grid_positions(width, col_score, 9)
        y_positions = self._pick_grid_positions(height, row_score, 10)
        return x_positions, y_positions

    def _pick_grid_positions(self, limit: int, score_fn, count: int) -> list[int]:
        candidates = sorted(range(limit), key=score_fn, reverse=True)
        selected: list[int] = []
        min_gap = 30

        for index in candidates:
            if all(abs(index - chosen) >= min_gap for chosen in selected):
                selected.append(index)
                if len(selected) == count:
                    break

        selected.sort()
        return selected

    def _average_step(self, positions: list[int]) -> int:
        if len(positions) < 2:
            return self.cell if hasattr(self, "cell") else 48

        total = 0
        for left, right in zip(positions, positions[1:]):
            total += right - left
        return int(round(total / (len(positions) - 1)))

    def _create_font(self, font_names: list[str], size: int, bold: bool = False):
        for font_name in font_names:
            font_path = pygame.font.match_font(font_name.replace(" ", ""), bold=bold)
            if font_path:
                return pygame.font.Font(font_path, size)

        return pygame.font.SysFont("segoeui", size, bold=bold)

    def _create_piece_font(self, size: int):
        if self.LOCAL_FONT_REGULAR.exists():
            return pygame.font.Font(str(self.LOCAL_FONT_REGULAR), size)

        if self.LOCAL_FONT_BOLD.exists():
            return pygame.font.Font(str(self.LOCAL_FONT_BOLD), size)

        return self._create_font(["segoe ui", "tahoma", "arial"], size, bold=True)

    def _pixel_to_square(self, pos: tuple[int, int]) -> Optional[int]:
        x, y = pos

        local_x = x - self.left
        local_y = y - self.top

        if not (0 <= local_x <= self.board_w and 0 <= local_y <= self.board_h):
            return None

        # Use the scaled/display grid positions when mapping pixels to board squares.
        col = min(range(self.GRID_COLS), key=lambda index: abs(local_x - self.display_grid_xs[index]))
        row = min(range(self.GRID_ROWS), key=lambda index: abs(local_y - self.display_grid_ys[index]))

        center_x, center_y = self._square_center(row, col)

        # Compute average step for the displayed grid to determine a sensible click tolerance.
        disp_step_x = self._average_step(self.display_grid_xs)
        disp_step_y = self._average_step(self.display_grid_ys)

        if abs(x - center_x) > disp_step_x * 0.38 or abs(y - center_y) > disp_step_y * 0.38:
            return None

        return row * 9 + col


class HumanPlayer:
    def __init__(self, name: str = "Human") -> None:
        self.name = name

    def get_move(self, board: Board) -> Optional[int]:
        """CLI-friendly prompt to get a move in UCI format (e.g. a0a1).

        Returns an integer-encoded move or None if the player resigns/aborts.
        """
        try:
            raw = input(f"Nhap nuoc cho {self.name} (UCI, e.g. a0a1). Enter= resign: ").strip()
        except KeyboardInterrupt:
            return None

        if raw == "" or raw.lower() in ("resign", "quit", "exit"):
            return None

        try:
            return uci_to_move(raw)
        except Exception:
            print("UCI khong hop le (dinh dang a0a1). Thu lai.")
            return self.get_move(board)
