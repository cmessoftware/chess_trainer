"""F07-003 — Stockfish evaluation before and after a move."""

from __future__ import annotations

import asyncio
import os
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Literal

import chess
import chess.engine

ScoreKind = Literal["cp", "mate"]


@dataclass(frozen=True)
class EngineScore:
    """Raw engine score from White's point of view (F07-003; not player-normalized)."""

    kind: ScoreKind
    white_cp: int | None
    white_mate: int | None

    def as_white_cp_or_mate_units(self, mate_cp: int = 100_000) -> int:
        if self.kind == "mate" and self.white_mate is not None:
            sign = 1 if self.white_mate > 0 else -1
            return sign * (mate_cp - abs(self.white_mate))
        if self.white_cp is None:
            raise ValueError("cp score is missing")
        return self.white_cp


@dataclass(frozen=True)
class PlyEngineAnalysis:
    fen_before: str
    fen_after: str
    move_uci: str
    eval_before: EngineScore
    eval_after: EngineScore
    depth: int
    engine_name: str = "Stockfish"


def resolve_stockfish_path() -> Path | None:
    env = os.environ.get("STOCKFISH_PATH")
    repo = Path(__file__).resolve().parents[3]
    candidates: list[Path] = []
    if env:
        raw = Path(env)
        candidates.append(raw)
        if not raw.is_absolute():
            candidates.append(repo / raw)
    for name in ("stockfish.exe", "stockfish"):
        candidates.append(repo / "bin" / name)
    for path in candidates:
        if path.is_file():
            return path.resolve()
    return None


def configure_asyncio_for_engine() -> None:
    """Allow UCI subprocesses on Windows Jupyter (SelectorEventLoop has no subprocess)."""
    if sys.platform != "win32":
        return
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass


def stockfish_available() -> bool:
    return resolve_stockfish_path() is not None


def parse_engine_score(score: chess.engine.PovScore) -> EngineScore:
    white = score.white()
    if white.is_mate():
        return EngineScore(kind="mate", white_cp=None, white_mate=white.mate())
    return EngineScore(kind="cp", white_cp=white.score(), white_mate=None)


def analyze_fen(
    fen: str,
    *,
    engine: Any,
    depth: int = 12,
) -> EngineScore:
    board = chess.Board(fen)
    info = engine.analyse(board, chess.engine.Limit(depth=depth))
    return parse_engine_score(info["score"])


def analyze_ply(
    fen_before: str,
    move_uci: str,
    *,
    engine: Any | None = None,
    depth: int = 12,
) -> PlyEngineAnalysis:
    """Evaluate the position before and after ``move_uci`` (F07-003)."""
    board = chess.Board(fen_before)
    move = chess.Move.from_uci(move_uci)
    if move not in board.legal_moves:
        raise ValueError(f"Illegal move {move_uci} in {fen_before}")

    def _run(eng: Any) -> PlyEngineAnalysis:
        before = analyze_fen(board.fen(), engine=eng, depth=depth)
        board_after = board.copy()
        board_after.push(move)
        after = analyze_fen(board_after.fen(), engine=eng, depth=depth)
        name = "Stockfish"
        try:
            ident = eng.id
            if isinstance(ident, dict) and ident.get("name"):
                name = str(ident["name"])
        except Exception:
            pass
        return PlyEngineAnalysis(
            fen_before=board.fen(),
            fen_after=board_after.fen(),
            move_uci=move.uci(),
            eval_before=before,
            eval_after=after,
            depth=depth,
            engine_name=name,
        )

    if engine is not None:
        return _run(engine)
    with open_stockfish() as eng:
        return _run(eng)


@contextmanager
def open_stockfish(path: str | Path | None = None) -> Iterator[chess.engine.SimpleEngine]:
    try:
        from mm_lab_imports import load_repo_dotenv

        load_repo_dotenv(Path(__file__), override=False)
    except ImportError:
        pass
    resolved = Path(path) if path else resolve_stockfish_path()
    if resolved is None or not resolved.is_file():
        raise FileNotFoundError(
            "Stockfish binary not found. Set STOCKFISH_PATH in .env or place bin/stockfish.exe"
        )
    configure_asyncio_for_engine()
    try:
        engine = chess.engine.SimpleEngine.popen_uci(str(resolved))
    except NotImplementedError as exc:
        raise RuntimeError(
            "No se pudo lanzar Stockfish desde Jupyter en Windows (asyncio subprocess). "
            "Restart kernel y re-ejecutá Paso 0 y 3. Si persiste, corré analyze_ply fuera de Jupyter."
        ) from exc
    try:
        yield engine
    finally:
        engine.quit()


configure_asyncio_for_engine()
