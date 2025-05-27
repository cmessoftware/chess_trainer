import json
from pathlib import Path

def load_tactic(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def load_all_tactics(folder="data/tactics"):
    folder = Path(folder)
    return [load_tactic(p) for p in folder.glob("*.json")]
