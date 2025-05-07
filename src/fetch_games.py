import requests
import chess.pgn
import os
from datetime import datetime
import time

class GameFetcher:
    def __init__(self, data_dir="data/uploads"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def fetch_lichess_games(self, username, perf_type="blitz", max_games=100):
        """Obtiene partidas de un usuario desde Lichess."""
        url = f"https://lichess.org/api/games/user/{username}"
        params = {"perfType": perf_type, "max": max_games}
        headers = {"Accept": "application/x-chess-pgn"}
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            pgn_data = response.text
            
            # Guardar PGN en archivo
            filename = f"{self.data_dir}/{username}_lichess_{perf_type}_{datetime.now().strftime('%Y%m%d')}.pgn"
            with open(filename, "w") as f:
                f.write(pgn_data)
            return filename
        except requests.RequestException as e:
            print(f"Error al obtener partidas de Lichess para {username}: {e}")
            return None

    def fetch_chesscom_games(self, username, year, month):
        """Obtiene partidas de un usuario desde Chess.com para un mes/año específico."""
        url = f"https://api.chess.com/pub/player/{username}/games/{year}/{month}/pgn"
        headers = {"Accept": "application/x-chess-pgn"}
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            pgn_data = response.text
            
            # Guardar PGN en archivo
            filename = f"{self.data_dir}/{username}_chesscom_{year}{month}.pgn"
            with open(filename, "w") as f:
                f.write(pgn_data)
            return filename
        except requests.RequestException as e:
            print(f"Error al obtener partidas de Chess.com para {username}: {e}")
            return None

    def fetch_multiple_users(self, users, platform="lichess", perf_type="blitz", year=None, month=None):
        """Obtiene partidas de múltiples usuarios."""
        results = []
        for username in users:
            if platform == "lichess":
                filename = self.fetch_lichess_games(username, perf_type)
            elif platform == "chesscom":
                if year and month:
                    filename = self.fetch_chesscom_games(username, year, month)
                else:
                    print("Se requieren año y mes para Chess.com")
                    continue
            else:
                print("Plataforma no soportada")
                continue
            
            if filename:
                results.append((username, filename))
            time.sleep(1)  # Respetar límites de tasa
        return results