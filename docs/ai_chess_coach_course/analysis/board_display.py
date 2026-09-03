"""Render a chess board in Jupyter (SVG), not python-chess ASCII."""

from __future__ import annotations

from typing import Any

import chess
import chess.svg


def board_svg(
    board: chess.Board,
    *,
    lastmove: chess.Move | str | None = None,
    size: int = 420,
    flipped: bool = False,
    check: chess.Square | None = None,
) -> str:
    move = lastmove
    if isinstance(move, str) and move:
        move = chess.Move.from_uci(move)
    kwargs: dict[str, Any] = {"board": board, "size": size, "flipped": flipped}
    if move:
        kwargs["lastmove"] = move
    if check is None and board.is_check():
        check = board.king(board.turn)
    if check is not None:
        kwargs["check"] = check
    return chess.svg.board(**kwargs)


def show_board(
    board: chess.Board,
    *,
    lastmove: chess.Move | str | None = None,
    size: int = 420,
    flipped: bool = False,
) -> None:
    """Display an interactive-looking SVG board in a notebook cell."""
    from IPython.display import SVG, display

    display(SVG(board_svg(board, lastmove=lastmove, size=size, flipped=flipped)))
