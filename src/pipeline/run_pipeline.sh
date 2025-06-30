#!/bin/bash
# Usage: run_pipeline.sh {all | from <step> | auto_tag | analyze_tactics | generate_exercises | generate_features [args]}
# Examples:
# ./run_pipeline.sh all
# ./run_pipeline.sh generate_exercises
# ./run_pipeline.sh from analyze_tactics
# ./run_pipeline.sh analyze_tactics --source lichess --max-games 1000
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
export STOCKFISH_PATH=/usr/games/stockfish
export PGN_PATH=/app/src/data/games

LOG_DIR=/app/src/logs
mkdir -p "$LOG_DIR"

# Validations
[ -z "$STOCKFISH_PATH" ] && { echo -e "${RED}❌ STOCKFISH_PATH not defined${NC}"; exit 1; }
[ -z "$PGN_PATH" ] && { echo -e "${RED}❌ PGN_PATH not defined${NC}"; exit 1; }

# Check if the PGN_PATH directory exists
cd /app/src || exit 1


# Step runner
run_step() {
  STEP_NAME="$1"
  STEP_FUNC="$2"
  shift 2
  LOG_FILE="$LOG_DIR/${STEP_NAME}.log"

  read -p "$(echo -e "${YELLOW}❓ ¿Quieres ejecutar el paso: ${CYAN}${STEP_NAME}${NC}? (y/n): ")" confirm
  if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏭️  Paso '${STEP_NAME}' saltado por el usuario.${NC}"
    return 0
  fi

  echo -e "${CYAN}▶ Ejecutando $STEP_NAME...${NC}"
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
    return $STATUS
  fi

  END=$(date +%s)
  DURATION=$((END - START))
  echo -e "${GREEN}✔ $STEP_NAME completado en $DURATION segundos.${NC}"
  return 0
}

# Helper to recorrer lista de pasos y preguntar por cada uno si se quiere ejecutar
run_steps_interactive() {
  local steps=("$@")
  for step in "${steps[@]}"; do
    run_step "$step" "$step"
    local status=$?
    if [ $status -ne 0 ] && [ $status -ne 2 ]; then
      echo -e "${RED}❌ Error ejecutando el paso '${step}'. Abortando.${NC}"
      exit $status
    fi
  done
}

# Step implementations

# Clean analysis-related tables
clean_analysis_data() {
  echo -e "${CYAN}🧹 Cleaning analysis-related tables...${NC}"
  python db/truncate_analysis_data.py
  echo -e "${GREEN}✔ Analysis tables cleaned (features, processed_features, tactics).${NC}"
}

# Delete all data from the database
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

create_issues() {
  echo -e "${CYAN}📝 Creating GitHub issues from TODOs...${NC}"
  python /app/src/tools/create_issues.py 
  if [ $? -eq 0 ]; then
     echo "✅ Issues creados correctamente."
  else
      echo "❌ Error al extraer los TODOs."
      exit 1
  fi
}

import_pgns() {
  echo -e "${CYAN}🔍 Checking if there are new games to import...${NC}"
  python scripts/import_pgns_parallel.py --input "$PGN_PATH"
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
  
  # Parse additional arguments for potential pass-through
  local pass_through_args=()
  local use_source_batching=true
  
  while [[ $# -gt 0 ]]; do
    case $1 in
      --source)
        # If a specific source is provided, disable batching and use direct processing
        use_source_batching=false
        pass_through_args+=(--source "$2")
        shift 2
        ;;
      --max-games)
        # If max-games is provided with source batching disabled, pass it through
        if [ "$use_source_batching" = false ]; then
          pass_through_args+=(--max-games "$2")
        fi
        shift 2
        ;;
      *)
        pass_through_args+=("$1")
        shift
        ;;
    esac
  done
  
  # If source batching is disabled (specific source provided), use direct processing
  if [ "$use_source_batching" = false ]; then
    echo -e "${CYAN}🎯 Processing with provided parameters...${NC}"
    python /app/src/scripts/analyze_games_tactics_parallel.py "${pass_through_args[@]}"
    return $?
  fi
  
  # Source batching mode - process each source sequentially
  echo -e "${CYAN}🔄 Running analyze_tactics sequentially by source with batches of 10,000 games...${NC}"
  
  # Get list of available sources from the database
  echo -e "${CYAN}📊 Getting available sources from database...${NC}"
  local sources=($(python pipeline/pipeline_helper.py --operation get-sources --format space-separated 2>/dev/null))
  
  if [ ${#sources[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No sources found in database, running without source filter...${NC}"
    python /app/src/scripts/analyze_games_tactics_parallel.py --max-games 10000 "${pass_through_args[@]}"
    return $?
  fi
  
  echo -e "${GREEN}📋 Found sources: ${sources[*]}${NC}"
  
  # Process each source sequentially
  for source in "${sources[@]}"; do
    echo -e "${CYAN}🎯 Processing source: ${source}${NC}"
    
    # Get total games for this source that haven't been analyzed for tactics
    local total_games=$(python pipeline/pipeline_helper.py --operation count-unanalyzed --source "$source")
    
    echo -e "${CYAN}📈 Total unanalyzed games for source '$source': $total_games${NC}"
    
    if [ "$total_games" -eq 0 ]; then
      echo -e "${YELLOW}⏭️  No unanalyzed games found for source '$source', skipping...${NC}"
      continue
    fi
    
    # Calculate number of batches needed
    local batch_size=10000
    local batches=$(( (total_games + batch_size - 1) / batch_size ))
    
    echo -e "${CYAN}🔄 Will process $batches batch(es) of $batch_size games each for source '$source'${NC}"
    
    # Process batches for this source
    for ((batch=1; batch<=batches; batch++)); do
      echo -e "${CYAN}⚙️  Processing batch $batch/$batches for source '$source'...${NC}"
      
      local start_time=$(date +%s)
      
      python /app/src/scripts/analyze_games_tactics_parallel.py \
        --source "$source" \
        --max-games "$batch_size" \
        --offset $(( (batch - 1) * batch_size )) \
        "${pass_through_args[@]}"
      
      local exit_code=$?
      local end_time=$(date +%s)
      local duration=$((end_time - start_time))
      
      if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Batch $batch/$batches completed successfully for source '$source' in ${duration}s${NC}"
      else
        echo -e "${RED}❌ Batch $batch/$batches failed for source '$source' (exit code: $exit_code)${NC}"
        return $exit_code
      fi
      
      # Small delay between batches to prevent overwhelming the system
      sleep 2
    done
    
    echo -e "${GREEN}🎉 Completed processing all batches for source '$source'${NC}"
  done
  
  echo -e "${GREEN}🏁 Tactical analysis completed for all sources!${NC}"
}

generate_exercises() {
  echo "${CYAN} 🧹 Clearing generate_exercises logs"
  rm -rf /app/src/logs/generate_features*
  python /app/src/scripts/generate_exercises_from_elite.py
}

generate_features() {
  echo "${CYAN} 🧹 Clearing generate_features logs"
  rm -rf /app/src/logs/generate_features*
  
  echo -e "${CYAN}🔄 Running generate_features sequentially by source with batches of 10,000 games...${NC}"
  
  # Get list of available sources from the database
  echo -e "${CYAN}📊 Getting available sources from database...${NC}"
  local sources=($(python pipeline/pipeline_helper.py --operation get-sources --format space-separated))
  
  if [ ${#sources[@]} -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No sources found in database, running without source filter...${NC}"
    python scripts/generate_features_parallel.py --max-games 10000 "$@"
    return $?
  fi
  
  echo -e "${GREEN}📋 Found sources: ${sources[*]}${NC}"
  
  # Process each source sequentially
  for source in "${sources[@]}"; do
    echo -e "${CYAN}🎯 Processing source: ${source}${NC}"
    
    # Get total games for this source
    local total_games=$(python pipeline/pipeline_helper.py --operation count-games --source "$source")
    
    echo -e "${CYAN}📈 Total games for source '$source': $total_games${NC}"
    
    if [ "$total_games" -eq 0 ]; then
      echo -e "${YELLOW}⏭️  No games found for source '$source', skipping...${NC}"
      continue
    fi
    
    # Calculate number of batches needed
    local batch_size=10000
    local batches=$(( (total_games + batch_size - 1) / batch_size ))
    
    echo -e "${CYAN}🔄 Will process $batches batch(es) of $batch_size games each for source '$source'${NC}"
    
    # Process batches for this source
    for ((batch=1; batch<=batches; batch++)); do
      echo -e "${CYAN}⚙️  Processing batch $batch/$batches for source '$source'...${NC}"
      
      local start_time=$(date +%s)
      
      python scripts/generate_features_parallel.py \
        --source "$source" \
        --max-games "$batch_size" \
        --offset $(( (batch - 1) * batch_size )) \
        "$@"
      
      local exit_code=$?
      local end_time=$(date +%s)
      local duration=$((end_time - start_time))
      
      if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✅ Batch $batch/$batches completed successfully for source '$source' in ${duration}s${NC}"
      else
        echo -e "${RED}❌ Batch $batch/$batches failed for source '$source' (exit code: $exit_code)${NC}"
        return $exit_code
      fi
      
      # Small delay between batches to prevent overwhelming the system
      sleep 2
    done
    
    echo -e "${GREEN}🎉 Completed processing all batches for source '$source'${NC}"
  done
  
  echo -e "${GREEN}🏁 Feature generation completed for all sources!${NC}"
}

clean_db() {
  python db/truncate_postgres_tables.py
}

export_dataset() {
  python /app/src/scripts/export_features_dataset_parallel.py
}

get_random_games() {
  echo -e "${CYAN}📥 Importing random games from remote servers...${NC}"
  # python scripts/generate_pgn_from_chess_servers.py "$@"
  # Example usage:
  python /app/src/scripts/fetch_lichess_intermediate_games.py 
  # Validate required parameters for generate_pgn_from_chess_servers.py
}

get_games() {
  echo -e "${CYAN}📥 Importing new games from remote servers...${NC}"
  # python scripts/generate_pgn_from_chess_servers.py "$@"
  # Example usage:
  python /app/src/scripts/download_games_parallel.py --server chess.com --users cmess4401 cmess1315 --since 2008-01-01
  # Validate required parameters for generate_pgn_from_chess_servers.py
  #TODO: Uncomment when ready9  ]
  # if [ $# -lt 2 ]; then
  #   echo -e "${YELLOW}Usage:${NC} $0 get_games <server> <username> [options]"
  #   echo -e "${YELLOW}Example:${NC} $0 get_games lichess.org myuser --max-games 10"
  #   exit 1
  # fi
  echo -e "${GREEN}✔ Games imported successfully.${NC}"
}

inspect_pgn() {
  echo -e "${CYAN}🔍 Inspecting PGN files...${NC}"
  python /app/src/scripts/inspect_pgn.py --output "$PGN_PATH" 
  echo -e "${GREEN}✔ PGN inspection completed.${NC}"
}

inspect_pgn_zip() {
  echo -e "${CYAN}🔍 Inspecting PGN files...${NC}"
  python /app/src/scripts/inspect_pgn_cli.py "$@"
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
  python /app/src/scripts/init_db.py
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
  local steps=("init_db" "import_pgns" "generate_features" "analyze_tactics" "export_dataset" "generate_exercises" "get_random_games")
  local upto_index=-1

  for i in "${!steps[@]}"; do
    if [ "${steps[$i]}" = "$upto_step" ]; then
      upto_index=$i
      break
    fi
  done

  if [ $upto_index -eq -1 ]; then
    echo -e "${RED}❌ Step '$upto_step' not found in pipeline.${NC}"
    return 1
  fi

  local selected_steps=("${steps[@]:0:upto_index+1}")
  run_steps_interactive "${selected_steps[@]}"
}

# Full pipeline
run_all() { 
  run_step init_db init_db
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'init_db' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step clean_cache clean_cache
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'clean_cache' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step get_games get_games
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'get_games' failed. Stopping pipeline.${NC}"; exit 1; }

  run_step import_pgns import_pgns  
  [ $? -ne 0 ] && { echo -e "${RED}❌ Step 'import_pgns' failed. Stopping pipeline.${NC}"; exit 1; }

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
  for step in auto_tag analyze_tactics generate_exercises generate_features export_dataset clean_db import_pgns init_db clean_cache clean_games inspect_pgn_zip check_db run_upto clean_analysis_data get_random_games;  do
    if [ "$found" -eq 1 ]; then run_step "$step" "$step"; fi
    if [ "$step" = "$1" ]; then found=1; run_step "$step" "$step"; fi
  done
}

run_interactive_pipeline() {
  # Lista de pasos que se desean ejecutar interactivamente
  local steps=("init_db" "clean_cache" "get_games" "import_pgns" "inspect_pgn" "generate_features" "analyze_tactics" "export_dataset" "generate_exercises" "clean_analysis_data" "clean_games" "inspect_pgn_zip" "check_db" "run_upto" "create_issues")

  echo -e "${CYAN}🧪 Modo interactivo: Ejecutar pasos del pipeline uno por uno${NC}"
  run_steps_interactive "${steps[@]}"
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
  auto_tag|analyze_tactics|generate_exercises|generate_features|clean_db|export_dataset|import_pgns|init_db|clean_cache|get_games|inspect_pgn|clean_games|inspect_pgn_zip|check_db|run_upto|clean_analysis_data|create_issues|get_random_games)
    STEP="$1"
    shift
    run_step "$STEP" "$STEP" "$@"
    ;;
  interactive)
    run_interactive_pipeline
    ;;
  *)
    echo -e "${YELLOW}Usage:${NC} $0 {all | from <step> | auto_tag | analyze_tactics | generate_exercises | generate_features [args] | \
clean_db | export_dataset | import_pgns | init_db | clean_cache | get_games | inspect_pgn | clean_games| inspect_pgn_zip| check_db| run_upto | clean_analysis_data|create_issues| get_random_games}"
    exit 1
    ;;
esac
