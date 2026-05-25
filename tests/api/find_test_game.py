"""
Script para encontrar un game_id con features y análisis existentes
"""

import sys
import os

# Agregar path del proyecto
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, "src"))
sys.path.insert(0, os.path.join(project_root, "src", "api"))

from api.database import SessionLocal
from db.models.features import Features
from db.models.games import Games
from sqlalchemy import func

db = SessionLocal()

try:
    # Buscar games con features
    print("Buscando games con features...")

    games_with_features = (
        db.query(Features.game_id, func.count(Features.game_id).label("feature_count"))
        .group_by(Features.game_id)
        .having(func.count(Features.game_id) > 20)  # Al menos 20 movimientos
        .limit(10)
        .all()
    )

    print(f"\n{len(games_with_features)} games encontrados con features:\n")

    for game_id, count in games_with_features:
        # Verificar que el game exista
        game = db.query(Games).filter(Games.game_id == game_id).first()
        if game:
            print(f"  - {game_id}")
            print(f"    Features: {count}")
            print(f"    Result: {game.result}")
            print(f"    White: {game.white_player} (ELO: {game.white_elo})")
            print(f"    Black: {game.black_player} (ELO: {game.black_elo})")
            print()

    if games_with_features:
        print(f"\nUsar este game_id para tests: {games_with_features[0][0]}")

finally:
    db.close()
