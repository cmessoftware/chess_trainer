from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd
from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Float,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    Text,
    create_engine,
    func,
    inspect,
    insert,
    or_,
    select,
)
from sqlalchemy.engine import Engine, make_url

COURSE_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PLAYER = "cmess1315"
DEFAULT_SQLITE_PATH = COURSE_ROOT / "course_data.sqlite"
DEFAULT_COURSE_DB_URL = f"sqlite:///{DEFAULT_SQLITE_PATH.resolve()}"
DEFAULT_DB_ENV_VAR = "CHESS_COURSE_DB_URL"

COURSE_METADATA = MetaData()

GAMES_TABLE = Table(
    "games",
    COURSE_METADATA,
    Column("game_id", String),
    Column("pgn", String),
    Column("source", String),
    Column("white_player", String),
    Column("black_player", String),
    Column("white_elo", String),
    Column("black_elo", String),
    Column("result", String),
    Column("time_control", String),
    Column("opening", String),
    Column("eco", String),
    Column("date_played", String),
    Column("created_at", String),
    Column("import_batch_id", String),
    Column("source_filename", String),
    Column("imported_by", String),
    PrimaryKeyConstraint("game_id", name="games_pkey"),
)

FEATURES_TABLE = Table(
    "features",
    COURSE_METADATA,
    Column("game_id", String),
    Column("move_number", Integer),
    Column("player_color", Integer),
    Column("fen", String),
    Column("move_san", String),
    Column("move_uci", String),
    Column("error_label", String),
    Column("material_balance", Float),
    Column("material_total", Float),
    Column("num_pieces", Integer),
    Column("branching_factor", Integer),
    Column("self_mobility", Integer),
    Column("opponent_mobility", Integer),
    Column("phase", String),
    Column("has_castling_rights", Integer),
    Column("move_number_global", Integer),
    Column("is_repetition", Integer),
    Column("is_low_mobility", Integer),
    Column("is_center_controlled", Integer),
    Column("is_pawn_endgame", Integer),
    Column("tags", JSON),
    Column("score_diff", Float),
    Column("site", String),
    Column("event", String),
    Column("date", String),
    Column("white_player", String),
    Column("black_player", String),
    Column("result", String),
    Column("num_moves", Integer),
    Column("is_stockfish_test", Boolean),
    Column("created_at", String),
    PrimaryKeyConstraint("game_id","move_number","player_color", name="features_pkey"),
)

GAME_COLUMNS = tuple(GAMES_TABLE.c.keys())
FEATURE_COLUMNS = tuple(FEATURES_TABLE.c.keys())


def _to_sqlite_url(path: os.PathLike[str] | str) -> str:
    return f"sqlite:///{Path(path).expanduser().resolve()}"


def resolve_course_db_url(db_url: os.PathLike[str] | str | None = None) -> str:
    candidate = db_url or os.environ.get(DEFAULT_DB_ENV_VAR)
    if candidate is None:
        return DEFAULT_COURSE_DB_URL

    candidate = str(candidate)
    if "://" in candidate:
        return candidate
    return _to_sqlite_url(candidate)


def create_course_engine(db_url: os.PathLike[str] | str | None = None) -> Engine:
    resolved = resolve_course_db_url(db_url)
    engine_kwargs: dict = {"future": True}
    if resolved.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(resolved, **engine_kwargs)


def _normalise_rows(rows: pd.DataFrame | Iterable[dict] | None) -> list[dict]:
    if rows is None:
        return []

    def _normalise_value(value):
        if value is None:
            return None

        if isinstance(value, (dict, list, tuple, set)):
            return value

        try:
            if pd.isna(value):
                return None
        except (TypeError, ValueError):
            pass

        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()

        if hasattr(value, "item") and callable(value.item):
            try:
                native_value = value.item()
            except Exception:
                native_value = value
            else:
                try:
                    if pd.isna(native_value):
                        return None
                except (TypeError, ValueError):
                    pass
                return native_value

        return value

    if isinstance(rows, pd.DataFrame):
        records = rows.to_dict(orient="records")
        normalised_rows = []
        for row in records:
            normalised_rows.append(
                {key: _normalise_value(value) for key, value in row.items()}
            )
        return normalised_rows

    normalised_rows = []
    for row in rows:
        row_dict = dict(row)
        normalised_rows.append(
            {key: _normalise_value(value) for key, value in row_dict.items()}
        )
    return normalised_rows


def _selected_columns(table: Table, columns: Sequence[str] | None):
    if not columns:
        return [table]

    missing = [column for column in columns if column not in table.c]
    if missing:
        raise ValueError(f"Unknown columns for {table.name}: {', '.join(sorted(missing))}")
    return [table.c[column] for column in columns]


class CourseFeaturesRepository:
    def __init__(
        self,
        db_url: os.PathLike[str] | str | None = None,
        *,
        engine: Engine | None = None,
        ensure_schema: bool = False,
    ) -> None:
        self.db_url = resolve_course_db_url(db_url)
        self.engine = engine or create_course_engine(self.db_url)
        if ensure_schema:
            self.create_schema()

    @property
    def sqlite_path(self) -> Path | None:
        url = make_url(self.db_url)
        if url.get_backend_name() != "sqlite" or not url.database:
            return None
        return Path(url.database)

    def create_schema(self) -> None:
        COURSE_METADATA.create_all(self.engine)

    def database_exists(self) -> bool:
        sqlite_path = self.sqlite_path
        return sqlite_path.exists() if sqlite_path else True

    def has_table(self, table_name: str) -> bool:
        if not self.database_exists():
            return False
        return inspect(self.engine).has_table(table_name)

    def feature_count(self) -> int:
        if not self.has_table(FEATURES_TABLE.name):
            return 0
        with self.engine.connect() as connection:
            return int(connection.execute(select(func.count()).select_from(FEATURES_TABLE)).scalar_one())

    def game_count(self) -> int:
        if not self.has_table(GAMES_TABLE.name):
            return 0
        with self.engine.connect() as connection:
            return int(connection.execute(select(func.count()).select_from(GAMES_TABLE)).scalar_one())

    def load_games(
        self,
        *,
        columns: Sequence[str] | None = None,
        player: str | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        requested_columns = list(columns or GAME_COLUMNS)
        if not self.has_table(GAMES_TABLE.name):
            return pd.DataFrame(columns=requested_columns)

        stmt = select(*_selected_columns(GAMES_TABLE, columns))
        if player:
            stmt = stmt.where(
                or_(GAMES_TABLE.c.white_player == player, GAMES_TABLE.c.black_player == player)
            )
        if limit is not None:
            stmt = stmt.limit(limit)

        with self.engine.connect() as connection:
            return pd.read_sql(stmt, connection)

    def fetch_games_for_player(self, player: str) -> pd.DataFrame:
        return self.load_games(player=player)

    def load_features(
        self,
        *,
        columns: Sequence[str] | None = None,
        game_ids: Sequence[str] | None = None,
        error_labels: Sequence[str] | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        requested_columns = list(columns or FEATURE_COLUMNS)
        if not self.has_table(FEATURES_TABLE.name):
            return pd.DataFrame(columns=requested_columns)

        if game_ids is not None and not game_ids:
            return pd.DataFrame(columns=requested_columns)

        stmt = select(*_selected_columns(FEATURES_TABLE, columns))
        if game_ids is not None:
            stmt = stmt.where(FEATURES_TABLE.c.game_id.in_(list(game_ids)))
        if error_labels is not None:
            stmt = stmt.where(FEATURES_TABLE.c.error_label.in_(list(error_labels)))
        if limit is not None:
            stmt = stmt.limit(limit)

        with self.engine.connect() as connection:
            return pd.read_sql(stmt, connection)

    def fetch_features_for_game_ids(self, game_ids: Sequence[str]) -> pd.DataFrame:
        return self.load_features(game_ids=game_ids)

    def replace_course_slice(
        self,
        *,
        games: pd.DataFrame | Iterable[dict] | None = None,
        features: pd.DataFrame | Iterable[dict] | None = None,
    ) -> None:
        if self.sqlite_path is None:
            raise ValueError("replace_course_slice only supports SQLite targets.")

        game_rows = _normalise_rows(games)
        feature_rows = _normalise_rows(features)

        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with self.engine.begin() as connection:
            COURSE_METADATA.drop_all(connection, tables=[FEATURES_TABLE, GAMES_TABLE], checkfirst=True)
            COURSE_METADATA.create_all(connection, tables=[GAMES_TABLE, FEATURES_TABLE], checkfirst=True)
            if game_rows:
                connection.execute(insert(GAMES_TABLE), game_rows)
            if feature_rows:
                connection.execute(insert(FEATURES_TABLE), feature_rows)



def export_course_slice(
    *,
    source_db_url: os.PathLike[str] | str,
    output_db_url: os.PathLike[str] | str | None = None,
    player: str = DEFAULT_PLAYER,
) -> dict:
    source_repository = CourseFeaturesRepository(source_db_url)
    games_df = source_repository.fetch_games_for_player(player)
    game_ids = games_df["game_id"].tolist() if "game_id" in games_df else []
    features_df = source_repository.fetch_features_for_game_ids(game_ids)

    destination_repository = CourseFeaturesRepository(output_db_url)
    destination_repository.replace_course_slice(games=games_df, features=features_df)

    return {
        "db_url": destination_repository.db_url,
        "sqlite_path": str(destination_repository.sqlite_path) if destination_repository.sqlite_path else None,
        "games": len(games_df),
        "features": len(features_df),
    }
