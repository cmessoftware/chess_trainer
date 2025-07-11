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

# Exponer comandos
Export-ModuleMember -Function Initialize-MLflow, Start-MLflowWithPostgres, Open-MLflowUI, Run-MLExperiment, Cleanup-MLflowSQLite, Train-ChessErrorModel, Test-ChessPrediction
