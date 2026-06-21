from pathlib import Path
import sys

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from migrate_to_sqlite import resolve_player_filter


def test_resolve_player_filter_no_default_player():
    assert resolve_player_filter(None) is None
    assert resolve_player_filter(None, skill_group="Expert") is None
    assert resolve_player_filter(None, player_elo_min=2000, player_elo_max=2199) is None
    assert resolve_player_filter(None, source="elite") is None


def test_resolve_player_filter_explicit_player():
    assert resolve_player_filter("cmess1315") == "cmess1315"
    assert resolve_player_filter("cmess1315", skill_group="Expert") == "cmess1315"
