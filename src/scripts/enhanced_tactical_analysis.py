#!/usr/bin/env python3
"""
Enhanced batch tactical analysis for better coverage.
Optimized version of analyze_games_tactics_parallel.py with better efficiency.
"""

from scripts.analyze_games_tactics_parallel import analyze_game_parallel
from db.repository.games_repository import GamesRepository
from db.repository.features_repository import FeaturesRepository
from db.repository.analyzed_tacticals_repository import Analyzed_tacticalsRepository
import argparse
import os
import sys
import signal
import atexit
import psutil
from concurrent.futures import ProcessPoolExecutor, as_completed
from dotenv import load_dotenv

sys.path.append('/app/src')

load_dotenv()

# Global variables for cleanup
active_processes = []
current_executor = None


def cleanup_processes():
    """Clean up any remaining processes"""
    global active_processes, current_executor

    print("🧹 Cleaning up processes...")

    if current_executor:
        try:
            current_executor.shutdown(wait=False, cancel_futures=True)
        except:
            pass

    # Kill any remaining stockfish processes
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            if 'stockfish' in proc.info['name'].lower():
                proc.terminate()
        except:
            pass

    # Clean up any zombie processes
    for proc_info in active_processes:
        try:
            if proc_info and proc_info.is_running():
                proc_info.terminate()
        except:
            pass


def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print(f"\n🛑 Received signal {signum}, shutting down gracefully...")
    cleanup_processes()
    sys.exit(0)


# Register cleanup functions
atexit.register(cleanup_processes)
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def run_enhanced_tactical_analysis(source: str = None, max_games: int = 1000, force_reprocess: bool = False):
    """
    Run enhanced tactical analysis with better coverage and efficiency.

    Args:
        source: Filter games by source
        max_games: Maximum number of games to process
        force_reprocess: Reprocess games that already have some tactical data
    """
    global current_executor, active_processes

    print(f"🧠 Starting enhanced tactical analysis...")
    print(f"📋 Parameters:")
    print(f"   - Source filter: {source}")
    print(f"   - Max games: {max_games}")
    print(f"   - Force reprocess: {force_reprocess}")

    features_repo = FeaturesRepository()
    analyzed_tacticals_repo = Analyzed_tacticalsRepository()

    # Get games that need tactical analysis
    if force_reprocess:
        # Process all games regardless of existing tactical data
        if source:
            game_ids = features_repo.get_game_ids_with_features_by_source(
                source, max_games)
        else:
            game_ids = features_repo.get_game_ids_with_features(max_games)
    else:
        # Only process games without tactical data and not already analyzed
        if source:
            game_ids = features_repo.get_unanalyzed_game_ids_by_source(
                source, max_games)
        else:
            game_ids = features_repo.get_unanalyzed_game_ids(max_games)

    if not game_ids:
        print("⚠️ No games found that need tactical analysis")
        return

    print(f"📊 Found {len(game_ids)} games to analyze")

    # Process games in smaller batches for better memory management
    batch_size = 50
    successful = 0
    failed = 0

    try:
        for i in range(0, len(game_ids), batch_size):
            batch = game_ids[i:i + batch_size]
            print(
                f"🔄 Processing batch {i//batch_size + 1}/{(len(game_ids) + batch_size - 1)//batch_size}")

            # Conservative worker count
            # Limit to 2 workers to avoid resource issues
            max_workers = min(2, os.cpu_count() or 1)

            current_executor = ProcessPoolExecutor(max_workers=max_workers)
            try:
                futures = [current_executor.submit(
                    analyze_game_parallel, game_id) for game_id in batch]

                # 15 minute timeout for batch
                for future in as_completed(futures, timeout=900):
                    try:
                        game_id, tags_df = future.result(
                            timeout=300)  # 5 minute timeout per game

                        if tags_df is not None and len(tags_df) > 0:
                            features_repo.update_features_tags_and_score_diff(
                                game_id, tags_df)
                            print(
                                f"✅ Game {game_id} analyzed - {len(tags_df)} tactical features")
                            successful += 1
                        else:
                            print(
                                f"⚠️ Game {game_id} analyzed - no tactical patterns found")
                            successful += 1  # Still count as successful

                        # Always register that the game has been analyzed
                        try:
                            analyzed_tacticals_repo.save_analyzed_tactical_hash(
                                game_id)
                            print(
                                f"📝 Game {game_id} registered in analyzed_tacticals table")
                        except Exception as e:
                            print(
                                f"⚠️ Warning: Could not register game {game_id} in analyzed_tacticals: {e}")

                    except Exception as e:
                        print(f"❌ Error analyzing game: {e}")
                        failed += 1
                        # Still try to register the game to avoid reprocessing
                        try:
                            # Extract game_id from future if possible
                            if hasattr(future, '_state') and future._state == 'FINISHED':
                                try:
                                    game_id, _ = future.result(timeout=1)
                                except:
                                    game_id = batch[futures.index(future)] if futures.index(
                                        future) < len(batch) else "unknown"
                            else:
                                game_id = "unknown"

                            if game_id != "unknown":
                                analyzed_tacticals_repo.save_analyzed_tactical_hash(
                                    game_id)
                                print(
                                    f"📝 Game {game_id} registered as failed in analyzed_tacticals table")
                        except:
                            pass  # Don't fail the whole process for registration issues

            finally:
                # Explicitly shutdown the executor with timeout
                if current_executor:
                    try:
                        current_executor.shutdown(
                            wait=True, cancel_futures=True)
                        print(
                            f"🔄 Batch {i//batch_size + 1} completed, executor shutdown successfully")
                    except Exception as e:
                        print(f"⚠️ Warning during executor shutdown: {e}")
                    finally:
                        current_executor = None

    except KeyboardInterrupt:
        print("🛑 Analysis interrupted by user")
        cleanup_processes()
        return
    except Exception as e:
        print(f"❌ Unexpected error during analysis: {e}")
        cleanup_processes()
        return
    finally:
        # Final cleanup
        cleanup_processes()

    print(f"✅ Enhanced tactical analysis completed:")
    print(f"   - Successful: {successful}")
    print(f"   - Failed: {failed}")
    print(f"   - Success rate: {(successful/(successful+failed)*100):.1f}%")

    # Report coverage improvement
    if source:
        tactical_coverage = features_repo.get_tactical_coverage_by_source(
            source)
        games_coverage = analyzed_tacticals_repo.get_analysis_coverage_by_source(
            source)
    else:
        tactical_coverage = features_repo.get_tactical_coverage()
        games_coverage = analyzed_tacticals_repo.get_analysis_coverage()

    print(f"📊 Current tactical coverage:")
    print(
        f"   - Features: {tactical_coverage['with_tactical']}/{tactical_coverage['total']} ({tactical_coverage['percentage']:.1f}%)")
    print(
        f"   - Games analyzed: {games_coverage['analyzed']}/{games_coverage['total']} ({games_coverage['percentage']:.1f}%)")

    print("🏁 Analysis process completed - returning control to terminal")
    sys.stdout.flush()
    sys.stderr.flush()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enhanced batch tactical analysis for better coverage"
    )
    parser.add_argument("--source", type=str, help="Filter games by source")
    parser.add_argument("--max-games", type=int, default=1000,
                        help="Maximum number of games to process")
    parser.add_argument("--force-reprocess", action="store_true",
                        help="Reprocess games that already have tactical data")

    args = parser.parse_args()

    try:
        run_enhanced_tactical_analysis(
            source=args.source,
            max_games=args.max_games,
            force_reprocess=args.force_reprocess
        )
    except KeyboardInterrupt:
        print("🛑 Analysis interrupted by user")
        cleanup_processes()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Unexpected error in main: {e}")
        cleanup_processes()
        sys.exit(1)
    finally:
        print("🏁 Main execution completed - exiting cleanly")
        cleanup_processes()
        sys.exit(0)
