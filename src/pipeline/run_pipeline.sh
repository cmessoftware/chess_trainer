#!/bin/bash
# Usage: run_pipeline.sh {all | from <step> | auto_tag | analyze_game_tactics | generate_exercises | generate_dataset [args]}
# Examples:
# ./run_pipeline.sh all
# ./run_pipeline.sh generate_exercises
# ./run_pipeline.sh from analyze_game_tactics
# ./run_pipeline.sh generate_dataset --max-games 5

set -e

# Colors
GREEN="\033[0;32m"
RED="\033[0;31m"
CYAN="\033[0;36m"
YELLOW="\033[1;33m"
NC="\033[0m"

# Paths
export PYTHONPATH=/app/src
export CHESS_TRAINER_DB=/app/src/data/chess_trainer.db
export STOCKFISH_PATH=/usr/games/stockfish
export PGN_PATH=/app/src/data/games

LOG_DIR=/app/src/logs
mkdir -p "$LOG_DIR"

# Validations
[ -z "$CHESS_TRAINER_DB" ] && { echo -e "${RED}❌ CHESS_TRAINER_DB not defined${NC}"; exit 1; }
[ -z "$STOCKFISH_PATH" ] && { echo -e "${RED}❌ STOCKFISH_PATH not defined${NC}"; exit 1; }
[ -z "$PGN_PATH" ] && { echo -e "${RED}❌ PGN_PATH not defined${NC}"; exit 1; }

# Create DB if missing
if [ ! -f "$CHESS_TRAINER_DB" ]; then
  echo -e "${YELLOW}🛠️ Creating database...${NC}"
  sqlite3 "$CHESS_TRAINER_DB" "VACUUM;"
  echo -e "${GREEN}✔ Database created at $CHESS_TRAINER_DB${NC}"
fi

# Ensure schema
echo -e "${CYAN}🛠 Checking database schema...${NC}"
python /app/src/scripts/init_db.py

# Check for 'games' table
TABLE_EXISTS=$(sqlite3 "$CHESS_TRAINER_DB" "SELECT name FROM sqlite_master WHERE type='table' AND name='games';")
[ "$TABLE_EXISTS" != "games" ] && {
  echo -e "${RED}❌ 'games' table is missing.${NC}"
  sqlite3 "$CHESS_TRAINER_DB" ".tables"
  exit 1
}

cd /app/src || exit 1

# Step runner
run_step() {
  STEP_NAME="$1"
  STEP_FUNC="$2"
  shift 2
  LOG_FILE="$LOG_DIR/${STEP_NAME}.log"

  echo -e "${CYAN}▶ Running $STEP_NAME...${NC}"
  START=$(date +%s)

  {
    echo "🕒 $(date) - Starting step: $STEP_NAME"
    $STEP_FUNC "$@"
    echo "✅ Finished successfully"
  } 2>&1 | tee "$LOG_FILE"

  END=$(date +%s)
  DURATION=$((END - START))
  echo -e "${GREEN}✔ $STEP_NAME completed in $DURATION seconds.${NC}"
}

# Step implementations

import_new_games() {
  echo -e "${CYAN}🔍 Verificando si hay partidas nuevas para importar...${NC}"
  python scripts/save_games_to_db.py --input "$PGN_PATH"
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✔ Nuevas partidas importadas correctamente.${NC}"
  else
    echo -e "${RED}❌ Error al importar nuevas partidas.${NC}"
    exit 1
  fi
 
}

auto_tag() {
  python scripts/auto_tag_games.py
}

analyze_game_tactics() {
  python scripts/analyze_game_tactics.py
}

generate_exercises() {
  python scripts/generate_exercises_from_elite.py
}

generate_dataset() {
  python scripts/generate_full_report.py \
    --input-dir "$PGN_PATH" \
    --output /app/src/data/training_dataset.csv \
    "$@"
}

clean_db() {
  python scripts/clean_db.py
}

export_dataset() {
  python scripts/export_dataset_to_csv.py
}

init_db() {
  echo -e "${CYAN}🛠️ Initializing database schema...${NC}"
  python scripts/init_db.py
  echo -e "${GREEN}✔ Database schema initialized.${NC}"
}

clear_cache() {
  echo -e "${CYAN}🧹 Clearing Python cache...${NC}"
  cd /app || exit 1
  find . -type d -name "__pycache__" -exec rm -rf {} +
  find . -type f -name "*.pyc" -delete
  echo -e "${GREEN}✔ Cache cleared.${NC}"
  cd /app/src/pipeline || exit 1
}

# Full pipeline
run_all() {
  run_step init_db init_db
  run_step import_new_games import_new_games  
  run_step auto_tag auto_tag
  run_step generate_dataset generate_dataset
  run_step analyze_game_tactics analyze_game_tactics
  run_step generate_exercises generate_exercises
  run_step export_dataset export_dataset 
  echo -e "${GREEN}🎉 Pipeline executed successfully.${NC}"
}

# From a specific step
run_from_step() {
  local found=0
  for step in auto_tag analyze_game_tactics generate_exercises generate_dataset export_dataset clean_db import_new_games init_db clear_cache;  do
    if [ "$found" -eq 1 ]; then run_step "$step" "$step"; fi
    if [ "$step" = "$1" ]; then found=1; run_step "$step" "$step"; fi
  done
}

# Dispatcher
case "$1" in
  all)
    run_all
    ;;
  from)
    shift
    run_from_step "$1"
    ;;
  auto_tag|analyze_game_tactics|generate_exercises|generate_dataset|clean_db|export_dataset|import_new_games|init_db|clear_cache)
    STEP="$1"
    shift
    run_step "$STEP" "$STEP" "$@"
    ;;
  *)
    echo -e "${YELLOW}Usage:${NC} $0 {all | from <step> | auto_tag | analyze_game_tactics | generate_exercises | generate_dataset [args] | \
clean_db | export_dataset | import_new_games | init_db | clear_cache}"
    exit 1
    ;;
esac
