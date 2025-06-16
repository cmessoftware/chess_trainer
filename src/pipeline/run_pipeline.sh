#!/bin/bash
# Usage: run_pipeline.sh {all | from <step> | auto_tag | analyze_tactics | generate_exercises | generate_features [args]}
# Examples:
# ./run_pipeline.sh all
# ./run_pipeline.sh generate_exercises
# ./run_pipeline.sh from analyze_tactics
# ./run_pipeline.sh generate_features --max-games 5

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
export STOCKFISH_PATH=/usr/local/bin/stockfish
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
    STATUS=$?
    if [ $STATUS -eq 0 ]; then
      echo "✅ Finished successfully"
    else
      echo "❌ Step failed with exit code $STATUS"
    fi
    exit $STATUS
  } 2>&1 | tee "$LOG_FILE"
  STATUS=${PIPESTATUS[0]}
  if [ $STATUS -ne 0 ]; then
    echo -e "${RED}❌ $STEP_NAME failed. Check log: $LOG_FILE${NC}"
    exit $STATUS
  fi

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
  echo -e "${CYAN}🔍 Checking if there are new games to import...${NC}"
  python scripts/import_games_parallel.py --input "$PGN_PATH"
  if [ $? -eq 0 ]; then
    echo -e "${GREEN}✔ New games imported successfully.${NC}"
  else
    echo -e "${RED}❌ Error importing new games.${NC}"
    exit 1
  fi
}

auto_tag() {
  python scripts/auto_tag_games.py
}

analyze_tactics() {
  echo -e "${CYAN}🔍 Analyzing tactics in games...${NC}"
  echo -e "${YELLOW}This step can take a long time depending on the number of games.${NC}"
  echo "${CYAN} 🧹 Clearing analized_tacticals logs"
  rm -rf /app/src/logs/analized_tacticals*
  python scripts/analyze_games_tactics_parallel.py
}

generate_exercises() {
  echo "${CYAN} 🧹 Clearing generate_exercises logs"
  rm -rf /app/src/logs/generate_features*
  python scripts/generate_exercises_from_elite.py
}

generate_features() {
  echo "${CYAN} 🧹 Clearing generate_features logs"
  rm -rf /app/src/logs/generate_features*
  python scripts/generate_features_parallel.py \
    "$@"
}

clean_db() {
  python db/truncate_postgres_tables.py
}

export_dataset() {
  python scripts/export_features_dataset.py
}

get_games() {
  echo -e "${CYAN}📥 Importing new games from remote servers...${NC}"
  # python scripts/generate_pgn_from_chess_servers.py "$@"
  # Example usage:
  python scripts/generate_pgn_from_chess_servers.py --server lichess.org --users cmess4401 cmess1315 --since 2010-01-01
  # Validate required parameters for generate_pgn_from_chess_servers.py
  #TODO: Uncomment when ready
  # if [ $# -lt 2 ]; then
  #   echo -e "${YELLOW}Usage:${NC} $0 get_games <server> <username> [options]"
  #   echo -e "${YELLOW}Example:${NC} $0 get_games lichess.org myuser --max-games 10"
  #   exit 1
  # fi
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
  read -p "$(echo -e "${YELLOW}❓ Do you want to clean ALL pgn files? If yes, you must import games again (get_games command) (y/n): ${NC}")" confirm
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

run_upto() {
  local upto_step="$1"
  shift
  echo -e "${CYAN}▶ Running pipeline up to and including step: $upto_step...${NC}"

  # Define the steps in order
  local steps=("init_db" "clean_db" "import_games" "inspect_pgn" "generate_features" "analyze_tactics" "export_dataset" "generate_exercises") 
  local found=0

  for step in "${steps[@]}"; do
    read -p "$(echo -e "${YELLOW}❓ Do you want to continue to the next step: ${CYAN}${step}${NC}? (y/n): ")" confirm
    if [ $? -ne 0 ]; then
      echo -e "${RED}❌ Step '$step' failed. Stopping pipeline.${NC}"
      exit 1
    fi
    run_step "$step" "$step" "$@"
    if [ "$step" = "$upto_step" ]; then
      found=1
      echo -e "${GREEN}✔ Step '$step' completed. Stopping as requested.${NC}"
      break
    fi
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
      echo -e "${RED}⏹ Pipeline execution stopped by user after '$step'.${NC}"
      exit 0
    fi
  done

  if [ $found -eq 0 ]; then
    echo -e "${RED}❌ Step '$upto_step' not found in pipeline.${NC}"
    return 1
  fi
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

  run_step generate_features generate_features
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'generate_features' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step analyze_tactics analyze_tactics
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'analyze_tactics' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step export_dataset export_dataset 
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'export_dataset' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step generate_exercises generate_exercises
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'generate_exercises' failed. Stopping pipeline.${NC}"; exit 1; }

  
  echo -e "${GREEN}🎉 Pipeline executed successfully.${NC}"
}

# From a specific step
run_from_step() {
  local found=0
  for step in auto_tag analyze_tactics generate_exercises generate_features export_dataset clean_db import_games init_db clean_cache clean_games inspect_pgn_zip check_db run_upto;  do
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
  auto_tag|analyze_tactics|generate_exercises|generate_features|clean_db|export_dataset|import_games|init_db|clean_cache|get_games|inspect_pgn|clean_games|inspect_pgn_zip|check_db|run_upto)
    STEP="$1"
    shift
    run_step "$STEP" "$STEP" "$@"
    ;;
  *)
    echo -e "${YELLOW}Usage:${NC} $0 {all | from <step> | auto_tag | analyze_tactics | generate_exercises | generate_features [args] | \
clean_db | export_dataset | import_games | init_db | clean_cache | get_games | inspect_pgn | clean_games| inspect_pgn_zip| check_db}"
    exit 1
    ;;
esac
