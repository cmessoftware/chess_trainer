import pytest
from ..modules.tagging import detect_tags_from_game

simple_pgn = """[Event "Test"]
[Site "?"]
[Date "2023.01.01"]
[Round "-"]
[White "A"]
[Black "B"]
[Result "1-0"]

1. e4 e5 2. Qh5 Nc6 3. Bc4 Nf6 4. Qxf7# 1-0"""

def test_detects_attack_tag():
    tags = detect_tags_from_game(simple_pgn)
    assert isinstance(tags, list)
    assert "attack_king" in tags or "sacrifice" in tags
