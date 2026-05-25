"""
Script para encontrar games con features por rangos de ELO
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
from sqlalchemy import func, or_, and_, Integer, cast

db = SessionLocal()

try:
    # Definir rangos ELO
    elo_ranges = [
        ("NOVICE", 1300, 1500),
        ("INTERMEDIATE", 1700, 1900),
        ("ADVANCED", 2300, 2500),
    ]

    for label, elo_min, elo_max in elo_ranges:
        print(f"\n{'='*70}")
        print(f"  {label} (ELO {elo_min}-{elo_max})")
        print(f"{'='*70}\n")

        # Buscar games donde white o black esté en el rango
        games_with_features = (
            db.query(
                Games.game_id,
                Games.white_player,
                Games.white_elo,
                Games.black_player,
                Games.black_elo,
                Games.result,
                func.count(Features.game_id).label("feature_count"),
            )
            .join(Features, Games.game_id == Features.game_id)
            .filter(
                or_(
                    and_(
                        Games.white_elo.isnot(None),
                        Games.white_elo != "",
                        cast(Games.white_elo, Integer) >= elo_min,
                        cast(Games.white_elo, Integer) <= elo_max,
                    ),
                    and_(
                        Games.black_elo.isnot(None),
                        Games.black_elo != "",
                        cast(Games.black_elo, Integer) >= elo_min,
                        cast(Games.black_elo, Integer) <= elo_max,
                    ),
                )
            )
            .group_by(
                Games.game_id,
                Games.white_player,
                Games.white_elo,
                Games.black_player,
                Games.black_elo,
                Games.result,
            )
            .having(func.count(Features.game_id) > 20)  # Al menos 20 features
            .limit(3)  # Top 3 por nivel
            .all()
        )

        if games_with_features:
            for i, game in enumerate(games_with_features, 1):
                print(f"{i}. Game ID: {game.game_id}")
                print(f"   Features: {game.feature_count}")
                print(f"   Result: {game.result}")
                print(f"   White: {game.white_player} (ELO: {game.white_elo or 'N/A'})")
                print(f"   Black: {game.black_player} (ELO: {game.black_elo or 'N/A'})")
                print()
        else:
            print(f"   ❌ No se encontraron games con features en este rango\n")

    print(f"\n{'='*70}")
    print("  RESUMEN PARA POSTMAN COLLECTION")
    print(f"{'='*70}\n")

    print("Usar estos game_ids en tu colección:\n")

    for label, elo_min, elo_max in elo_ranges:
        games = (
            db.query(Games.game_id)
            .join(Features, Games.game_id == Features.game_id)
            .filter(
                or_(
                    and_(
                        Games.white_elo.isnot(None),
                        Games.white_elo != "",
                        cast(Games.white_elo, Integer) >= elo_min,
                        cast(Games.white_elo, Integer) <= elo_max,
                    ),
                    and_(
                        Games.black_elo.isnot(None),
                        Games.black_elo != "",
                        cast(Games.black_elo, Integer) >= elo_min,
                        cast(Games.black_elo, Integer) <= elo_max,
                    ),
                )
            )
            .group_by(Games.game_id)
            .having(func.count(Features.game_id) > 20)
            .limit(1)
            .first()
        )

        if games:
            print(f"{label:15} → {games.game_id}")

finally:
    db.close()
