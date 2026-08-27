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
    and_,
    create_engine,
    func,
    inspect,
    insert,
    literal,
    or_,
    case,
    cast,
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
    Column("skill_group", String),
    Column("skill_group_description", String),
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

# Games table columns used in model training.
GAMES_TRAIN_COLUMNS = ["game_id",
                       "pgn",
                       "source",
                       "white_player",
                       "black_player",
                       "white_elo",
                       "black_elo",
                       "result",
                       "time_control",
                       "opening",
                       "eco",
                       "date_played"]


def _cleaned_elo(column):
    return func.nullif(func.trim(column), "")


def _safe_elo_integer(column, *, dialect_name: str):
    cleaned = _cleaned_elo(column)
    if dialect_name == "postgresql":
        return case(
            (cleaned.op("~")("^[0-9]+$"), cast(cleaned, Integer)),
            else_=literal(None),
        )
    if dialect_name == "sqlite":
        return case(
            (
                and_(
                    cleaned.is_not(None),
                    cleaned.op("GLOB")("[0-9]*"),
                    func.length(cleaned) > 0,
                ),
                cast(cleaned, Integer),
            ),
            else_=literal(None),
        )
    return cast(cleaned, Integer)


def _game_representative_elo_expr(*, dialect_name: str):
    """Average of valid white/black ELO; single side if only one is valid."""
    white_elo = _safe_elo_integer(GAMES_TABLE.c.white_elo, dialect_name=dialect_name)
    black_elo = _safe_elo_integer(GAMES_TABLE.c.black_elo, dialect_name=dialect_name)
    return case(
        (
            and_(white_elo.is_not(None), black_elo.is_not(None)),
            (white_elo + black_elo) / 2,
        ),
        (white_elo.is_not(None), white_elo),
        else_=black_elo,
    )


def _game_elo_in_range_condition(
    player_elo_min: int | None,
    player_elo_max: int | None,
    *,
    dialect_name: str,
    exclusive: bool = False,
):
    if exclusive:
        representative_elo = _game_representative_elo_expr(dialect_name=dialect_name)
        conditions = [representative_elo.is_not(None)]
        if player_elo_min is not None:
            conditions.append(representative_elo >= player_elo_min)
        if player_elo_max is not None:
            conditions.append(representative_elo <= player_elo_max)
        return and_(*conditions)

    white_elo = _safe_elo_integer(GAMES_TABLE.c.white_elo, dialect_name=dialect_name)
    black_elo = _safe_elo_integer(GAMES_TABLE.c.black_elo, dialect_name=dialect_name)

    def _side_in_range(column):
        conditions = [column.is_not(None)]
        if player_elo_min is not None:
            conditions.append(column >= player_elo_min)
        if player_elo_max is not None:
            conditions.append(column <= player_elo_max)
        return and_(*conditions)

    return or_(_side_in_range(white_elo), _side_in_range(black_elo))


GAME_COLUMNS = tuple(GAMES_TABLE.c.keys())
FEATURE_COLUMNS = tuple(FEATURES_TABLE.c.keys())
DERIVED_FEATURES_REQUIRING_GAME_JOIN = {"player_elo", "elo", "opening"}


def _player_elo_expr(dialect_name: str):
    white_elo = _safe_elo_integer(GAMES_TABLE.c.white_elo, dialect_name=dialect_name)
    black_elo = _safe_elo_integer(GAMES_TABLE.c.black_elo, dialect_name=dialect_name)
    return case(
        (FEATURES_TABLE.c.player_color == 1, white_elo),
        else_=black_elo,
    )


def _derived_feature_columns(dialect_name: str) -> dict:
    player_elo = _player_elo_expr(dialect_name).label("player_elo")
    return {
        "player_elo": player_elo,
        "elo": player_elo,
        "score_cp": FEATURES_TABLE.c.score_diff.label("score_cp"),
        "opening": GAMES_TABLE.c.opening,
        "king_safety": (FEATURES_TABLE.c.self_mobility - FEATURES_TABLE.c.opponent_mobility).label(
            "king_safety"
        ),
        "center_control": FEATURES_TABLE.c.branching_factor.label("center_control"),
        "mate_in": literal(0).label("mate_in"),
        "depth_score_diff": literal(0).label("depth_score_diff"),
    }
DEFAULT_EXCLUDED_SOURCES = ("stockfish",)
# Stamped on SQLite export only; not present in PostgreSQL games table.
SQLITE_GAME_METADATA_COLUMNS = ("skill_group", "skill_group_description")
DEFAULT_EXPORT_GAME_CHUNK_SIZE = 400


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


def _selected_feature_columns(columns: Sequence[str] | None, *, dialect_name: str):
    if not columns:
        return [FEATURES_TABLE], False

    derived_columns = _derived_feature_columns(dialect_name)
    selected_columns = []
    missing_columns = []
    join_required = False

    for column in columns:
        if column in FEATURES_TABLE.c:
            selected_columns.append(FEATURES_TABLE.c[column])
        elif column in GAMES_TABLE.c:
            selected_columns.append(GAMES_TABLE.c[column])
            join_required = True
        elif column in derived_columns:
            selected_columns.append(derived_columns[column])
            if column in DERIVED_FEATURES_REQUIRING_GAME_JOIN:
                join_required = True
        else:
            missing_columns.append(column)

    if missing_columns:
        raise ValueError(
            f"Unknown columns for features: {', '.join(sorted(missing_columns))}"
        )

    return selected_columns, join_required


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

    def count_games(
        self,
        *,
        player: str | None = None,
        source: str | None = None,
        exclude_sources: Sequence[str] | None = None,
        player_elo_min: int | None = None,
        player_elo_max: int | None = None,
        exclusive_elo_band: bool = False,
        exclude_game_ids: Sequence[str] | None = None,
    ) -> int:
        if not self.has_table(GAMES_TABLE.name):
            return 0

        stmt = select(func.count()).select_from(GAMES_TABLE)
        if player:
            stmt = stmt.where(
                or_(GAMES_TABLE.c.white_player == player, GAMES_TABLE.c.black_player == player)
            )
        if source:
            stmt = stmt.where(GAMES_TABLE.c.source == source)
        if exclude_sources:
            stmt = stmt.where(GAMES_TABLE.c.source.notin_(list(exclude_sources)))
        if exclude_game_ids:
            stmt = stmt.where(GAMES_TABLE.c.game_id.notin_(list(exclude_game_ids)))
        if player_elo_min is not None or player_elo_max is not None:
            stmt = stmt.where(
                _game_elo_in_range_condition(
                    player_elo_min,
                    player_elo_max,
                    dialect_name=self.engine.dialect.name,
                    exclusive=exclusive_elo_band,
                )
            )
        with self.engine.connect() as connection:
            return int(connection.execute(stmt).scalar_one())

    def load_games(
        self,
        *,
        columns: Sequence[str] | None = None,
        player: str | None = None,
        source: str | None = None,
        exclude_sources: Sequence[str] | None = None,
        player_elo_min: int | None = None,
        player_elo_max: int | None = None,
        exclusive_elo_band: bool = False,
        exclude_game_ids: Sequence[str] | None = None,
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
        if source:
            stmt = stmt.where(GAMES_TABLE.c.source == source)
        if exclude_sources:
            stmt = stmt.where(GAMES_TABLE.c.source.notin_(list(exclude_sources)))
        if exclude_game_ids:
            stmt = stmt.where(GAMES_TABLE.c.game_id.notin_(list(exclude_game_ids)))
        if player_elo_min is not None or player_elo_max is not None:
            stmt = stmt.where(
                _game_elo_in_range_condition(
                    player_elo_min,
                    player_elo_max,
                    dialect_name=self.engine.dialect.name,
                    exclusive=exclusive_elo_band,
                )
            )
        if limit is not None:
            stmt = stmt.order_by(
                GAMES_TABLE.c.date_played.desc(),
                GAMES_TABLE.c.created_at.desc(),
                GAMES_TABLE.c.game_id,
            ).limit(limit)

        with self.engine.connect() as connection:
            return pd.read_sql(stmt, connection)

    def get_game(
        self,
        game_id: str,
        *,
        columns: Sequence[str] | None = None,
    ) -> pd.Series | None:
        """Fetch one games row by id (exact match after strip/quotes)."""
        gid = str(game_id).strip().strip("\"'")
        if not gid or not self.has_table(GAMES_TABLE.name):
            return None

        requested = list(columns or GAME_COLUMNS)
        stmt = select(*_selected_columns(GAMES_TABLE, requested)).where(
            GAMES_TABLE.c.game_id == gid
        )
        with self.engine.connect() as connection:
            frame = pd.read_sql(stmt, connection)
        if frame.empty:
            return None
        return frame.iloc[0]

    def list_sources(self) -> list[str]:
        if not self.has_table(GAMES_TABLE.name):
            return []

        stmt = (
            select(GAMES_TABLE.c.source)
            .where(GAMES_TABLE.c.source.is_not(None))
            .distinct()
            .order_by(GAMES_TABLE.c.source)
        )
        with self.engine.connect() as connection:
            return [row[0] for row in connection.execute(stmt).all() if row[0]]

    def list_game_ids(self) -> list[str]:
        if not self.has_table(GAMES_TABLE.name):
            return []

        stmt = select(GAMES_TABLE.c.game_id).where(GAMES_TABLE.c.game_id.is_not(None))
        with self.engine.connect() as connection:
            return [row[0] for row in connection.execute(stmt).all() if row[0]]

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

        selected_columns, join_required = _selected_feature_columns(
            columns,
            dialect_name=self.engine.dialect.name,
        )

        stmt = select(*selected_columns).select_from(FEATURES_TABLE)
        if join_required:
            stmt = stmt.join(GAMES_TABLE, FEATURES_TABLE.c.game_id == GAMES_TABLE.c.game_id)

        if game_ids is not None:
            stmt = stmt.where(FEATURES_TABLE.c.game_id.in_(list(game_ids)))
        if error_labels is not None:
            stmt = stmt.where(FEATURES_TABLE.c.error_label.in_(list(error_labels)))
        if limit is not None:
            stmt = stmt.limit(limit)

        with self.engine.connect() as connection:
            return pd.read_sql(stmt, connection)

    def fetch_features_for_game_ids(
        self,
        game_ids: Sequence[str],
        *,
        chunk_size: int = DEFAULT_EXPORT_GAME_CHUNK_SIZE,
    ) -> pd.DataFrame:
        ids = list(game_ids)
        if not ids:
            return self.load_features(game_ids=[])

        if len(ids) <= chunk_size:
            return self.load_features(game_ids=ids)

        chunks: list[pd.DataFrame] = []
        for start in range(0, len(ids), chunk_size):
            batch_ids = ids[start : start + chunk_size]
            chunks.append(self.load_features(game_ids=batch_ids))
        return pd.concat(chunks, ignore_index=True)

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

    def merge_course_slice(
        self,
        *,
        games: pd.DataFrame | Iterable[dict] | None = None,
        features: pd.DataFrame | Iterable[dict] | None = None,
    ) -> None:
        if self.sqlite_path is None:
            raise ValueError("merge_course_slice only supports SQLite targets.")

        game_rows = _normalise_rows(games)
        feature_rows = _normalise_rows(features)
        game_ids = sorted({row["game_id"] for row in game_rows if row.get("game_id")})

        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        with self.engine.begin() as connection:
            COURSE_METADATA.create_all(connection, tables=[GAMES_TABLE, FEATURES_TABLE], checkfirst=True)
            if game_ids:
                connection.execute(
                    FEATURES_TABLE.delete().where(FEATURES_TABLE.c.game_id.in_(game_ids))
                )
                connection.execute(
                    GAMES_TABLE.delete().where(GAMES_TABLE.c.game_id.in_(game_ids))
                )
            if game_rows:
                connection.execute(insert(GAMES_TABLE), game_rows)
            if feature_rows:
                connection.execute(insert(FEATURES_TABLE), feature_rows)



def export_course_slice(
    *,
    source_db_url: os.PathLike[str] | str,
    output_db_url: os.PathLike[str] | str | None = None,
    player: str | None = None,
    source: str | None = None,
    max_games: int | None = None,
    player_elo_min: int | None = None,
    player_elo_max: int | None = None,
    skill_group: str | None = None,
    exclusive_elo_band: bool = False,
    exclude_game_ids: Sequence[str] | None = None,
    merge: bool = False,
    export_chunk_size: int = DEFAULT_EXPORT_GAME_CHUNK_SIZE,
    columns = GAMES_TRAIN_COLUMNS,
) -> dict:
    if max_games is not None and max_games <= 0:
        raise ValueError("max_games must be a positive integer.")

    source_repository = CourseFeaturesRepository(source_db_url)
    source_columns = list(columns)

    merged_exclude_ids: list[str] = list(exclude_game_ids or [])
    if merge and output_db_url is not None:
        destination_repository = CourseFeaturesRepository(output_db_url)
        if destination_repository.has_table(GAMES_TABLE.name):
            existing_ids = destination_repository.list_game_ids()
            merged_exclude_ids = sorted(set(merged_exclude_ids) | set(existing_ids))

    games_df = source_repository.load_games(
        columns=source_columns,
        player=player,
        source=source,
        exclude_sources=DEFAULT_EXCLUDED_SOURCES,
        player_elo_min=player_elo_min,
        player_elo_max=player_elo_max,
        exclusive_elo_band=exclusive_elo_band,
        exclude_game_ids=merged_exclude_ids or None,
        limit=max_games,
    )
    skill_group_description = None
    if skill_group:
        from dataset.skill_groups import SKILL_GROUP_BY_NAME

        group = SKILL_GROUP_BY_NAME.get(skill_group)
        skill_group_description = group.description if group else None

    if skill_group and not games_df.empty:
        games_df["skill_group"] = skill_group
        if skill_group_description:
            games_df["skill_group_description"] = skill_group_description

    destination_repository = CourseFeaturesRepository(output_db_url)
    chunk_size = max(1, export_chunk_size)
    games_exported = 0
    features_exported = 0

    if games_df.empty:
        if not merge:
            destination_repository.replace_course_slice(games=pd.DataFrame(), features=pd.DataFrame())
    else:
        for start in range(0, len(games_df), chunk_size):
            chunk_games = games_df.iloc[start : start + chunk_size].reset_index(drop=True)
            chunk_ids = chunk_games["game_id"].tolist()
            chunk_features = source_repository.fetch_features_for_game_ids(
                chunk_ids,
                chunk_size=chunk_size,
            )
            if merge or start > 0:
                destination_repository.merge_course_slice(games=chunk_games, features=chunk_features)
            else:
                destination_repository.replace_course_slice(games=chunk_games, features=chunk_features)
            games_exported += len(chunk_games)
            features_exported += len(chunk_features)

    return {
        "db_url": destination_repository.db_url,
        "sqlite_path": str(destination_repository.sqlite_path) if destination_repository.sqlite_path else None,
        "games_exported": games_exported,
        "features_exported": features_exported,
        "games_total": destination_repository.game_count(),
        "features_total": destination_repository.feature_count(),
        "player": player,
        "source": source,
        "max_games": max_games,
        "player_elo_min": player_elo_min,
        "player_elo_max": player_elo_max,
        "skill_group": skill_group,
        "skill_group_description": skill_group_description,
        "exclusive_elo_band": exclusive_elo_band,
        "excluded_game_ids": len(merged_exclude_ids),
        "export_chunk_size": chunk_size,
        "merge": merge,
    }
