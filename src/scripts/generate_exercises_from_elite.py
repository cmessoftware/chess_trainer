from dotenv import load_dotenv
import os
import chess
import chess.engine
import chess.pgn
import sqlite3
import json
import io
from db.tactical_db import save_tactic_to_db
import dotenv
dotenv.load_dotenv()


STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH")
if not STOCKFISH_PATH:
    raise ValueError("STOCKFISH_PATH environment variable is not set.")

DB_PATH = os.environ.get("CHESS_TRAINER_DB")
if not DB_PATH:
    raise ValueError("CHESS_TRAINER_DB environment variable is not set.")

OUTPUT_DIR = "data/tactics/elite"
TAGS = ["sacrifice", "blunder", "tactical"]
MAX_EXERCISES = 50

#MIGRATED-TODO: Migrate code to repository pattern and use a repository for exercises


def generate_elite_exercises(depth=10, multipv=3):

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT game_id, pgn, tags FROM games")
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
            info = engine.analyse(board, chess.engine.Limit(
                depth=depth), multipv=multipv)
            if multipv == 1:
                info = [info]
                score_before = info["score"].white().score(mate_score=10000)
            else:
                score_before = info[0]["score"].white().score(mate_score=10000)
            if score_before is None:
                continue

            board.push(move)
            info = engine.analyse(board, chess.engine.Limit(
                depth=depth), multipv=multipv)
            if multipv == 1:
                info = [info]
                score_after = info["score"].white().score(mate_score=10000)
            else:
                score_after = info[0]["score"].white().score(mate_score=10000)
            if score_before is None or score_after is None:
                continue

            if score_before is not None and score_after is not None:
                drop = score_before - score_after
                if drop >= 150:
                    fen = board_before.fen()
                    san = board_before.san(move)
                    solution = move.uci()

                    exercise = {
                        "id": exercise_id,
                        "fen": fen,
                        "move": san,
                        "uci": solution,
                        "tags": tags,
                        "source_game_id": gid
                    }
                    save_tactic_to_db(exercise)
                    exercise_id += 1
                    if exercise_id >= MAX_EXERCISES:
                        break
        if exercise_id >= MAX_EXERCISES:
            break

    conn.close()
    engine.quit()
    print(
        f"✅ {exercise_id} exercise(s) saved to table tactical_exercises in {DB_PATH}")


# To run:
if __name__ == "__main__":
    generate_elite_exercises()
