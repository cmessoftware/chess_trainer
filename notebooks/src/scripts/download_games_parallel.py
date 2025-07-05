import argparse
from datetime import date
import os
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from modules.fetch_games import fetch_chesscom_games, fetch_lichess_games

GAME_PERSONAL_DIR = "/app/src/data/games/personal"
GAME_NOVICE_DIR = "/app/src/data/games/novice"
GAME_DIR = "/app/src/data/games"

MY_USERNAMES = ["cmess4401", "cmess1315"]
NOVICES_USERNAMES = [
    "punnal", "Siqueirosdaniel", "Omer204", "BCA_MARKLEY_11",
    "broskiphone", "LMAO93", "juannp17", "Zupay60", "Daniyair",
    "lugo29", "Pajaro09", "chess1625"
]

USERS = MY_USERNAMES + NOVICES_USERNAMES


def chunk_list(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


def fetch_games_for_users_chunk(server, users_chunk, since, until, max_games):
    novice_games = []
    personal_games = []

    for user in users_chunk:
        try:
            print(f"Fetching games for {user} from {server}...")
            if server == "chess.com":
                games = fetch_chesscom_games(user, since, until)
            elif server == "lichess.org":
                games = fetch_lichess_games(user, since, until)

            print(f"Found {len(games)} games for {user} on {server}")

            if user in MY_USERNAMES:
                personal_games.extend(games)
            else:
                if len(games) > int(max_games):
                    print(
                        f"Warning: More than {max_games} games found for novice user {user}. Limiting to {max_games} games.")
                    games = games[:int(max_games)]
                if games:
                    novice_games.extend(games)

        except Exception as e:
            print(f"❌ Error fetching for {user} on {server}: {e}")
    return personal_games, novice_games


def main():
    try:
        today = date.today().strftime("%Y-%m-%d")
        parser = argparse.ArgumentParser(
            description="Download chess games in PGN format from chess.com or lichess.")
        parser.add_argument("--server", nargs="+", choices=["chess.com", "lichess.org"],
                            default=["lichess.org", "chess.com"])
        parser.add_argument("--users", nargs="+", required=False,
                            default=USERS,
                            help="One or more usernames (space-separated)")
        parser.add_argument("--max-games-per-games", type=int, default=1000,
                            help="Maximum number of games to fetch per user (default: 1000)")
        parser.add_argument("--since", required=False,
                            default="2025-01-01",
                            help="Start date (YYYY-MM-DD)")
        parser.add_argument("--until", default=today,
                            help="End date (YYYY-MM-DD)")
        parser.add_argument("--output", required=False,
                            help="Output PGN filename")
        args = parser.parse_args()

        print(f"📥 Arguments: {args}")

        if args.since > args.until:
            raise ValueError("'since' date cannot be after 'until' date.")

        args.users = USERS if not args.users else args.users
        max_games = args.max_games_per_games
        user_chunks = list(chunk_list(args.users, 4))  # 👈 chunk size ajustable

        all_novice_games = []
        all_personal_games = []

        for server in args.server:
            with ThreadPoolExecutor(max_workers=4) as executor:
                futures = [
                    executor.submit(fetch_games_for_users_chunk, server,
                                    chunk, args.since, args.until, max_games)
                    for chunk in user_chunks
                ]
                for future in as_completed(futures):
                    personal, novice = future.result()
                    all_personal_games.extend(personal)
                    all_novice_games.extend(novice)

        print(f"✅ Total novice games fetched: {len(all_novice_games)}")
        print(f"✅ Total personal games fetched: {len(all_personal_games)}")

        if args.output is None:
            joined_servers = "_".join(args.server)
            args.output = f"games_{joined_servers}_{args.since}_{args.until}.pgn"

        if not all_personal_games and not all_novice_games:
            print(
                f"⚠️ No games found for users in date range {args.since} to {args.until}.")
            return

        if all_novice_games:
            os.makedirs(GAME_NOVICE_DIR, exist_ok=True)
            novice_game_path = os.path.join(GAME_NOVICE_DIR, args.output)
            with open(novice_game_path, "w", encoding="utf-8") as f:
                for pgn in all_novice_games:
                    f.write(pgn.strip() + "\n\n")
            print(
                f"📁 Saved {len(all_novice_games)} novice games to {novice_game_path}")

        if all_personal_games:
            os.makedirs(GAME_PERSONAL_DIR, exist_ok=True)
            personal_game_path = os.path.join(GAME_PERSONAL_DIR, args.output)
            with open(personal_game_path, "w", encoding="utf-8") as f:
                for pgn in all_personal_games:
                    f.write(pgn.strip() + "\n\n")
            print(
                f"📁 Saved {len(all_personal_games)} personal games to {personal_game_path}")
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        if e.__cause__:
            print(f"Caused by: {e.__cause__}")
        print("Please check the arguments and try again.")
        return


if __name__ == "__main__":
    main()
