# /app/src/db/repository/Features_repository.py

import logging
from typing import Dict, List
import chess
import pandas as pd
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from db.models.features import Features
from db.db_utils import DBUtils, Session
from db.session import get_session
from modules.pgn_utils import get_game_id

logger = logging.getLogger(__name__)

# TODO: Actualizar tabla,
# 1. en la base tiene el campo pgn, acá ya no está.
# 2. EL campo move_number se llama move_number_global en la base de datos


class FeaturesRepository:
    def __init__(self, session_factory=get_session):
        self.session_factory = session_factory
        self.session = self.session_factory()
        self.model = Features
        self.db_utils = DBUtils()

    def get_all(self):
        return self.session.query(Features).all()

    def get_by_game_id(self, game_id):
        return self.session.query(Features).filter(Features.game_id == game_id).all()

    def get_by_game_and_move(self, game_id, move_number):
        return self.session.query(Features).filter_by(game_id=game_id, move_number=move_number).first()

    def add_Features(self, features: Features):
        self.session.add(features)
        self.session.commit()

    def delete_by_game_id(self, game_id):
        self.session.query(Features).filter_by(game_id=game_id).delete()
        self.session.commit()

    def update_Features(self, Features_id, **kwargs):
        self.session.query(Features).filter_by(id=Features_id).update(kwargs)
        self.session.commit()

    def is_feature_in_db(self, game_id: str, move_number: int, player_color: str) -> bool:
        """
        Checks if a specific feature already exists in the database.

        :param game_id: Unique game ID.
        :param move_number: Move number.
        :param player_color: Player color ('white', 'black' or 'none').
        :return: True if the feature already exists, False otherwise.
        """
        return self.session.query(Features).filter(
            Features.game_id == game_id,
            Features.move_number == move_number,
            Features.player_color == player_color
        ).first() is not None

    def get_features_from_games(self, parsed_game: chess.pgn.Game) -> pd.DataFrame:

        print(
            f"Processing game from database... {parsed_game.headers.get('White', 'Unknown')} vs {parsed_game.headers.get('Black', 'Unknown')}")

        parsed_game.accept(chess.pgn.StringExporter(
            headers=True, variations=True, comments=True))
        game_id = get_game_id(parsed_game)
        features = self._extract_features_from_game(parsed_game, game_id)

        if not features:
            print("⚠️ No features extracted.")
            return pd.DataFrame()

        if isinstance(features, dict):
            # <-- safety check si devolviera un solo dict por error
            features = [features]

        if not isinstance(features, list):
            print("❌ Error: generate_features_from_game no devolvió una lista")
            return

        df = pd.DataFrame([features])
        return df

    def _extract_features_from_game(self, game: chess.pgn.Game, game_id: str) -> dict:
        return {
            "game_id": game_id,
            "white_player": game.headers.get("White", ""),
            "black_player": game.headers.get("Black", ""),
            "result": game.headers.get("Result", ""),
            "event": game.headers.get("Event", ""),
            "site": game.headers.get("Site", ""),
            "date": game.headers.get("Date", ""),
        }

    def save_many_features(self, feature_rows: list[dict]):
        print(f"🔍 Saving {len(feature_rows)} features...")

        # TODO: Este fragmento de código debería estar en un método publico de la capa de servicios.
        if not isinstance(feature_rows, list):
            logger.error(
                "❌ save_many_features received an invalid type. Expected: List[Dict]")
            return

        seen_keys = set()
        unique_rows = []

        for i, row in enumerate(feature_rows):
            if not isinstance(row, dict):
                logger.warning(
                    f"❌ Fila inválida en la posición {i}: tipo incorrecto ({type(row)}).")
                continue
            try:
                key = (row["game_id"], row["move_number"], row["player_color"])
                if key not in seen_keys:
                    seen_keys.add(key)
                    unique_rows.append(row)
            except Exception as err:
                logger.warning(
                    f"❌ Invalid row at position {i}: {row} - Error: {err}")

        if not unique_rows:
            logger.warning(
                "⚠️ No valid features left to insert after filtering.")
            return
        # FIN TODO

        print(f"🔍 Inserting {len(unique_rows)} unique features...")
        # Log first 5 for debugging
        # print(f"🔍 Unique rows: {unique_rows[:5]}...")

        try:
            with self.session_factory() as session:
                stmt = insert(self.model).values(unique_rows)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["game_id", "move_number", "player_color"])
                result = session.execute(stmt)
                session.commit()
                logger.info(
                    f"✅ Inserted {result.rowcount} rows. Skipped {len(unique_rows) - result.rowcount}.")
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error al insertar features: {e}")
            raise e

    def update_features_tags_and_score_diff(self, game_id: str, tags_df: pd.DataFrame):
        """
        Updates the `tags` and `score_diff` columns in the features table,
        only if the combination game_id + move_number + player_color already exists.

        :param game_id: Unique game hash
        :param tags_df: DataFrame with columns: move_number, player_color, tag, score_diff
        """
        if tags_df is None or tags_df.empty:
            print(f"⚠️ No tags to update for game {game_id}")
            return
        print(
            f"🔍 Updating {len(tags_df)} tags and score_diff for game {game_id}")

        updated_count = 0
        skipped = 0

        with self.session_factory() as session:
            try:
                print(
                    f"🔍 Processing tags for game {game_id}...tags_df: {tags_df}")
                for _, row in tags_df.iterrows():
                    move_number = int(row.get("move_number", -1))
                    player_color = row.get("player_color")
                    tag = row.get("tag")
                    score_diff = row.get("score_diff")
                    print(
                        f"🔍 Processing row: move_number={move_number}, player_color={player_color}, tag={tag}, score_diff={score_diff}")

                    # Map color if it comes as int
                    # if isinstance(player_color, int):
                    #     player_color = {0: "white", 1: "black"}.get(
                    #         player_color, "unknown")

                    # if isinstance(player_color, bool):
                    #     player_color = "white" if player_color else "black"

                    # if player_color not in {"white", "black"} or move_number < 0:
                    #     print(f"❌ Invalid values for tag: {row}")
                    #     skipped += 1
                    #     continue
                    if isinstance(player_color, str):
                        player_color = 1 if "white" else 0

                    if isinstance(player_color, bool):
                        player_color = 1 if True else 0

                    print(
                        f"Checking existence for game {game_id}, move {move_number}, color {player_color}")
                    exists = self.is_feature_in_db(
                        game_id=game_id,
                        move_number=move_number,
                        player_color=player_color
                    )

                    if not exists:
                        print(
                            f"⏭️ Feature for game {game_id}, move {move_number}, color {player_color} does not exist, skipping update.")
                        skipped += 1
                        continue

                    # exists = session.query(Features).filter_by(
                    #     game_id=game_id,
                    #     move_number=move_number,
                    #     player_color=player_color
                    # ).first()

                    stmt = (
                        update(self.model)
                        .where(
                            self.model.game_id == game_id,
                            self.model.move_number == move_number,
                            self.model.player_color == player_color
                        )
                        .values(
                            tags=tag,
                            score_diff=score_diff
                        )
                    )
                    session.execute(stmt)
                    updated_count += 1

                session.commit()
                print(f"✅ {updated_count} tags updated for game {game_id}")
                if skipped:
                    print(
                        f"⏭️ {skipped} moves skipped because they do not exist in the features table")

            except Exception as e:
                session.rollback()
                print(f"❌ Error updating features for {game_id}: {e}")
                raise
