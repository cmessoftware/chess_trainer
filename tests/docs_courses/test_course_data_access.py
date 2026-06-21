from pathlib import Path
import sys

import pandas as pd

COURSE_ROOT = Path(__file__).resolve().parents[2] / "docs" / "ai_chess_coach_course"
if str(COURSE_ROOT) not in sys.path:
    sys.path.insert(0, str(COURSE_ROOT))

from data_access.features_repository import CourseFeaturesRepository
from notebook_data_helper import CourseDataHelper



def _sample_games() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "game_id": "g1",
                "pgn": "1. e4 e5",
                "source": "personal",
                "white_player": "cmess1315",
                "black_player": "opponent",
                "white_elo": "1800",
                "black_elo": "1750",
                "result": "1-0",
                "time_control": "600+0",
                "opening": "C20",
                "eco": "C20",
                "date_played": "2025-01-01",
                "created_at": "2025-01-01T00:00:00",
                "import_batch_id": "batch-1",
                "source_filename": "games.pgn",
                "imported_by": "course-test",
            }
        ]
    )



def _sample_features() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "game_id": "g1",
                "move_number": 1,
                "player_color": 1,
                "fen": "fen-1",
                "error_label": "good",
                "material_total": 32.0,
                "num_pieces": 32,
                "has_castling_rights": True,
                "is_pawn_endgame": False,
                "score_diff": 20,
                "tags": {"phase": "opening"},
            },
            {
                "game_id": "g1",
                "move_number": 2,
                "player_color": 0,
                "fen": "fen-2",
                "error_label": "mistake",
                "material_total": 30.0,
                "num_pieces": 30,
                "has_castling_rights": False,
                "is_pawn_endgame": False,
                "score_diff": -40,
                "tags": {"phase": "middlegame"},
            },
        ]
    )



def test_sqlite_repository_and_helper_load_data(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)
    repository.replace_course_slice(games=_sample_games(), features=_sample_features())

    helper = CourseDataHelper(db_path)

    assert helper.game_count() == 1
    assert helper.feature_count() == 2

    label_distribution = helper.error_label_distribution()
    assert list(label_distribution["error_label"]) == ["good", "mistake"]
    assert list(label_distribution["count"]) == [1, 1]

    features = helper.load_features(columns=["game_id", "move_number", "error_label"])
    assert list(features.columns) == ["game_id", "move_number", "error_label"]
    assert set(features["error_label"]) == {"good", "mistake"}



def test_repository_filters_games_by_player(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)
    repository.replace_course_slice(games=_sample_games(), features=_sample_features())

    matching = repository.fetch_games_for_player("cmess1315")
    missing = repository.fetch_games_for_player("someone-else")

    assert len(matching) == 1
    assert missing.empty


def _sample_games_multi_source() -> pd.DataFrame:
    rows = []
    for index in range(5):
        rows.append(
            {
                "game_id": f"g{index}",
                "pgn": "1. e4 e5",
                "source": "personal" if index < 3 else "lichess",
                "white_player": f"player-{index}",
                "black_player": "opponent",
                "white_elo": "1800",
                "black_elo": "1750",
                "result": "1-0",
                "time_control": "600+0",
                "opening": "C20",
                "eco": "C20",
                "date_played": f"2025-01-0{index + 1}",
                "created_at": f"2025-01-0{index + 1}T00:00:00",
                "import_batch_id": "batch-1",
                "source_filename": "games.pgn",
                "imported_by": "course-test",
            }
        )
    return pd.DataFrame(rows)


def test_repository_filters_games_by_source_and_max_games(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)
    repository.replace_course_slice(games=_sample_games_multi_source(), features=pd.DataFrame())

    personal = repository.load_games(source="personal")
    lichess = repository.load_games(source="lichess")
    capped = repository.load_games(source="lichess", limit=1)

    assert len(personal) == 3
    assert len(lichess) == 2
    assert len(capped) == 1
    assert capped.iloc[0]["game_id"] == "g4"
    assert repository.list_sources() == ["lichess", "personal"]


def test_load_games_elo_filter_skips_empty_elo_values(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)
    games = pd.DataFrame(
        [
            {
                "game_id": "valid-1",
                "pgn": "1. e4",
                "source": "fide",
                "white_player": "a",
                "black_player": "b",
                "white_elo": "1100",
                "black_elo": "",
                "result": "1-0",
                "time_control": "600+0",
                "opening": "A00",
                "eco": "A00",
                "date_played": "2025-01-02",
                "created_at": "2025-01-02T00:00:00",
            },
            {
                "game_id": "invalid-1",
                "pgn": "1. e4",
                "source": "fide",
                "white_player": "c",
                "black_player": "d",
                "white_elo": "",
                "black_elo": "",
                "result": "1-0",
                "time_control": "600+0",
                "opening": "A00",
                "eco": "A00",
                "date_played": "2025-01-01",
                "created_at": "2025-01-01T00:00:00",
            },
        ]
    )
    repository.replace_course_slice(games=games, features=pd.DataFrame())

    matched = repository.load_games(player_elo_min=600, player_elo_max=1199)

    assert len(matched) == 1
    assert matched.iloc[0]["game_id"] == "valid-1"


def test_merge_course_slice_accumulates_exports(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)

    elite_games = _sample_games_multi_source().iloc[:2].copy()
    elite_games["source"] = "elite"
    elite_games["game_id"] = ["elite-1", "elite-2"]

    personal_games = _sample_games().copy()
    personal_games.loc[0, "game_id"] = "personal-1"

    repository.replace_course_slice(games=elite_games, features=pd.DataFrame())
    repository.merge_course_slice(games=personal_games, features=_sample_features().assign(game_id="personal-1"))

    assert repository.game_count() == 3
    assert repository.feature_count() == 2
    assert set(repository.load_games()["source"]) == {"elite", "personal"}

    updated_elite = elite_games.copy()
    updated_elite.loc[0, "result"] = "0-1"
    repository.merge_course_slice(games=updated_elite.iloc[:1], features=pd.DataFrame())

    assert repository.game_count() == 3
    assert repository.load_games().query("game_id == 'elite-1'").iloc[0]["result"] == "0-1"


def test_exclusive_elo_band_assigns_game_to_single_group(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)
    games = pd.DataFrame(
        [
            {
                "game_id": "avg-intermediate",
                "pgn": "1. e4",
                "source": "fide",
                "white_player": "a",
                "black_player": "b",
                "white_elo": "1300",
                "black_elo": "1800",
                "result": "1-0",
                "time_control": "600+0",
                "opening": "A00",
                "eco": "A00",
                "date_played": "2025-01-01",
                "created_at": "2025-01-01T00:00:00",
            },
            {
                "game_id": "avg-beginner",
                "pgn": "1. e4",
                "source": "fide",
                "white_player": "c",
                "black_player": "d",
                "white_elo": "900",
                "black_elo": "1100",
                "result": "1-0",
                "time_control": "600+0",
                "opening": "A00",
                "eco": "A00",
                "date_played": "2025-01-02",
                "created_at": "2025-01-02T00:00:00",
            },
        ]
    )
    repository.replace_course_slice(games=games, features=pd.DataFrame())

    either_side = repository.load_games(player_elo_min=1200, player_elo_max=1599, exclusive_elo_band=False)
    exclusive = repository.load_games(player_elo_min=1200, player_elo_max=1599, exclusive_elo_band=True)
    beginner = repository.load_games(player_elo_min=600, player_elo_max=1199, exclusive_elo_band=True)

    assert set(either_side["game_id"]) == {"avg-intermediate"}
    assert set(exclusive["game_id"]) == {"avg-intermediate"}
    assert set(beginner["game_id"]) == {"avg-beginner"}


def test_games_store_skill_group_description_and_join_to_features(tmp_path):
    db_path = tmp_path / "course.sqlite"
    repository = CourseFeaturesRepository(db_path)

    games = _sample_games().copy()
    games["skill_group"] = "Intermediate"
    games["skill_group_description"] = "Intermediate (1200-1599)"

    repository.replace_course_slice(games=games, features=_sample_features())

    loaded_games = repository.load_games(columns=["game_id", "skill_group", "skill_group_description"])
    assert loaded_games.iloc[0]["skill_group"] == "Intermediate"
    assert loaded_games.iloc[0]["skill_group_description"] == "Intermediate (1200-1599)"

    features = repository.load_features(
        columns=["game_id", "move_number", "skill_group", "skill_group_description"]
    )
    assert features.iloc[0]["skill_group"] == "Intermediate"
    assert features.iloc[0]["skill_group_description"] == "Intermediate (1200-1599)"
