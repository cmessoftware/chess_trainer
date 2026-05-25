#!/usr/bin/env python3
"""
Descarga Mejorada de Partidas Recientes de Chess.com

Este script usa múltiples estrategias para descargar las partidas más recientes:
1. Retry con backoff exponencial
2. User-Agent personalizado
3. Manejo de rate limiting
4. Fallback a diferentes endpoints

Permite especificar usuarios y fecha desde por parámetros de línea de comandos.

Usage:
    python download_recent_chess_com.py --users manuelfrp79 cmess4401 --after-date 2025-01-15
    python download_recent_chess_com.py --users manuelfrp79 --after-date 2025-02-01 --output-dir ./custom_output

Parameters:
    --users: Lista de usuarios de Chess.com (requerido)
    --after-date: Fecha desde la cual descargar (formato YYYY-MM-DD, default: 2025-01-01)
    --output-dir: Directorio de salida (default: ./data/validation_recent)
"""

import requests
import time
import json
from datetime import datetime, timedelta
from pathlib import Path
import chess.pgn
from io import StringIO
import random
import argparse

class ChessComDownloader:
    def __init__(self):
        self.session = requests.Session()
        # User-Agent más realista
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def exponential_backoff(self, attempt, base_delay=1, max_delay=60):
        """Calculate delay with jitter for exponential backoff."""
        delay = min(base_delay * (2 ** attempt), max_delay)
        jitter = random.uniform(0.1, 0.9) * delay
        return delay + jitter
    
    def safe_request(self, url, max_retries=5):
        """Make request with retry logic."""
        for attempt in range(max_retries):
            try:
                print(f"🔄 Request attempt {attempt + 1}: {url}")
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 403:
                    print(f"❌ Forbidden (403) - Possible rate limit or blocked")
                    if attempt < max_retries - 1:
                        delay = self.exponential_backoff(attempt, base_delay=5)
                        print(f"⏳ Waiting {delay:.1f} seconds...")
                        time.sleep(delay)
                elif response.status_code == 429:
                    print(f"❌ Rate limited (429)")
                    if attempt < max_retries - 1:
                        delay = self.exponential_backoff(attempt, base_delay=10)
                        print(f"⏳ Rate limit - waiting {delay:.1f} seconds...")
                        time.sleep(delay)
                else:
                    print(f"❌ HTTP {response.status_code}: {response.text[:200]}")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Request error: {e}")
                if attempt < max_retries - 1:
                    delay = self.exponential_backoff(attempt)
                    print(f"⏳ Waiting {delay:.1f} seconds...")
                    time.sleep(delay)
        
        return None
    
    def get_user_profile(self, username):
        """Get user profile to verify existence."""
        url = f"https://api.chess.com/pub/player/{username}"
        
        print(f"👤 Checking user profile: {username}")
        response = self.safe_request(url)
        
        if response:
            try:
                profile = response.json()
                print(f"✅ Found user: {profile.get('username', 'Unknown')}")
                print(f"   Status: {profile.get('status', 'Unknown')}")
                return profile
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response")
        
        return None
    
    def get_archives_list(self, username):
        """Get list of available archives."""
        url = f"https://api.chess.com/pub/player/{username}/games/archives"
        
        print(f"📅 Getting archives for {username}")
        response = self.safe_request(url)
        
        if response:
            try:
                data = response.json()
                archives = data.get('archives', [])
                print(f"✅ Found {len(archives)} archives")
                return archives
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response")
        
        return []
    
    def download_monthly_games(self, username, year, month, after_timestamp=None):
        """Download games for specific month."""
        url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month:02d}"
        
        print(f"📥 Downloading {username} {year}-{month:02d}")
        response = self.safe_request(url)
        
        if response:
            try:
                data = response.json()
                games = data.get('games', [])
                
                print(f"   📊 Raw games: {len(games)}")
                
                # Filter by timestamp if provided
                if after_timestamp:
                    filtered_games = [
                        game for game in games 
                        if game.get('end_time', 0) > after_timestamp
                    ]
                    print(f"   🔍 After filter: {len(filtered_games)}")
                    return filtered_games
                
                return games
                
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON response")
        
        return []
    
    def convert_games_to_pgn(self, games, username):
        """Convert chess.com games to PGN format."""
        pgn_content = []
        successful = 0
        
        print(f"🔄 Converting {len(games)} games to PGN...")
        
        for i, game in enumerate(games):
            try:
                # Basic info
                white = game.get('white', {}).get('username', 'Unknown')
                black = game.get('black', {}).get('username', 'Unknown')
                
                # Result
                white_result = game.get('white', {}).get('result', 'unknown')
                if white_result == 'win':
                    result = '1-0'
                elif game.get('black', {}).get('result', 'unknown') == 'win':
                    result = '0-1' 
                else:
                    result = '1/2-1/2'
                
                # Ratings
                white_elo = game.get('white', {}).get('rating', 1500)
                black_elo = game.get('black', {}).get('rating', 1500)
                
                # Date and time
                end_time = game.get('end_time', 0)
                date_obj = datetime.fromtimestamp(end_time)
                date_str = date_obj.strftime('%Y.%m.%d')
                
                # Time control and URL
                time_control = game.get('time_control', 'unknown')
                game_url = game.get('url', '')
                
                # Get PGN moves
                pgn_text = game.get('pgn', '')
                if not pgn_text:
                    continue
                
                # Create complete PGN
                pgn_game = f"""[Event "Live Chess"]
[Site "Chess.com"]
[Date "{date_str}"]
[Round "-"]
[White "{white}"]
[Black "{black}"]
[Result "{result}"]
[WhiteElo "{white_elo}"]
[BlackElo "{black_elo}"]
[TimeControl "{time_control}"]
[EndTime "{end_time}"]
[Termination "{game.get('white', {}).get('result', 'unknown')}"]
[Link "{game_url}"]

{pgn_text}

"""
                pgn_content.append(pgn_game)
                successful += 1
                
                if (i + 1) % 50 == 0:
                    print(f"   📝 Processed {i + 1}/{len(games)} games")
                    
            except Exception as e:
                print(f"⚠️ Error processing game {i}: {e}")
                continue
        
        print(f"✅ Successfully converted {successful}/{len(games)} games")
        return pgn_content
    
    def download_recent_games(self, username, after_date, output_dir):
        """Download all games after specified date."""
        print(f"\n🎯 DOWNLOADING RECENT GAMES: {username}")
        print("=" * 50)
        
        # Check user exists
        if not self.get_user_profile(username):
            print(f"❌ User {username} not found or inaccessible")
            return None
        
        # Get archives
        archives = self.get_archives_list(username)
        if not archives:
            print(f"❌ No archives found for {username}")
            return None
        
        # Filter relevant archives (last 12 months)
        after_timestamp = int(after_date.timestamp())
        current_date = datetime.now()
        all_games = []
        
        # Check recent months
        for months_back in range(12):  # Check last 12 months
            target_date = current_date - timedelta(days=30 * months_back)
            year = target_date.year
            month = target_date.month
            
            # Skip if month is before our cutoff
            month_start = datetime(year, month, 1)
            if month_start < after_date.replace(day=1):
                continue
            
            print(f"\n📅 Checking {year}-{month:02d}")
            games = self.download_monthly_games(username, year, month, after_timestamp)
            
            if games:
                all_games.extend(games)
                print(f"   ✅ Added {len(games)} games (total: {len(all_games)})")
            
            # Rate limiting
            time.sleep(2)
        
        if not all_games:
            print(f"❌ No new games found for {username}")
            return None
        
        # Convert to PGN
        pgn_games = self.convert_games_to_pgn(all_games, username)
        
        if not pgn_games:
            print(f"❌ No valid PGN games generated")
            return None
        
        # Save to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        filename = f"{username}_recent_{timestamp}.pgn"
        filepath = Path(output_dir) / filename
        
        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for pgn_game in pgn_games:
                f.write(pgn_game)
        
        print(f"💾 Saved to: {filepath}")
        print(f"📊 Total games: {len(pgn_games)}")
        
        return filepath

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Download recent Chess.com games for specified users',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python download_recent_chess_com.py --users manuelfrp79 cmess4401
  python download_recent_chess_com.py --users manuelfrp79 --after-date 2025-01-15
  python download_recent_chess_com.py --users manuelfrp79 --after-date 2025-02-01 --output-dir ./custom_output
        """
    )
    
    parser.add_argument(
        '--users',
        nargs='+',
        required=True,
        help='List of Chess.com usernames to download games from (space separated)'
    )
    
    parser.add_argument(
        '--after-date',
        type=str,
        default='2025-01-01',
        help='Download games after this date (YYYY-MM-DD format, default: 2025-01-01)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./data/validation_recent',
        help='Output directory for downloaded PGN files (default: ./data/validation_recent)'
    )
    
    return parser.parse_args()

def main():
    print("🚀 DESCARGA DE PARTIDAS RECIENTES - CHESS.COM")
    print("=" * 60)
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Configuration from arguments
    users = args.users
    try:
        after_date = datetime.strptime(args.after_date, '%Y-%m-%d')
    except ValueError:
        print(f"❌ Invalid date format: {args.after_date}. Use YYYY-MM-DD format.")
        return 1
    
    output_dir = Path(args.output_dir)
    
    print(f"👥 Users: {users}")
    print(f"📅 After: {after_date.date()}")
    print(f"📁 Output: {output_dir}")
    
    downloader = ChessComDownloader()
    downloaded_files = []
    
    for username in users:
        try:
            filepath = downloader.download_recent_games(username, after_date, output_dir)
            if filepath:
                downloaded_files.append(filepath)
            else:
                print(f"❌ Failed to download games for {username}")
        
        except Exception as e:
            print(f"❌ Error processing {username}: {e}")
        
        # Wait between users
        print(f"\n⏳ Waiting 5 seconds before next user...")
        time.sleep(5)
    
    # Summary
    print(f"\n🎉 DOWNLOAD SUMMARY")
    print("=" * 30)
    
    if downloaded_files:
        print(f"✅ Successfully downloaded:")
        total_size = 0
        for filepath in downloaded_files:
            size = filepath.stat().st_size
            total_size += size
            print(f"  📄 {filepath.name} ({size:,} bytes)")
        
        print(f"\n📊 Total: {len(downloaded_files)} files, {total_size:,} bytes")
        
        # Create combined file
        combined_file = output_dir / f"combined_recent_{datetime.now().strftime('%Y%m%d_%H%M')}.pgn"
        with open(combined_file, 'w', encoding='utf-8') as combined:
            for filepath in downloaded_files:
                with open(filepath, 'r', encoding='utf-8') as individual:
                    combined.write(individual.read())
                    combined.write('\n')
        
        print(f"📦 Combined file: {combined_file}")
        
        print(f"\n🔄 NEXT STEPS:")
        print(f"1. Import: python src/scripts/import_pgns_parallel.py --source validation_recent --pgn-files \"{combined_file}\" --max-games 500")
        print(f"2. Features: python src/scripts/generate_features_with_tactics.py --source validation_recent --max-games 500 --workers 2")
        print(f"3. Analysis: python src/ml/external_validation_personal.py --skip-import --skip-features")
        
    else:
        print("❌ No files downloaded")
        print("\n💡 Possible solutions:")
        print("- Check internet connection")  
        print("- Verify usernames exist")
        print("- Try again later (rate limiting)")
        print("- Use VPN if IP is blocked")
        return 1
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())