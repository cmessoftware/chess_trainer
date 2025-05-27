import os
import sqlite3
import chess.pgn
import chess.engine
import io
import json

STOCKFISH_PATH = "/usr/bin/stockfish"  # Ajustá según tu entorno
MAX_MOVES = 15  # Analizar solo primeras N jugadas
BLUNDER_THRESHOLD = 150  # en centipawns
DB_PATH = os.environ.get("CHESS_TRAINER_DB", "chess_trainer.db")

def analyze_game_errors(pgn_text):
    tags = set()
    try:
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        board = game.board()
        moves = list(game.mainline_moves())

        with chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH) as engine:
            for i, move in enumerate(moves[:MAX_MOVES]):
                info_before = engine.analyse(board, chess.engine.Limit(depth=12))
                score_before = info_before["score"].white().score(mate_score=10000)

                board.push(move)

                info_after = engine.analyse(board, chess.engine.Limit(depth=12))
                score_after = info_after["score"].white().score(mate_score=10000)

                if score_before is not None and score_after is not None:
                    diff = abs(score_before - score_after)
                    if diff >= BLUNDER_THRESHOLD:
                        tags.add("blunder")

                # Heurística de jugada rápida impulsiva
                if i <= 5 and diff >= 100:
                    tags.add("impulsive_mistake")

            # Reglas posicionales simples
            if not board.has_castling_rights(chess.WHITE) and not board.has_castling_rights(chess.BLACK):
                if board.fullmove_number < 10:
                    tags.add("undeveloped")

    except Exception as e:
        print(f"❌ Error processing PGN: {e}")
    return list(tags)


def process_games(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, pgn, tags FROM games")
    games = cursor.fetchall()

    for gid, pgn, tag_json in games:
        new_tags = analyze_game_errors(pgn)
        existing_tags = json.loads(tag_json) if tag_json else []
        full_tags = list(set(existing_tags + new_tags))
        cursor.execute("UPDATE games SET tags = ? WHERE id = ?", (json.dumps(full_tags), gid))

    conn.commit()
    conn.close()
    print(f"✅ Processed {len(games)} game(s)")


if __name__ == "__main__":
    process_games()
