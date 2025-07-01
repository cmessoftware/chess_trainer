from ..scripts.analyze_games_tactics import analyze_game_tactics

simple_blunder_pgn = """[Event "Blunder"]
[Site "?"]
[Date "2023.01.01"]
[Round "-"]
[White "A"]
[Black "B"]
[Result "0-1"]

1. e4 e5 2. Nf3 Qh4 3. Nxh4 g5 4. Nf5 d5 5. Qh5 Bxf5 6. exf5 Nc6 7. Qxg5 f6 8. Qg7 Bxg7 9. c3 O-O-O"""


def test_detects_blunder():
    tags = analyze_game_tactics(simple_blunder_pgn)
    assert isinstance(tags, list)
    assert "blunder" in tags or "impulsive_mistake" in tags
