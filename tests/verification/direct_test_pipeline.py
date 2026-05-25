#!/usr/bin/env python3
"""
Direct Database Setup and Test Pipeline

This script runs directly inside the notebooks container to:
1. Setup database tables
2. Import sample games from Parquet
3. Generate features for test data
4. Create balanced dataset

Usage:
    python direct_test_pipeline.py
"""

import pandas as pd
import os
import sys
import time
import logging
from pathlib import Path
from sqlalchemy import create_engine, text

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.append('/notebooks/src')

def setup_database():
    """Setup database tables and import sample data."""
    logger.info("🔄 Setting up database...")
    
    # Database URL
    DB_URL = os.environ.get("CHESS_TRAINER_DB_URL", "postgresql://chess:chess_pass@postgres:5432/chess_trainer_db")
    
    try:
        engine = create_engine(DB_URL)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        
        # Create tables
        logger.info("🔄 Creating tables...")
        
        create_tables_sql = """
        -- Drop and recreate schema
        DROP SCHEMA IF EXISTS public CASCADE;
        CREATE SCHEMA public;
        
        -- Create games table
        CREATE TABLE games (
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
        
        CREATE INDEX idx_games_source ON games(source);
        CREATE INDEX idx_games_elo ON games(white_elo, black_elo);
        
        -- Create features table  
        CREATE TABLE features (
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
        
        CREATE INDEX idx_features_game_id ON features(game_id);
        CREATE INDEX idx_features_source ON features(source);
        
        -- Create tactical analysis table
        CREATE TABLE analyzed_tacticals (
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
        
        CREATE INDEX idx_tacticals_game_id ON analyzed_tacticals(game_id);
        CREATE INDEX idx_tacticals_type ON analyzed_tacticals(tactic_type);
        
        -- Create processed features tracking
        CREATE TABLE processed_features (
            id SERIAL PRIMARY KEY,
            game_id VARCHAR(255) NOT NULL UNIQUE,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_processed_game_id ON processed_features(game_id);
        """
        
        with engine.connect() as conn:
            conn.execute(text(create_tables_sql))
            conn.commit()
        
        logger.info("✅ Tables created successfully")
        
        # Import sample games from Parquet files
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
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_features_sample():
    """Generate features for sample data."""
    logger.info("🎯 Generating features for sample data...")
    
    try:
        # Import the feature generation script
        from scripts.generate_features_with_tactics import main as generate_features_main
        
        # Generate features for each source with small limits
        sources = ["elite", "fide", "novice", "personal"]
        limits = [200, 200, 100, 100]  # Very small for quick test
        
        for source, limit in zip(sources, limits):
            logger.info(f"🔄 Processing {source} ({limit} games)...")
            
            # Simulate command line arguments
            sys.argv = [
                "generate_features_with_tactics.py",
                "--source", source,
                "--max-games", str(limit),
                "--workers", "2"
            ]
            
            try:
                generate_features_main()
                logger.info(f"✅ {source} features completed")
            except Exception as e:
                logger.warning(f"⚠️ Error with {source}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Feature generation failed: {e}")
        return False

def export_datasets():
    """Export datasets to Parquet."""
    logger.info("📤 Exporting datasets...")
    
    try:
        from scripts.export_features_dataset_parallel import main as export_main
        
        # Reset sys.argv for export script
        sys.argv = ["export_features_dataset_parallel.py"]
        export_main()
        
        logger.info("✅ Dataset export completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Dataset export failed: {e}")
        return False

def create_balanced_dataset():
    """Create balanced dataset."""
    logger.info("🎯 Creating balanced dataset...")
    
    try:
        from scripts.generate_combined_dataset import main as combined_main
        
        # Reset sys.argv for combined dataset script
        sys.argv = ["generate_combined_dataset.py"]
        combined_main()
        
        logger.info("✅ Balanced dataset created")
        return True
        
    except Exception as e:
        logger.error(f"❌ Balanced dataset creation failed: {e}")
        return False

def main():
    """Main execution function."""
    logger.info("🚀 Starting Direct Test Pipeline...")
    start_time = time.time()
    
    # Step 1: Setup database
    if not setup_database():
        logger.error("❌ Database setup failed")
        return False
    
    # Step 2: Generate features (optional for quick test)
    logger.info("⏭️ Skipping feature generation for quick test")
    # if not generate_features_sample():
    #     logger.warning("⚠️ Feature generation had issues, continuing...")
    
    # Step 3: Export datasets (will export what exists)
    if not export_datasets():
        logger.warning("⚠️ Dataset export had issues, continuing...")
    
    # Step 4: Create balanced dataset (with existing data)
    if not create_balanced_dataset():
        logger.warning("⚠️ Balanced dataset creation had issues")
    
    # Final summary
    end_time = time.time()
    duration = end_time - start_time
    
    logger.info(f"🎉 Test pipeline completed in {duration:.2f} seconds!")
    
    # Verify final state
    try:
        DB_URL = os.environ.get("CHESS_TRAINER_DB_URL", "postgresql://chess:chess_pass@postgres:5432/chess_trainer_db")
        engine = create_engine(DB_URL)
        
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT 'games' as table_name, COUNT(*) as count FROM games
                UNION ALL
                SELECT 'features' as table_name, COUNT(*) as count FROM features
                UNION ALL  
                SELECT 'analyzed_tacticals' as table_name, COUNT(*) as count FROM analyzed_tacticals;
            """))
            
            logger.info("📊 Final database state:")
            for row in result:
                logger.info(f"   - {row[0]}: {row[1]:,} records")
                
    except Exception as e:
        logger.warning(f"⚠️ Could not verify final state: {e}")
    
    logger.info("✅ Test pipeline ready - database is set up for full overnight run!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
