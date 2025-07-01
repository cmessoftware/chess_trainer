from dotenv import load_dotenv
import os
import chess
import chess.engine
import chess.pgn
import json
import io
from db.tactical_db import save_tactic_to_db
from db.postgres_utils import execute_postgres_query
import dotenv
dotenv.load_dotenv()


STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH")
if not STOCKFISH_PATH:
    raise ValueError("STOCKFISH_PATH environment variable is not set.")

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
if not DB_URL:
    raise ValueError("CHESS_TRAINER_DB_URL environment variable is not set.")

OUTPUT_DIR = "data/tactics/elite"
TAGS = ["sacrifice", "blunder", "tactical"]
MAX_EXERCISES = 50

# MIGRATED-TODO: Migrate code to repository pattern and use a repository for exercises


def generate_elite_exercises(depth=10, multipv=3):

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

    # Get games from PostgreSQL (tags are now in features table)
    games = execute_postgres_query("SELECT game_id, pgn FROM games")

    exercise_id = 0
    for row in games:
        gid, pgn_text = row['game_id'], row['pgn']

        # Get tags from features table for this game if needed
        # For now, we'll skip the tag filtering and process all games
        # For now, process all games (tags filtering can be added later from features table)
        tags = TAGS  # Use default tags for processing
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

    engine.quit()
    print(
        f"✅ {exercise_id} exercise(s) saved to table tactical_exercises in PostgreSQL")


# To run:
if __name__ == "__main__":
    generate_elite_exercises()
