#!/usr/bin/env python3
"""
Descarga de Partidas Nuevas de Chess.com para Validación Externa

Este script descarga partidas de usuarios específicos de chess.com 
posteriores a las fechas ya procesadas, para validación del modelo PERSONAL.

Usuarios objetivo:
- cmess1315 
- cmess4401 (últimas partidas: 2025-02-05)

Usage:
    python src/scripts/download_chess_com_validation.py --users cmess1315,cmess4401 --after-date 2025-02-06
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

def get_user_archives(username):
    """Get available archives for a chess.com user."""
    url = f"https://api.chess.com/pub/player/{username}/games/archives"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        archives = response.json()['archives']
        print(f"✅ Found {len(archives)} archives for {username}")
        return archives
        
    except Exception as e:
        print(f"❌ Error getting archives for {username}: {e}")
        return []

def download_monthly_games(username, year, month, after_date=None):
    """Download games from a specific month."""
    url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month:02d}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        
        games_data = response.json()
        games = games_data.get('games', [])
        
        print(f"📅 {username} {year}-{month:02d}: {len(games)} games")
        
        # Filter games after specified date
        if after_date:
            after_timestamp = int(after_date.timestamp())
            filtered_games = [
                game for game in games 
                if game.get('end_time', 0) > after_timestamp
            ]
            print(f"  🔍 After {after_date.date()}: {len(filtered_games)} games")
            games = filtered_games
        
        return games
        
    except Exception as e:
        print(f"❌ Error downloading {username} {year}-{month:02d}: {e}")
        return []

def convert_to_pgn_format(games, username):
    """Convert chess.com API format to PGN."""
    pgn_games = []
    
    for game in games:
        try:
            # Get basic game info
            white = game.get('white', {}).get('username', 'Unknown')
            black = game.get('black', {}).get('username', 'Unknown') 
            
            # Get result
            white_result = game.get('white', {}).get('result', 'unknown')
            black_result = game.get('black', {}).get('result', 'unknown')
            
            if white_result == 'win':
                result = '1-0'
            elif black_result == 'win':
                result = '0-1'
            else:
                result = '1/2-1/2'
            
            # Get ratings
            white_rating = game.get('white', {}).get('rating', 'Unknown')
            black_rating = game.get('black', {}).get('rating', 'Unknown')
            
            # Get date
            end_time = game.get('end_time', 0)
            date = datetime.fromtimestamp(end_time).strftime('%Y.%m.%d')
            
            # Get time control
            time_control = game.get('time_control', 'Unknown')
            
            # Get PGN moves
            pgn_moves = game.get('pgn', '')
            
            if not pgn_moves:
                continue
                
            # Parse existing PGN to extract just the moves
            try:
                game_io = StringIO(pgn_moves)
                parsed_game = chess.pgn.read_game(game_io)
                if parsed_game:
                    moves = str(parsed_game.mainline_moves()).replace(',', ' ')
                else:
                    continue
            except:
                # Fallback: try to extract moves from PGN string
                lines = pgn_moves.strip().split('\n')
                move_lines = [line for line in lines if not line.startswith('[') and line.strip()]
                moves = ' '.join(move_lines)
            
            # Create PGN format
            pgn_content = f'''[Event "Chess.com Game"]
[Site "Chess.com"]
[Date "{date}"]
[Round "-"]
[White "{white}"]
[Black "{black}"]
[Result "{result}"]
[WhiteElo "{white_rating}"]
[BlackElo "{black_rating}"]
[TimeControl "{time_control}"]
[EndTime "{end_time}"]

{moves} {result}

'''
            pgn_games.append(pgn_content)
            
        except Exception as e:
            print(f"⚠️ Error processing game: {e}")
            continue
    
    return pgn_games

def download_new_games(username, after_date, output_dir):
    """Download new games for a user after specified date."""
    print(f"\n🎯 Downloading NEW games for {username} after {after_date.date()}")
    
    # Get archives
    archives = get_user_archives(username)
    if not archives:
        return None
    
    all_games = []
    
    # Process recent archives (last few months)
    current_date = datetime.now()
    
    for months_back in range(6):  # Check last 6 months
        target_date = current_date - timedelta(days=30 * months_back)
        year = target_date.year
        month = target_date.month
        
        # Check if this archive might have games after our cutoff
        if datetime(year, month, 1) >= after_date.replace(day=1):
            print(f"📅 Checking {year}-{month:02d}...")
            games = download_monthly_games(username, year, month, after_date)
            all_games.extend(games)
            
            # Rate limiting
            time.sleep(1)
    
    if not all_games:
        print(f"❌ No new games found for {username}")
        return None
    
    # Convert to PGN
    print(f"🔄 Converting {len(all_games)} games to PGN...")
    pgn_games = convert_to_pgn_format(all_games, username)
    
    if not pgn_games:
        print(f"❌ No valid PGN games for {username}")
        return None
    
    # Save to file
    filename = f"{username}_validation_{datetime.now().strftime('%Y%m%d')}.pgn"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        for pgn_game in pgn_games:
            f.write(pgn_game)
    
    print(f"💾 Saved {len(pgn_games)} games to {filepath}")
    return filepath

def main():
    parser = argparse.ArgumentParser(description="Download new chess.com games for validation")
    parser.add_argument('--users', type=str, required=True,
                       help='Comma-separated list of usernames (e.g., cmess1315,cmess4401)')
    parser.add_argument('--after-date', type=str, required=True,
                       help='Download games after this date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', type=str, default='./data/validation',
                       help='Directory to save PGN files')
    
    args = parser.parse_args()
    
    # Parse date
    try:
        after_date = datetime.strptime(args.after_date, '%Y-%m-%d')
    except ValueError:
        print("❌ Invalid date format. Use YYYY-MM-DD")
        return
    
    # Parse users
    users = [user.strip() for user in args.users.split(',')]
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🚀 DOWNLOADING NEW CHESS.COM GAMES FOR VALIDATION")
    print("="*60)
    print(f"👥 Users: {users}")
    print(f"📅 After: {after_date.date()}")
    print(f"📁 Output: {output_dir}")
    
    downloaded_files = []
    
    for username in users:
        print(f"\n{'='*20} {username.upper()} {'='*20}")
        
        filepath = download_new_games(username, after_date, output_dir)
        if filepath:
            downloaded_files.append(filepath)
        
        # Rate limiting between users
        time.sleep(2)
    
    # Summary
    print(f"\n🎉 DOWNLOAD COMPLETED")
    print("="*30)
    
    if downloaded_files:
        print(f"✅ Downloaded files:")
        for filepath in downloaded_files:
            print(f"  📄 {filepath}")
        
        print(f"\n🔄 NEXT STEPS:")
        print("1. Import games for validation:")
        for filepath in downloaded_files:
            filename = os.path.basename(filepath)
            print(f"   python src/scripts/import_pgns_parallel.py --source validation_external --pgn-files \"{filepath}\" --max-games 100 --workers 1")
        
        print("\n2. Generate features:")
        print("   python src/scripts/generate_features_with_tactics.py --source validation_external --max-games 200 --workers 2")
        
        print("\n3. Run validation:")
        print("   python src/ml/external_validation_personal.py --pgn-file \"validation_combined.pgn\" --skip-import --skip-features")
        
    else:
        print("❌ No files downloaded")

if __name__ == "__main__":
    main()