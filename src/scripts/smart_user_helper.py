#!/usr/bin/env python3
"""
Smart User Discovery Helper for Chess Games

This script implements intelligent heuristic algorithms for discovering chess users
across different platforms (Lichess, Chess.com) with various skill levels and playing styles.

Usage Examples:
    # Discover intermediate Lichess users (1600-2000 rating)
    python smart_user_helper.py --platform lichess --skill-level intermediate --max-users 50

    # Discover expert Chess.com users (2000+ rating)  
    python smart_user_helper.py --platform chess.com --skill-level expert --max-users 25

    # Discover random users from both platforms
    python smart_user_helper.py --platform both --skill-level all --max-users 100

    # Discover users with specific game types
    python smart_user_helper.py --platform lichess --game-types rapid blitz --max-users 30

Environment Variables:
    CHESS_TRAINER_DB_URL: PostgreSQL connection URL (optional, for caching discovered users)
    USER_DISCOVERY_CACHE_TTL: Cache TTL in hours (default: 24)
    USER_DISCOVERY_MAX_RETRIES: Max API retries (default: 3)

Features:
    - Multi-platform user discovery (Lichess, Chess.com)
    - Skill-level based filtering (beginner, intermediate, advanced, expert)  
    - Game type filtering (rapid, blitz, bullet, classical)
    - Intelligent caching to avoid re-discovering same users
    - Rate limiting and respectful API usage
    - Robust error handling and retry mechanisms
    - Export discovered users to various formats (JSON, CSV, TXT)
"""

import dotenv
import argparse
import json
import csv
import os
import random
import time
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path

# Optional imports for web scraping
try:
    from bs4 import BeautifulSoup
    import re
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("smart_user_discovery.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()

# Configuration
CACHE_TTL_HOURS = int(os.environ.get("USER_DISCOVERY_CACHE_TTL", 24))
MAX_RETRIES = int(os.environ.get("USER_DISCOVERY_MAX_RETRIES", 3))
REQUEST_DELAY = float(os.environ.get("USER_DISCOVERY_REQUEST_DELAY", 1.0))
OUTPUT_DIR = os.environ.get(
    "USER_DISCOVERY_OUTPUT_DIR", "/app/data/discovered_users")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


class Platform(Enum):
    LICHESS = "lichess"
    CHESS_COM = "chess.com"
    BOTH = "both"


class SkillLevel(Enum):
    BEGINNER = "beginner"      # 0-1200
    INTERMEDIATE = "intermediate"  # 1200-1800
    ADVANCED = "advanced"      # 1800-2200
    EXPERT = "expert"          # 2200+
    ALL = "all"


class GameType(Enum):
    BULLET = "bullet"
    BLITZ = "blitz"
    RAPID = "rapid"
    CLASSICAL = "classical"
    ALL = "all"


@dataclass
class UserProfile:
    username: str
    platform: str
    ratings: Dict[str, int]
    total_games: int
    last_seen: Optional[datetime]
    profile_url: str
    discovery_date: datetime
    skill_level: str
    verified: bool = False


class SmartUserDiscovery:
    """
    Intelligent user discovery system using multiple heuristic strategies.
    """

    def __init__(self, discovery_method: str = "efficient"):
        self.discovered_users: Set[str] = set()
        self.user_profiles: List[UserProfile] = []
        self.cache_file = Path(OUTPUT_DIR) / "user_cache.json"
        self.known_users_file = Path(OUTPUT_DIR) / "known_users.json"
        self.discovery_method = discovery_method
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "chess_trainer/1.0 (+https://github.com/cmessoftware/chess_trainer)"
        })
        self._load_cache()
        self._load_known_users()

    def _load_cache(self):
        """Load previously discovered users from cache."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)

                # Filter out expired entries
                cutoff_time = datetime.now() - timedelta(hours=CACHE_TTL_HOURS)
                valid_profiles = []

                for profile_data in cache_data.get('profiles', []):
                    discovery_date = datetime.fromisoformat(
                        profile_data['discovery_date'])
                    if discovery_date > cutoff_time:
                        profile = UserProfile(**profile_data)
                        valid_profiles.append(profile)
                        self.discovered_users.add(
                            f"{profile.platform}:{profile.username}")

                self.user_profiles = valid_profiles
                logger.info(
                    f"📁 Loaded {len(valid_profiles)} cached user profiles")

            except Exception as e:
                logger.warning(f"⚠️ Error loading cache: {e}")

    def _save_cache(self):
        """Save discovered users to cache."""
        try:
            cache_data = {
                'profiles': [
                    {
                        'username': p.username,
                        'platform': p.platform,
                        'ratings': p.ratings,
                        'total_games': p.total_games,
                        'last_seen': p.last_seen.isoformat() if p.last_seen else None,
                        'profile_url': p.profile_url,
                        'discovery_date': p.discovery_date.isoformat(),
                        'skill_level': p.skill_level,
                        'verified': p.verified
                    }
                    for p in self.user_profiles
                ],
                'last_updated': datetime.now().isoformat()
            }

            with open(self.cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)

            logger.info(f"💾 Saved {len(self.user_profiles)} profiles to cache")

        except Exception as e:
            logger.error(f"❌ Error saving cache: {e}")

    def _load_known_users(self):
        """Load known users from the known_users.json file."""
        if not self.known_users_file.exists():
            logger.info("📝 Known users file not found, creating template...")
            return

        try:
            with open(self.known_users_file, 'r') as f:
                known_data = json.load(f)

            known_users = known_data.get('known_users', [])
            loaded_count = 0

            for user_data in known_users:
                username = user_data.get('username')
                platform = user_data.get('platform')

                if not username or not platform:
                    continue

                user_key = f"{platform}:{username}"

                # Add to our known users set for potential discovery
                if user_key not in self.discovered_users:
                    # Create a basic profile for known users
                    # (will be enriched later when discovered)
                    estimated_skill = user_data.get(
                        'estimated_skill', 'intermediate')

                    # Add to discovered users set so it gets prioritized
                    self.discovered_users.add(user_key)
                    loaded_count += 1

            if loaded_count > 0:
                logger.info(
                    f"👥 Loaded {loaded_count} known users for prioritized discovery")

        except Exception as e:
            logger.warning(f"⚠️ Error loading known users: {e}")

    def _get_skill_level_range(self, skill_level: SkillLevel) -> Tuple[int, int]:
        """Get rating range for skill level."""
        ranges = {
            SkillLevel.BEGINNER: (0, 1200),
            SkillLevel.INTERMEDIATE: (1200, 1800),
            SkillLevel.ADVANCED: (1800, 2200),
            SkillLevel.EXPERT: (2200, 3000),
            SkillLevel.ALL: (0, 3000)
        }
        return ranges[skill_level]

    def _make_request_with_retry(self, url: str, timeout: int = 10) -> Optional[Dict]:
        """Make HTTP request with retry logic."""
        for attempt in range(MAX_RETRIES):
            try:
                time.sleep(REQUEST_DELAY)  # Rate limiting
                response = self.session.get(url, timeout=timeout)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limited
                    wait_time = 2 ** attempt
                    logger.warning(f"⏳ Rate limited, waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.warning(f"⚠️ HTTP {response.status_code} for {url}")

            except Exception as e:
                logger.warning(f"⚠️ Request attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)

        return None

    def _generate_potential_usernames(self, count: int = 100) -> List[str]:
        """Generate potential usernames using various heuristics."""
        usernames = []

        # Strategy 1: Chess-themed prefixes + numbers
        chess_prefixes = [
            "chess", "king", "queen", "rook", "bishop", "knight", "pawn",
            "check", "mate", "castle", "gambit", "tactic", "blitz", "rapid",
            "master", "player", "user", "capy", "bot", "pro", "elo"
        ]

        # Strategy 2: Common name patterns
        common_patterns = [
            "player", "user", "gamer", "chessnut", "tactician", "strategist"
        ]

        # Strategy 3: Year-based suffixes
        years = list(range(1990, 2024))

        # Strategy 4: Number-based suffixes
        numbers = list(range(1, 10000))

        # Generate combinations
        for _ in range(count):
            strategy = random.choice([1, 2, 3, 4])

            if strategy == 1:
                # Chess prefix + number
                prefix = random.choice(chess_prefixes)
                suffix = random.choice(
                    ["", "123", "2023", "pro", "xd", "elo", str(random.randint(1, 9999))])
                username = prefix + suffix

            elif strategy == 2:
                # Common pattern + number
                prefix = random.choice(common_patterns)
                suffix = str(random.randint(1, 9999))
                username = prefix + suffix

            elif strategy == 3:
                # Random prefix + year
                prefix = random.choice(chess_prefixes + common_patterns)
                year = random.choice(years)
                username = f"{prefix}{year}"

            else:
                # Completely random combination
                prefix = random.choice(chess_prefixes)
                middle = random.choice(["", "_", ""])
                suffix = random.choice(
                    [str(random.randint(1, 99)), str(random.randint(2020, 2024))])
                username = f"{prefix}{middle}{suffix}"

            usernames.append(username)

        return list(set(usernames))  # Remove duplicates

    def discover_lichess_users(self, skill_level: SkillLevel, game_types: List[GameType], max_users: int) -> List[UserProfile]:
        """Discover Lichess users efficiently using real user sources."""
        logger.info(
            f"🔍 Discovering Lichess users efficiently (skill: {skill_level.value}, max: {max_users})")

        discovered = []
        min_rating, max_rating = self._get_skill_level_range(skill_level)

        # Get real users efficiently instead of random generation
        logger.info("🚀 Using configured discovery methods...")
        real_usernames = self._get_usernames_by_method(
            Platform.LICHESS, max_users * 2)

        logger.info(f"📋 Found {len(real_usernames)} real users to process")

        for username in real_usernames:
            if len(discovered) >= max_users:
                break

            # Skip if already discovered
            user_key = f"lichess:{username}"
            if user_key in self.discovered_users:
                continue

            # Get user profile
            profile_data = self._make_request_with_retry(
                f"https://lichess.org/api/user/{username}")
            if not profile_data:
                continue

            try:
                # Extract ratings
                perfs = profile_data.get("perfs", {})
                ratings = {}

                for game_type in ["bullet", "blitz", "rapid", "classical"]:
                    if game_type in perfs:
                        ratings[game_type] = perfs[game_type].get("rating", 0)

                if not ratings:
                    continue

                # Check skill level match
                avg_rating = sum(ratings.values()) / len(ratings)
                if not (min_rating <= avg_rating <= max_rating) and skill_level != SkillLevel.ALL:
                    continue

                # Check game type match
                if GameType.ALL not in game_types:
                    has_matching_game_type = any(
                        game_type.value in ratings for game_type in game_types
                    )
                    if not has_matching_game_type:
                        continue

                # Create user profile
                profile = UserProfile(
                    username=username,
                    platform="lichess",
                    ratings=ratings,
                    total_games=sum(perfs.get(gt, {}).get("games", 0) for gt in [
                                    "bullet", "blitz", "rapid", "classical"]),
                    last_seen=datetime.now(),  # Lichess doesn't provide last seen in basic API
                    profile_url=f"https://lichess.org/@/{username}",
                    discovery_date=datetime.now(),
                    skill_level=skill_level.value,
                    verified=True
                )

                discovered.append(profile)
                self.discovered_users.add(user_key)
                self.user_profiles.append(profile)

                logger.info(
                    f"✅ Found Lichess user: {username} (avg rating: {avg_rating:.0f})")

            except Exception as e:
                logger.warning(
                    f"⚠️ Error processing Lichess user {username}: {e}")

        logger.info(f"🎯 Discovered {len(discovered)} Lichess users")
        return discovered

    def discover_chesscom_users(self, skill_level: SkillLevel, game_types: List[GameType], max_users: int) -> List[UserProfile]:
        """Discover Chess.com users efficiently using real user sources."""
        logger.info(
            f"🔍 Discovering Chess.com users efficiently (skill: {skill_level.value}, max: {max_users})")

        discovered = []
        min_rating, max_rating = self._get_skill_level_range(skill_level)

        # Get real users efficiently instead of random generation
        logger.info("🚀 Using configured discovery methods...")
        real_usernames = self._get_usernames_by_method(
            Platform.CHESS_COM, max_users * 2)

        logger.info(f"📋 Found {len(real_usernames)} real users to process")

        for username in real_usernames:
            if len(discovered) >= max_users:
                break

            # Skip if already discovered
            user_key = f"chess.com:{username}"
            if user_key in self.discovered_users:
                continue

            # Get user profile
            profile_data = self._make_request_with_retry(
                f"https://api.chess.com/pub/player/{username}")
            if not profile_data:
                continue

            # Get user stats
            stats_data = self._make_request_with_retry(
                f"https://api.chess.com/pub/player/{username}/stats")
            if not stats_data:
                continue

            try:
                # Extract ratings
                ratings = {}
                total_games = 0

                for game_type in ["chess_bullet", "chess_blitz", "chess_rapid", "chess_daily"]:
                    if game_type in stats_data:
                        game_stats = stats_data[game_type]
                        if "last" in game_stats and "rating" in game_stats["last"]:
                            clean_type = game_type.replace(
                                "chess_", "").replace("daily", "classical")
                            ratings[clean_type] = game_stats["last"]["rating"]
                            total_games += game_stats.get("record", {}).get("win", 0) + \
                                game_stats.get("record", {}).get("loss", 0) + \
                                game_stats.get("record", {}).get("draw", 0)

                if not ratings:
                    continue

                # Check skill level match
                avg_rating = sum(ratings.values()) / len(ratings)
                if not (min_rating <= avg_rating <= max_rating) and skill_level != SkillLevel.ALL:
                    continue

                # Check game type match
                if GameType.ALL not in game_types:
                    has_matching_game_type = any(
                        game_type.value in ratings for game_type in game_types
                    )
                    if not has_matching_game_type:
                        continue

                # Extract last seen if available
                last_seen = None
                if "last_login_date" in profile_data:
                    try:
                        last_seen = datetime.fromtimestamp(
                            profile_data["last_login_date"])
                    except:
                        pass

                # Create user profile
                profile = UserProfile(
                    username=username,
                    platform="chess.com",
                    ratings=ratings,
                    total_games=total_games,
                    last_seen=last_seen,
                    profile_url=f"https://www.chess.com/member/{username}",
                    discovery_date=datetime.now(),
                    skill_level=skill_level.value,
                    verified=True
                )

                discovered.append(profile)
                self.discovered_users.add(user_key)
                self.user_profiles.append(profile)

                logger.info(
                    f"✅ Found Chess.com user: {username} (avg rating: {avg_rating:.0f})")

            except Exception as e:
                logger.warning(
                    f"⚠️ Error processing Chess.com user {username}: {e}")

        logger.info(f"🎯 Discovered {len(discovered)} Chess.com users")
        return discovered

    def discover_users(self, platform: Platform, skill_level: SkillLevel,
                       game_types: List[GameType], max_users: int) -> List[UserProfile]:
        """Main method to discover users across platforms."""
        logger.info(f"🚀 Starting user discovery...")
        logger.info(f"📋 Parameters:")
        logger.info(f"   - Platform: {platform.value}")
        logger.info(f"   - Skill level: {skill_level.value}")
        logger.info(f"   - Game types: {[gt.value for gt in game_types]}")
        logger.info(f"   - Max users: {max_users}")

        all_discovered = []

        if platform in [Platform.LICHESS, Platform.BOTH]:
            users_per_platform = max_users if platform == Platform.LICHESS else max_users // 2
            lichess_users = self.discover_lichess_users(
                skill_level, game_types, users_per_platform)
            all_discovered.extend(lichess_users)

        if platform in [Platform.CHESS_COM, Platform.BOTH]:
            users_per_platform = max_users if platform == Platform.CHESS_COM else max_users // 2
            chesscom_users = self.discover_chesscom_users(
                skill_level, game_types, users_per_platform)
            all_discovered.extend(chesscom_users)

        # Save cache
        self._save_cache()

        logger.info(
            f"🎉 Discovery completed! Found {len(all_discovered)} total users")
        return all_discovered

    def export_users(self, users: List[UserProfile], format: str = "json", filename: str = None):
        """Export discovered users to various formats."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"discovered_users_{timestamp}.{format}"

        filepath = Path(OUTPUT_DIR) / filename

        try:
            if format == "json":
                data = {
                    'export_date': datetime.now().isoformat(),
                    'total_users': len(users),
                    'users': [
                        {
                            'username': u.username,
                            'platform': u.platform,
                            'ratings': u.ratings,
                            'total_games': u.total_games,
                            'profile_url': u.profile_url,
                            'skill_level': u.skill_level,
                            'discovery_date': u.discovery_date.isoformat()
                        }
                        for u in users
                    ]
                }

                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)

            elif format == "csv":
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        ['username', 'platform', 'avg_rating', 'total_games', 'skill_level', 'profile_url'])

                    for user in users:
                        avg_rating = sum(user.ratings.values()) / \
                            len(user.ratings) if user.ratings else 0
                        writer.writerow([
                            user.username, user.platform, f"{avg_rating:.0f}",
                            user.total_games, user.skill_level, user.profile_url
                        ])

            elif format == "txt":
                with open(filepath, 'w') as f:
                    f.write(
                        f"# Discovered Chess Users - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Total users: {len(users)}\n\n")

                    for user in users:
                        avg_rating = sum(user.ratings.values()) / \
                            len(user.ratings) if user.ratings else 0
                        f.write(
                            f"{user.username} ({user.platform}) - Rating: {avg_rating:.0f} - Games: {user.total_games}\n")

            logger.info(f"📄 Exported {len(users)} users to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"❌ Error exporting users: {e}")
            return None

    def _get_real_lichess_users_from_leaderboards(self, max_users: int = 50) -> List[str]:
        """Get real users from Lichess leaderboards - much more efficient than random generation."""
        real_users = []

        # Lichess leaderboard endpoints for different categories
        leaderboard_endpoints = [
            "bullet",  # Bullet leaderboard
            "blitz",   # Blitz leaderboard
            "rapid",   # Rapid leaderboard
            "classical",  # Classical leaderboard
            "ultraBullet",  # Ultra bullet leaderboard
        ]

        users_per_board = max_users // len(leaderboard_endpoints) + 1

        for board_type in leaderboard_endpoints:
            if len(real_users) >= max_users:
                break

            url = f"https://lichess.org/api/player/top/{users_per_board}/{board_type}"
            data = self._make_request_with_retry(url)

            if data and "users" in data:
                for user in data["users"]:
                    if len(real_users) >= max_users:
                        break
                    real_users.append(user["id"])

            logger.info(
                f"📈 Got {len([u for u in real_users if len(real_users) <= max_users])} users from {board_type} leaderboard")

        return real_users[:max_users]

    def _get_real_lichess_users_from_tournaments(self, max_users: int = 50) -> List[str]:
        """Get real users from recent Lichess tournaments."""
        real_users = []

        # Get recent tournaments
        url = "https://lichess.org/api/tournament"
        tournaments_data = self._make_request_with_retry(url)

        if not tournaments_data:
            return real_users

        # Take first few tournaments
        recent_tournaments = tournaments_data.get("created", [])[:3]

        for tournament in recent_tournaments:
            if len(real_users) >= max_users:
                break

            tournament_id = tournament.get("id")
            if not tournament_id:
                continue

            # Get tournament results
            url = f"https://lichess.org/api/tournament/{tournament_id}/results"
            results_data = self._make_request_with_retry(url)

            if results_data:
                # Parse the results (it's a stream of JSON objects)
                lines = results_data.text.strip().split(
                    '\n') if hasattr(results_data, 'text') else []

                for line in lines:
                    if len(real_users) >= max_users:
                        break
                    try:
                        result = json.loads(line)
                        username = result.get("username")
                        if username:
                            real_users.append(username)
                    except:
                        continue

        logger.info(f"🏆 Got {len(real_users)} users from recent tournaments")
        return real_users[:max_users]

    def _get_real_lichess_users_from_games_stream(self, max_users: int = 50) -> List[str]:
        """Get real users from Lichess live games stream."""
        real_users = set()

        # Use the TV stream to get current games
        url = "https://lichess.org/api/tv/channels"
        channels_data = self._make_request_with_retry(url)

        if not channels_data:
            return list(real_users)

        # Extract usernames from current TV games
        for channel_name, channel_data in channels_data.items():
            if len(real_users) >= max_users:
                break

            game_info = channel_data.get("gameId")
            if game_info:
                # Get game details
                game_url = f"https://lichess.org/api/game/{game_info}"
                game_data = self._make_request_with_retry(game_url)

                if game_data and "players" in game_data:
                    for color in ["white", "black"]:
                        player = game_data["players"].get(color, {})
                        username = player.get("user", {}).get("id")
                        if username:
                            real_users.add(username)

        logger.info(f"📺 Got {len(real_users)} users from live TV games")
        return list(real_users)[:max_users]

    def _get_real_chesscom_users_from_leaderboards(self, max_users: int = 50) -> List[str]:
        """Get real users from Chess.com leaderboards."""
        real_users = []

        # Chess.com leaderboard endpoints
        leaderboard_endpoints = [
            "live_rapid",
            "live_blitz",
            "live_bullet",
            "daily",
            "daily960"
        ]

        users_per_board = max_users // len(leaderboard_endpoints) + 1

        for board_type in leaderboard_endpoints:
            if len(real_users) >= max_users:
                break

            url = f"https://api.chess.com/pub/leaderboards/{board_type}"
            data = self._make_request_with_retry(url)

            if data and board_type in data:
                leaderboard_data = data[board_type]
                for entry in leaderboard_data[:users_per_board]:
                    if len(real_users) >= max_users:
                        break
                    username = entry.get("username")
                    if username:
                        real_users.append(username)

            logger.info(f"📈 Got users from Chess.com {board_type} leaderboard")

        return real_users[:max_users]

    def _get_real_chesscom_users_from_clubs(self, max_users: int = 50) -> List[str]:
        """Get real users from popular Chess.com clubs."""
        real_users = []

        # Popular Chess.com clubs (these are public and have many members)
        popular_clubs = [
            "chess-com-official",
            "team-usa",
            "team-europe",
            "chess-network",
            "bullet-chess"
        ]

        users_per_club = max_users // len(popular_clubs) + 1

        for club_id in popular_clubs:
            if len(real_users) >= max_users:
                break

            url = f"https://api.chess.com/pub/club/{club_id}/members"
            data = self._make_request_with_retry(url)

            if data and "weekly" in data:
                members = data["weekly"][:users_per_club]
                for member in members:
                    if len(real_users) >= max_users:
                        break
                    username = member.get("username")
                    if username:
                        real_users.append(username)

            logger.info(f"🏛️ Got users from Chess.com club: {club_id}")

        return real_users[:max_users]

    def _get_real_users_efficiently(self, platform: Platform, max_users: int) -> List[str]:
        """Get real users using efficient methods instead of random generation."""
        real_users = []

        if platform in [Platform.LICHESS, Platform.BOTH]:
            lichess_target = max_users if platform == Platform.LICHESS else max_users // 2

            # Try multiple efficient sources for Lichess
            methods = [
                self._get_real_lichess_users_from_leaderboards,
                self._get_real_lichess_users_from_games_stream,
                self._get_real_lichess_users_from_tournaments
            ]

            users_per_method = lichess_target // len(methods) + 1

            for method in methods:
                if len(real_users) >= lichess_target:
                    break
                try:
                    method_users = method(users_per_method)
                    real_users.extend(method_users)
                    logger.info(
                        f"✅ {method.__name__}: got {len(method_users)} users")
                except Exception as e:
                    logger.warning(f"⚠️ {method.__name__} failed: {e}")

            # Fallback to web scraping if needed
            if len(real_users) < lichess_target // 2:
                logger.info("🕷️ Using web scraping as fallback for Lichess...")
                try:
                    scraping_users = self._get_users_via_web_scraping(
                        Platform.LICHESS, lichess_target)
                    real_users.extend(scraping_users)
                    logger.info(
                        f"✅ Web scraping: got {len(scraping_users)} additional users")
                except Exception as e:
                    logger.warning(f"⚠️ Web scraping fallback failed: {e}")

        if platform in [Platform.CHESS_COM, Platform.BOTH]:
            chesscom_target = max_users if platform == Platform.CHESS_COM else max_users // 2
            current_lichess_users = len(real_users)

            # Try efficient sources for Chess.com
            methods = [
                self._get_real_chesscom_users_from_leaderboards,
                self._get_real_chesscom_users_from_clubs
            ]

            users_per_method = chesscom_target // len(methods) + 1

            for method in methods:
                if len(real_users) - current_lichess_users >= chesscom_target:
                    break
                try:
                    method_users = method(users_per_method)
                    real_users.extend(method_users)
                    logger.info(
                        f"✅ {method.__name__}: got {len(method_users)} users")
                except Exception as e:
                    logger.warning(f"⚠️ {method.__name__} failed: {e}")

            # Fallback to web scraping if needed
            if (len(real_users) - current_lichess_users) < chesscom_target // 2:
                logger.info(
                    "🕷️ Using web scraping as fallback for Chess.com...")
                try:
                    scraping_users = self._get_users_via_web_scraping(
                        Platform.CHESS_COM, chesscom_target)
                    real_users.extend(scraping_users)
                    logger.info(
                        f"✅ Web scraping: got {len(scraping_users)} additional users")
                except Exception as e:
                    logger.warning(f"⚠️ Web scraping fallback failed: {e}")

        # Remove duplicates and return
        unique_users = list(set(real_users))
        logger.info(f"🎯 Total unique real users found: {len(unique_users)}")
        return unique_users[:max_users]

    def _get_users_via_web_scraping(self, platform: Platform, max_users: int = 50) -> List[str]:
        """Fallback method: Get users via web scraping when APIs are limited."""
        if not WEB_SCRAPING_AVAILABLE:
            logger.warning(
                "⚠️ Web scraping not available - install beautifulsoup4 for this feature")
            return []

        real_users = []

        if platform in [Platform.LICHESS, Platform.BOTH]:
            try:
                # Scrape Lichess recent games page
                url = "https://lichess.org/games"
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Look for user links in the games list
                    user_links = soup.find_all('a', href=True)
                    for link in user_links:
                        href = link.get('href', '')
                        if href.startswith('/@/'):
                            username = href.replace('/@/', '')
                            if username and len(username) > 2:
                                real_users.append(username)
                                if len(real_users) >= max_users // 2:
                                    break

                logger.info(
                    f"🕷️ Web scraping got {len(real_users)} Lichess users")

            except Exception as e:
                logger.warning(f"⚠️ Web scraping Lichess failed: {e}")

        if platform in [Platform.CHESS_COM, Platform.BOTH]:
            try:
                # Scrape Chess.com live games or leaderboards
                url = "https://www.chess.com/games/live"
                response = requests.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })

                if response.status_code == 200:
                    # Simple regex to find usernames in the page
                    usernames = re.findall(
                        r'/member/([a-zA-Z0-9_-]+)', response.text)

                    chesscom_users = list(set(usernames))[:max_users // 2]
                    real_users.extend(chesscom_users)

                logger.info(
                    f"🕷️ Web scraping got {len(chesscom_users)} Chess.com users")

            except Exception as e:
                logger.warning(f"⚠️ Web scraping Chess.com failed: {e}")

        return real_users[:max_users]

    def _get_usernames_by_method(self, platform: Platform, max_users: int) -> List[str]:
        """Get usernames using the configured discovery method."""
        if self.discovery_method == "efficient":
            logger.info(
                "🚀 Using efficient discovery methods (leaderboards, tournaments, etc.)")
            return self._get_real_users_efficiently(platform, max_users)

        elif self.discovery_method == "random":
            logger.info("🎲 Using random username generation method")
            return self._generate_potential_usernames(max_users * 3)

        elif self.discovery_method == "mixed":
            logger.info("🔄 Using mixed discovery methods")
            # Try efficient first, then supplement with random if needed
            efficient_users = self._get_real_users_efficiently(
                platform, max_users // 2)
            remaining = max_users - len(efficient_users)

            if remaining > 0:
                random_users = self._generate_potential_usernames(
                    remaining * 2)
                efficient_users.extend(random_users)

            return efficient_users[:max_users]

        else:
            logger.warning(
                f"⚠️ Unknown discovery method: {self.discovery_method}, using efficient")
            return self._get_real_users_efficiently(platform, max_users)

    def get_known_usernames(self, platform: Platform, max_users: int = 100) -> List[str]:
        """Get usernames from the known users list for a specific platform."""
        if not self.known_users_file.exists():
            return []

        try:
            with open(self.known_users_file, 'r') as f:
                known_data = json.load(f)

            known_users = known_data.get('known_users', [])
            platform_users = []

            for user_data in known_users:
                username = user_data.get('username')
                user_platform = user_data.get('platform')

                if not username or not user_platform:
                    continue

                # Check if platform matches
                if platform == Platform.BOTH or user_platform == platform.value:
                    platform_users.append(username)

                if len(platform_users) >= max_users:
                    break

            logger.info(
                f"👥 Retrieved {len(platform_users)} known users for {platform.value}")
            return platform_users

        except Exception as e:
            logger.warning(f"⚠️ Error getting known users: {e}")
            return []

    def add_known_user(self, username: str, platform: str, description: str = "",
                       estimated_skill: str = "intermediate", notes: str = ""):
        """Add a new known user to the known_users.json file."""
        try:
            # Load existing data
            known_data = {"known_users": []}
            if self.known_users_file.exists():
                with open(self.known_users_file, 'r') as f:
                    known_data = json.load(f)

            # Check if user already exists
            existing_users = known_data.get('known_users', [])
            for existing_user in existing_users:
                if (existing_user.get('username') == username and
                        existing_user.get('platform') == platform):
                    logger.warning(
                        f"⚠️ User {username} on {platform} already exists in known users")
                    return False

            # Add new user
            new_user = {
                "username": username,
                "platform": platform,
                "description": description,
                "estimated_skill": estimated_skill,
                "added_by": "manual",
                "added_date": datetime.now().isoformat(),
                "notes": notes
            }

            known_data['known_users'].append(new_user)
            known_data['last_updated'] = datetime.now().isoformat()

            # Save updated data
            with open(self.known_users_file, 'w') as f:
                json.dump(known_data, f, indent=2)

            logger.info(f"✅ Added known user: {username} ({platform})")
            return True

        except Exception as e:
            logger.error(f"❌ Error adding known user: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Smart User Discovery Helper for Chess Games",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Discover intermediate Lichess users
  python smart_user_helper.py --platform lichess --skill-level intermediate --max-users 50

  # Discover expert users from both platforms
  python smart_user_helper.py --platform both --skill-level expert --max-users 100

  # Export discovered users to CSV
  python smart_user_helper.py --platform lichess --skill-level all --max-users 25 --export-format csv
        """
    )

    parser.add_argument('--platform', choices=['lichess', 'chess.com', 'both'],
                        default='lichess', help='Chess platform to discover users from')
    parser.add_argument('--skill-level', choices=['beginner', 'intermediate', 'advanced', 'expert', 'all'],
                        default='intermediate', help='Target skill level of users')
    parser.add_argument('--game-types', nargs='+', choices=['bullet', 'blitz', 'rapid', 'classical', 'all'],
                        default=['all'], help='Target game types')
    parser.add_argument('--max-users', type=int, default=50,
                        help='Maximum number of users to discover')
    parser.add_argument('--discovery-method', choices=['efficient', 'random', 'mixed'], default='efficient',
                        help='User discovery method: efficient (leaderboards/tournaments), random (generated names), or mixed')
    parser.add_argument('--export-format', choices=['json', 'csv', 'txt'], default='json',
                        help='Export format for discovered users')
    parser.add_argument('--export-filename',
                        help='Custom filename for export (optional)')
    parser.add_argument('--verbose', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Convert arguments to enums
    platform = Platform(args.platform)
    skill_level = SkillLevel(args.skill_level)
    game_types = [GameType(gt) for gt in args.game_types]

    # Initialize discovery system
    discovery = SmartUserDiscovery(discovery_method=args.discovery_method)

    try:
        # Discover users
        discovered_users = discovery.discover_users(
            platform=platform,
            skill_level=skill_level,
            game_types=game_types,
            max_users=args.max_users
        )

        if discovered_users:
            # Export results
            export_path = discovery.export_users(
                users=discovered_users,
                format=args.export_format,
                filename=args.export_filename
            )

            # Print summary
            print(f"\n📊 Discovery Summary:")
