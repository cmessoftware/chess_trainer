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
import dotenv
dotenv.load_dotenv()

# Configuration
CACHE_TTL_HOURS = int(os.environ.get("USER_DISCOVERY_CACHE_TTL", 24))
MAX_RETRIES = int(os.environ.get("USER_DISCOVERY_MAX_RETRIES", 3))
REQUEST_DELAY = float(os.environ.get("USER_DISCOVERY_REQUEST_DELAY", 1.0))
OUTPUT_DIR = os.environ.get("USER_DISCOVERY_OUTPUT_DIR", "/app/data/discovered_users")

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
    
    def __init__(self):
        self.discovered_users: Set[str] = set()
        self.user_profiles: List[UserProfile] = []
        self.cache_file = Path(OUTPUT_DIR) / "user_cache.json"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "chess_trainer/1.0 (+https://github.com/cmessoftware/chess_trainer)"
        })
        self._load_cache()
    
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
                    discovery_date = datetime.fromisoformat(profile_data['discovery_date'])
                    if discovery_date > cutoff_time:
                        profile = UserProfile(**profile_data)
                        valid_profiles.append(profile)
                        self.discovered_users.add(f"{profile.platform}:{profile.username}")
                
                self.user_profiles = valid_profiles
                logger.info(f"📁 Loaded {len(valid_profiles)} cached user profiles")
                
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
                suffix = random.choice(["", "123", "2023", "pro", "xd", "elo", str(random.randint(1, 9999))])
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
                suffix = random.choice([str(random.randint(1, 99)), str(random.randint(2020, 2024))])
                username = f"{prefix}{middle}{suffix}"
            
            usernames.append(username)
        
        return list(set(usernames))  # Remove duplicates

    def discover_lichess_users(self, skill_level: SkillLevel, game_types: List[GameType], max_users: int) -> List[UserProfile]:
        """Discover Lichess users using API exploration."""
        logger.info(f"🔍 Discovering Lichess users (skill: {skill_level.value}, max: {max_users})")
        
        discovered = []
        min_rating, max_rating = self._get_skill_level_range(skill_level)
        potential_usernames = self._generate_potential_usernames(max_users * 10)  # Generate more than needed
        
        for username in potential_usernames:
            if len(discovered) >= max_users:
                break
                
            # Skip if already discovered
            user_key = f"lichess:{username}"
            if user_key in self.discovered_users:
                continue
            
            # Get user profile
            profile_data = self._make_request_with_retry(f"https://lichess.org/api/user/{username}")
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
                    total_games=sum(perfs.get(gt, {}).get("games", 0) for gt in ["bullet", "blitz", "rapid", "classical"]),
                    last_seen=datetime.now(),  # Lichess doesn't provide last seen in basic API
                    profile_url=f"https://lichess.org/@/{username}",
                    discovery_date=datetime.now(),
                    skill_level=skill_level.value,
                    verified=True
                )
                
                discovered.append(profile)
                self.discovered_users.add(user_key)
                self.user_profiles.append(profile)
                
                logger.info(f"✅ Found Lichess user: {username} (avg rating: {avg_rating:.0f})")
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing Lichess user {username}: {e}")
        
        logger.info(f"🎯 Discovered {len(discovered)} Lichess users")
        return discovered

    def discover_chesscom_users(self, skill_level: SkillLevel, game_types: List[GameType], max_users: int) -> List[UserProfile]:
        """Discover Chess.com users using API exploration."""
        logger.info(f"🔍 Discovering Chess.com users (skill: {skill_level.value}, max: {max_users})")
        
        discovered = []
        min_rating, max_rating = self._get_skill_level_range(skill_level)
        potential_usernames = self._generate_potential_usernames(max_users * 10)
        
        for username in potential_usernames:
            if len(discovered) >= max_users:
                break
                
            # Skip if already discovered
            user_key = f"chess.com:{username}"
            if user_key in self.discovered_users:
                continue
            
            # Get user profile
            profile_data = self._make_request_with_retry(f"https://api.chess.com/pub/player/{username}")
            if not profile_data:
                continue
            
            # Get user stats
            stats_data = self._make_request_with_retry(f"https://api.chess.com/pub/player/{username}/stats")
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
                            clean_type = game_type.replace("chess_", "").replace("daily", "classical")
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
                        last_seen = datetime.fromtimestamp(profile_data["last_login_date"])
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
                
                logger.info(f"✅ Found Chess.com user: {username} (avg rating: {avg_rating:.0f})")
                
            except Exception as e:
                logger.warning(f"⚠️ Error processing Chess.com user {username}: {e}")
        
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
            lichess_users = self.discover_lichess_users(skill_level, game_types, users_per_platform)
            all_discovered.extend(lichess_users)
        
        if platform in [Platform.CHESS_COM, Platform.BOTH]:
            users_per_platform = max_users if platform == Platform.CHESS_COM else max_users // 2
            chesscom_users = self.discover_chesscom_users(skill_level, game_types, users_per_platform)
            all_discovered.extend(chesscom_users)
        
        # Save cache
        self._save_cache()
        
        logger.info(f"🎉 Discovery completed! Found {len(all_discovered)} total users")
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
                    writer.writerow(['username', 'platform', 'avg_rating', 'total_games', 'skill_level', 'profile_url'])
                    
                    for user in users:
                        avg_rating = sum(user.ratings.values()) / len(user.ratings) if user.ratings else 0
                        writer.writerow([
                            user.username, user.platform, f"{avg_rating:.0f}", 
                            user.total_games, user.skill_level, user.profile_url
                        ])
                        
            elif format == "txt":
                with open(filepath, 'w') as f:
                    f.write(f"# Discovered Chess Users - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"# Total users: {len(users)}\n\n")
                    
                    for user in users:
                        avg_rating = sum(user.ratings.values()) / len(user.ratings) if user.ratings else 0
                        f.write(f"{user.username} ({user.platform}) - Rating: {avg_rating:.0f} - Games: {user.total_games}\n")
            
            logger.info(f"📄 Exported {len(users)} users to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Error exporting users: {e}")
            return None

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
    parser.add_argument('--export-format', choices=['json', 'csv', 'txt'], default='json',
                        help='Export format for discovered users')
    parser.add_argument('--export-filename', help='Custom filename for export (optional)')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Convert arguments to enums
    platform = Platform(args.platform)
    skill_level = SkillLevel(args.skill_level)
    game_types = [GameType(gt) for gt in args.game_types]
    
    # Initialize discovery system
    discovery = SmartUserDiscovery()
    
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
            print(f"   - Total users found: {len(discovered_users)}")
            print(f"   - Platforms: {', '.join(set(u.platform for u in discovered_users))}")
            print(f"   - Skill levels: {', '.join(set(u.skill_level for u in discovered_users))}")
            print(f"   - Export file: {export_path}")
            
            # Show sample users
            if len(discovered_users) > 0:
                print(f"\n👥 Sample discovered users:")
                for i, user in enumerate(discovered_users[:5]):
                    avg_rating = sum(user.ratings.values()) / len(user.ratings) if user.ratings else 0
                    print(f"   {i+1}. {user.username} ({user.platform}) - {avg_rating:.0f} rating - {user.total_games} games")
                
                if len(discovered_users) > 5:
                    print(f"   ... and {len(discovered_users) - 5} more users")
        else:
            print("❌ No users discovered. Try adjusting the search parameters.")
            
    except KeyboardInterrupt:
        logger.info("⚠️ Discovery interrupted by user")
    except Exception as e:
        logger.error(f"❌ Discovery failed: {e}")
        raise

if __name__ == "__main__":
    main()
