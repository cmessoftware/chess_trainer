#!/bin/bash
"""
🌙 OVERNIGHT ML PIPELINE EXECUTOR
==================================

This script runs the complete ML pipeline overnight to generate:
1. Regenerate database tables with Alembic
2. Import PGN games (from existing Parquet files)
3. Generate features + tactics (integrated process)
4. Export individual datasets by source
5. Create balanced combined dataset (150k optimal)

Configuration:
- Elite: 50k games (sample from 1.6M available)
- Fide: 50k games (sample from 2M available)  
- Novice: 25k games (from 122k available)
- Personal: 25k games (from 337k available)
- Total: 150k games - optimal for ML training

Usage:
    docker-compose exec notebooks /notebooks/overnight_ml_pipeline.sh
    
    # Or run specific steps:
    ./overnight_ml_pipeline.sh --step recreate-tables
    ./overnight_ml_pipeline.sh --step import-games
    ./overnight_ml_pipeline.sh --step generate-features
    ./overnight_ml_pipeline.sh --step export-datasets
    ./overnight_ml_pipeline.sh --step create-balanced-dataset
"""

set -e  # Exit on any error

# Colors for output
GREEN="\033[0;32m"
RED="\033[0;31m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
BLUE="\033[0;34m"
MAGENTA="\033[0;35m"
NC="\033[0m"

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="/notebooks/logs/overnight_$(date +%Y%m%d_%H%M%S)"
TOTAL_START_TIME=$(date +%s)

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_DIR/overnight_pipeline.log"
}

# Error handling
handle_error() {
    local exit_code=$?
    local line_number=$1
    log "${RED}❌ ERROR: Pipeline failed at line $line_number with exit code $exit_code${NC}"
    log "${RED}❌ Check logs in: $LOG_DIR${NC}"
    exit $exit_code
}

trap 'handle_error $LINENO' ERR

# Step timing
start_step() {
    STEP_START_TIME=$(date +%s)
    log "${CYAN}🚀 Starting: $1${NC}"
    log "${BLUE}📅 Time: $(date)${NC}"
}

end_step() {
    local step_end_time=$(date +%s)
    local step_duration=$((step_end_time - STEP_START_TIME))
    local hours=$((step_duration / 3600))
    local minutes=$(((step_duration % 3600) / 60))
    local seconds=$((step_duration % 60))
    
    log "${GREEN}✅ Completed: $1${NC}"
    log "${BLUE}⏱️  Duration: ${hours}h ${minutes}m ${seconds}s${NC}"
    log ""
}

# Step 1: Recreate database tables with Alembic
recreate_tables() {
    start_step "Database Tables Recreation"
    
    log "${CYAN}🔄 Dropping existing schema and recreating with Alembic...${NC}"
    
    # Connect to PostgreSQL and recreate schema
    docker-compose exec postgres psql -U chess_user -d chess_db -c "
        DROP SCHEMA IF EXISTS public CASCADE;
        CREATE SCHEMA public;
        GRANT ALL ON SCHEMA public TO chess_user;
        GRANT ALL ON SCHEMA public TO public;
    " 2>&1 | tee -a "$LOG_DIR/recreate_tables.log"
    
    # Run Alembic migration
    cd /notebooks
    alembic upgrade head 2>&1 | tee -a "$LOG_DIR/alembic_migration.log"
    
    # Verify tables
    docker-compose exec postgres psql -U chess_user -d chess_db -c "\dt" 2>&1 | tee -a "$LOG_DIR/verify_tables.log"
    
    end_step "Database Tables Recreation"
}

# Step 2: Import games from Parquet files
import_games() {
    start_step "Games Import from Parquet"
    
    log "${CYAN}🔄 Importing games from existing Parquet files...${NC}"
    
    # Create import script for games
    cat > /tmp/import_games_from_parquet.py << 'EOF'
import pandas as pd
import os
import sys
from pathlib import Path
from sqlalchemy import create_engine
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Database connection
DB_URL = os.environ.get("CHESS_TRAINER_DB_URL", "postgresql://chess_user:chess_pass@postgres:5432/chess_db")
engine = create_engine(DB_URL)

# Parquet files to import
parquet_files = [
    ("/notebooks/data/export/elite/elite_games.parquet", "elite"),
    ("/notebooks/data/export/fide/fide_games.parquet", "fide"),
    ("/notebooks/data/export/novice/novice_games.parquet", "novice"),
    ("/notebooks/data/export/personal/personal_games.parquet", "personal"),
    ("/notebooks/data/export/stockfish/stockfish_games.parquet", "stockfish")
]

total_imported = 0

for parquet_path, source in parquet_files:
    if os.path.exists(parquet_path):
        logger.info(f"📖 Loading {source} games from {parquet_path}")
        df = pd.read_parquet(parquet_path)
        
        # Ensure required columns
        if 'source' not in df.columns:
            df['source'] = source
        
        # Import in chunks
        chunk_size = 5000
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i + chunk_size]
            chunk.to_sql('games', engine, if_exists='append', index=False, method='multi')
            logger.info(f"   📊 {source}: {i + len(chunk):,}/{len(df):,} games imported")
        
        total_imported += len(df)
        logger.info(f"✅ {source}: {len(df):,} games imported")
    else:
        logger.warning(f"⚠️ File not found: {parquet_path}")

logger.info(f"🎉 Total games imported: {total_imported:,}")
EOF
    
    python /tmp/import_games_from_parquet.py 2>&1 | tee -a "$LOG_DIR/import_games.log"
    
    end_step "Games Import from Parquet"
}

# Step 3: Generate features with tactics (integrated)
generate_features() {
    start_step "Features + Tactics Generation"
    
    log "${CYAN}🔄 Generating features and tactical analysis...${NC}"
    
    # Run integrated feature generation by source with optimal limits
    sources=("elite" "fide" "novice" "personal")
    limits=(50000 50000 25000 25000)  # Optimal balanced limits
    
    for i in "${!sources[@]}"; do
        source="${sources[$i]}"
        limit="${limits[$i]}"
        
        log "${CYAN}🎯 Processing $source (limit: $limit games)...${NC}"
        
        python /notebooks/src/scripts/generate_features_with_tactics.py \
            --source "$source" \
            --max-games "$limit" \
            --workers 6 \
            --chunk-size 500 \
            2>&1 | tee -a "$LOG_DIR/features_${source}.log"
        
        log "${GREEN}✅ $source features completed${NC}"
    done
    
    end_step "Features + Tactics Generation"
}

# Step 4: Export datasets by source
export_datasets() {
    start_step "Dataset Export by Source"
    
    log "${CYAN}🔄 Exporting datasets by source...${NC}"
    
    python /notebooks/src/scripts/export_features_dataset_parallel.py 2>&1 | tee -a "$LOG_DIR/export_datasets.log"
    
    end_step "Dataset Export by Source"
}

# Step 5: Create balanced combined dataset
create_balanced_dataset() {
    start_step "Balanced Dataset Creation"
    
    log "${CYAN}🔄 Creating optimally balanced dataset (150k games)...${NC}"
    log "${CYAN}   - Elite: 50k games${NC}"
    log "${CYAN}   - Fide: 50k games${NC}"
    log "${CYAN}   - Novice: 25k games${NC}"
    log "${CYAN}   - Personal: 25k games${NC}"
    
    python /notebooks/src/scripts/generate_combined_dataset.py 2>&1 | tee -a "$LOG_DIR/balanced_dataset.log"
    
    end_step "Balanced Dataset Creation"
}

# Full pipeline execution
run_full_pipeline() {
    log "${MAGENTA}🌙 OVERNIGHT ML PIPELINE STARTED${NC}"
    log "${BLUE}📅 Start time: $(date)${NC}"
    log "${BLUE}📂 Logs directory: $LOG_DIR${NC}"
    log ""
    
    # Execute all steps
    recreate_tables
    import_games
    generate_features
    export_datasets
    create_balanced_dataset
    
    # Final summary
    local total_end_time=$(date +%s)
    local total_duration=$((total_end_time - TOTAL_START_TIME))
    local total_hours=$((total_duration / 3600))
    local total_minutes=$(((total_duration % 3600) / 60))
    local total_seconds=$((total_duration % 60))
    
    log "${MAGENTA}🎉 OVERNIGHT PIPELINE COMPLETED SUCCESSFULLY!${NC}"
    log "${BLUE}📅 End time: $(date)${NC}"
    log "${BLUE}⏱️  Total duration: ${total_hours}h ${total_minutes}m ${total_seconds}s${NC}"
    log "${BLUE}📂 All logs saved in: $LOG_DIR${NC}"
    
    # Verify final results
    log "${CYAN}📊 Final verification:${NC}"
    docker-compose exec postgres psql -U chess_user -d chess_db -c "
        SELECT 'games' as table_name, COUNT(*) as count FROM games
        UNION ALL
        SELECT 'features' as table_name, COUNT(*) as count FROM features
        UNION ALL  
        SELECT 'analyzed_tacticals' as table_name, COUNT(*) as count FROM analyzed_tacticals;
    " 2>&1 | tee -a "$LOG_DIR/final_verification.log"
    
    log "${GREEN}✅ Check data/processed/ for the balanced dataset: training_dataset_balanced.parquet${NC}"
}

# Parse command line arguments
case "${1:-}" in
    --step)
        case "${2:-}" in
            recreate-tables)
                recreate_tables
                ;;
            import-games)
                import_games
                ;;
            generate-features)
                generate_features
                ;;
            export-datasets)
                export_datasets
                ;;
            create-balanced-dataset)
                create_balanced_dataset
                ;;
            *)
                echo "❌ Unknown step: ${2:-}"
                echo "Available steps: recreate-tables, import-games, generate-features, export-datasets, create-balanced-dataset"
                exit 1
                ;;
        esac
        ;;
    "")
        # Run full pipeline
        run_full_pipeline
        ;;
    *)
        echo "❌ Unknown option: $1"
        echo "Usage: $0 [--step STEP_NAME]"
        exit 1
        ;;
esac
