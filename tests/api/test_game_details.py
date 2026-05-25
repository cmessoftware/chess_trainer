"""
Script para obtener detalles de un game_id específico
"""

import sys
import os

# Add src to path
sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src"))
)

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Database connection
DATABASE_URL = "postgresql://chess_user:chess_password@localhost:5432/chess_trainer_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_game_details(game_id: str):
    """Get game details including features count"""
    db = SessionLocal()

    try:
        # Get game info
        game_query = text(
            """
            SELECT 
                white_player,
                black_player,
                white_elo,
                black_elo,
                result,
                total_moves
            FROM games
            WHERE game_id = :game_id
        """
        )

        game = db.execute(game_query, {"game_id": game_id}).fetchone()

        if not game:
            print(f"❌ Game {game_id} not found")
            return

        print(f"\n{'='*80}")
        print(f"🎮 GAME DETAILS: {game_id}")
        print(f"{'='*80}")
        print(f"White: {game.white_player} (ELO: {game.white_elo})")
        print(f"Black: {game.black_player} (ELO: {game.black_elo})")
        print(f"Result: {game.result}")
        print(f"Total Moves: {game.total_moves}")

        # Get features count
        features_query = text(
            """
            SELECT 
                COUNT(*) FILTER (WHERE player_color = 'white') as white_features,
                COUNT(*) FILTER (WHERE player_color = 'black') as black_features
            FROM features
            WHERE game_id = :game_id
        """
        )

        features = db.execute(features_query, {"game_id": game_id}).fetchone()

        print(f"\n📊 FEATURES:")
        print(f"White features: {features.white_features}")
        print(f"Black features: {features.black_features}")

        # Get SHAP model counts
        shap_query = text(
            """
            SELECT 
                COUNT(*) FILTER (WHERE player_color = 'white') as white_shaps,
                COUNT(*) FILTER (WHERE player_color = 'black') as black_shaps
            FROM shap_model_results
            WHERE game_id = :game_id
        """
        )

        shaps = db.execute(shap_query, {"game_id": game_id}).fetchone()

        print(f"\n🔬 SHAP RESULTS:")
        print(f"White SHAPs: {shaps.white_shaps}")
        print(f"Black SHAPs: {shaps.black_shaps}")

        # Get error distribution by player
        errors_white_query = text(
            """
            SELECT error_label, COUNT(*) as count
            FROM features
            WHERE game_id = :game_id AND player_color = 'white'
            AND error_label IN ('blunder', 'mistake', 'inaccuracy')
            GROUP BY error_label
            ORDER BY count DESC
        """
        )

        errors_black_query = text(
            """
            SELECT error_label, COUNT(*) as count
            FROM features
            WHERE game_id = :game_id AND player_color = 'black'
            AND error_label IN ('blunder', 'mistake', 'inaccuracy')
            GROUP BY error_label
            ORDER BY count DESC
        """
        )

        errors_white = db.execute(errors_white_query, {"game_id": game_id}).fetchall()
        errors_black = db.execute(errors_black_query, {"game_id": game_id}).fetchall()

        print(f"\n⚠️ ERRORS BY PLAYER:")
        print(f"White errors:")
        for error in errors_white:
            print(f"  - {error.error_label}: {error.count}")

        print(f"Black errors:")
        for error in errors_black:
            print(f"  - {error.error_label}: {error.count}")

        print(f"\n{'='*80}")
        print(f"✅ GAME READY FOR TESTING")
        print(f"{'='*80}")
        print(f"\nRECOMMENDED TEST REQUESTS:")
        print(f"\n1. Test White Player:")
        print(f"   POST /analysis/llm-report")
        print(f"   {{")
        print(f'     "game_id": "{game_id}",')
        print(f'     "player_color": "white",')
        print(f'     "player_elo": {game.white_elo or 1500}')
        print(f"   }}")

        print(f"\n2. Test Black Player:")
        print(f"   POST /analysis/llm-report")
        print(f"   {{")
        print(f'     "game_id": "{game_id}",')
        print(f'     "player_color": "black",')
        print(f'     "player_elo": {game.black_elo or 1500}')
        print(f"   }}")

    finally:
        db.close()


if __name__ == "__main__":
    game_id = "aec7f86c250f0248fa65d9e1c5a320609ebe04ceaa09a0da601855bc404b71eb"
    get_game_details(game_id)
