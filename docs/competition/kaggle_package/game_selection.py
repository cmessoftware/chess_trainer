"""Select games per Kaggle elo_band quota (best-effort cap)."""

from __future__ import annotations

import pandas as pd

from kaggle_package.config import KAGGLE_ELO_BAND_GAME_QUOTAS, RANDOM_STATE


def select_games_by_elo_band(
    games: pd.DataFrame,
    *,
    random_state: int = RANDOM_STATE,
) -> pd.DataFrame:
    if games.empty:
        return games.copy()

    selected_frames: list[pd.DataFrame] = []
    for band, quota in KAGGLE_ELO_BAND_GAME_QUOTAS.items():
        band_games = games.loc[games["elo_band"] == band]
        if band_games.empty:
            continue
        sample_size = min(len(band_games), quota)
        selected_frames.append(
            band_games.sample(n=sample_size, random_state=random_state).copy()
        )

    if not selected_frames:
        return games.iloc[0:0].copy()

    return (
        pd.concat(selected_frames, ignore_index=True)
        .drop_duplicates(subset=["game_id"])
        .reset_index(drop=True)
    )
