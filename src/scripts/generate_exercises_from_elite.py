import sqlite3
import chess.pgn
import chess.engine
import json
import io
import os

STOCKFISH_PATH = "/usr/bin/stockfish"
DB_PATH = os.environ.get("CHESS_TRAINER_DB", "chess_trainer.db")
OUTPUT_DIR = "data/tactics/elite"
TAGS = ["sacrifice", "blunder", "tactical"]
MAX_EXERCISES = 50

os.makedirs(OUTPUT_DIR, exist_ok=True)

engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT id, pgn, tags FROM games")
rows = cursor.fetchall()

exercise_id = 0
for gid, pgn_text, tag_json in rows:
    tags = json.loads(tag_json) if tag_json else []
    if not any(tag in tags for tag in TAGS):
        continue

    game = chess.pgn.read_game(io.StringIO(pgn_text))
    board = game.board()
    moves = list(game.mainline_moves())

    for i, move in enumerate(moves):
        board_before = board.copy()
        info = engine.analyse(board, chess.engine.Limit(depth=12))
        score_before = info["score"].white().score(mate_score=10000)

        board.push(move)
        info = engine.analyse(board, chess.engine.Limit(depth=12))
        score_after = info["score"].white().score(mate_score=10000)

        if score_before is not None and score_after is not None:
            drop = score_before - score_after
            if drop >= 150:
                fen = board_before.fen()
                san = board_before.san(move)
                solution = move.uci()

                exercise = {
                    "id": f"elite_{exercise_id}",
                    "fen": fen,
                    "move": san,
                    "uci": solution,
                    "tags": tags,
                    "source_game_id": gid
                }
                with open(f"{OUTPUT_DIR}/elite_{exercise_id}.json", "w") as f:
                    json.dump(exercise, f, indent=2)
                exercise_id += 1
                if exercise_id >= MAX_EXERCISES:
                    break
    if exercise_id >= MAX_EXERCISES:
        break

conn.close()
engine.quit()
print(f"✅ {exercise_id} exercise(s) saved to {OUTPUT_DIR}/")
