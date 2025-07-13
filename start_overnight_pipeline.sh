#!/bin/bash
"""
🚀 SIMPLIFIED OVERNIGHT ML PIPELINE
===================================

This script runs a simplified but complete ML pipeline to:
1. Setup database with sample data for testing
2. Generate features + tactics 
3. Export datasets
4. Create balanced combined dataset

For overnight run, this will validate the process with smaller datasets first.

Usage:
    ./start_overnight_pipeline.sh        # Run full pipeline
    ./start_overnight_pipeline.sh test   # Run quick test with small sample
"""

set -e

# Colors
GREEN="\033[0;32m"
RED="\033[0;31m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
NC="\033[0m"

# Configuration
MODE="${1:-full}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="pipeline_${TIMESTAMP}.log"

echo -e "${CYAN}🚀 Starting Simplified ML Pipeline (${MODE} mode)${NC}"
echo -e "${BLUE}📅 Start time: $(date)${NC}"
echo -e "${BLUE}📝 Logs: ${LOG_FILE}${NC}"

# Ensure services are running
echo -e "${CYAN}🔄 Ensuring services are running...${NC}"
docker-compose up -d

# Wait for PostgreSQL
echo -e "${CYAN}⏳ Waiting for PostgreSQL to be ready...${NC}"
sleep 10

if [ "$MODE" = "test" ]; then
    echo -e "${YELLOW}🧪 Running QUICK TEST mode with sample data${NC}"
    python quick_ml_pipeline.py 2>&1 | tee -a "$LOG_FILE"
else
    echo -e "${CYAN}🌙 Running FULL OVERNIGHT mode${NC}"
    
    # Step 1: Setup database with full data import
    echo -e "${CYAN}📋 Step 1: Setting up database and importing ALL games...${NC}"
    
    cat > /tmp/full_import.py << 'EOF'
import pandas as pd
import os
import sys
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_URL = os.environ.get("CHESS_TRAINER_DB_URL", "postgresql://chess_user:chess_pass@postgres:5432/chess_db")

try:
    engine = create_engine(DB_URL)
    
    # Create all tables
    create_tables_sql = """
    DROP SCHEMA IF EXISTS public CASCADE;
    CREATE SCHEMA public;
    GRANT ALL ON SCHEMA public TO chess_user;
    GRANT ALL ON SCHEMA public TO public;
    
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
    
    logger.info("✅ Database schema recreated")
    
    # Import games with optimal sampling for balanced dataset
    parquet_files = [
        ("/notebooks/data/export/elite/elite_games.parquet", "elite", 50000),
        ("/notebooks/data/export/fide/fide_games.parquet", "fide", 50000), 
        ("/notebooks/data/export/novice/novice_games.parquet", "novice", 25000),
        ("/notebooks/data/export/personal/personal_games.parquet", "personal", 25000)
    ]
    
    total_imported = 0
    
    for parquet_path, source, limit in parquet_files:
        if os.path.exists(parquet_path):
            logger.info(f"📖 Loading {source} games (target: {limit:,})")
            df = pd.read_parquet(parquet_path)
            
            # Sample for optimal dataset
            if len(df) > limit:
                df = df.sample(n=limit, random_state=42)
                logger.info(f"   📊 Sampled {limit:,} from {len(df):,} available")
            else:
                logger.info(f"   📊 Using all {len(df):,} available games")
            
            # Ensure source column
            if "source" not in df.columns:
                df["source"] = source
            
            # Clean and import
            df = df.drop_duplicates(subset=["id"])
            
            # Import in chunks
            chunk_size = 5000
            for i in range(0, len(df), chunk_size):
                chunk = df.iloc[i:i + chunk_size]
                chunk.to_sql("games", engine, if_exists="append", index=False, method="multi")
                logger.info(f"   📋 {source}: {i + len(chunk):,}/{len(df):,} imported")
            
            total_imported += len(df)
            logger.info(f"✅ {source}: {len(df):,} games imported")
        else:
            logger.warning(f"⚠️ File not found: {parquet_path}")
    
    logger.info(f"🎉 Total games imported: {total_imported:,}")
    
    # Verify import
    with engine.connect() as conn:
        result = conn.execute(text("SELECT source, COUNT(*) FROM games GROUP BY source ORDER BY source"))
        logger.info("📊 Final games distribution:")
        for row in result:
            logger.info(f"   - {row[0]}: {row[1]:,} games")

except Exception as e:
    logger.error(f"❌ Full import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF
    
    docker-compose exec notebooks python /tmp/full_import.py 2>&1 | tee -a "$LOG_FILE"
    
    # Step 2: Generate features for ALL imported games
    echo -e "${CYAN}🎯 Step 2: Generating features for ALL games...${NC}"
    
    # Run feature generation for each source with the imported limits
    for source in elite fide novice personal; do
        echo -e "${CYAN}   🔄 Processing $source...${NC}"
        docker-compose exec notebooks python /notebooks/src/scripts/generate_features_with_tactics.py \
            --source "$source" \
            --max-games 999999 \
            --workers 6 \
            --chunk-size 1000 \
            2>&1 | tee -a "$LOG_FILE"
    done
    
    # Step 3: Export datasets
    echo -e "${CYAN}📤 Step 3: Exporting datasets...${NC}"
    docker-compose exec notebooks python /notebooks/src/scripts/export_features_dataset_parallel.py 2>&1 | tee -a "$LOG_FILE"
    
    # Step 4: Create balanced dataset
    echo -e "${CYAN}🎯 Step 4: Creating balanced dataset...${NC}"
    docker-compose exec notebooks python /notebooks/src/scripts/generate_combined_dataset.py 2>&1 | tee -a "$LOG_FILE"
    
fi

echo -e "${GREEN}🎉 Pipeline completed successfully!${NC}"
echo -e "${BLUE}📅 End time: $(date)${NC}"
echo -e "${BLUE}📋 Check logs: ${LOG_FILE}${NC}"

# Show final summary
echo -e "${CYAN}📊 Final Summary:${NC}"
docker-compose exec postgres psql -U chess_user -d chess_db -c "
    SELECT 'games' as table_name, COUNT(*) as count FROM games
    UNION ALL
    SELECT 'features' as table_name, COUNT(*) as count FROM features
    UNION ALL  
    SELECT 'analyzed_tacticals' as table_name, COUNT(*) as count FROM analyzed_tacticals;
" 2>/dev/null || echo "⚠️ Database verification skipped"

echo -e "${GREEN}✅ Check data/processed/ for the final balanced dataset${NC}"
