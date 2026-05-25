# /app/src/db/repository/Features_repository.py

import logging
from typing import Dict, List
import chess
import pandas as pd
from sqlalchemy import and_, join, or_, select, update
import sqlalchemy
from sqlalchemy.dialects.postgresql import insert
from db.models.features import Features
from db.models.games import Games
from db.db_utils import DBUtils, Session
from db.session import get_session
from modules.pgn_utils import get_game_id

logger = logging.getLogger(__name__)


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
        print(f"Extracted features for game {game_id}: {features}")

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
        print(f"Saving {len(feature_rows)} features...")

        # MIGRATED-TODO: Este fragmento de código debería estar en un método publico de la capa de servicios.
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

        print(f"Inserting {len(unique_rows)} unique features...")
        # Log first 5 for debugging
        # print(f"Unique rows: {unique_rows[:5]}...")

        try:
            with self.session_factory() as session:
                stmt = insert(self.model).values(unique_rows)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["game_id", "move_number", "player_color"])
                result = session.execute(stmt)
                session.commit()
                logger.info(
                    f"SUCCESS: Inserted {result.rowcount} rows. Skipped {len(unique_rows) - result.rowcount}.")
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
            f"Updating {len(tags_df)} tags and score_diff for game {game_id}")

        updated_count = 0
        skipped = 0

        with self.session_factory() as session:
            try:
                print(
                    f"Processing tags for game {game_id}...tags_df: {tags_df.head(3)}")
                for _, row in tags_df.iterrows():
                    move_number = int(row.get("move_number", -1))
                    player_color = row.get("player_color")
                    tag = row.get("tag")
                    score_diff = row.get("score_diff")
                    error_label = row.get("error_label", None)
                    print(
                        f"Processing row: move_number={move_number}, player_color={player_color}, tag={tag}, score_diff={score_diff}")

                    if isinstance(player_color, str):
                        player_color = 1 if "white" else 0

                    if isinstance(player_color, bool):
                        player_color = 1 if True else 0

                    print(
                        f"Checking existence for game {game_id}, move {move_number}, color {player_color}")
                    try:
                        exists = self.is_feature_in_db(
                            game_id=game_id,
                            move_number=move_number,
                            player_color=player_color
                        )
                    except sqlalchemy.exc.PendingRollbackError as e:
                        logger.error(f"Sesión en rollback, se resetea: {e}")
                        self.session.rollback()
                        raise e  # O seguir de forma controlada

                    if not exists:
                        print(
                            f"⏭️ Feature for game {game_id}, move {move_number}, color {player_color} does not exist, skipping update.")
                        skipped += 1
                        continue
                    else:
                        print(
                            f"Updating {game_id}, move: {move_number}, color: {player_color}")

                    print(
                        f"Preparando update - move: {move_number}, player_color: {player_color}, tag: {tag}")

                    tags_array = [tag] if tag else []
                    print(f"tags_array generado: {tags_array}")

                    stmt = (
                        update(self.model)
                        .where(
                            self.model.game_id == game_id,
                            self.model.move_number == move_number,
                            self.model.player_color == player_color
                        )
                        .values(
                            tags=tags_array,
                            error_label=error_label,
                            score_diff=score_diff
                        )
                    )
                    print(f"STMT generado: {stmt}")

                    session.execute(stmt)
                    updated_count += 1

                session.commit()
                print(f"SUCCESS: {updated_count} tags updated for game {game_id}")
                if skipped:
                    print(
                        f"⏭️ {skipped} moves skipped because they do not exist in the features table")

            except Exception as e:
                session.rollback()
                print(f"❌ Error updating features for {game_id}: {e}")
                raise

    def get_unique_sources(self):
        with self.session_factory() as session:
            stmt = select(Games.source).distinct()
            result = session.execute(stmt).fetchall()
            return [row[0] for row in result if row[0] is not None]

    def get_features_with_filters(
        self,
        # Source of the games (e.g., "personal", "novice", "elite", "stockfish", "fide")
        source,
        output_path: str = "filtered_features.parquet",
        min_elo: int = None,
        max_elo: int = None,
        player_name: str = None,
        opening: str = None,
        limit: int = None

    ):
        """
        Exporta un archivo Parquet con los features filtrados por ELO, jugador, apertura y
        límite de cantidad de partidas completas (no por jugadas).
        """
        print(f"Exportando dataset filtrado a {output_path}...")

        try:
            with self.session_factory() as session:
                filters = []

                if min_elo is not None:
                    filters.append(Games.white_elo >= min_elo)
                    filters.append(Games.black_elo >= min_elo)

                if max_elo is not None:
                    filters.append(Games.white_elo <= max_elo)
                    filters.append(Games.black_elo <= max_elo)

                if player_name:
                    filters.append(or_(
                        Games.white_player.ilike(f"%{player_name}%"),
                        Games.black_player.ilike(f"%{player_name}%")
                    ))

                if source:
                    filters.append(Games.source == source)

                if opening:
                    filters.append(or_(
                        Games.eco.ilike(f"%{opening}%"),
                        Games.opening.ilike(f"%{opening}%")
                    ))

                # Paso 1: Obtener game_ids que cumplen los filtros
                game_stmt = select(Games.game_id).distinct()
                if filters:
                    game_stmt = game_stmt.where(and_(*filters))
                if limit is not None:
                    game_stmt = game_stmt.limit(limit)

                filtered_game_ids = [row[0]
                                     for row in session.execute(game_stmt).fetchall()]
                if not filtered_game_ids:
                    print("⚠️ No se encontraron partidas que cumplan los filtros.")
                    return

                # Paso 2: Obtener todos los features que pertenecen a esos game_ids
                j = join(Features, Games, Features.game_id == Games.game_id)

                stmt = select(
                    Features.game_id,
                    Features.move_number,
                    Features.player_color,
                    Features.fen,
                    Features.move_san,
                    Features.move_uci,
                    Features.material_balance,
                    Features.material_total,
                    Features.num_pieces,
                    Features.branching_factor,
                    Features.self_mobility,
                    Features.opponent_mobility,
                    Features.phase,
                    Features.has_castling_rights,
                    Features.move_number_global,
                    Features.is_repetition,
                    Features.is_low_mobility,
                    Features.is_center_controlled,
                    Features.is_pawn_endgame,
                    Features.tags,
                    Features.score_diff,
                    Features.is_stockfish_test,
                    Features.num_moves,
                    Features.error_label,
                    Games.source,
                    Games.date_played,
                    Games.time_control,
                    Games.white_player,
                    Games.black_player,
                    Games.white_elo,
                    Games.black_elo,
                    Games.result,
                    Games.eco,
                    Games.opening
                ).select_from(j).where(Features.game_id.in_(filtered_game_ids))

                result = session.execute(stmt)
                df = pd.DataFrame(result.fetchall(), columns=result.keys())

                return df

        except Exception as e:
            print(f"❌ Error exportando dataset filtrado: {e}")
            raise

    def update_tactical_data(self, tactical_data):
        """
        Update existing features with tactical analysis data.
        tactical_data should be a list of dictionaries with tactical information.
        """
        if not tactical_data:
            return
        
        updated_count = 0
        
        try:
            with self.session_factory() as session:
                for tactic in tactical_data:
                    game_id = tactic.get('game_id')
                    move_number = tactic.get('move_number')
                    
                    if not game_id or not move_number:
                        continue
                    
                    # Find existing feature record
                    feature_record = session.query(Features).filter_by(
                        game_id=game_id, 
                        move_number=move_number
                    ).first()
                    
                    if feature_record:
                        # Update with tactical information
                        if tactic.get('error_label'):
                            feature_record.error_label = tactic.get('error_label')
                        
                        if tactic.get('score_diff') is not None:
                            feature_record.score_diff = tactic.get('score_diff')
                        
                        # Add tactical tag to existing tags
                        current_tags = feature_record.tags or []
                        if isinstance(current_tags, str):
                            current_tags = []
                        
                        tactical_tag = tactic.get('tag')
                        if tactical_tag and tactical_tag not in current_tags:
                            current_tags.append(tactical_tag)
                            feature_record.tags = current_tags
                        
                        updated_count += 1
                
                session.commit()
                logger.info(f"Updated {updated_count} features with tactical data")
                
        except Exception as e:
            logger.error(f"Error updating tactical data: {e}")
            session.rollback()
            raise

    def get_by_game_and_move(self, game_id, move_number):
        """
        Get a feature record by game_id and move_number.
        """
        try:
            with self.session_factory() as session:
                return session.query(Features).filter_by(
                    game_id=game_id, 
                    move_number=move_number
                ).first()
        except Exception as e:
            logger.error(f"Error getting feature by game and move: {e}")
            return None

    def update_tactical_data_single(self, feature_id, tactical_data):
        """
        Update a single feature record with tactical data.
        """
        try:
            with self.session_factory() as session:
                feature = session.query(Features).filter_by(id=feature_id).first()
                
                if feature:
                    # Update tactical information
                    if tactical_data.get('error_label'):
                        feature.error_label = tactical_data.get('error_label')
                    
                    if tactical_data.get('score_diff') is not None:
                        feature.score_diff = tactical_data.get('score_diff')
                    
                    # Add tactical tag to existing tags
                    current_tags = feature.tags or []
                    if isinstance(current_tags, str):
                        current_tags = []
                    
                    tactical_tag = tactical_data.get('tag')
                    if tactical_tag and tactical_tag not in current_tags:
                        current_tags.append(tactical_tag)
                        feature.tags = current_tags
                    
                    session.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error updating single tactical data: {e}")
            return False

    def update_feature_by_composite_key(self, game_id, move_number, player_color, tactical_data):
        """
        Update a feature record using composite key (game_id, move_number, player_color).
        """
        try:
            with self.session_factory() as session:
                feature = session.query(Features).filter_by(
                    game_id=game_id, 
                    move_number=move_number,
                    player_color=player_color
                ).first()
                
                if feature:
                    # Update tactical information
                    if tactical_data.get('error_label'):
                        feature.error_label = tactical_data.get('error_label')
                    
                    if tactical_data.get('score_diff') is not None:
                        feature.score_diff = tactical_data.get('score_diff')
                    
                    # Add tactical tag to existing tags
                    current_tags = feature.tags or []
                    if isinstance(current_tags, str):
                        current_tags = []
                    
                    tactical_tag = tactical_data.get('tag')
                    if tactical_tag and tactical_tag not in current_tags:
                        current_tags.append(tactical_tag)
                        feature.tags = current_tags
                    
                    session.commit()
                    return True
                else:
                    logger.warning(f"No feature found for game {game_id}, move {move_number}, color {player_color}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error updating feature by composite key: {e}")
            return False
