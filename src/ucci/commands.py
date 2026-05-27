from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .adapter import GoParams


class UCCICommand(str, Enum):
    UCI = "uci"
    UCCI = "ucci"
    ISREADY = "isready"
    SETOPTION = "setoption"
    UCINEWGAME = "ucinewgame"
    POSITION = "position"
    GO = "go"
    STOP = "stop"
    QUIT = "quit"
    PONDERHIT = "ponderhit"
    DEBUG = "debug"


@dataclass(slots=True)
class SetOptionParams:
    name: str
    value: Optional[str] = None


@dataclass(slots=True)
class PositionParams:
    fen: Optional[str] = None
    moves: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParsedCommand:
    command: UCCICommand
    go: Optional[GoParams] = None
    setoption: Optional[SetOptionParams] = None
    position: Optional[PositionParams] = None
    debug_value: Optional[bool] = None


_GO_KEYS = {"wtime", "btime", "winc", "binc", "movestogo", "depth", "nodes", "movetime"}


def parse_line(line: str) -> Optional[ParsedCommand]:
    text = line.strip()
    if not text:
        return None

    tokens = text.split()
    command = tokens[0].lower()

    try:
        if command == UCCICommand.UCCI.value:
            return ParsedCommand(UCCICommand.UCCI)
        if command == UCCICommand.UCI.value:
            return ParsedCommand(UCCICommand.UCI)
        if command == UCCICommand.ISREADY.value:
            return ParsedCommand(UCCICommand.ISREADY)
        if command == UCCICommand.UCINEWGAME.value:
            return ParsedCommand(UCCICommand.UCINEWGAME)
        if command == UCCICommand.STOP.value:
            return ParsedCommand(UCCICommand.STOP)
        if command == UCCICommand.QUIT.value:
            return ParsedCommand(UCCICommand.QUIT)
        if command == UCCICommand.PONDERHIT.value:
            return ParsedCommand(UCCICommand.PONDERHIT)
        if command == UCCICommand.DEBUG.value:
            debug_val = True
            if len(tokens) > 1 and tokens[1].lower() == "off":
                debug_val = False
            return ParsedCommand(UCCICommand.DEBUG, debug_value=debug_val)
        if command == UCCICommand.SETOPTION.value:
            return ParsedCommand(UCCICommand.SETOPTION, setoption=_parse_setoption(tokens[1:]))
        if command == UCCICommand.POSITION.value:
            return ParsedCommand(UCCICommand.POSITION, position=_parse_position(tokens[1:]))
        if command == UCCICommand.GO.value:
            return ParsedCommand(UCCICommand.GO, go=_parse_go(tokens[1:]))
    except (TypeError, ValueError):
        return None

    return None


UCICommand = UCCICommand


def _parse_setoption(tokens: list[str]) -> SetOptionParams:
    name_tokens: list[str] = []
    value_tokens: list[str] = []
    i = 0
    while i < len(tokens):
        token = tokens[i].lower()
        if token == "name":
            i += 1
            while i < len(tokens) and tokens[i].lower() != "value":
                name_tokens.append(tokens[i])
                i += 1
            continue
        if token == "value":
            value_tokens.extend(tokens[i + 1 :])
            break
        i += 1

    name = " ".join(name_tokens).strip()
    value = " ".join(value_tokens).strip() or None
    return SetOptionParams(name=name, value=value)


def _parse_position(tokens: list[str]) -> PositionParams:
    if not tokens:
        return PositionParams()

    index = 0
    fen: Optional[str] = None
    moves: list[str] = []

    if tokens[index].lower() == "startpos":
        index += 1
    elif tokens[index].lower() == "fen":
        index += 1
        fen_tokens: list[str] = []
        while index < len(tokens) and tokens[index].lower() != "moves":
            fen_tokens.append(tokens[index])
            index += 1
        fen = " ".join(fen_tokens).strip() or None

    if index < len(tokens) and tokens[index].lower() == "moves":
        moves = tokens[index + 1 :]

    return PositionParams(fen=fen, moves=moves)


def _parse_go(tokens: list[str]) -> GoParams:
    params = GoParams()
    i = 0
    while i < len(tokens):
        token = tokens[i].lower()
        if token in _GO_KEYS:
            if i + 1 < len(tokens):
                value = int(tokens[i + 1])
                setattr(params, token, value)
                i += 2
                continue
            break
        if token == "infinite":
            params.infinite = True
            i += 1
            continue
        if token == "ponder":
            params.ponder = True
            i += 1
            continue
        if token == "searchmoves":
            i += 1
            while i < len(tokens) and tokens[i].lower() not in _GO_KEYS and tokens[i].lower() not in {"infinite", "ponder", "searchmoves"}:
                i += 1
            continue
        i += 1

    return params
