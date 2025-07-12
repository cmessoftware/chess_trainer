# Comandos específicos para MLflow integrado con PostgreSQL
# Este script debe ser incluido desde PowerShell-Helpers.ps1

function Initialize-MLflow {
    """Inicializa MLflow con PostgreSQL"""
    Write-Host "🔄 Inicializando MLflow con PostgreSQL..." -ForegroundColor Blue
    
    # Sincronizar código actualizado
    docker-compose cp "src/" mlflow:/mlflow/src/
    
    # Verificar la configuración de la base de datos
    docker-compose exec mlflow python /mlflow/src/ml/init_mlflow_db.py
    
    # Abrir la UI de MLflow
    Open-MLflowUI
    
    Write-Host "✅ MLflow inicializado correctamente" -ForegroundColor Green
}

function Start-MLflowWithPostgres {
    """Inicia el servidor MLflow con PostgreSQL"""
    Write-Host "🚀 Iniciando MLflow con PostgreSQL..." -ForegroundColor Blue
    
    # Detenemos el servicio si está corriendo
    docker-compose stop mlflow
    
    # Iniciamos MLflow con la configuración actualizada
    docker-compose up -d mlflow
    
    # Esperamos a que el servicio esté disponible
    Start-Sleep -Seconds 5
    
    # Verificamos si está corriendo
    $status = docker-compose ps mlflow | Select-String "Up"
    if ($status) {
        Write-Host "✅ MLflow está corriendo con PostgreSQL" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "❌ Error iniciando MLflow" -ForegroundColor Red
        return $false
    }
}

function Open-MLflowUI {
    """Abre la UI de MLflow en el navegador"""
    Write-Host "🌐 Abriendo UI de MLflow..." -ForegroundColor Blue
    Start-Process "http://localhost:5000"
}

function Run-MLExperiment {
    param (
        [string]$ExperimentName = "chess_error_prediction",
        [string]$ModelType = "RandomForest"
    )
    
    """Ejecuta un experimento de ML con MLflow"""
    Write-Host "🧪 Ejecutando experimento $ExperimentName con $ModelType..." -ForegroundColor Blue
    
    # Sincronizar código
    docker-compose cp "src/" notebooks:/notebooks/src/
    
    # Ejecutar experimento
    docker-compose exec -e EXPERIMENT_NAME=$ExperimentName -e MODEL_TYPE=$ModelType notebooks python /notebooks/src/ml/train_error_model.py
    
    Write-Host "✅ Experimento completado" -ForegroundColor Green
    
    # Abrir la UI de MLflow para ver resultados
    Open-MLflowUI
}

function Cleanup-MLflowSQLite {
    """Verifica y elimina el archivo SQLite de MLflow si la migración a PostgreSQL está completa"""
    Write-Host "🧹 Verificando y limpiando archivo SQLite de MLflow..." -ForegroundColor Blue
    
    # Sincronizar código actualizado
    docker-compose cp "src/" mlflow:/mlflow/src/
    
    # Ejecutar script de limpieza
    docker-compose exec mlflow python /mlflow/src/ml/cleanup_mlflow_sqlite.py
    
    Write-Host "✅ Verificación y limpieza completada" -ForegroundColor Green
}

function Train-ChessErrorModel {
    """Entrena el modelo de predicción de errores usando MLflow"""
    Write-Host "🎯 Entrenando modelo de predicción de errores..." -ForegroundColor Blue
    
    # Sincronizar código actualizado
    docker-compose cp "src/" mlflow:/mlflow/src/
    
    # Ejecutar entrenamiento
    docker-compose exec mlflow python /mlflow/src/ml/chess_error_predictor.py
    
    Write-Host "✅ Entrenamiento completado. Revisa MLflow UI para ver métricas" -ForegroundColor Green
    Open-MLflowUI
}

function Test-ChessPrediction {
    param (
        [string]$FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        [string]$Move = "e2e4"
    )
    
    """Prueba predicción en tiempo real"""
    Write-Host "🔮 Probando predicción para jugada $Move..." -ForegroundColor Blue
    
    # Sincronizar código
    docker-compose cp "src/" mlflow:/mlflow/src/
    
    # Ejecutar predicción
    docker-compose exec -e TEST_FEN="$FEN" -e TEST_MOVE="$Move" mlflow python /mlflow/src/ml/realtime_predictor.py
    
    Write-Host "✅ Predicción completada" -ForegroundColor Green
}

function Analyze-ChessDatasets {
    """Ejecuta análisis ML comparativo en todos los datasets reales (NO DESTRUCTIVO)"""
    Write-Host "🔬 Iniciando análisis ML de datasets reales..." -ForegroundColor Blue
    Write-Host "⚠️ MODO NO DESTRUCTIVO: Solo lectura de datos existentes" -ForegroundColor Yellow
    
    # Sincronizar código actualizado
    docker-compose cp "src/ml/analyze_real_datasets.py" notebooks:/notebooks/
    
    # Asegurar que el contenedor de notebooks esté corriendo
    Write-Host "📦 Iniciando contenedor de notebooks..." -ForegroundColor Blue
    docker-compose up -d notebooks
    
    # Esperar a que esté disponible
    Start-Sleep -Seconds 3
    
    # Ejecutar análisis
    Write-Host "🚀 Ejecutando análisis comparativo..." -ForegroundColor Blue
    docker-compose exec notebooks python /notebooks/analyze_real_datasets.py
    
    Write-Host "✅ Análisis completado. Revisa los resultados en el log." -ForegroundColor Green
}

function Test-ELOStandardization {
    """Ejecuta pruebas de estandarización ELO (Issue #21)"""
    Write-Host "📊 Ejecutando pruebas de estandarización ELO..." -ForegroundColor Blue
    
    # Sincronizar código actualizado
    docker-compose cp "tests/test_elo_standardization.py" notebooks:/notebooks/
    
    # Asegurar que el contenedor de notebooks esté corriendo
    docker-compose up -d notebooks
    
    # Esperar a que esté disponible
    Start-Sleep -Seconds 3
    
    # Ejecutar pruebas
    docker-compose exec notebooks python /notebooks/test_elo_standardization.py
    
    Write-Host "✅ Pruebas de ELO completadas" -ForegroundColor Green
}

function Compare-PlayerLevels {
    """Compara patrones de error entre diferentes niveles de jugadores"""
    Write-Host "🎯 Comparando patrones de error por nivel de jugador..." -ForegroundColor Blue
    
    # Ejecutar análisis de datasets
    Analyze-ChessDatasets
    
    Write-Host "💡 Revisa los resultados para comparar:" -ForegroundColor Cyan
    Write-Host "  • Elite vs Novice: Precisión del modelo" -ForegroundColor White
    Write-Host "  • Personal vs FIDE: Distribución de errores" -ForegroundColor White  
    Write-Host "  • Stockfish vs Humanos: Patrones tácticos" -ForegroundColor White
    
    Write-Host "✅ Comparación completada" -ForegroundColor Green
}
