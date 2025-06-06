import argparse
from datetime import date
import os
from modules.fetch_games import fetch_chesscom_games, fetch_lichess_games

GAME_DIR = "/app/src/data/games/"

def main():
    try:
        today = date.today().strftime("%Y-%m-%d")
        parser = argparse.ArgumentParser(description="Download chess games in PGN format from chess.com or lichess.")
        parser.add_argument("--server", nargs="+", choices=["chess.com", "lichess.org"], required=True, help="Chess server(s), e.g., --server chess.com lichess.org")
        parser.add_argument("--users", nargs="+", required=True, help="One or more usernames (space-separated)")
        parser.add_argument("--since", required=True, help="Start date (YYYY-MM-DD)")
        parser.add_argument("--until", default=today, required=False, help="End date (YYYY-MM-DD)")
        parser.add_argument("--output", required=False, help="Output PGN file")
        args = parser.parse_args()

        valid_servers = {"chess.com", "lichess.org"}
        invalid_servers = set(args.server) - valid_servers
        if invalid_servers:
            raise ValueError(f"Invalid server(s): {', '.join(invalid_servers)}. Must be one or more of {', '.join(valid_servers)}.")

        if args.since > args.until:
            raise ValueError("'since' date cannot be after 'until' date.")

        all_games = []

        for server in args.server:
            for user in args.users:
                print(f"Fetching games for {user} from {server}...")
                if server == "chess.com":
                    games = fetch_chesscom_games(user, args.since, args.until)
                else:
                    games = fetch_lichess_games(user, args.since, args.until)
                print(f"Found {len(games)} games for {user} on {server}")
                all_games.extend(games)

        if args.output is None:
            joined_servers = "_".join(args.server)
            args.output = f"games_{joined_servers}_{args.since}_{args.until}.pgn"

        game_path = os.path.join(GAME_DIR, args.output)
        os.makedirs(GAME_DIR, exist_ok=True)

        if not all_games:
            print("No games found for the specified users and date range.")
            return

        print(f"Saving games to {game_path}...")
        with open(game_path, "w", encoding="utf-8") as f:
            for pgn in all_games:
                f.write(pgn.strip() + "\n\n")

        print(f"Saved {len(all_games)} games to {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
if __name__ == "__main__":
    main()
