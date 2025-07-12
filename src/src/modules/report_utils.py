import os
import chess
from modules.feature_engineering import is_center_controlled, is_pawn_endgame
from pgn_utils import get_game_id


def check_pgn_headers(directory):
    results = []
    for filename in os.listdir(directory):
        if filename.endswith(".pgn"):
            path = os.path.join(directory, filename)
            with open(path, "r", encoding="utf-8") as f:
                while True:
                    game = chess.pgn.read_game(f)
                    if game is None:
                        break
                    setup = game.headers.get("SetUp", "0")
                    fen = game.headers.get("FEN", None)
                    if setup == "1" and fen:
                        results.append(
                            (filename, game.headers.get("Event", ""), fen))
    return results

# Usalo así:
# resultados = check_pgn_headers("data/games")
# for archivo, evento, fen in resultados:
#     print(f"🎯 Juego con FEN en {archivo} ({evento}): {fen}")
