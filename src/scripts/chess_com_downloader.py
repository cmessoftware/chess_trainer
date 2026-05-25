#!/usr/bin/env python3
"""
🚀 Chess.com PGN Downloader - Mejorado contra errores 403
Descarga partidas de cualquier usuario de Chess.com con rate limiting inteligente.

Usage:
    python chess_com_downloader.py USERNAME [--after-date YYYY-MM-DD] [--output-dir PATH]

Examples:
    python chess_com_downloader.py cmess1315
    python chess_com_downloader.py magnus --after-date 2025-01-01
    python chess_com_downloader.py hikaru --after-date 2024-01-01 --output-dir downloads/
"""

import argparse
import requests
import json
import time
from datetime import datetime, timedelta
import os
from pathlib import Path
import chess.pgn
from io import StringIO
import random


class ChessComAPI:
    """Robust Chess.com API client with anti-blocking measures."""

    def __init__(self):
        self.session = requests.Session()
        # Use realistic browser headers
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Cache-Control": "max-age=0",
            }
        )

        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 2.0  # Minimum 2 seconds between requests
        self.max_retries = 5

    def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_delay:
            wait_time = self.min_delay - elapsed
            print(f"⏳ Rate limiting: waiting {wait_time:.1f} seconds...")
            time.sleep(wait_time)

        # Add random jitter to avoid synchronized requests
        jitter = random.uniform(0.5, 1.5)
        time.sleep(jitter)

        self.last_request_time = time.time()

    def _safe_request(self, url, description="Request"):
        """Make a safe request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                self._wait_for_rate_limit()

                print(f"🔄 {description} (attempt {attempt + 1}/{self.max_retries})")

                response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    print(f"❌ Forbidden (403) - Chess.com is blocking us")
                    if attempt < self.max_retries - 1:
                        delay = min(60, (2**attempt) * 10)  # Exponential backoff
                        print(f"⏳ Waiting {delay} seconds before retry...")
                        time.sleep(delay)
                elif response.status_code == 404:
                    print(f"❌ Not found (404) - User or resource doesn't exist")
                    return None
                elif response.status_code == 429:
                    print(f"❌ Rate limited (429)")
                    if attempt < self.max_retries - 1:
                        delay = min(120, (2**attempt) * 15)
                        print(f"⏳ Rate limit - waiting {delay} seconds...")
                        time.sleep(delay)
                else:
                    print(f"❌ HTTP {response.status_code}: {response.reason}")

            except requests.exceptions.RequestException as e:
                print(f"❌ Network error: {e}")
                if attempt < self.max_retries - 1:
                    delay = min(30, (2**attempt) * 5)
                    print(f"⏳ Network error - waiting {delay} seconds...")
                    time.sleep(delay)

        print(f"❌ Failed after {self.max_retries} attempts")
        return None

    def get_user_profile(self, username):
        """Get user profile to verify existence."""
        url = f"https://api.chess.com/pub/player/{username.lower()}"
        response = self._safe_request(url, f"Getting profile for {username}")

        if response:
            try:
                profile = response.json()
                print(f"✅ Found user: {profile.get('name', username)}")
                print(f"   Username: {profile.get('username', 'Unknown')}")
                print(
                    f"   Country: {profile.get('country', 'Unknown').split('/')[-1] if profile.get('country') else 'Unknown'}"
                )
                return profile
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in profile response: {e}")

        return None

    def get_user_archives(self, username):
        """Get available archives for a user."""
        url = f"https://api.chess.com/pub/player/{username.lower()}/games/archives"
        response = self._safe_request(url, f"Getting archives for {username}")

        if response:
            try:
                data = response.json()
                archives = data.get("archives", [])
                print(f"✅ Found {len(archives)} monthly archives")
                return archives
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in archives response: {e}")

        return []

    def download_monthly_games(self, username, year, month, after_date=None):
        """Download games for a specific month."""
        url = f"https://api.chess.com/pub/player/{username.lower()}/games/{year}/{month:02d}"
        response = self._safe_request(url, f"Downloading {username} {year}-{month:02d}")

        if response:
            try:
                data = response.json()
                games = data.get("games", [])

                if after_date:
                    after_timestamp = int(after_date.timestamp())
                    original_count = len(games)
                    games = [g for g in games if g.get("end_time", 0) > after_timestamp]
                    print(
                        f"📅 {original_count} games → {len(games)} after {after_date.date()}"
                    )
                else:
                    print(f"📅 {len(games)} games total")

                return games

            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in games response: {e}")

        return []


def convert_chess_com_to_pgn(games, username):
    """Convert Chess.com games to PGN format."""
    pgn_games = []

    for i, game in enumerate(games):
        try:
            white = game.get("white", {}).get("username", "Unknown")
            black = game.get("black", {}).get("username", "Unknown")
            result = game.get("result", "*")

            # Convert end_time to date
            end_time = game.get("end_time")
            if end_time:
                game_date = datetime.fromtimestamp(end_time).strftime("%Y.%m.%d")
            else:
                game_date = "????.??.??"

            # Get time control
            time_control = game.get("time_control", "Unknown")
            time_class = game.get("time_class", "unknown")

            # Build PGN
            headers = [
                f'[Event "Chess.com {time_class.title()} Game"]',
                f'[Site "Chess.com"]',
                f'[Date "{game_date}"]',
                f'[Round "-"]',
                f'[White "{white}"]',
                f'[Black "{black}"]',
                f'[Result "{result}"]',
                f'[TimeControl "{time_control}"]',
                f'[Termination "{game.get("termination", "Unknown")}"]',
            ]

            # Add opening if available
            if game.get("eco"):
                headers.append(f'[ECO "{game["eco"]}"]')

            headers.append("")  # Empty line after headers

            # Add moves - Chess.com API provides 'pgn' field with full notation
            pgn_text = game.get("pgn", "")
            if pgn_text:
                # Extract only the moves part (after the headers)
                pgn_lines = pgn_text.split('\n')
                moves_started = False
                moves_lines = []
                for line in pgn_lines:
                    if moves_started or (line and not line.startswith('[')):
                        moves_started = True
                        moves_lines.append(line)
                if moves_lines:
                    headers.append('\n'.join(moves_lines).strip())
                else:
                    headers.append(result)
            else:
                headers.append(result)

            headers.append("")  # Empty line between games

            pgn_games.extend(headers)

            if (i + 1) % 10 == 0:
                print(f"   Converted {i + 1}/{len(games)} games...")

        except Exception as e:
            print(f"⚠️ Error converting game {i}: {e}")
            continue

    return "\n".join(pgn_games)


def main():
    parser = argparse.ArgumentParser(
        description="Download Chess.com games in PGN format"
    )
    parser.add_argument("username", help="Chess.com username")
    parser.add_argument(
        "--after-date", type=str, help="Download games after this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/games/personal",
        help="Output directory for PGN files",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="Number of recent months to check (default: 12)",
    )

    args = parser.parse_args()

    # Parse after_date
    after_date = None
    if args.after_date:
        try:
            after_date = datetime.strptime(args.after_date, "%Y-%m-%d")
        except ValueError:
            print(f"❌ Invalid date format: {args.after_date}. Use YYYY-MM-DD")
            return

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print("🚀 CHESS.COM PGN DOWNLOADER")
    print("=" * 50)
    print(f"👤 Username: {args.username}")
    print(f"📅 After date: {args.after_date or 'All games'}")
    print(f"📁 Output: {output_dir}")
    print(f"📊 Months to check: {args.months}")
    print()

    # Initialize API client
    api = ChessComAPI()

    # Check user exists
    print("🔍 Verifying user...")
    profile = api.get_user_profile(args.username)
    if not profile:
        print("❌ User not found or inaccessible")
        return

    # Get archives
    print("\n📚 Getting game archives...")
    archives = api.get_user_archives(args.username)
    if not archives:
        print("❌ No archives found")
        return

    # Process recent months only
    archives = sorted(archives)[-args.months :]  # Get last N months
    print(f"📅 Processing {len(archives)} recent archive(s)")

    # Download games
    all_games = []

    for archive_url in archives:
        try:
            # Extract year/month from URL
            parts = archive_url.split("/")
            year, month = int(parts[-2]), int(parts[-1])

            games = api.download_monthly_games(args.username, year, month, after_date)
            all_games.extend(games)

        except Exception as e:
            print(f"❌ Error processing {archive_url}: {e}")

    if not all_games:
        print("❌ No games found")
        return

    print(f"\n📊 Total games downloaded: {len(all_games)}")

    # Convert to PGN
    print("🔄 Converting to PGN format...")
    pgn_content = convert_chess_com_to_pgn(all_games, args.username)

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{args.username.lower()}_{timestamp}.pgn"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pgn_content)

    print(f"✅ Saved to: {output_file}")
    print(f"📏 File size: {output_file.stat().st_size:,} bytes")
    print(f"🎉 Download completed successfully!")


if __name__ == "__main__":
    main()
