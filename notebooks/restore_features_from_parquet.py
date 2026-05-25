#!/usr/bin/env python3
"""
Restore Features Table from Parquet Files

This script loads the pre-extracted features from Parquet files back into PostgreSQL.
Since features were already generated using generate_features_with_tactics.py,
we just need to restore them to the database.

Usage:
    python restore_features_from_parquet.py
"""

import pandas as pd
import os
import sys
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Configuration
DB_URL = os.environ.get(
    "CHESS_TRAINER_DB_URL", "postgresql://chess_user:chess_pass@postgres:5432/chess_db"
)
PARQUET_BASE_PATH = "/notebooks/data/export/"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def create_features_table(engine):
    """Create features table if it doesn't exist."""
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS features (
        id SERIAL PRIMARY KEY,
        game_id VARCHAR(255) NOT NULL,
        source VARCHAR(100),
        white_elo INTEGER,
        black_elo INTEGER,
        time_control VARCHAR(50),
        opening_name VARCHAR(200),
        opening_eco VARCHAR(10),
        game_result VARCHAR(20),
        total_moves INTEGER,
        avg_move_time FLOAT,
        blunders_white INTEGER DEFAULT 0,
        blunders_black INTEGER DEFAULT 0,
        mistakes_white INTEGER DEFAULT 0,
        mistakes_black INTEGER DEFAULT 0,
        inaccuracies_white INTEGER DEFAULT 0,
        inaccuracies_black INTEGER DEFAULT 0,
        brilliant_moves_white INTEGER DEFAULT 0,
        brilliant_moves_black INTEGER DEFAULT 0,
        good_moves_white INTEGER DEFAULT 0,
        good_moves_black INTEGER DEFAULT 0,
        book_moves_white INTEGER DEFAULT 0,
        book_moves_black INTEGER DEFAULT 0,
        best_moves_white INTEGER DEFAULT 0,
        best_moves_black INTEGER DEFAULT 0,
        accuracy_white FLOAT,
        accuracy_black FLOAT,
        avg_centipawn_loss_white FLOAT,
        avg_centipawn_loss_black FLOAT,
        time_pressure_moves_white INTEGER DEFAULT 0,
        time_pressure_moves_black INTEGER DEFAULT 0,
        castle_kingside_white BOOLEAN DEFAULT FALSE,
        castle_queenside_white BOOLEAN DEFAULT FALSE,
        castle_kingside_black BOOLEAN DEFAULT FALSE,
        castle_queenside_black BOOLEAN DEFAULT FALSE,
        en_passant_captures INTEGER DEFAULT 0,
        promotions_white INTEGER DEFAULT 0,
        promotions_black INTEGER DEFAULT 0,
        checks_given_white INTEGER DEFAULT 0,
        checks_given_black INTEGER DEFAULT 0,
        pieces_captured_white INTEGER DEFAULT 0,
        pieces_captured_black INTEGER DEFAULT 0,
        material_advantage_white FLOAT DEFAULT 0,
        material_advantage_black FLOAT DEFAULT 0,
        position_evaluation_final FLOAT,
        tactical_motifs_count INTEGER DEFAULT 0,
        endgame_type VARCHAR(50),
        pawn_structure_score_white FLOAT DEFAULT 0,
        pawn_structure_score_black FLOAT DEFAULT 0,
        king_safety_white FLOAT DEFAULT 0,
        king_safety_black FLOAT DEFAULT 0,
        piece_activity_white FLOAT DEFAULT 0,
        piece_activity_black FLOAT DEFAULT 0,
        center_control_white FLOAT DEFAULT 0,
        center_control_black FLOAT DEFAULT 0,
        development_speed_white FLOAT DEFAULT 0,
        development_speed_black FLOAT DEFAULT 0,
        space_advantage_white FLOAT DEFAULT 0,
        space_advantage_black FLOAT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(game_id)
    );
    
    CREATE INDEX IF NOT EXISTS idx_features_game_id ON features(game_id);
    CREATE INDEX IF NOT EXISTS idx_features_source ON features(source);
    CREATE INDEX IF NOT EXISTS idx_features_elo ON features(white_elo, black_elo);
    """

    with engine.connect() as conn:
        conn.execute(text(create_table_sql))
        conn.commit()

    logger.info("✅ Features table created/verified")


def load_parquet_to_postgres(source_name, parquet_file_path, engine):
    """Load a specific Parquet file into PostgreSQL."""
    if not os.path.exists(parquet_file_path):
        logger.warning(f"⚠️ Parquet file not found: {parquet_file_path}")
        return 0

    try:
        # Read Parquet file
        logger.info(f"📖 Reading {source_name} features from {parquet_file_path}")
        df = pd.read_parquet(parquet_file_path)

        if df.empty:
            logger.warning(f"⚠️ Empty dataset for {source_name}")
            return 0

        # Add source column if not present
        if "source" not in df.columns:
            df["source"] = source_name

        # Ensure game_id column exists
        if "game_id" not in df.columns and "id" in df.columns:
            df["game_id"] = df["id"]

        # Clean column names (remove special characters)
        df.columns = df.columns.str.replace(r"[^\w]", "_", regex=True)

        # Insert data in chunks
        chunk_size = 1000
        total_rows = len(df)
        inserted_rows = 0

        logger.info(
            f"💾 Inserting {total_rows:,} {source_name} features in chunks of {chunk_size}"
        )

        for i in range(0, total_rows, chunk_size):
            chunk = df.iloc[i : i + chunk_size]

            try:
                chunk.to_sql(
                    "features", engine, if_exists="append", index=False, method="multi"
                )
                inserted_rows += len(chunk)

                if i % (chunk_size * 10) == 0:  # Log every 10 chunks
                    logger.info(
                        f"   📊 {source_name}: {inserted_rows:,}/{total_rows:,} rows inserted"
                    )

            except Exception as e:
                logger.error(
                    f"❌ Error inserting chunk {i}-{i+chunk_size} for {source_name}: {e}"
                )
                continue

        logger.info(
            f"✅ {source_name}: {inserted_rows:,} features inserted successfully"
        )
        return inserted_rows

    except Exception as e:
        logger.error(f"❌ Error loading {source_name} features: {e}")
        return 0


def main():
    """Main restoration process."""
    logger.info("🚀 Starting features restoration from Parquet files...")

    start_time = time.time()

    try:
        # Create database engine
        engine = create_engine(DB_URL)
        logger.info("🔗 Connected to PostgreSQL")

        # Create features table
        create_features_table(engine)

        # Sources to restore
        sources = ["elite", "fide", "novice", "personal", "stockfish"]
        total_inserted = 0

        for source in sources:
            parquet_path = os.path.join(
                PARQUET_BASE_PATH, source, f"{source}_features.parquet"
            )

            logger.info(f"🔄 Processing {source.upper()} features...")
            inserted = load_parquet_to_postgres(source, parquet_path, engine)
            total_inserted += inserted

            if inserted > 0:
                logger.info(f"✅ {source.upper()}: {inserted:,} features restored")
            else:
                logger.warning(f"⚠️ {source.upper()}: No features restored")

        # Final summary
        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"🎉 Features restoration completed!")
        logger.info(f"📊 Summary:")
        logger.info(f"   - Total features restored: {total_inserted:,}")
        logger.info(f"   - Duration: {duration:.2f} seconds")
        logger.info(f"   - Features per second: {total_inserted / duration:.2f}")

        # Verify restoration
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM features"))
            total_count = result.scalar()
            logger.info(f"✅ Verification: {total_count:,} features in database")

            # Count by source
            result = conn.execute(
                text(
                    "SELECT source, COUNT(*) FROM features GROUP BY source ORDER BY source"
                )
            )
            logger.info("📋 Features by source:")
            for row in result:
                logger.info(f"   - {row[0]}: {row[1]:,} features")

    except Exception as e:
        logger.error(f"❌ Fatal error during restoration: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
