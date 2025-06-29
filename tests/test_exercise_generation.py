import json
from pathlib import Path

TACTICS_PATH = Path("data/tactics/elite")

def test_exercises_present():
    files = list(TACTICS_PATH.glob("*.json"))
    assert len(files) > 0, "No exercises generated"

    for f in files:
        with open(f) as jf:
            data = json.load(jf)
            assert "fen" in data
            assert "uci" in data
            assert "id" in data
