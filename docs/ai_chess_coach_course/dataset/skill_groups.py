from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

PLAYER_ELO_FLOOR = 600
PLAYER_ELO_CEILING = 3000


@dataclass(frozen=True)
class CourseSkillGroup:
    """Course export / reporting band (coarser than elo_band)."""

    name: str
    min_elo: int
    max_elo: int
    description: str

    def contains(self, player_elo: float | int | None) -> bool:
        if player_elo is None or pd.isna(player_elo):
            return False
        value = float(player_elo)
        return self.min_elo <= value <= self.max_elo


COURSE_SKILL_GROUPS: tuple[CourseSkillGroup, ...] = (
    CourseSkillGroup("Beginner", 600, 1199, "Beginner (<1200)"),
    CourseSkillGroup("Intermediate", 1200, 1599, "Intermediate (1200-1599)"),
    CourseSkillGroup("Advanced Amateur", 1600, 1999, "Advanced Amateur (1600-1999)"),
    CourseSkillGroup("Expert", 2000, 2199, "Expert (2000-2199)"),
    CourseSkillGroup("Master Candidate", 2200, 2399, "Master Candidate (2200-2399)"),
    CourseSkillGroup("Master+", 2400, PLAYER_ELO_CEILING, "Master+ (2400+)"),
)

SKILL_GROUP_BY_NAME = {group.name: group for group in COURSE_SKILL_GROUPS}
SKILL_GROUP_DESCRIPTION_BY_NAME = {group.name: group.description for group in COURSE_SKILL_GROUPS}

# Balanced course export target with exclusive ELO assignment (avg white/black).
# Advanced Amateur and Expert are capped by PostgreSQL availability (~986 / ~1404).
COURSE_SKILL_GROUP_GAME_QUOTAS: dict[str, int] = {
    "Beginner": 2300,
    "Intermediate": 3810,
    "Advanced Amateur": 986,
    "Expert": 1404,
    "Master Candidate": 1000,
    "Master+": 500,
}
COURSE_TARGET_GAME_COUNT = sum(COURSE_SKILL_GROUP_GAME_QUOTAS.values())


def representative_game_elo(white_elo: object, black_elo: object) -> float | None:
    values = [
        float(value)
        for value in (pd.to_numeric(white_elo, errors="coerce"), pd.to_numeric(black_elo, errors="coerce"))
        if value is not None and not pd.isna(value)
    ]
    if not values:
        return None
    return sum(values) / len(values)


def skill_group_description(name: str | None) -> str | None:
    if name is None or pd.isna(name):
        return None
    return SKILL_GROUP_DESCRIPTION_BY_NAME.get(str(name))


def derive_skill_group(player_elo: pd.Series) -> pd.Series:
    numeric_elo = pd.to_numeric(player_elo, errors="coerce")
    labels = pd.Series(pd.NA, index=numeric_elo.index, dtype="object")
    for group in COURSE_SKILL_GROUPS:
        mask = numeric_elo.between(group.min_elo, group.max_elo, inclusive="both")
        labels = labels.mask(mask, group.name)
    return labels


def derive_skill_group_description(skill_group: pd.Series) -> pd.Series:
    return skill_group.map(skill_group_description)
