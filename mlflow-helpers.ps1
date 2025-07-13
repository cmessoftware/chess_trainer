# Comandos específicos para MLflow integrado con PostgreSQL
# Este script debe ser incluido desde PowerShell-Helpers.ps1

function Initialize-MLflow {
    """Inicializa MLflow integrado en notebooks"""
    Write-Host "🔄 Inicializando MLflow integrado..." -ForegroundColor Blue
    
    # Asegurar que notebooks esté corriendo (incluye MLflow)
    Write-Host "📦 Iniciando contenedor de notebooks con MLflow..." -ForegroundColor Blue
    docker-compose up -d notebooks
    
    # Esperar a que los servicios estén disponibles
    Start-Sleep -Seconds 10
    
    # Verificar que MLflow esté disponible
    $mlflowStatus = Test-MLflowAvailable
    if ($mlflowStatus) {
        Write-Host "✅ MLflow integrado iniciado correctamente" -ForegroundColor Green
        Open-MLflowUI
    }
    else {
        Write-Host "⚠️ MLflow tardando en iniciarse, reintentando..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
        Open-MLflowUI
    }
}

function Start-MLflowWithPostgres {
    """Inicia MLflow integrado en notebooks"""
    Write-Host "🚀 Iniciando MLflow integrado en notebooks..." -ForegroundColor Blue
    
    # Reiniciar contenedor de notebooks (incluye MLflow)
    docker-compose restart notebooks
    
    # Esperamos a que el servicio esté disponible
    Start-Sleep -Seconds 10
    
    # Verificamos si está corriendo
    $status = Test-MLflowAvailable
    if ($status) {
        Write-Host "✅ MLflow integrado está corriendo correctamente" -ForegroundColor Green
        return $true
    }
    else {
        Write-Host "❌ Error iniciando MLflow integrado" -ForegroundColor Red
        return $false
    }
}

function Test-MLflowAvailable {
    """Verifica si MLflow está disponible"""
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/health" -UseBasicParsing -TimeoutSec 5
        return $response.StatusCode -eq 200
    }
    catch {
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
    
    """Ejecuta un experimento de ML con MLflow integrado"""
    Write-Host "🧪 Ejecutando experimento $ExperimentName con $ModelType..." -ForegroundColor Blue
    
    # Asegurar que notebooks esté corriendo
    docker-compose up -d notebooks
    Start-Sleep -Seconds 5
    
    # Ejecutar experimento (el código ya está disponible en /notebooks/src)
    docker-compose exec -e EXPERIMENT_NAME=$ExperimentName -e MODEL_TYPE=$ModelType notebooks python /notebooks/src/ml/train_error_model.py
    
    Write-Host "✅ Experimento completado" -ForegroundColor Green
    
    # Abrir la UI de MLflow para ver resultados
    Open-MLflowUI
}

function Cleanup-MLflowSQLite {
    """Verifica y elimina el archivo SQLite de MLflow si la migración a PostgreSQL está completa"""
    Write-Host "🧹 Verificando y limpiando archivo SQLite de MLflow..." -ForegroundColor Blue
    
    # Ejecutar script de limpieza en notebooks
    docker-compose exec notebooks python /notebooks/src/ml/cleanup_mlflow_sqlite.py
    
    Write-Host "✅ Verificación y limpieza completada" -ForegroundColor Green
}

function Train-ChessErrorModel {
    """Entrena el modelo de predicción de errores usando MLflow integrado"""
    Write-Host "🎯 Entrenando modelo de predicción de errores..." -ForegroundColor Blue
    
    # Asegurar que notebooks esté corriendo
    docker-compose up -d notebooks
    Start-Sleep -Seconds 5
    
    # Ejecutar entrenamiento
    docker-compose exec notebooks python /notebooks/src/ml/chess_error_predictor.py
    
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
    
    # Ejecutar predicción en notebooks
    docker-compose exec -e TEST_FEN="$FEN" -e TEST_MOVE="$Move" notebooks python /notebooks/src/ml/realtime_predictor.py
    
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
