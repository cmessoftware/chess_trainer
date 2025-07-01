from ..modules.fetch_games import fetch_lichess_games

def test_fetch_lichess():
    games = fetch_lichess_games("magnuscarlsen", max_games=1)
    assert len(games) == 1