#!/bin/bash

# MLflow commands integrated with PostgreSQL
# This script runs inside Docker containers

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

function initialize_mlflow() {
    echo -e "${BLUE}🔄 Inicializando MLflow con PostgreSQL...${NC}"
    
    # Verify database configuration
    python /mlflow/src/ml/init_mlflow_db.py
    
    # Open MLflow UI (container context)
    echo -e "${BLUE}🌐 MLflow UI disponible en http://localhost:5000${NC}"
    
    echo -e "${GREEN}✅ MLflow inicializado correctamente${NC}"
}

function start_mlflow_with_postgres() {
    echo -e "${BLUE}🚀 Iniciando MLflow con PostgreSQL...${NC}"
    
    # Initialize database if needed
    python /mlflow/src/ml/init_mlflow_db.py
    
    # Start MLflow server
    mlflow server \
        --backend-store-uri postgresql://mlflow:mlflow@postgres:5432/mlflow \
        --default-artifact-root /mlflow/artifacts \
        --host 0.0.0.0 \
        --port 5000 &
    
    # Wait for service to be available
    sleep 5
    
    # Check if service is running
    if pgrep -f "mlflow server" > /dev/null; then
        echo -e "${GREEN}✅ MLflow está corriendo con PostgreSQL${NC}"
        return 0
    else
        echo -e "${RED}❌ Error iniciando MLflow${NC}"
        return 1
    fi
}

function run_ml_experiment() {
    local experiment_name=${1:-"chess_error_prediction"}
    local model_type=${2:-"RandomForest"}
    
    echo -e "${BLUE}🧪 Ejecutando experimento $experiment_name con $model_type...${NC}"
    
    # Set environment variables
    export EXPERIMENT_NAME="$experiment_name"
    export MODEL_TYPE="$model_type"
    
    # Run experiment
    python /notebooks/src/ml/train_error_model.py
    
    echo -e "${GREEN}✅ Experimento completado${NC}"
    echo -e "${BLUE}🌐 Revisa resultados en http://localhost:5000${NC}"
}

function cleanup_mlflow_sqlite() {
    echo -e "${BLUE}🧹 Verificando y limpiando archivo SQLite de MLflow...${NC}"
    
    # Run cleanup script
    python /mlflow/src/ml/cleanup_mlflow_sqlite.py
    
    echo -e "${GREEN}✅ Verificación y limpieza completada${NC}"
}

function train_chess_error_model() {
    echo -e "${BLUE}🎯 Entrenando modelo de predicción de errores...${NC}"
    
    # Run training
    python /mlflow/src/ml/chess_error_predictor.py
    
    echo -e "${GREEN}✅ Entrenamiento completado. Revisa MLflow UI para ver métricas${NC}"
    echo -e "${BLUE}🌐 MLflow UI: http://localhost:5000${NC}"
}

function test_chess_prediction() {
    local fen=${1:-"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"}
    local move=${2:-"e2e4"}
    
    echo -e "${BLUE}🔮 Probando predicción para jugada $move...${NC}"
    
    # Set environment variables
    export TEST_FEN="$fen"
    export TEST_MOVE="$move"
    
    # Run prediction
    python /mlflow/src/ml/realtime_predictor.py
    
    echo -e "${GREEN}✅ Predicción completada${NC}"
}

function analyze_chess_datasets() {
    echo -e "${BLUE}🔬 Iniciando análisis ML de datasets reales...${NC}"
    echo -e "${YELLOW}⚠️ MODO NO DESTRUCTIVO: Solo lectura de datos existentes${NC}"
    
    echo -e "${BLUE}🚀 Ejecutando análisis comparativo...${NC}"
    python /notebooks/analyze_real_datasets.py
    
    echo -e "${GREEN}✅ Análisis completado. Revisa los resultados en el log.${NC}"
}

function test_elo_standardization() {
    echo -e "${BLUE}📊 Ejecutando pruebas de estandarización ELO...${NC}"
    
    # Run tests
    python /notebooks/test_elo_standardization.py
    
    echo -e "${GREEN}✅ Pruebas de ELO completadas${NC}"
}

function compare_player_levels() {
    echo -e "${BLUE}🎯 Comparando patrones de error por nivel de jugador...${NC}"
    
    # Run dataset analysis
    analyze_chess_datasets
    
    echo -e "${CYAN}💡 Revisa los resultados para comparar:${NC}"
    echo -e "${WHITE}  • Elite vs Novice: Precisión del modelo${NC}"
    echo -e "${WHITE}  • Personal vs FIDE: Distribución de errores${NC}"
    echo -e "${WHITE}  • Stockfish vs Humanos: Patrones tácticos${NC}"
    
    echo -e "${GREEN}✅ Comparación completada${NC}"
}

# Help function
function show_help() {
    echo -e "${CYAN}Available functions:${NC}"
    echo -e "${WHITE}  initialize_mlflow                    - Initialize MLflow with PostgreSQL${NC}"
    echo -e "${WHITE}  start_mlflow_with_postgres           - Start MLflow server${NC}"
    echo -e "${WHITE}  run_ml_experiment [name] [model]     - Run ML experiment${NC}"
    echo -e "${WHITE}  cleanup_mlflow_sqlite                - Cleanup SQLite files${NC}"
    echo -e "${WHITE}  train_chess_error_model              - Train chess error model${NC}"
    echo -e "${WHITE}  test_chess_prediction [fen] [move]   - Test prediction${NC}"
    echo -e "${WHITE}  analyze_chess_datasets               - Analyze datasets${NC}"
    echo -e "${WHITE}  test_elo_standardization             - Test ELO standardization${NC}"
    echo -e "${WHITE}  compare_player_levels                - Compare player levels${NC}"
}

# If script is executed directly, show help
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    if [[ $# -eq 0 ]]; then
        show_help
    else
        # Execute function if provided as argument
        "$@"
    fi
fi
