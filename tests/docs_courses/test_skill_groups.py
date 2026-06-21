from pathlib import Path
import sys

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from dataset.skill_groups import (
    derive_skill_group,
    derive_skill_group_description,
    skill_group_description,
)


def test_skill_group_description_lookup():
    assert skill_group_description("Beginner") == "Beginner (<1200)"
    assert skill_group_description("Master+") == "Master+ (2400+)"
    assert skill_group_description("unknown") is None
    assert skill_group_description(None) is None


def test_derive_skill_group_description_from_elo():
    player_elo = pd.Series([1100, 1500, 2100, 2500])
    groups = derive_skill_group(player_elo)
    descriptions = derive_skill_group_description(groups)

    assert descriptions.tolist() == [
        "Beginner (<1200)",
        "Intermediate (1200-1599)",
        "Expert (2000-2199)",
        "Master+ (2400+)",
    ]


def test_course_skill_group_quotas_sum_to_target():
    from dataset.skill_groups import COURSE_SKILL_GROUP_GAME_QUOTAS, COURSE_TARGET_GAME_COUNT

    assert sum(COURSE_SKILL_GROUP_GAME_QUOTAS.values()) == COURSE_TARGET_GAME_COUNT
    assert COURSE_TARGET_GAME_COUNT == 10_000
