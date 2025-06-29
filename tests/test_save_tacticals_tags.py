import pytest
import pandas as pd


@pytest.fixture
def sample_tags_df():
    return pd.DataFrame([
        {
            "move_number": 12,
            "player_color": 1,  # Blanco
            "tag": "discovered_attack",
            "score_diff": 150,
            "error_label": "good"
        },
        {
            "move_number": 15,
            "player_color": 0,  # Negro
            "tag": "pin",
            "score_diff": -80,
            "error_label": "inaccuracy"
        }
    ])


@pytest.fixture
def repo(mocker):
    # Mock or provide your repo object here
    return mocker.Mock()


def test_update_features_tags_and_score_diff_basic(repo, sample_tags_df):
    repo.update_features_tags_and_score_diff(
        game_id='abcd1234...',
        tags_df=sample_tags_df
    )
    repo.update_features_tags_and_score_diff.assert_called_once_with(
        game_id='abcd1234...',
        tags_df=sample_tags_df
    )


def test_update_features_tags_and_score_diff_empty_df(repo):
    empty_df = pd.DataFrame(
        columns=["move_number", "player_color", "tag", "score_diff", "error_label"])
    repo.update_features_tags_and_score_diff(
        game_id='emptygame',
        tags_df=empty_df
    )
    repo.update_features_tags_and_score_diff.assert_called_once_with(
        game_id='emptygame',
        tags_df=empty_df
    )


def test_update_features_tags_and_score_diff_multiple_tags(repo):
    tags_df = pd.DataFrame([
        {"move_number": 1, "player_color": 1, "tag": "fork",
            "score_diff": 50, "error_label": "good"},
        {"move_number": 2, "player_color": 0, "tag": "skewer",
            "score_diff": -30, "error_label": "mistake"},
        {"move_number": 3, "player_color": 1, "tag": "double_attack",
            "score_diff": 100, "error_label": "good"},
    ])
    repo.update_features_tags_and_score_diff(
        game_id='multitag',
        tags_df=tags_df
    )
    repo.update_features_tags_and_score_diff.assert_called_once_with(
        game_id='multitag',
        tags_df=tags_df
    )


def test_update_features_tags_and_score_diff_invalid_data(repo):
    tags_df = pd.DataFrame([
        {"move_number": None, "player_color": 2, "tag": "",
            "score_diff": None, "error_label": None}
    ])
    repo.update_features_tags_and_score_diff(
        game_id='invalid',
        tags_df=tags_df
    )
    repo.update_features_tags_and_score_diff.assert_called_once_with(
        game_id='invalid',
        tags_df=tags_df
    )
