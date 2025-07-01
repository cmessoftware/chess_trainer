from modules.analyze_games_tactics import classify_error_label
import pytest
import sys
sys.path.insert(0, '/app/src')


@pytest.mark.parametrize("score_diff, expected_label", [
    (None, None),
    (0, "good"),
    (49, "good"),
    (100, "inaccuracy"),
    (149, "inaccuracy"),
    (200, "mistake"),
    (499, "mistake"),
    (501, "blunder"),
    (800, "blunder"),
])
def test_classify_error_label(score_diff, expected_label):
    result = classify_error_label(score_diff)
    assert result == expected_label, f"score_diff={score_diff} → {result}, esperado={expected_label}"
