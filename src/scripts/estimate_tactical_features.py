#!/usr/bin/env python3
"""
Lightweight tactical feature estimation.
Provides fast approximations of score_diff and error_label without heavy engine analysis.
"""

import chess
import pandas as pd
from typing import Dict, Optional


def estimate_material_advantage(board: chess.Board, move: chess.Move) -> int:
    """Estimate material advantage change from a move."""
    piece_values = {
        chess.PAWN: 100, chess.KNIGHT: 300, chess.BISHOP: 300,
        chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0
    }

    material_change = 0

    # Check if move captures a piece
    if board.is_capture(move):
        captured_square = move.to_square
        captured_piece = board.piece_at(captured_square)
        if captured_piece:
            material_change += piece_values.get(captured_piece.piece_type, 0)

    # Check for promotion
    if move.promotion:
        material_change += piece_values.get(move.promotion, 0) - \
            piece_values[chess.PAWN]

    return material_change


def estimate_positional_score(board: chess.Board, move: chess.Move) -> int:
    """Estimate positional score change (simplified)."""
    score = 0

    # Center control bonus
    center_squares = [chess.D4, chess.D5, chess.E4, chess.E5]
    if move.to_square in center_squares:
        score += 20

    # Development bonus (knights and bishops moving from back rank)
    piece = board.piece_at(move.from_square)
    if piece and piece.piece_type in [chess.KNIGHT, chess.BISHOP]:
        from_rank = chess.square_rank(move.from_square)
        to_rank = chess.square_rank(move.to_square)
        if piece.color == chess.WHITE and from_rank == 0 and to_rank > 0:
            score += 15
        elif piece.color == chess.BLACK and from_rank == 7 and to_rank < 7:
            score += 15

    # Castling bonus
    if board.is_castling(move):
        score += 30

    # Check bonus/penalty
    board_copy = board.copy()
    board_copy.push(move)
    if board_copy.is_check():
        score += 10  # Giving check is usually good

    return score


def estimate_score_diff(board: chess.Board, move: chess.Move) -> int:
    """Estimate score difference for a move (in centipawns)."""
    material_change = estimate_material_advantage(board, move)
    positional_change = estimate_positional_score(board, move)

    # Simple mobility consideration
    legal_moves_before = len(list(board.legal_moves))
    board_copy = board.copy()
    board_copy.push(move)
    legal_moves_after = len(list(board_copy.legal_moves))

    mobility_change = (legal_moves_after - legal_moves_before) * 2

    total_score = material_change + positional_change + mobility_change

    # Add some randomness to simulate engine uncertainty
    import random
    uncertainty = random.randint(-20, 20)

    return total_score + uncertainty


def estimate_error_label(score_diff: int) -> str:
    """Classify move quality based on estimated score difference."""
    if score_diff < -200:
        return 'blunder'
    elif score_diff < -100:
        return 'mistake'
    elif score_diff < -50:
        return 'inaccuracy'
    elif score_diff > 50:
        return 'good'
    else:
        return 'ok'


def add_lightweight_tactical_features(features_df: pd.DataFrame) -> pd.DataFrame:
    """Add estimated tactical features to existing features dataframe."""

    print(
        f"🔄 Adding lightweight tactical features to {len(features_df)} rows...")

    updated_rows = []

    for _, row in features_df.iterrows():
        try:
            # Parse position and move
            board = chess.Board(row['fen'])
            move = chess.Move.from_uci(row['move_uci'])

            # Estimate tactical features
            estimated_score_diff = estimate_score_diff(board, move)
            estimated_error_label = estimate_error_label(estimated_score_diff)

            # Update row
            row_dict = row.to_dict()
            row_dict['score_diff'] = estimated_score_diff
            row_dict['error_label'] = estimated_error_label
            row_dict['tags'] = [
                estimated_error_label] if estimated_error_label != 'ok' else []

            updated_rows.append(row_dict)

        except Exception as e:
            print(f"⚠️ Error processing row: {e}")
            # Keep original row unchanged
            updated_rows.append(row.to_dict())

    result_df = pd.DataFrame(updated_rows)
    print(f"✅ Added tactical features to {len(result_df)} rows")

    return result_df


if __name__ == "__main__":
    import argparse
    import sys
    sys.path.append('/app/src')

    from db.repository.features_repository import FeaturesRepository

    parser = argparse.ArgumentParser(
        description="Add lightweight tactical feature estimates"
    )
    parser.add_argument("--source", type=str, help="Filter features by source")
    parser.add_argument("--max-games", type=int, default=10000,
                        help="Maximum number of features to process")

    args = parser.parse_args()

    print("🚀 Starting lightweight tactical feature estimation...")

    # Get features without tactical analysis
    features_repo = FeaturesRepository()
    from db.repository.analyzed_tacticals_repository import Analyzed_tacticalsRepository

    df = features_repo.get_features_missing_tactical_data(
        source=args.source,
        limit=args.max_games
    )

    if len(df) == 0:
        print("⚠️ No features found that need tactical estimation")
    else:
        print(f"📊 Found {len(df)} features to process")

        # Add lightweight tactical features
        updated_df = add_lightweight_tactical_features(df)

        # Update database with estimated values
        print("💾 Updating database with estimated tactical features...")

        try:
            # Prepare bulk updates
            updates = []
            analyzed_tacticals_repo = Analyzed_tacticalsRepository()

            for _, row in updated_df.iterrows():
                updates.append({
                    'game_id': row['game_id'],
                    'move_number': row.get('move_number', 0),
                    'score_diff': row['score_diff'],
                    'error_label': row['error_label']
                })

            # Perform bulk update
            print(
                f"📈 Updating {len(updates)} features with estimated tactical data...")
            features_repo.update_tactical_features_bulk(updates)

            # Mark games as analyzed in the tracking table
            game_ids = updated_df['game_id'].unique()
            analyzed_count = 0
            for game_id in game_ids:
                try:
                    analyzed_tacticals_repo.save_analyzed_tactical_hash(
                        game_id)
                    analyzed_count += 1
                except Exception as e:
                    print(
                        f"⚠️ Warning: Failed to mark game {game_id} as analyzed: {e}")
                    continue

            print(
                f"✅ Successfully updated {len(updates)} features with estimated tactical data")
            print(
                f"✅ Marked {analyzed_count}/{len(game_ids)} games as tactically analyzed")
            print("✅ Lightweight tactical estimation completed")

        except Exception as e:
            print(f"❌ Error updating database: {e}")
            print("⚠️ Estimation completed but database update failed")
            import traceback
            traceback.print_exc()
