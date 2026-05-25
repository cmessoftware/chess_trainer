from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

import pandas as pd
from sqlalchemy import create_engine


@dataclass
class FeaturesRepository:
    """PostgreSQL-first repository for course datasets built from `features`."""

    db_url: str | None = None
    schema: str | None = None

    def __post_init__(self) -> None:
        self.db_url = self.db_url or os.getenv("CHESS_TRAINER_DB_URL")
        if not self.db_url:
            raise ValueError("CHESS_TRAINER_DB_URL is required to query course datasets")

        self.engine = create_engine(self.db_url)
        self.schema = self.schema if self.schema is not None else (None if self.engine.dialect.name == "sqlite" else "public")

    def _table(self, table_name: str) -> str:
        return f"{self.schema}.{table_name}" if self.schema else table_name

    def load_features_for_training(
        self,
        labels: Iterable[str] | None = None,
        limit: int | None = None,
    ) -> pd.DataFrame:
        params: dict[str, object] = {}
        where = ["f.error_label IS NOT NULL"]

        if labels:
            labels = [label.strip().lower() for label in labels]
            placeholders = []
            for idx, label in enumerate(labels):
                key = f"label_{idx}"
                placeholders.append(f":{key}")
                params[key] = label
            where.append(f"LOWER(f.error_label) IN ({', '.join(placeholders)})")

        limit_clause = ""
        if limit is not None:
            params["limit"] = int(limit)
            limit_clause = " LIMIT :limit"

        query = f"""
            SELECT
                f.game_id,
                f.move_number,
                f.player_color,
                f.error_label,
                f.material_balance,
                f.material_total,
                f.num_pieces,
                f.branching_factor,
                f.self_mobility,
                f.opponent_mobility,
                f.phase,
                f.has_castling_rights,
                f.move_number_global,
                f.is_repetition,
                f.is_low_mobility,
                f.is_center_controlled,
                f.is_pawn_endgame,
                f.score_diff,
                f.tags,
                g.opening,
                g.eco,
                -- Prefer elo matching move side (player_color), then fallback to any non-empty elo.
                COALESCE(
                    CASE
                        WHEN f.player_color = 1 THEN NULLIF(g.white_elo, '')
                        WHEN f.player_color = 0 THEN NULLIF(g.black_elo, '')
                    END,
                    NULLIF(g.white_elo, ''),
                    NULLIF(g.black_elo, '')
                ) AS elo
            FROM {self._table('features')} f
            LEFT JOIN {self._table('games')} g ON g.game_id = f.game_id
            WHERE {' AND '.join(where)}
            ORDER BY f.game_id, f.move_number
            {limit_clause}
        """

        return pd.read_sql(query, con=self.engine, params=params)
