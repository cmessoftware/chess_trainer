"""Interactive Chessground board for Jupyter (FEN + drag). Same contract as React ChessinsightBoard."""

from __future__ import annotations

import json
import uuid
from pathlib import Path

import chess

UI_DIR = Path(__file__).resolve().parents[1] / "ui" / "chessinsight_board"
MOUNT_JS = UI_DIR / "mount.js"


def legal_dests(board: chess.Board) -> dict[str, list[str]]:
    dests: dict[str, list[str]] = {}
    for move in board.legal_moves:
        origin = chess.square_name(move.from_square)
        dests.setdefault(origin, []).append(chess.square_name(move.to_square))
    return dests


def last_move_uci(move: chess.Move | str | None) -> str | None:
    if move is None:
        return None
    if isinstance(move, chess.Move):
        return move.uci()
    token = str(move).strip()
    return token or None


def interactive_board_html(
    board: chess.Board,
    *,
    lastmove: chess.Move | str | None = None,
    orientation: str = "white",
    view_only: bool = False,
    size: int = 420,
) -> str:
    mount_js = MOUNT_JS.read_text(encoding="utf-8")
    uid = f"cib-{uuid.uuid4().hex[:12]}"
    side = "black" if str(orientation).lower() in {"black", "b"} else "white"
    props = {
        "fen": board.fen(),
        "orientation": side,
        "lastMove": last_move_uci(lastmove),
        "viewOnly": view_only,
        "dests": {} if view_only else legal_dests(board),
    }
    props_json = json.dumps(props)
    return f"""
<div class="chessinsight-board-wrap" style="max-width:{size}px">
  <div id="{uid}" class="cg-wrap" style="width:{size}px;height:{size}px"></div>
  <p data-role="last-try" style="font:12px sans-serif;margin:8px 0 0">Arrastrá piezas: cada jugada legal actualiza el tablero.</p>
</div>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/chessground@9.2.1/assets/chessground.base.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/chessground@9.2.1/assets/chessground.brown.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/chessground@9.2.1/assets/chessground.cburnett.css">
<style>
  .chessinsight-board-wrap cg-board {{ border-radius: 4px; }}
</style>
<script type="module">
{mount_js}
mountChessinsightBoard(document.getElementById({json.dumps(uid)}), {props_json});
</script>
"""


def show_interactive_board(
    board: chess.Board,
    *,
    lastmove: chess.Move | str | None = None,
    orientation: str = "white",
    view_only: bool = False,
    size: int = 420,
) -> None:
    from IPython.display import HTML, display

    display(
        HTML(
            interactive_board_html(
                board,
                lastmove=lastmove,
                orientation=orientation,
                view_only=view_only,
                size=size,
            )
        )
    )
