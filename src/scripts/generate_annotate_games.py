import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from modules.annotate_game import annotate_game
from modules.pgn_utils import load_pgn_from_file, game_to_string, save_game_to_file

pgn_path = "src/data/games/SigamaMega_vs_cmess1315_2025.05.27.pgn"

game = load_pgn_from_file(pgn_path)
annotated = annotate_game(game, use_stockfish=False, use_commentator=True)
pgn_path_no_ext = os.path.splitext(pgn_path)[0]
save_game_to_file(annotated, f"{pgn_path_no_ext}.annotated.pgn")
print(game_to_string(annotated))
