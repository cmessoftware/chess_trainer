import argparse
from datetime import date
import os
import traceback
from modules.fetch_games import fetch_chesscom_games, fetch_lichess_games

GAME_PERSONAL_DIR = "/app/src/data/games/personal"
GAME_NOVICE_DIR = "/app/src/data/games/novice"
GAME_DIR = "/app/src/data/games"
# Define your usernames here
MY_USERNAMES = ["cmess4401", "cmess1315"]
NOVICES_USERNAMES = ["punnal", "Siqueirosdaniel", "Omer204", "BCA_MARKLEY_11",
                     "broskiphone", "LMAO93", "juannp17", "Zupay60", "Daniyair", "lugo29", "Pajaro09"]
USERS = MY_USERNAMES + NOVICES_USERNAMES


def main():
    try:
        today = date.today().strftime("%Y-%m-%d")
        parser = argparse.ArgumentParser(
            description="Download chess games in PGN format from chess.com or lichess.")
        parser.add_argument("--server", nargs="+", choices=["chess.com", "lichess.org"],
                            default=["lichess.org", "chess.com"],
                            help="Chess server(s), e.g., --server chess.com lichess.org")
        parser.add_argument("--users", nargs="+", required=False,
                            help="One or more usernames (space-separated)")
        parser.add_argument("--max-games-per-games",
                            help="Maximum number of games to fetch per user (default: 1000)")
        parser.add_argument("--since", required=True,
                            help="Start date (YYYY-MM-DD)")
        parser.add_argument("--until", default=today,
                            required=False, help="End date (YYYY-MM-DD)")
        parser.add_argument("--output", required=False, help="Output PGN file")
        args = parser.parse_args()

        print(f"Arguments: {args}")

        valid_servers = {"chess.com", "lichess.org"}
        invalid_servers = set(args.server) - valid_servers
        if invalid_servers:
            raise ValueError(
                f"Invalid server(s): {', '.join(invalid_servers)}. Must be one or more of {', '.join(valid_servers)}.")

        if args.since > args.until:
            raise ValueError("'since' date cannot be after 'until' date.")
        args.users = USERS

        all_novice_games = []
        all_personal_games = []

        for server in args.server:
            for user in args.users:
                print(f"Fetching games for {user} from {server}...")
                if server == "chess.com":
                    games = fetch_chesscom_games(
                        user, args.since, args.until)
                else:
                    games = fetch_lichess_games(
                        user, args.since, args.until)
                print(f"Found {len(games)} games for {user} on {server}")

                if user in MY_USERNAMES:
                    all_personal_games.extend(games)
                else:
                    # Assuming novice users are those not in MY_USERNAMES
                    # Save max 1000 games per novice user
                    if len(games) > int(args.max_games_per_games):
                        print(
                            f"Warning: More than {args.max_games_per_games} games found for novice user {user}. Limiting to {args.max_games_per_games} games.")
                        games = games[:args.max_games_per_games]
                    print(f"Saving {len(games)} games for novice user {user}")
                    if len(games) > 0:
                        print(
                            f"Adding {len(games)} games to novice games list.")
                if not games:
                    print(f"No games found for {user} on {server}.")
                else:
                    all_novice_games.extend(games)

        print(f"Total novice games fetched: {len(all_novice_games)}")
        print(f"Total personal games fetched: {len(all_personal_games)}")

        if args.output is None:
            joined_servers = "_".join(args.server)
            args.output = f"games_{joined_servers}_{args.since}_{args.until}.pgn"

        if not all_personal_games and not all_novice_games:
            print(
                f"No games found for the users {', '.join(args.users)} and date range {args.since} to {args.until}.")
            return

        if all_novice_games:
            novice_game_path = os.path.join(GAME_NOVICE_DIR, args.output)
            os.makedirs(GAME_NOVICE_DIR, exist_ok=True)

            print(f"Saving novice games to {novice_game_path}...")
            with open(novice_game_path, "w", encoding="utf-8") as f:
                for pgn in all_novice_games:
                    f.write(pgn.strip() + "\n\n")

            print(
                f"Saved {len(all_novice_games)} novice games to {GAME_PERSONAL_DIR}/{args.output}")
        elif all_personal_games:
            personal_game_path = os.path.join(GAME_PERSONAL_DIR, args.output)
            os.makedirs(GAME_PERSONAL_DIR, exist_ok=True)

            print(f"Saving personal games to {personal_game_path}...")
            with open(novice_game_path, "w", encoding="utf-8") as f:
                for pgn in all_novice_games:
                    f.write(pgn.strip() + "\n\n")

            print(
                f"Saved {len(all_novice_games)} novice games to {GAME_NOVICE_DIR}/{args.output}")

    except Exception as e:
        print(f"Error: {e} - {traceback.format_exc()}")
        if e.__cause__:
            print(f"Cause: {e.__cause__}")
        exit(1)


if __name__ == "__main__":
    main()
