import os
import requests
from dotenv import load_dotenv

load_dotenv()

class LichessPublisher:
    def __init__(self):
        self.token = os.getenv("LICHESS_TOKEN")
        if not self.token:
            raise ValueError("Falta LICHESS_TOKEN en .env")
        self.headers = {
            "Authorization": f"Bearer {self.token}"
        }

    def upload_pgn_file(self, file_path, study_name="Partida Anotada"):
        url = "https://lichess.org/api/study"

        with open(file_path, "rb") as f:
            files = {
                'pgn': (file_path, f),
                'name': (None, study_name),
                'visibility': (None, "unlisted")  # Podés usar "public" o "invite"
            }

            response = requests.post(url, headers=self.headers, files=files)

        if response.status_code != 200:
            raise Exception(f"Error al subir estudio: {response.status_code} - {response.text}")

        json = response.json()
        return f"https://lichess.org/study/{json['id']}"
