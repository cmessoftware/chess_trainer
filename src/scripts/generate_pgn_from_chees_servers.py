import argparse
import requests
import os
from datetime import datetime
import json
from modules.fetch_games import fetch_chesscom_games, fetch_lichess_games

GAME_DIR = "/app/src/data/games/"

def main():
    parser = argparse.ArgumentParser(description="Download chess games in PGN format from chess.com or lichess.")
    parser.add_argument("--server", choices=["chess.com", "lichess.org"], required=True, help="Chess server")
    parser.add_argument("--users", nargs="+", required=True, help="List of usernames")
    parser.add_argument("--since", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--until", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument("--output", required=False, help="Output PGN file")
    args = parser.parse_args()
    
    """
    Fetch games from chess.com or lichess.org based on user input.
    """
    if args.server not in ["chess.com", "lichess.org"]:
        raise ValueError("Server must be either 'chess.com' or 'lichess.org'.")

    if args.since is None or args.until is None:
        raise ValueError("Both 'since' and 'until' dates must be provided.")

    if args.since > args.until:
        raise ValueError("'since' date cannot be after 'until' date.")

    all_games = []
    for user in args.users:
        print(f"Fetching games for {user} from {args.server}...")
        if args.server == "chess.com":
            games = fetch_chesscom_games(user, args.since, args.until)
        else:
            games = fetch_lichess_games(user, args.since, args.until)
        print(f"Found {len(games)} games for {user}")
        all_games.extend(games)

    if args.output is None:
        args.output = f"games_{args.server}_{args.since}_{args.until}.pgn"
        
    game_path = os.path.join(GAME_DIR, args.output)
    os.makedirs(GAME_DIR, exist_ok=True)
    
    if all_games == None or len(all_games) == 0:
        print(f"No games found for the specified users and date range.")
        return
    
    print(f"Saving games to {game_path}...")

    with open(game_path, "w", encoding="utf-8") as f:
        for pgn in all_games:
            f.write(pgn.strip() + "\n\n")
    print(f"Saved {len(all_games)} games to {args.output}")

if __name__ == "__main__":
    main()
    
# This script fetches chess games from chess.com or lichess.org for specified users and date range,
# and saves them in PGN format to a specified output file.
# Usage:
# python generate_pgn_from_chees_servers.py --server chess.com --users user1 user2 --since 2023-01-01 --until 2023-12-31 --output games.pgn
# python generate_pgn_from_chees_servers.py --server lichess --users user1 user2 --since 2023-01-01 --until 2023-12-31 --output games.pgn