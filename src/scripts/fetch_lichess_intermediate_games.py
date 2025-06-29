import os
import requests
import time
import random
from typing import List, Set
from tqdm import tqdm
import dotenv
# Cargar variables de entorno desde .env
dotenv.load_dotenv()

PGN_PATH = os.environ.get("PGN_PATH")


def get_random_lichess_user() -> str:
    """Genera un nombre de usuario plausible para probar contra la API"""
    prefixes = ["chess", "king", "rook", "tactic",
                "blitz", "user", "capy", "rapid"]
    suffixes = ["123", "2023", "pro", "bot", "9000", "xd", "elo", ""]
    return random.choice(prefixes) + random.choice(suffixes) + str(random.randint(1, 9999))


def get_lichess_profile(username: str) -> dict:
    """Devuelve el perfil del usuario de Lichess (o None si no existe)"""
    try:
        r = requests.get(f"https://lichess.org/api/user/{username}", timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def download_pgn_games(username: str, max_games: int = 20) -> List[str]:
    """Descarga partidas PGN rápidas y rated del usuario"""
    try:
        url = (
            f"https://lichess.org/api/games/user/{username}"
            f"?max={max_games}&perfType=rapid&rated=true&clocks=false&evals=false"
        )
        headers = {
            "Accept": "application/x-chess-pgn"
        }
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200 and r.text.strip():
            return r.text.strip().split("\n\n")
    except:
        pass
    return []


def fetch_lichess_intermediate_games(target_count: int = 10000, max_per_user: int = 20) -> List[str]:
    """Descarga partidas de usuarios rapid entre 1700 y 2000 ELO"""
    games = []
    tried_users: Set[str] = set()
    pbar = tqdm(total=target_count, desc="⏳ Descargando partidas intermedias")

    while len(games) < target_count:
        username = get_random_lichess_user()
        if username in tried_users:
            continue
        tried_users.add(username)

        profile = get_lichess_profile(username)
        if not profile:
            continue

        rapid_rating = profile.get("perfs", {}).get(
            "rapid", {}).get("rating", 0)
        if not (1700 <= rapid_rating <= 2000):
            continue

        user_games = download_pgn_games(username, max_per_user)
        if user_games:
            games.extend(user_games)
            pbar.update(len(user_games))
            print(
                f"✅ {username} ({rapid_rating}) ➜ {len(user_games)} partidas acumuladas: {len(games)}")

        time.sleep(1)

    pbar.close()
    return games


if __name__ == "__main__":
    games = fetch_lichess_intermediate_games(target_count=100, max_per_user=10)
    with open(f"{PGN_PATH}/intermediate/lichess_games.pgn", "w", encoding="utf-8") as f:
        f.write("\n\n".join(games))
    print(
        f"Guardadas {len(games)} partidas en 'intermediate_lichess_games.pgn'")
