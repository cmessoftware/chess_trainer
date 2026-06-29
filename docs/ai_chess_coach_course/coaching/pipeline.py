"""Run SHAP + pattern engine across complete games."""

from __future__ import annotations

from typing import Any, Callable

import pandas as pd

from coaching.game_analysis import (
    DEFAULT_COURSE_PLAYER,
    collect_player_game_frames,
    fetch_player_color_index,
    select_player_game_ids,
)
from coaching.pattern_engine import PatternObservation, detect_patterns_for_sample
from dataset.feature_engineering import split_features_and_target


def align_feature_rows(
    metadata_rows: pd.DataFrame,
    full_split_df: pd.DataFrame,
    *,
    feature_columns: list[str],
) -> tuple[pd.DataFrame, pd.Series]:
    """Map metadata rows back to encoded feature matrix rows by index."""
    aligned = full_split_df.loc[metadata_rows.index]
    X, y = split_features_and_target(
        aligned,
        feature_columns=feature_columns,
        sanitize_feature_names=True,
    )
    return X, y


def explain_player_games(
    model: Any,
    explainer_factory: Callable[[pd.DataFrame], Any],
    explain_fn: Callable[..., dict[str, Any]],
    *,
    dataset: pd.DataFrame,
    full_split_df: pd.DataFrame,
    feature_columns: list[str],
    game_ids: list[str],
    player_name: str = DEFAULT_COURSE_PLAYER,
    player_color_index: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.Series, list[dict[str, Any]], list[PatternObservation], list[dict[str, Any]]]:
    """
    Analyze every coached-player move in the selected games.

    Returns metadata rows, labels, SHAP explanations, pattern observations, game summaries.
    """
    player_moves, game_summaries = collect_player_game_frames(
        dataset,
        game_ids,
        player_name=player_name,
        player_color_index=player_color_index,
    )
    X_moves, y_moves = align_feature_rows(player_moves, full_split_df, feature_columns=feature_columns)
    explainer = explainer_factory(X_moves)
    explanations = [explain_fn(model, explainer, X_moves.iloc[[index]]) for index in range(len(X_moves))]
    patterns = detect_patterns_for_sample(X_moves, explanations)
    return player_moves, y_moves, X_moves, explanations, patterns, game_summaries


def prepare_player_game_analysis(
    repo: Any,
    dataset: pd.DataFrame,
    *,
    player_name: str = DEFAULT_COURSE_PLAYER,
    n_games: int = 1,
    random_state: int = 42,
    game_ids: list[str] | None = None,
) -> tuple[list[str], pd.DataFrame | None]:
    selected = select_player_game_ids(
        dataset,
        player_name=player_name,
        n_games=n_games,
        random_state=random_state,
        game_ids=game_ids,
    )
    color_index = fetch_player_color_index(repo, selected) if repo is not None else None
    return selected, color_index
