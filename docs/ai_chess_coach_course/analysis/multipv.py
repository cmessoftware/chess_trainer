"""F07-014 — Stockfish MultiPV candidates with PV and evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import chess
import chess.engine

from analysis.engine_eval import (
    EngineScore,
    PlayerScore,
    normalize_for_player,
    open_stockfish,
    parse_engine_score,
)
from analysis.game_models import PlayerColor, parse_player_color
from analysis.notation import pv_uci_to_san, uci_to_san


@dataclass(frozen=True)
class CandidateLine:
    """One MultiPV line (F07-014)."""

    multipv_rank: int
    move_uci: str
    move_san: str
    pv_uci: tuple[str, ...]
    pv_san: tuple[str, ...]
    score: EngineScore
    player_score: PlayerScore


@dataclass(frozen=True)
class MultiPVResult:
    """F07-014 — MultiPV candidates for a FEN."""

    fen: str
    player_color: PlayerColor
    depth: int
    engine_name: str
    lines: tuple[CandidateLine, ...]


@dataclass(frozen=True)
class PlayedMoveEval:
    """F07-015 — played move ranked in MultiPV or scored independently."""

    move_uci: str
    move_san: str
    in_multipv: bool
    multipv_rank: int | None
    source: str
    score: EngineScore
    player_score: PlayerScore
    pv_uci: tuple[str, ...]
    pv_san: tuple[str, ...]


def _as_info_list(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        return [raw]
    raise TypeError(f"Unexpected analyse() result: {type(raw)!r}")


def _pv_moves(board: chess.Board, raw_pv: Any) -> list[chess.Move]:
    if not raw_pv:
        return []
    moves: list[chess.Move] = []
    work = board.copy()
    for item in raw_pv:
        move = item if isinstance(item, chess.Move) else chess.Move.from_uci(str(item))
        if move not in work.legal_moves:
            break
        moves.append(move)
        work.push(move)
    return moves


def _engine_name(engine: Any) -> str:
    name = "Stockfish"
    try:
        ident = engine.id
        if isinstance(ident, dict) and ident.get("name"):
            name = str(ident["name"])
    except Exception:
        pass
    return name


def analyze_multipv(
    fen: str,
    *,
    engine: Any | None = None,
    depth: int = 12,
    multipv: int = 3,
    player_color: PlayerColor | str | int | None = None,
) -> MultiPVResult:
    """Return up to ``multipv`` legal candidate lines from the FEN (F07-014)."""
    if multipv < 1:
        raise ValueError("multipv must be >= 1")
    board = chess.Board(fen)
    stm: PlayerColor = "white" if board.turn == chess.WHITE else "black"
    color = stm if player_color is None else (
        player_color if player_color in ("white", "black") else parse_player_color(player_color)
    )

    def _run(eng: Any) -> MultiPVResult:
        try:
            raw = eng.analyse(board, chess.engine.Limit(depth=depth), multipv=multipv)
        except TypeError:
            raw = eng.analyse(board, chess.engine.Limit(depth=depth))
        infos = _as_info_list(raw)
        lines: list[CandidateLine] = []
        seen: set[str] = set()
        for info in infos:
            if "score" not in info:
                continue
            pv_moves = _pv_moves(board, info.get("pv") or [])
            if not pv_moves:
                continue
            first = pv_moves[0]
            uci = first.uci()
            if uci in seen:
                continue
            seen.add(uci)
            pv_uci = tuple(m.uci() for m in pv_moves)
            pv_san = pv_uci_to_san(board.fen(), pv_uci)
            score = parse_engine_score(info["score"])
            rank = int(info.get("multipv") or (len(lines) + 1))
            lines.append(
                CandidateLine(
                    multipv_rank=rank,
                    move_uci=uci,
                    move_san=pv_san[0],
                    pv_uci=pv_uci,
                    pv_san=pv_san,
                    score=score,
                    player_score=normalize_for_player(score, color),
                )
            )
            if len(lines) >= multipv:
                break
        lines.sort(key=lambda line: line.multipv_rank)
        return MultiPVResult(
            fen=board.fen(),
            player_color=color,
            depth=depth,
            engine_name=_engine_name(eng),
            lines=tuple(lines),
        )

    if engine is not None:
        return _run(engine)
    with open_stockfish() as eng:
        return _run(eng)


def _line_from_played_move(
    board: chess.Board,
    move: chess.Move,
    score: EngineScore,
    color: PlayerColor,
) -> tuple[str, tuple[str, ...], tuple[str, ...], PlayerScore]:
    san = uci_to_san(board.fen(), move.uci())
    return san, (move.uci(),), (san,), normalize_for_player(score, color)


def _analyse_played_independently(
    eng: Any,
    board: chess.Board,
    move: chess.Move,
    depth: int,
) -> EngineScore:
    try:
        raw = eng.analyse(
            board, chess.engine.Limit(depth=depth), root_moves=[move]
        )
    except TypeError:
        after = board.copy()
        after.push(move)
        raw = eng.analyse(after, chess.engine.Limit(depth=depth))
    infos = _as_info_list(raw)
    if not infos or "score" not in infos[0]:
        after = board.copy()
        after.push(move)
        raw = eng.analyse(after, chess.engine.Limit(depth=depth))
        infos = _as_info_list(raw)
    if not infos or "score" not in infos[0]:
        raise RuntimeError("Engine returned no score for the played move")
    return parse_engine_score(infos[0]["score"])


def evaluate_played_move(
    fen: str,
    move_uci: str,
    *,
    engine: Any | None = None,
    depth: int = 12,
    multipv: int = 3,
    player_color: PlayerColor | str | int | None = None,
    multipv_result: MultiPVResult | None = None,
) -> PlayedMoveEval:
    """Rank the played move in MultiPV, or analyse it on its own (F07-015)."""
    board = chess.Board(fen)
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        raise ValueError(f"Illegal move {move_uci} in {fen}")
    stm: PlayerColor = "white" if board.turn == chess.WHITE else "black"
    color = stm if player_color is None else (
        player_color if player_color in ("white", "black") else parse_player_color(player_color)
    )

    def _run(eng: Any) -> PlayedMoveEval:
        result = multipv_result
        if result is None:
            result = analyze_multipv(
                fen,
                engine=eng,
                depth=depth,
                multipv=multipv,
                player_color=color,
            )
        for line in result.lines:
            if line.move_uci == move.uci():
                return PlayedMoveEval(
                    move_uci=move.uci(),
                    move_san=line.move_san,
                    in_multipv=True,
                    multipv_rank=line.multipv_rank,
                    source="multipv",
                    score=line.score,
                    player_score=line.player_score,
                    pv_uci=line.pv_uci,
                    pv_san=line.pv_san,
                )
        score = _analyse_played_independently(eng, board, move, depth)
        san, pv_uci, pv_san, player_score = _line_from_played_move(
            board, move, score, color
        )
        return PlayedMoveEval(
            move_uci=move.uci(),
            move_san=san,
            in_multipv=False,
            multipv_rank=None,
            source="independent",
            score=score,
            player_score=player_score,
            pv_uci=pv_uci,
            pv_san=pv_san,
        )

    if engine is not None:
        return _run(engine)
    with open_stockfish() as eng:
        return _run(eng)
