import requests

#MIGRATED-TODO: Get lichess study api and test.


def download_study_pgn(study_id: str, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://lichess.org/api/study/{study_id}.pgn"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text
