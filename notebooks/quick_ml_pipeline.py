#!/usr/bin/env python3
"""
Quick ML Pipeline Runner
========================

Simplified script to regenerate tables and run the optimized ML pipeline.
"""

import os
import sys
import time
import logging
import subprocess
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

def run_command(cmd, description):
    """Run a command and log the results."""
    logger.info(f"🔄 {description}")
    logger.info(f"📝 Command: {cmd}")
    
    start_time = time.time()
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    end_time = time.time()
    duration = end_time - start_time
    
    if result.returncode == 0:
        logger.info(f"✅ {description} completed in {duration:.2f}s")
        if result.stdout:
            logger.info(f"📋 Output: {result.stdout[:500]}...")
    else:
        logger.error(f"❌ {description} failed in {duration:.2f}s")
        logger.error(f"📋 Error: {result.stderr}")
        return False
    
    return True

def main():
    """Run the complete pipeline."""
    logger.info("🚀 Starting Quick ML Pipeline...")
    
    # Step 1: Just start with importing games directly from Parquet to PostgreSQL
    logger.info("📊 Step 1: Setting up database and importing games from Parquet")
    
    # Create a comprehensive import script
    import_script = '''
import pandas as pd
import os
import sys
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Database URL
DB_URL = os.environ.get("CHESS_TRAINER_DB_URL", "postgresql://chess_user:chess_pass@postgres:5432/chess_db")

try:
    engine = create_engine(DB_URL)
    
    # Test connection
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("✅ Database connection successful")
    
    # Create tables if they don't exist
    logger.info("🔄 Creating tables...")
    
    create_tables_sql = """
    -- Create games table
    CREATE TABLE IF NOT EXISTS games (
        id VARCHAR(255) PRIMARY KEY,
        pgn TEXT NOT NULL,
        source VARCHAR(100),
        white_player VARCHAR(255),
        black_player VARCHAR(255), 
        white_elo INTEGER,
        black_elo INTEGER,
        result VARCHAR(20),
        time_control VARCHAR(50),
        opening VARCHAR(200),
        eco VARCHAR(10),
        date_played DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_games_source ON games(source);
    CREATE INDEX IF NOT EXISTS idx_games_elo ON games(white_elo, black_elo);
    
    -- Create features table  
    CREATE TABLE IF NOT EXISTS features (
        id SERIAL PRIMARY KEY,
        game_id VARCHAR(255) NOT NULL UNIQUE,
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
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_features_game_id ON features(game_id);
    CREATE INDEX IF NOT EXISTS idx_features_source ON features(source);
    
    -- Create tactical analysis table
    CREATE TABLE IF NOT EXISTS analyzed_tacticals (
        id SERIAL PRIMARY KEY,
        game_id VARCHAR(255) NOT NULL,
        move_number INTEGER NOT NULL,
        color VARCHAR(10) NOT NULL,
        tactic_type VARCHAR(100) NOT NULL,
        evaluation_before FLOAT,
        evaluation_after FLOAT,
        centipawn_difference FLOAT,
        move_played VARCHAR(20) NOT NULL,
        best_move VARCHAR(20),
        position_fen TEXT,
        tactical_motif VARCHAR(100),
        difficulty_score FLOAT,
        time_spent FLOAT,
        is_blunder BOOLEAN DEFAULT FALSE,
        is_mistake BOOLEAN DEFAULT FALSE,
        is_inaccuracy BOOLEAN DEFAULT FALSE,
        is_brilliant BOOLEAN DEFAULT FALSE,
        is_good BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_tacticals_game_id ON analyzed_tacticals(game_id);
    CREATE INDEX IF NOT EXISTS idx_tacticals_type ON analyzed_tacticals(tactic_type);
    
    -- Create processed features tracking
    CREATE TABLE IF NOT EXISTS processed_features (
        id SERIAL PRIMARY KEY,
        game_id VARCHAR(255) NOT NULL UNIQUE,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    CREATE INDEX IF NOT EXISTS idx_processed_game_id ON processed_features(game_id);
    """
    
    with engine.connect() as conn:
        conn.execute(text(create_tables_sql))
        conn.commit()
    
    logger.info("✅ Tables created successfully")
    
    # Import games from Parquet files (sample for testing)
    parquet_files = [
        ("/notebooks/data/export/elite/elite_games.parquet", "elite", 1000),
        ("/notebooks/data/export/fide/fide_games.parquet", "fide", 1000), 
        ("/notebooks/data/export/novice/novice_games.parquet", "novice", 500),
        ("/notebooks/data/export/personal/personal_games.parquet", "personal", 500)
    ]
    
    total_imported = 0
    
    for parquet_path, source, limit in parquet_files:
        if os.path.exists(parquet_path):
            logger.info(f"📖 Loading {source} games from {parquet_path} (limit: {limit})")
            df = pd.read_parquet(parquet_path)
            
            # Sample for testing
            if len(df) > limit:
                df = df.sample(n=limit, random_state=42)
            
            # Ensure required columns
            if "source" not in df.columns:
                df["source"] = source
            
            # Clean data
            df = df.drop_duplicates(subset=["id"])
            
            # Import to database
            try:
                df.to_sql("games", engine, if_exists="append", index=False, method="multi")
                total_imported += len(df)
                logger.info(f"✅ {source}: {len(df):,} games imported")
            except Exception as e:
                logger.error(f"❌ Error importing {source}: {e}")
        else:
            logger.warning(f"⚠️ File not found: {parquet_path}")
    
    logger.info(f"🎉 Total games imported: {total_imported:,}")
    
    # Verify import
    with engine.connect() as conn:
        result = conn.execute(text("SELECT source, COUNT(*) FROM games GROUP BY source ORDER BY source"))
        logger.info("📊 Games by source:")
        for row in result:
            logger.info(f"   - {row[0]}: {row[1]:,} games")

except Exception as e:
    logger.error(f"❌ Database setup failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''
    
    # Write and run the import script
    with open('/tmp/setup_db_and_import.py', 'w') as f:
        f.write(import_script)
    
    success = run_command(
        "docker-compose exec notebooks python /tmp/setup_db_and_import.py",
        "Database setup and games import"
    )
    
    if not success:
        logger.error("❌ Database setup failed")
        return False
    
    # Step 2: Generate features using the existing script
    logger.info("🎯 Step 2: Generating features and tactics for sample data")
    
    sources = ["elite", "fide", "novice", "personal"]
    limits = [1000, 1000, 500, 500]  # Small test limits
    
    for source, limit in zip(sources, limits):
        success = run_command(
            f"docker-compose exec notebooks python /notebooks/src/scripts/generate_features_with_tactics.py --source {source} --max-games {limit} --workers 4",
            f"Feature generation for {source} ({limit} games)"
        )
        
        if not success:
            logger.warning(f"⚠️ Feature generation failed for {source}")
    
    # Step 3: Export datasets
    logger.info("📤 Step 3: Exporting datasets")
    
    success = run_command(
        "docker-compose exec notebooks python /notebooks/src/scripts/export_features_dataset_parallel.py",
        "Dataset export"
    )
    
    # Step 4: Create balanced dataset
    logger.info("🎯 Step 4: Creating balanced dataset")
    
    success = run_command(
        "docker-compose exec notebooks python /notebooks/src/scripts/generate_combined_dataset.py",
        "Balanced dataset creation"
    )
    
    logger.info("🎉 Quick ML Pipeline completed!")
    
if __name__ == "__main__":
    main()
