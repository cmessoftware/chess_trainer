import pandas as pd
from ..modules.tactical_analysis import evaluate_tactical_features
import chess.engine


def test_score_diff():
    row = pd.Series(
        {"fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 3", "move_uci": "f3g5"})
    with chess.engine.SimpleEngine.popen_uci("engines/stockfish") as engine:
        result = evaluate_tactical_features(row, engine)
        assert result[2] is not None
