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


check_db() {
  echo -e "${CYAN}🔍 Checking database connection...${NC}"
  # Ensure schema
  echo -e "${CYAN}🛠 Checking database schema...${NC}"
  python /app/src/scripts/init_db.py
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✔ Database connection is OK.${NC}"
  else
    echo -e "${RED}❌ Database connection failed.${NC}"
    exit 1
  fi
}


import_games() {
  echo -e "${CYAN}🔍 Verificando si hay partidas nuevas para importar...${NC}"
  python scripts/import_games.py --input "$PGN_PATH"
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
  python scripts/analyze_game_tactics_parallel.py
}

generate_exercises() {
  python scripts/generate_exercises_from_elite.py
}

generate_dataset() {
  python scripts/generate_dataset.py \
    --input-dir "$PGN_PATH" \
    --output /app/src/data/training_dataset.csv \
    "$@"
}

clean_db() {
  python db/truncate_postgres_tables.py
}

#TODO: No migra tags y score_diff a CSV.
export_dataset() {
  python scripts/export_dataset_to_csv.py
}

get_games() {
  echo -e "${CYAN}📥 Importing new games from remotes servers...${NC}"
  # python scripts/generate_pgn_from_chess_servers.py "$@"
  # Example usage:
  python scripts/generate_pgn_from_chess_servers.py --server lichess.org --users cmess4401 cmess1315 --since 2025-01-01
  # Validate required parameters for generate_pgn_from_chees_servers.py
  if [ $# -lt 2 ]; then
    echo -e "${YELLOW}Usage:${NC} $0 get_games <server> <username> [options]"
    echo -e "${YELLOW}Example:${NC} $0 get_games lichess myuser --max-games 10"
    exit 1
  fi
  echo -e "${GREEN}✔ Games imported successfully.${NC}"
}

inspect_pgn() {
  echo -e "${CYAN}🔍 Inspecting PGN files...${NC}"
  python scripts/inspect_pgn.py --output "$PGN_PATH" 
  echo -e "${GREEN}✔ PGN inspection completed.${NC}"
}

inspect_pgn_zip() {
  echo -e "${CYAN}🔍 Inspecting PGN files...${NC}"
  python scripts/inspect_pgn_cli.py "$@"
  echo -e "${GREEN}✔ PGN inspection completed.${NC}"
}

clean_games() {
  echo -e "${CYAN}🧹 Cleaning PGN files...${NC}"
  read -p "$(echo -e "${YELLOW}❓ Do you want clean ALL pgn files? If yes do you must import games again (get_games command) (y/n): ${NC}")" confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo -e "${RED}⏹ Pipeline execution stopped by user.${NC}"
    exit 0
  fi
  rm -r "$PGN_PATH"
  echo -e "${GREEN}✔ PGN files cleaned.${NC}"
}

init_db() {
  echo -e "${CYAN}🛠️ Initializing database schema...${NC}"
  python scripts/init_db.py
  echo -e "${GREEN}✔ Database schema initialized.${NC}"
}

clean_cache() {
  echo -e "${CYAN}🧹 Clearing Python cache...${NC}"
  cd /app || exit 1
  find . -type d -name "__pycache__" -exec rm -rf {} +
  find . -type f -name "*.pyc" -delete
  echo -e "${GREEN}✔ Cache cleared.${NC}"
  cd /app/src/pipeline || exit 1
}

run_sqlite_web() {
  echo -e "${CYAN}🌐 Starting SQLite Web...${NC}"
  python -m sqlite_web /app/src/data/chess_trainer.db -H 0.0.0.0 -p 8081
}

# Full pipeline
run_all() { 
  run_step init_db init_db
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'init_db' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step clean_cache clean_cache
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'clean_cache' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step get_games get_games
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'get_games' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step import_games import_games  
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'import_games' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step inspect_pgn inspect_pgn
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'inspect_pgn' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step auto_tag auto_tag
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'auto_tag' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step generate_dataset generate_dataset
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'generate_dataset' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step analyze_game_tactics analyze_game_tactics
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'analyze_game_tactics' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step generate_exercises generate_exercises
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'generate_exercises' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step export_dataset export_dataset 
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'export_dataset' failed. Stopping pipeline.${NC}"; exit 1; }

  read -p "$(echo -e "${YELLOW}❓ run sqlite_web? (y/n): ${NC}")" confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo -e "${RED}⏹ Pipeline execution stopped by user.${NC}"
    exit 0
  fi
  run_step run_sqlite_web run_sqlite_web
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'run_sqlite_web' failed. Stopping pipeline.${NC}"; exit 1; }

  echo -e "${GREEN}🎉 Pipeline executed successfully.${NC}"
}

# From a specific step
run_from_step() {
  local found=0
  for step in auto_tag analyze_game_tactics generate_exercises generate_dataset export_dataset clean_db import_games init_db clean_cache run_sqlite_web clean_games inspect_pgn_zip check_db;  do
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
  auto_tag|analyze_game_tactics|generate_exercises|generate_dataset|clean_db|export_dataset|import_games|init_db|clean_cache|get_games|inspect_pgn|run_sqlite_web|clean_games|inspect_pgn_zip|check_db)
    STEP="$1"
    shift
    run_step "$STEP" "$STEP" "$@"
    ;;
  *)
    echo -e "${YELLOW}Usage:${NC} $0 {all | from <step> | auto_tag | analyze_game_tactics | generate_exercises | generate_dataset [args] | \
clean_db | export_dataset | import_games | init_db | clean_cache | get_games | inspect_pgn | run_sqlite_web|clean_games| inspect_pgn_zip| check_db}"
    exit 1
    ;;
esac
