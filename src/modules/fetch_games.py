
import json
import requests
from datetime import datetime
from decorators.auto_logger import auto_log_module_functions

HEADERS = {
    "User-Agent": "chess_trainer/1.0 (+https://github.com/cmessoftware/chess_trainer)"
}


def fetch_chesscom_games(username, since, until):
    games = []
    since_dt = datetime.strptime(since, "%Y-%m-%d")
    until_dt = datetime.strptime(until, "%Y-%m-%d")
    # Chess.com API provides games by month
    months = set()
    current = since_dt
    while current <= until_dt:
        months.add((current.year, current.month))
        if current.month == 12:
            current = current.replace(year=current.year+1, month=1)
        else:
            current = current.replace(month=current.month+1)
    for year, month in months:
        print(
            f"Fetching Chess.com games for {username} from {year}-{month:02d}")
        url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month:02d}"
        resp = requests.get(url, headers=HEADERS)
        print(f"Response status: {resp.status_code}")
        if resp.status_code != 200:
            continue
        data = resp.json()
        for game in data.get("games", []):
            end_time = datetime.utcfromtimestamp(game["end_time"])
            if since_dt <= end_time <= until_dt:
                if "pgn" in game:
                    games.append(game["pgn"])
    return games


def fetch_lichess_games(username, since, until):
    # Lichess API allows filtering by date (timestamp in ms)
    since_ts = int(datetime.strptime(since, "%Y-%m-%d").timestamp())
    until_ts = int(datetime.strptime(until, "%Y-%m-%d").timestamp())
    url = f"https://lichess.org/api/games/user/{username}"
    params = {
        "since": since_ts * 1000,
        "until": until_ts * 1000,
        "max": 300,  # max per request
        "pgnInJson": True,
        "clocks": False,
        "evals": False,
        "opening": False,
    }
    headers = {"Accept": "application/x-ndjson"}
    resp = requests.get(url, params=params, headers=headers, stream=True)
    games = []
    if resp.status_code == 200:
        for line in resp.iter_lines():
            if line:
                try:
                    game = json.loads(line)
                    if "pgn" in game:
                        games.append(game["pgn"])
                except Exception:
                    continue
    return games


auto_log_module_functions(locals())
