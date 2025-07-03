#!/usr/bin/env python3
"""
Smart Random Games Fetcher for Chess Analysis Pipeline

This script implements intelligent game fetching strategies combining user discovery,
random sampling, and quality filtering to obtain diverse chess games for analysis.

Usage Examples:
    # Fetch random games from intermediate Lichess users
    python smart_random_games_fetcher.py --platform lichess --skill-level intermediate --max-games 100

    # Fetch games from both platforms with mixed skill levels
    python smart_random_games_fetcher.py --platform both --skill-level all --max-games 500 --output random_games.pgn

    # Fetch recent rapid games only
    python smart_random_games_fetcher.py --platform lichess --game-types rapid --max-games 200 --since 2024-01-01

    # Use pre-discovered users from file
    python smart_random_games_fetcher.py --users-file discovered_users.json --max-games 300

Environment Variables:
    CHESS_TRAINER_DB_URL: PostgreSQL connection URL (for avoiding duplicate games)
    PGN_PATH: Base path for PGN file storage
    GAME_FETCH_WORKERS: Number of parallel workers (default: 4)
    GAME_FETCH_RATE_LIMIT: Requests per second limit (default: 1.0)

Features:
    - Intelligent user discovery and game fetching
    - Multi-platform support (Lichess, Chess.com)
    - Quality filtering (minimum moves, time controls, ratings)
    - Duplicate game detection and avoidance
    - Balanced sampling across skill levels and time periods
    - Parallel fetching with rate limiting
    - Robust error handling and resumability
    - Multiple output formats (PGN, JSON metadata)
"""

import dotenv
import argparse
import json
import os
import random
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
import logging
import hashlib
import chess.pgn
from io import StringIO

# Import our smart user helper
from smart_user_helper import SmartUserDiscovery, Platform, SkillLevel, GameType, UserProfile

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("smart_games_fetcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()

# Configuration
DB_URL = os.environ.get("CHESS_TRAINER_DB_URL")
PGN_PATH = os.environ.get("PGN_PATH", "/app/data/games")
MAX_WORKERS = int(os.environ.get("GAME_FETCH_WORKERS", 4))
RATE_LIMIT = float(os.environ.get("GAME_FETCH_RATE_LIMIT", 1.0))
REQUEST_TIMEOUT = int(os.environ.get("GAME_FETCH_TIMEOUT", 30))

# Game quality filters
MIN_MOVES = int(os.environ.get("MIN_GAME_MOVES", 20))
MIN_RATING = int(os.environ.get("MIN_PLAYER_RATING", 800))
MAX_RATING = int(os.environ.get("MAX_PLAYER_RATING", 3500))


@dataclass
class GameMetadata:
    game_id: str
    platform: str
    white_player: str
    black_player: str
    white_rating: int
    black_rating: int
    time_control: str
    game_type: str
    result: str
    opening: str
    date: str
    url: str
    moves_count: int
    duration_seconds: Optional[int]
    fetch_date: datetime
    pgn_text: str


class SmartGamesFetcher:
    """
    Intelligent chess games fetcher with multiple discovery and sampling strategies.
    """

    def __init__(self):
        self.fetched_games: List[GameMetadata] = []
        self.known_game_ids: Set[str] = set()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "chess_trainer/1.0 (+https://github.com/cmessoftware/chess_trainer)"
        })
        self.user_discovery = SmartUserDiscovery()
        self._load_existing_games()

    def _load_existing_games(self):
        """Load existing game IDs to avoid duplicates."""
        try:
            if DB_URL:
                # Try to connect to database and get existing game IDs
                import psycopg2
                conn = psycopg2.connect(DB_URL)
                cur = conn.cursor()
                cur.execute("SELECT game_id FROM games")
                existing_ids = cur.fetchall()
                self.known_game_ids.update([row[0] for row in existing_ids])
                conn.close()
                logger.info(
                    f"📊 Loaded {len(self.known_game_ids)} existing game IDs from database")
        except Exception as e:
            logger.warning(
                f"⚠️ Could not load existing games from database: {e}")

    def _generate_game_id(self, pgn_text: str) -> str:
        """Generate a unique game ID from PGN content."""
        return hashlib.sha256(pgn_text.encode('utf-8')).hexdigest()

    def _make_request_with_retry(self, url: str, params: Dict = None, max_retries: int = 3) -> Optional[requests.Response]:
        """Make HTTP request with retry logic and rate limiting."""
        time.sleep(1.0 / RATE_LIMIT)  # Rate limiting

        for attempt in range(max_retries):
            try:
                response = self.session.get(
                    url, params=params, timeout=REQUEST_TIMEOUT)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    logger.warning(f"⏳ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"⚠️ HTTP {response.status_code} for {url}")

            except Exception as e:
                logger.warning(f"⚠️ Request attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        return None

    def _parse_time_control(self, time_control_str: str) -> Tuple[str, str]:
        """Parse time control string to extract game type."""
        if not time_control_str or time_control_str == "-":
            return "unknown", "unknown"

        # Common patterns for time controls
        if "bullet" in time_control_str.lower() or any(tc in time_control_str for tc in ["60+0", "90+0", "120+1"]):
            return "bullet", time_control_str
        elif "blitz" in time_control_str.lower() or any(tc in time_control_str for tc in ["180+0", "300+0", "180+2", "300+3"]):
            return "blitz", time_control_str
        elif "rapid" in time_control_str.lower() or any(tc in time_control_str for tc in ["600+0", "900+10", "1800+0"]):
            return "rapid", time_control_str
        elif "daily" in time_control_str.lower() or "1/259200" in time_control_str:
            return "classical", time_control_str
        else:
            return "other", time_control_str

    def _extract_game_metadata_from_pgn(self, pgn_text: str, platform: str) -> Optional[GameMetadata]:
        """Extract metadata from PGN text."""
        try:
            game = chess.pgn.read_game(StringIO(pgn_text))
            if not game:
                return None

            headers = game.headers

            # Count moves
            moves_count = len(list(game.mainline_moves()))
            if moves_count < MIN_MOVES:
                return None

            # Extract ratings
            white_rating = 0
            black_rating = 0

            try:
                white_rating = int(headers.get("WhiteElo", "0"))
                black_rating = int(headers.get("BlackElo", "0"))
            except (ValueError, TypeError):
                pass

            # Filter by rating range
            if (white_rating > 0 and not (MIN_RATING <= white_rating <= MAX_RATING)) or \
               (black_rating > 0 and not (MIN_RATING <= black_rating <= MAX_RATING)):
                return None

            # Extract time control info
            time_control = headers.get("TimeControl", "")
            game_type, formatted_time_control = self._parse_time_control(
                time_control)

            # Generate game ID
            game_id = self._generate_game_id(pgn_text)

            # Skip if already known
            if game_id in self.known_game_ids:
                return None

            # Create metadata
            metadata = GameMetadata(
                game_id=game_id,
                platform=platform,
                white_player=headers.get("White", "Unknown"),
                black_player=headers.get("Black", "Unknown"),
                white_rating=white_rating,
                black_rating=black_rating,
                time_control=formatted_time_control,
                game_type=game_type,
                result=headers.get("Result", "*"),
                opening=headers.get("Opening", ""),
                date=headers.get("Date", ""),
                url=headers.get("Site", ""),
                moves_count=moves_count,
                duration_seconds=None,  # Could be extracted from PGN comments if available
                fetch_date=datetime.now(),
                pgn_text=pgn_text
            )

            return metadata

        except Exception as e:
            logger.warning(f"⚠️ Error parsing PGN: {e}")
            return None

    def _fetch_lichess_games(self, username: str, max_games: int, since_date: Optional[str] = None) -> List[GameMetadata]:
        """Fetch games from Lichess for a specific user."""
        logger.debug(
            f"🔍 Fetching Lichess games for {username} (max: {max_games})")

        games = []
        params = {
            "max": min(max_games, 100),  # Lichess API limit
            "pgnInJson": False,
            "clocks": False,
            "evals": False,
            "opening": True,
        }

        if since_date:
            try:
                since_ts = int(datetime.strptime(
                    since_date, "%Y-%m-%d").timestamp()) * 1000
                params["since"] = since_ts
            except ValueError:
                logger.warning(f"⚠️ Invalid date format: {since_date}")

        url = f"https://lichess.org/api/games/user/{username}"
        response = self._make_request_with_retry(url, params)

        if not response:
            return games

        try:
            # Lichess returns PGN format
            pgn_content = response.text

            # Split into individual games
            pgn_games = pgn_content.strip().split('\n\n\n')

            for pgn_text in pgn_games:
                if len(games) >= max_games:
                    break

                pgn_text = pgn_text.strip()
                if not pgn_text:
                    continue

                metadata = self._extract_game_metadata_from_pgn(
                    pgn_text, "lichess")
                if metadata:
                    games.append(metadata)
                    self.known_game_ids.add(metadata.game_id)

        except Exception as e:
            logger.warning(
                f"⚠️ Error processing Lichess games for {username}: {e}")

        logger.debug(f"✅ Fetched {len(games)} Lichess games for {username}")
        return games

    def _fetch_chesscom_games(self, username: str, max_games: int, since_date: Optional[str] = None) -> List[GameMetadata]:
        """Fetch games from Chess.com for a specific user."""
        logger.debug(
            f"🔍 Fetching Chess.com games for {username} (max: {max_games})")

        games = []

        # Get list of available archives (months)
        archives_url = f"https://api.chess.com/pub/player/{username}/games/archives"
        archives_response = self._make_request_with_retry(archives_url)

        if not archives_response:
            return games

        try:
            archives_data = archives_response.json()
            archives = archives_data.get("archives", [])

            # Filter archives by since_date if provided
            if since_date:
                try:
                    since_dt = datetime.strptime(since_date, "%Y-%m-%d")
                    filtered_archives = []
                    for archive_url in archives:
                        # Extract year/month from URL
                        parts = archive_url.split('/')
                        if len(parts) >= 2:
                            try:
                                year, month = int(parts[-2]), int(parts[-1])
                                archive_dt = datetime(year, month, 1)
                                if archive_dt >= since_dt:
                                    filtered_archives.append(archive_url)
                            except ValueError:
                                continue
                    archives = filtered_archives
                except ValueError:
                    logger.warning(f"⚠️ Invalid date format: {since_date}")

            # Sort archives (most recent first) and limit
            archives = sorted(archives, reverse=True)[:12]  # Max 12 months

            for archive_url in archives:
                if len(games) >= max_games:
                    break

                archive_response = self._make_request_with_retry(archive_url)
                if not archive_response:
                    continue

                archive_data = archive_response.json()
                month_games = archive_data.get("games", [])

                # Shuffle to get random games from the month
                random.shuffle(month_games)

                for game_data in month_games:
                    if len(games) >= max_games:
                        break

                    if "pgn" not in game_data:
                        continue

                    pgn_text = game_data["pgn"]
                    metadata = self._extract_game_metadata_from_pgn(
                        pgn_text, "chess.com")
                    if metadata:
                        games.append(metadata)
                        self.known_game_ids.add(metadata.game_id)

        except Exception as e:
            logger.warning(
                f"⚠️ Error processing Chess.com games for {username}: {e}")

        logger.debug(f"✅ Fetched {len(games)} Chess.com games for {username}")
        return games

    def _fetch_games_for_user(self, user_profile: UserProfile, max_games_per_user: int,
                              since_date: Optional[str] = None) -> List[GameMetadata]:
        """Fetch games for a single user across platforms."""
        try:
            if user_profile.platform == "lichess":
                return self._fetch_lichess_games(user_profile.username, max_games_per_user, since_date)
            elif user_profile.platform == "chess.com":
                return self._fetch_chesscom_games(user_profile.username, max_games_per_user, since_date)
            else:
                logger.warning(f"⚠️ Unknown platform: {user_profile.platform}")
                return []
        except Exception as e:
            logger.warning(
                f"⚠️ Error fetching games for {user_profile.username}: {e}")
            return []

    def fetch_random_games(self, platform: Platform, skill_level: SkillLevel,
                           game_types: List[GameType], max_games: int,
                           since_date: Optional[str] = None,
                           users_file: Optional[str] = None) -> List[GameMetadata]:
        """Main method to fetch random games using smart discovery."""
        logger.info(f"🚀 Starting smart random games fetching...")
        logger.info(f"📋 Parameters:")
        logger.info(f"   - Platform: {platform.value}")
        logger.info(f"   - Skill level: {skill_level.value}")
        logger.info(f"   - Game types: {[gt.value for gt in game_types]}")
        logger.info(f"   - Max games: {max_games}")
        logger.info(f"   - Since date: {since_date or 'No limit'}")
        logger.info(f"   - Users file: {users_file or 'Auto-discover'}")

        # Step 1: Get user profiles
        if users_file and Path(users_file).exists():
            logger.info(f"📂 Loading users from file: {users_file}")
            try:
                with open(users_file, 'r') as f:
                    users_data = json.load(f)

                user_profiles = []
                for user_data in users_data.get('users', []):
                    profile = UserProfile(
                        username=user_data['username'],
                        platform=user_data['platform'],
                        ratings=user_data['ratings'],
                        total_games=user_data['total_games'],
                        last_seen=None,
                        profile_url=user_data['profile_url'],
                        discovery_date=datetime.fromisoformat(
                            user_data['discovery_date']),
                        skill_level=user_data['skill_level'],
                        verified=True
                    )
                    user_profiles.append(profile)

                logger.info(f"✅ Loaded {len(user_profiles)} users from file")

            except Exception as e:
                logger.error(f"❌ Error loading users file: {e}")
                return []
        else:
            logger.info(f"🔍 Discovering users automatically...")
            # Discover more users than needed to have options
            discovery_target = max(50, min(200, max_games // 5))
            user_profiles = self.user_discovery.discover_users(
                platform=platform,
                skill_level=skill_level,
                game_types=game_types,
                max_users=discovery_target
            )

            if not user_profiles:
                logger.error("❌ No users discovered. Cannot fetch games.")
                return []

        # Step 2: Calculate games per user
        max_games_per_user = max(1, min(20, max_games // len(user_profiles)))
        logger.info(
            f"🎯 Targeting {max_games_per_user} games per user from {len(user_profiles)} users")

        # Step 3: Shuffle users for random sampling
        random.shuffle(user_profiles)

        # Step 4: Fetch games in parallel
        all_games = []

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Submit tasks
            future_to_user = {
                executor.submit(self._fetch_games_for_user, user, max_games_per_user, since_date): user
                for user in user_profiles
            }

            # Collect results
            for future in as_completed(future_to_user):
                user = future_to_user[future]
                try:
                    user_games = future.result()
                    all_games.extend(user_games)

                    if user_games:
                        logger.info(
                            f"✅ {user.username} ({user.platform}): {len(user_games)} games")

                    # Stop if we have enough games
                    if len(all_games) >= max_games:
                        logger.info(
                            f"🎯 Target reached! Collected {len(all_games)} games")
                        break

                except Exception as e:
                    logger.warning(
                        f"⚠️ Failed to fetch games for {user.username}: {e}")

        # Step 5: Final filtering and shuffling
        random.shuffle(all_games)
        final_games = all_games[:max_games]

        self.fetched_games.extend(final_games)

        logger.info(f"🎉 Successfully fetched {len(final_games)} random games!")
        return final_games

    def save_games(self, games: List[GameMetadata], output_file: str, include_metadata: bool = True):
        """Save games to appropriate directories based on ELO classification."""
        try:
            # Classify games by ELO rating
            novice_games = []
            elite_games = []
            ignored_games = []

            for game in games:
                avg_rating = self._calculate_average_rating(game)
                elo_category = self._get_output_directory_by_elo(avg_rating)

                if elo_category == "novice":
                    novice_games.append(game)
                elif elo_category == "elite":
                    elite_games.append(game)
                else:
                    ignored_games.append(game)
                    logger.debug(
                        f"🚫 Ignoring game {game.game_id} with avg rating {avg_rating:.0f} (below 1200)")

            saved_paths = []
            total_saved = 0

            # Save novice games
            if novice_games:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                novice_path = f"{PGN_PATH}/novice/smart_random_novice_{timestamp}.pgn"
                saved_path = self._save_games_to_file(
                    novice_games, novice_path, include_metadata)
                if saved_path:
                    saved_paths.append(saved_path)
                    total_saved += len(novice_games)
                    logger.info(
                        f"📁 Saved {len(novice_games)} novice games (1200-2000 ELO) to {saved_path}")

            # Save elite games
            if elite_games:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                elite_path = f"{PGN_PATH}/elite/smart_random_elite_{timestamp}.pgn"
                saved_path = self._save_games_to_file(
                    elite_games, elite_path, include_metadata)
                if saved_path:
                    saved_paths.append(saved_path)
                    total_saved += len(elite_games)
                    logger.info(
                        f"📁 Saved {len(elite_games)} elite games (>2000 ELO) to {saved_path}")

            # Summary
            logger.info(f"📊 Classification summary:")
            logger.info(f"   - Novice games (1200-2000): {len(novice_games)}")
            logger.info(f"   - Elite games (>2000): {len(elite_games)}")
            logger.info(f"   - Ignored games (<1200): {len(ignored_games)}")
            logger.info(f"   - Total saved: {total_saved}")

            return saved_paths[0] if saved_paths else None

        except Exception as e:
            logger.error(f"❌ Error saving games: {e}")
            return None

    def _save_games_to_file(self, games: List[GameMetadata], output_file: str, include_metadata: bool = True):
        """Save games to a specific file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Save PGN file
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, game in enumerate(games):
                    f.write(game.pgn_text.strip())
                    if i < len(games) - 1:
                        f.write('\n\n')

            # Save metadata if requested
            if include_metadata:
                metadata_file = output_path.with_suffix('.json')
                metadata = {
                    'export_date': datetime.now().isoformat(),
                    'total_games': len(games),
                    'elo_category': self._get_output_directory_by_elo(self._calculate_average_rating(games[0])) if games else None,
                    'avg_rating_range': {
                        'min': min(self._calculate_average_rating(g) for g in games) if games else 0,
                        'max': max(self._calculate_average_rating(g) for g in games) if games else 0,
                        'avg': sum(self._calculate_average_rating(g) for g in games) / len(games) if games else 0
                    },
                    'games': [asdict(game) for game in games]
                }

                # Convert datetime objects to strings for JSON serialization
                for game_data in metadata['games']:
                    if 'fetch_date' in game_data and isinstance(game_data['fetch_date'], datetime):
                        game_data['fetch_date'] = game_data['fetch_date'].isoformat()

                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2, default=str)

            return output_path

        except Exception as e:
            logger.error(f"❌ Error saving games to {output_file}: {e}")
            return None

    def _get_output_directory_by_elo(self, avg_rating: float) -> str:
        """
        Determine output directory based on average ELO rating.

        Args:
            avg_rating: Average rating of both players

        Returns:
            Directory path: 'novice' for 1200-2000, 'elite' for >2000, None for <1200
        """
        if avg_rating < 1200:
            return None  # Ignore games below 1200
        elif 1200 <= avg_rating <= 2000:
            return "novice"
        else:  # avg_rating > 2000
            return "elite"

    def _calculate_average_rating(self, game: GameMetadata) -> float:
        """Calculate average rating of both players."""
        return (game.white_rating + game.black_rating) / 2.0


def main():
    parser = argparse.ArgumentParser(
        description="Smart Random Games Fetcher for Chess Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch random intermediate games from Lichess
  python smart_random_games_fetcher.py --platform lichess --skill-level intermediate --max-games 100

  # Fetch recent rapid games from both platforms  
  python smart_random_games_fetcher.py --platform both --game-types rapid --max-games 200 --since 2024-01-01

  # Use pre-discovered users
  python smart_random_games_fetcher.py --users-file discovered_users.json --max-games 300
        """
    )

    parser.add_argument('--platform', choices=['lichess', 'chess.com', 'both'],
                        default='lichess', help='Chess platform to fetch games from')
    parser.add_argument('--skill-level', choices=['beginner', 'intermediate', 'advanced', 'expert', 'all'],
                        default='intermediate', help='Target skill level of players')
    parser.add_argument('--game-types', nargs='+', choices=['bullet', 'blitz', 'rapid', 'classical', 'all'],
                        default=['all'], help='Target game types')
    parser.add_argument('--max-games', type=int, default=100,
                        help='Maximum number of games to fetch')
    parser.add_argument(
        '--since', help='Fetch games since date (YYYY-MM-DD format)')
    parser.add_argument(
        '--users-file', help='JSON file with pre-discovered users (optional)')
    parser.add_argument('--output', help='Output PGN file path')
    parser.add_argument('--include-metadata', action='store_true',
                        help='Include JSON metadata file with game information')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Set default output file if not provided
    # Note: save_games() will automatically classify and save games by ELO
    # to appropriate directories (novice/elite), so this is just a placeholder
    if not args.output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        platform_str = args.platform.replace('.', '_')
        args.output = f"{PGN_PATH}/smart_random_{platform_str}_{args.skill_level}_{timestamp}.pgn"

    # Note: Output directories will be created automatically by save_games() based on ELO classification

    # Convert arguments to enums
    platform = Platform(args.platform)
    skill_level = SkillLevel(args.skill_level)
    game_types = [GameType(gt) for gt in args.game_types]

    # Initialize fetcher
    fetcher = SmartGamesFetcher()

    try:
        # Fetch games
        games = fetcher.fetch_random_games(
            platform=platform,
            skill_level=skill_level,
            game_types=game_types,
            max_games=args.max_games,
            since_date=args.since,
            users_file=args.users_file
        )

        if games:
            # Save games
            output_path = fetcher.save_games(
                games=games,
                output_file=args.output,
                include_metadata=args.include_metadata
            )

            # Print summary
            print(f"\n📊 Fetching Summary:")
            print(f"   - Total games fetched: {len(games)}")
            print(
                f"   - Platforms: {', '.join(set(g.platform for g in games))}")
            print(
                f"   - Game types: {', '.join(set(g.game_type for g in games))}")
            print(
                f"   - Rating range: {min(min(g.white_rating, g.black_rating) for g in games if g.white_rating > 0)} - {max(max(g.white_rating, g.black_rating) for g in games if g.white_rating > 0)}")
            print(f"   - Output file: {output_path}")

            # Show sample games
            print(f"\n🎮 Sample fetched games:")
            for i, game in enumerate(games[:5]):
                avg_rating = (
                    game.white_rating + game.black_rating) // 2 if game.white_rating > 0 and game.black_rating > 0 else 0
                print(
                    f"   {i+1}. {game.white_player} vs {game.black_player} ({game.platform}) - {avg_rating} avg rating - {game.moves_count} moves")

            if len(games) > 5:
                print(f"   ... and {len(games) - 5} more games")

        else:
            print("❌ No games fetched. Try adjusting the search parameters.")

    except KeyboardInterrupt:
        logger.info("⚠️ Fetching interrupted by user")
    except Exception as e:
        logger.error(f"❌ Game fetching failed: {e}")
        raise


if __name__ == "__main__":
    main()
