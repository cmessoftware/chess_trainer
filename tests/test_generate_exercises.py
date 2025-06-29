from ..modules.exercise_utils import hash_game
import chess.pgn
import io

def test_hash_game():
    pgn = "[Event \"Test\"]\n1. e4 e5 2. Nf3 Nc6 3. Bb5 a6"
    game = chess.pgn.read_game(io.StringIO(pgn))
    h = hash_game(game)
    assert isinstance(h, str) and len(h) == 64