# modules/exercise_utils.py

import os
import json
from datetime import datetime
from tactical_analysis import detect_tactics_from_game  
from pgn_utils import extract_fen_labels_from_game

EXERCISE_DIR = "data/generated_exercises/"

def generate_exercise_from_game(game, game_id=None):
    """
    Extrae tácticas de una partida y las guarda como archivo JSON.
    """
    if not game_id:
        game_id = f"{game.headers.get('White', 'unknown')}_vs_{game.headers.get('Black', 'unknown')}_{game.headers.get('Date', '0000.00.00')}"
        game_id = game_id.replace(" ", "_").replace(".", "-")

    fen_labels = extract_fen_labels_from_game(game)
    tactical_tags = detect_tactics_from_game(game)

    if not tactical_tags:
        print("No se detectaron tácticas relevantes en la partida.")
        return  # No hay táctica relevante

    os.makedirs(EXERCISE_DIR, exist_ok=True)
    output_path = os.path.join(EXERCISE_DIR, f"{game_id}.json")

    exercise_data = {
        "game_id": game_id,
        "date_generated": datetime.now().isoformat(),
        "tactical_tags": tactical_tags,
        "fen_labels": fen_labels,
        "source": "elite"
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(exercise_data, f, indent=2, ensure_ascii=False)
