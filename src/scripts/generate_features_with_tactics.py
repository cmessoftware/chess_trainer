#!/usr/bin/env python3
"""
Integrated feature generation with tactical analysis.
Combines basic feature extraction with Stockfish-based tactical evaluation.
"""

from db.repository.games_repository import GamesRepository
from db.repository.features_repository import FeaturesRepository
from scripts.analyze_games_tactics_parallel import analyze_game_parallel
import argparse
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from dotenv import load_dotenv

# Add src to path for imports
sys.path.append('/app/src')


load_dotenv()


def process_game_with_tactics(game_id: str):
    """Process a single game with both features and tactical analysis."""
    try:
        # First, generate basic features
        print(f"🎯 Processing game {game_id} - generating features...")

        # Then, run tactical analysis
        print(f"🧠 Processing game {game_id} - analyzing tactics...")
        game_id_result, tags_df = analyze_game_parallel(game_id)

        if tags_df is not None:
            features_repo = FeaturesRepository()
            features_repo.update_features_tags_and_score_diff(game_id, tags_df)
            print(
                f"✅ Game {game_id} completed with {len(tags_df)} tactical tags")
        else:
            print(f"⚠️ Game {game_id} completed - no tactical patterns found")

        return game_id, True

    except Exception as e:
        print(f"❌ Error processing game {game_id}: {e}")
        return game_id, False


def run_integrated_processing(source: str = None, max_games: int = 1000):
    """Run integrated feature generation and tactical analysis."""

    print(f"🚀 Starting integrated feature generation with tactical analysis...")
    print(f"📋 Parameters:")
    print(f"   - Source filter: {source}")
    print(f"   - Max games: {max_games}")

    games_repo = GamesRepository()

    # Get games that need processing (games without features)
    if source:
        # We need to get games by source that don't have features yet
        # Let's use a direct database query approach
        from sqlalchemy import select, not_, exists
        from db.models.games import Games
        from db.models.features import Features

        with games_repo.session_factory() as session:
            # Find games from source that don't have corresponding features
            stmt = select(Games).where(Games.source == source)
            if max_games:
                stmt = stmt.limit(max_games)
            games = session.execute(stmt).scalars().all()
    else:
        # Get games without source filter
        from sqlalchemy import select
        from db.models.games import Games

        with games_repo.session_factory() as session:
            stmt = select(Games)
            if max_games:
                stmt = stmt.limit(max_games)
            games = session.execute(stmt).scalars().all()

    print(f"📊 Found {len(games)} games to process")

    if not games:
        print("⚠️ No games found to process")
        return

    # Process games with both features and tactics
    successful = 0
    failed = 0

    # Lower workers due to Stockfish usage
    with ProcessPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(
            process_game_with_tactics, game.game_id) for game in games]

        for future in futures:
            game_id, success = future.result()
            if success:
                successful += 1
            else:
                failed += 1

    print(f"✅ Processing completed:")
    print(f"   - Successful: {successful}")
    print(f"   - Failed: {failed}")
    print(f"   - Success rate: {(successful/(successful+failed)*100):.1f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Integrated feature generation with tactical analysis"
    )
    parser.add_argument("--source", type=str, help="Filter games by source")
    parser.add_argument("--max-games", type=int, default=1000,
                        help="Maximum number of games to process")

    args = parser.parse_args()

    run_integrated_processing(source=args.source, max_games=args.max_games)
