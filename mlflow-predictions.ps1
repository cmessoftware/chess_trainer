# 🚀 Script PowerShell para Predicciones ML con MLflow
# Automatiza todo el proceso de entrenamiento y predicciones

Write-Host "🚀 CHESS TRAINER ML PREDICTIONS - MLFLOW PIPELINE" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Blue

function Test-PythonPackage {
    param([string]$Package)
    
    try {
        python -c "import $Package" 2>$null
        return $true
    }
    catch {
        return $false
    }
}

function Start-MLflowServices {
    Write-Host "🔧 Iniciando servicios MLflow..." -ForegroundColor Yellow
    
    # Verificar si Docker está corriendo
    $dockerRunning = docker ps 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker no está corriendo. Iniciando servicios..." -ForegroundColor Red
        docker-compose up -d
        Start-Sleep 10
    }
    
    # Verificar servicios específicos
    $mlflowRunning = docker ps --filter "name=mlflow" --format "table {{.Names}}" | Select-String "mlflow"
    if (-not $mlflowRunning) {
        Write-Host "🔄 Iniciando MLflow..." -ForegroundColor Yellow
        docker-compose up -d mlflow
        Start-Sleep 5
    }
    
    Write-Host "✅ Servicios MLflow iniciados" -ForegroundColor Green
    Write-Host "🌐 MLflow UI disponible en: http://localhost:5000" -ForegroundColor Cyan
}

function Test-Prerequisites {
    Write-Host "🔍 Verificando prerequisitos..." -ForegroundColor Yellow
    
    $allGood = $true
    
    # Verificar Python
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Python no encontrado" -ForegroundColor Red
        $allGood = $false
    }
    
    # Verificar paquetes Python
    $requiredPackages = @("pandas", "sklearn", "mlflow")
    foreach ($package in $requiredPackages) {
        if (Test-PythonPackage $package) {
            Write-Host "✅ $package instalado" -ForegroundColor Green
        }
        else {
            Write-Host "❌ $package no instalado" -ForegroundColor Red
            $allGood = $false
        }
    }
    
    # Verificar datasets
    $datasetPaths = @(
        "data/export/unified_all_sources.parquet",
        "data/export/unified_small_sources.parquet"
    )
    
    $datasetFound = $false
    foreach ($path in $datasetPaths) {
        if (Test-Path $path) {
            Write-Host "✅ Dataset encontrado: $path" -ForegroundColor Green
            $datasetFound = $true
            break
        }
    }
    
    if (-not $datasetFound) {
        Write-Host "❌ No se encontraron datasets" -ForegroundColor Red
        Write-Host "   Ejecuta el pipeline de datos primero" -ForegroundColor Yellow
        $allGood = $false
    }
    
    return $allGood
}

function Invoke-MLAnalysis {
    Write-Host "📊 Ejecutando análisis de datasets..." -ForegroundColor Yellow
    
    try {
        python src/ml/explore_datasets.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Análisis completado" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Error en análisis" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Error ejecutando análisis: $_" -ForegroundColor Red
        return $false
    }
}

function Invoke-MLTraining {
    Write-Host "🎯 Ejecutando entrenamiento básico..." -ForegroundColor Yellow
    
    try {
        python src/ml/train_basic_model.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Entrenamiento completado" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Error en entrenamiento" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Error ejecutando entrenamiento: $_" -ForegroundColor Red
        return $false
    }
}

function Invoke-MLPredictions {
    Write-Host "🔮 Ejecutando predicciones..." -ForegroundColor Yellow
    
    try {
        python src/ml/make_predictions.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Predicciones completadas" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Error en predicciones" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Error ejecutando predicciones: $_" -ForegroundColor Red
        return $false
    }
}

function Invoke-CompletePipeline {
    Write-Host "🚀 Ejecutando pipeline completo..." -ForegroundColor Yellow
    
    try {
        python src/ml/run_complete_pipeline.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Pipeline completo terminado" -ForegroundColor Green
            return $true
        }
        else {
            Write-Host "❌ Error en pipeline completo" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "❌ Error ejecutando pipeline: $_" -ForegroundColor Red
        return $false
    }
}

function Show-MLflowUI {
    Write-Host "🌐 Abriendo MLflow UI..." -ForegroundColor Cyan
    Start-Process "http://localhost:5000"
}

function Show-Menu {
    Write-Host "`n🎯 MENÚ DE OPCIONES" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Blue
    Write-Host "1. 🔧 Iniciar servicios MLflow"
    Write-Host "2. 📊 Análisis de datasets"
    Write-Host "3. 🎯 Entrenamiento básico"
    Write-Host "4. 🔮 Hacer predicciones"
    Write-Host "5. 🚀 Pipeline completo (todo)"
    Write-Host "6. 🌐 Abrir MLflow UI"
    Write-Host "7. 🔍 Verificar prerequisitos"
    Write-Host "0. ❌ Salir"
    Write-Host ""
}

# Función principal
function Main {
    
    # Verificar prerequisitos iniciales
    Write-Host "🔍 Verificación inicial..." -ForegroundColor Yellow
    if (-not (Test-Prerequisites)) {
        Write-Host "❌ Prerequisitos no cumplidos. Revisa los errores arriba." -ForegroundColor Red
        Write-Host "💡 Instala paquetes faltantes: pip install mlflow pandas scikit-learn" -ForegroundColor Yellow
        return
    }
    
    # Iniciar servicios automáticamente
    Start-MLflowServices
    
    # Menú interactivo
    do {
        Show-Menu
        $choice = Read-Host "Selecciona una opción (0-7)"
        
        switch ($choice) {
            "1" { Start-MLflowServices }
            "2" { Invoke-MLAnalysis }
            "3" { Invoke-MLTraining }
            "4" { Invoke-MLPredictions }
            "5" { Invoke-CompletePipeline }
            "6" { Show-MLflowUI }
            "7" { Test-Prerequisites }
            "0" { 
                Write-Host "👋 ¡Hasta luego!" -ForegroundColor Green
                break 
            }
            default { 
                Write-Host "⚠️ Opción no válida" -ForegroundColor Yellow 
            }
        }
        
        if ($choice -ne "0") {
            Write-Host "`nPresiona cualquier tecla para continuar..." -ForegroundColor Gray
            $null = Read-Host
        }
        
    } while ($choice -ne "0")
}

# Exportar funciones para uso independiente
Export-ModuleMember -Function Start-MLflowServices, Invoke-MLAnalysis, Invoke-MLTraining, Invoke-MLPredictions, Invoke-CompletePipeline, Show-MLflowUI

# Ejecutar si se llama directamente
if ($MyInvocation.InvocationName -ne ".") {
    Main
}
