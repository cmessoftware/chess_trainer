import requests
import time
import os

class GameFetcher:
    def __init__(self, data_dir="data/games"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def fetch_chesscom_games(self, username, year, month) -> str:
        """
        Fetches games from Chess.com for a specific user, year, and month.
        """
        if not username or not year or not month:
            raise ValueError("Username, year, and month are required.")
        
        # Validar el formato del año y mes
        if not (isinstance(year, int) and isinstance(month, int)):
            raise ValueError("Year and month must be integers.")
        
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12.")
        
        # Construir la URL para obtener las partidas
        url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month:02d}/pgn"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "application/x-chess-pgn",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.chess.com/"
        }
        session = requests.Session()
        session.get("https://www.chess.com", headers=headers)  # Obtener cookies
        try:
            response = session.get(url, headers=headers)
            response.raise_for_status()
            pgn_data = response.text
            filename = f"{self.data_dir}/{username}_chesscom_{year}{month:02d}.pgn"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(pgn_data)
            return filename
            
        except requests.RequestException as e:
            print(f"Error al obtener partidas de Chess.com para {username}: {e}")
            return None

    def fetch_lichess_games(self, username, perf_type):
        url = f"https://lichess.org/api/games/user/{username}?max=10&rated=true&perfType={perf_type}"
        headers = {"Accept": "application/x-chess-pgn"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            raise Exception(f"Error al obtener partidas de Lichess para {username}: {e}")

    def fetch_multiple_users(self, users, platform="lichess", perf_type="blitz", year=None, month=None):
        results = []
        for username in users:
            if platform == "lichess":
                pgn_data = self.fetch_lichess_games(username, perf_type)
                if pgn_data:
                    filename = f"{self.data_dir}/{username}_lichess_{perf_type}.pgn"
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(pgn_data)
                    results.append((username, filename))
            elif platform == "chesscom":
                if year and month:
                    filename = self.fetch_chesscom_games(username, year, month)
                    if filename:
                        results.append((username, filename))
                else:
                    print("Se requieren año y mes para Chess.com")
            time.sleep(1)  # Respetar límites de tasa
        return results