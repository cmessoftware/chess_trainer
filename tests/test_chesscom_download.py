from ..modules.fetch_games import fetch_chesscom_games

def test_fetch_chesscom():
    games = fetch_chesscom_games("cmess1315", max_games=1)
    assert isinstance(games, list)