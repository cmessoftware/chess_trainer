"""Generate one focused Jupyter lab per implemented F07 item."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "labs"

BOOTSTRAP = '''from pathlib import Path
import sys
_cwd = Path.cwd().resolve()
for _candidate in (_cwd, _cwd / "docs" / "ai_chess_coach_course"):
    if (_candidate / "mm_lab_imports.py").is_file():
        sys.path.insert(0, str(_candidate))
        break
from mm_lab_imports import prepare_sys_path, load_repo_dotenv
COURSE_ROOT = prepare_sys_path()
load_repo_dotenv(COURSE_ROOT, override=True)
from analysis.position_extractor import import_game_from_file
from analysis.game_models import select_analyzed_player
GAMES = COURSE_ROOT / "data" / "games"
GOLD = COURSE_ROOT / "data" / "expert_gold"
print("COURSE_ROOT", COURSE_ROOT)
print("expert_gold", GOLD)
'''

LOAD = '''PGN_PATH = GAMES / PGN_NAME
game = import_game_from_file(PGN_PATH)
player = select_analyzed_player(game, username=PLAYER_NAME, color=PLAYER_COLOR)
record = next(p for p in game.plies if p.san == TARGET_SAN)
print(game.headers.get("White"), "vs", game.headers.get("Black"))
print("ply", record.ply, "move", record.move_number, record.san, record.uci)
print("fen_before", record.fen_before)
'''


def md(text: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": [line + "\n" for line in text.strip("\n").split("\n")]}


def code(text: str) -> dict:
    src = text.strip("\n") + "\n"
    return {"cell_type": "code", "metadata": {}, "outputs": [], "execution_count": None, "source": [src]}


ITEMS: list[dict] = [
    {
        "id": "001",
        "title": "Game import",
        "sf": False,
        "pgn": "f07_002_white.pgn",
        "player": "cmess1315",
        "color": "None",
        "san": "e4",
        "compare": "PGN del libro vs `NormalizedGame`: mismos SAN, FENs legales, headers.",
        "body": "print('plies', len(game.plies), 'result', game.result)\nprint([p.san for p in game.plies])",
    },
    {
        "id": "002",
        "title": "Player selection",
        "sf": False,
        "pgn": "f07_002_white.pgn",
        "player": "cmess1315",
        "color": "None",
        "san": "Qh5",
        "compare": "Solo plies del jugador del libro (Blancas o Negras).",
        "body": "print(player.username, player.color, 'n=', player.move_count)\nprint([p.san for p in player.plies])",
    },
    {
        "id": "003",
        "title": "Stockfish analyze_ply",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "cmess1315",
        "color": "None",
        "san": "Qxf7#",
        "compare": "Eval White-POV antes/después; mate en Qxf7#.",
        "body": "from analysis.engine_eval import analyze_ply, stockfish_available\n"
        "if not stockfish_available():\n    print('Sin Stockfish')\nelse:\n"
        "    a = analyze_ply(record.fen_before, record.uci, depth=12)\n"
        "    print(a.eval_before, '->', a.eval_after, a.engine_name)",
    },
    {
        "id": "004",
        "title": "Eval normalization",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "opponent",
        "color": "'black'",
        "san": "Nf6",
        "compare": "POV del jugador (negras): mate para blancas es negativo para negras.",
        "body": "from analysis.engine_eval import analyze_ply_for_player, stockfish_available\n"
        "if not stockfish_available():\n    print('Sin Stockfish')\nelse:\n"
        "    e = analyze_ply_for_player(record.fen_before, record.uci, player.color, depth=12)\n"
        "    print('before', e.before, 'after', e.after)",
    },
    {
        "id": "005",
        "title": "Evaluation loss",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "opponent",
        "color": "'black'",
        "san": "Nf6",
        "compare": "Chernev/Kasparov: error que pierde. `eval_loss` >= 150 en Nf6 del pastor.",
        "body": "from analysis.engine_eval import analyze_ply_for_player, ply_evaluation_loss, stockfish_available\n"
        "if not stockfish_available():\n    print('Sin Stockfish')\nelse:\n"
        "    e = analyze_ply_for_player(record.fen_before, record.uci, player.color, depth=12)\n"
        "    loss = ply_evaluation_loss(e)\n    print(loss)",
    },
    {
        "id": "006",
        "title": "EVALUATION_DROP",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "opponent",
        "color": "'black'",
        "san": "Nf6",
        "compare": "El doc §1: DROP es retrospectivo, no la advertencia previa. Anotá si el libro ya pedía calcular ANTES de Nf6.",
        "body": "from analysis.engine_eval import analyze_ply_for_player, stockfish_available\n"
        "from analysis.engine_triggers import ply_evaluation_drop\n"
        "if not stockfish_available():\n    print('Sin Stockfish')\nelse:\n"
        "    e = analyze_ply_for_player(record.fen_before, record.uci, player.color, depth=12)\n"
        "    t = ply_evaluation_drop(e)\n    print(t.code, 'fired', t.fired, 'loss', t.eval_loss)",
    },
    {
        "id": "007",
        "title": "ONLY_MOVE",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "cmess1315",
        "color": "None",
        "san": "e4",
        "compare": "Doc §2: gap>=150 no basta. Acá `e4` no debe disparar. Para única defensa usá FEN de octava (Rxd1) o un caso de libro 'única jugada'.",
        "body": "from analysis.engine_triggers import only_move_trigger, ply_only_move\n"
        "from analysis.multipv import analyze_multipv\n"
        "from analysis.engine_eval import stockfish_available\n"
        "BACK_RANK = '6k1/5ppp/8/8/8/8/5PPP/R2r2K1 w - - 0 1'\n"
        "if not stockfish_available():\n    print('Sin Stockfish; solo legal-count')\n"
        "    import chess\n    print('legal', chess.Board(BACK_RANK).legal_moves.count())\n"
        "else:\n"
        "    mpv = analyze_multipv(record.fen_before, depth=12, player_color=player.color)\n"
        "    print('opening', only_move_trigger(mpv))\n"
        "    print('back rank', ply_only_move(BACK_RANK, depth=8))",
    },
    {
        "id": "008",
        "title": "POSITION_TRANSFORMATION",
        "sf": False,
        "pgn": "sample_game4.pgn",
        "player": "cmess1315",
        "color": "None",
        "san": "f5",
        "compare": "Libro: ruptura / rey. Código: PAWN_BREAK en f5. Probar también O-O-O (cambiar TARGET_SAN).",
        "body": "from analysis.engine_triggers import position_transformation_trigger\n"
        "t = position_transformation_trigger(record.fen_before, record.uci)\n"
        "print(t.fired, t.detail)\n"
        "oo = next(p for p in game.plies if p.san == 'O-O-O')\n"
        "print('O-O-O', position_transformation_trigger(oo.fen_before, oo.uci))",
    },
    {
        "id": "012",
        "title": "Criticality score",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "opponent",
        "color": "'black'",
        "san": "Nf6",
        "compare": "Score 0–10. Doc: no basar criticidad solo en DROP.",
        "body": "from analysis.engine_eval import analyze_ply_for_player, stockfish_available\n"
        "from analysis.criticality import assess_ply_criticality\n"
        "if not stockfish_available():\n    print('Sin Stockfish')\nelse:\n"
        "    e = analyze_ply_for_player(record.fen_before, record.uci, player.color, depth=12)\n"
        "    c = assess_ply_criticality(record, e)\n    print(c.score, c.level, c.critical, c.reasons)",
    },
    {
        "id": "013",
        "title": "Ranking",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "opponent",
        "color": "'black'",
        "san": "Nf6",
        "compare": "Nf6 debería estar arriba. SCORE_ALL es lento.",
        "body": "from analysis.criticality import rank_player_game\n"
        "from analysis.engine_eval import stockfish_available\n"
        "if not stockfish_available():\n    print('Sin Stockfish')\nelse:\n"
        "    for row in rank_player_game(player, depth=8, top_n=5):\n"
        "        print(row.rank, row.item.san, row.item.score, row.item.level)",
    },
    {
        "id": "014",
        "title": "MultiPV",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "opponent",
        "color": "'black'",
        "san": "Nf6",
        "compare": "Tres candidatas vs expert_candidates del libro. Anotá gap PV1-PV2 en cp (doc §2).",
        "body": "from analysis.multipv import analyze_multipv\nfrom analysis.engine_eval import stockfish_available\n"
        "if not stockfish_available():\n    print('Sin Stockfish')\nelse:\n"
        "    mpv = analyze_multipv(record.fen_before, depth=12, multipv=3, player_color=player.color)\n"
        "    for line in mpv.lines:\n        print(line.multipv_rank, line.move_san, line.player_score, line.pv_san[:5])\n"
        "    if len(mpv.lines) >= 2:\n"
        "        gap = mpv.lines[0].player_score.as_cp_units() - mpv.lines[1].player_score.as_cp_units()\n"
        "        print('gap pv1-pv2', gap)",
    },
    {
        "id": "015",
        "title": "Played-move eval",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "opponent",
        "color": "'black'",
        "san": "Nf6",
        "compare": "Si Nf6 no está en top 3, source=independent.",
        "body": "from analysis.multipv import analyze_multipv, evaluate_played_move\n"
        "from analysis.engine_eval import stockfish_available\n"
        "if not stockfish_available():\n    print('Sin Stockfish')\nelse:\n"
        "    mpv = analyze_multipv(record.fen_before, depth=12, player_color=player.color)\n"
        "    p = evaluate_played_move(record.fen_before, record.uci, depth=12, player_color=player.color, multipv_result=mpv)\n"
        "    print(p.move_san, p.in_multipv, p.source, p.player_score)",
    },
    {
        "id": "016",
        "title": "UCI/SAN",
        "sf": False,
        "pgn": "f07_002_white.pgn",
        "player": "cmess1315",
        "color": "None",
        "san": "Qh5",
        "compare": "SAN del PGN = uci_to_san(fen, uci).",
        "body": "from analysis.notation import uci_to_san, san_to_uci, roundtrip_uci\n"
        "print(uci_to_san(record.fen_before, record.uci), san_to_uci(record.fen_before, record.san))\n"
        "print('roundtrip', roundtrip_uci(record.fen_before, record.uci))",
    },
    {
        "id": "019",
        "title": "Played vs candidates",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "opponent",
        "color": "'black'",
        "san": "Nf6",
        "compare": "Gap vs mejor vs 'mejor era…' del libro. Propósito D1–D5 es proxy, no F07-018.",
        "body": "from analysis.comparison import compare_played_to_candidates\n"
        "from analysis.engine_eval import stockfish_available\n"
        "if not stockfish_available():\n    print('Sin Stockfish')\nelse:\n"
        "    vs = compare_played_to_candidates(record.fen_before, record.uci, depth=12, player_color=player.color)\n"
        "    print('best', vs.best.move_san if vs.best else None, 'gap', vs.eval_gap_vs_best_cp)\n"
        "    for row in vs.diffs:\n        print(row.candidate.move_san, row.eval_gap_cp, row.purpose.value)",
    },
    {
        "id": "028",
        "title": "Abstention",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "opponent",
        "color": "'black'",
        "san": "Nf6",
        "compare": "Nf6: NONE (se puede diagnosticar). 1.e4: UNKNOWN. No inventar causa cognitiva.",
        "body": "from analysis.comparison import compare_played_to_candidates\n"
        "from analysis.abstention import assess_diagnosis_abstention\n"
        "from analysis.engine_eval import stockfish_available\n"
        "if not stockfish_available():\n    print('Sin Stockfish')\nelse:\n"
        "    vs = compare_played_to_candidates(record.fen_before, record.uci, depth=12, player_color=player.color)\n"
        "    g = assess_diagnosis_abstention(vs)\n    print(g.status, g.reasons, g.message)",
    },
    {
        "id": "035",
        "title": "Review pack",
        "sf": True,
        "pgn": "f07_002_white.pgn",
        "player": "opponent",
        "color": "'black'",
        "san": "Nf6",
        "compare": "JSON vs plantilla expert_gold: FEN, candidatas, evidencia. primary_error debe ser null.",
        "body": "from analysis.comparison import compare_played_to_candidates\n"
        "from analysis.abstention import assess_diagnosis_abstention\n"
        "from analysis.review_pack import build_review_pack, write_review_pack, default_review_pack_name\n"
        "from analysis.engine_eval import stockfish_available\n"
        "if not stockfish_available():\n    print('Sin Stockfish')\nelse:\n"
        "    vs = compare_played_to_candidates(record.fen_before, record.uci, depth=12, player_color=player.color)\n"
        "    pack = build_review_pack(game, record, player, vs, assess_diagnosis_abstention(vs), pgn_source=str(PGN_PATH))\n"
        "    path = COURSE_ROOT / 'artifacts' / 'module07' / default_review_pack_name(game.game_id, record.ply, record.san)\n"
        "    write_review_pack(pack, path)\n    print(path)\n    print(pack['status'], pack['actual_result']['primary_error'], len(pack['candidates']))",
    },
]


def build(item: dict) -> dict:
    color = item["color"]
    cells = [
        md(
            f"# F07-{item['id']} — {item['title']}\n\n"
            f"Lab parcial. Compará con `data/expert_gold/` (libros primero).\n\n"
            f"**Stockfish:** {'sí' if item['sf'] else 'no'}.\n\n"
            f"**Qué comparar:** {item['compare']}"
        ),
        code(
            BOOTSTRAP
            + f'\nPGN_NAME = "{item["pgn"]}"\n'
            + f'PLAYER_NAME = "{item["player"]}"\n'
            + f"PLAYER_COLOR = {color}\n"
            + f'TARGET_SAN = "{item["san"]}"\n'
        ),
        code(LOAD),
        code(item["body"]),
        md(
            "Anotá acá (o en `expert_gold.jsonl`): ¿el experto pedía detenerse **antes** de la jugada? "
            "¿Coinciden candidatas? ¿El motor discrepa?"
        ),
    ]
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
        },
        "cells": cells,
    }


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:40]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    index_rows = ["# Labs F07 (parciales)\n", "Generados por `_gen_f07_item_labs.py`. Abrilos desde `docs/ai_chess_coach_course/`.\n"]
    for item in ITEMS:
        path = OUT / f"07_f07_{item['id']}_{_slug(item['title'])}.ipynb"
        path.write_text(json.dumps(build(item), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        index_rows.append(f"- [F07-{item['id']} {item['title']}]({path.name})")
    (OUT / "README.md").write_text("\n".join(index_rows) + "\n", encoding="utf-8")
    print("Wrote", len(ITEMS), "notebooks in", OUT)


if __name__ == "__main__":
    main()
