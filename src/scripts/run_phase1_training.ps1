# Script robusto para ejecutar Phase 1 baseline training
# Maneja interrupciones y guarda progreso

$ErrorActionPreference = "Continue"

Write-Host "`n🚀 Iniciando Phase 1 Baseline Training" -ForegroundColor Green
Write-Host "   Tiempo estimado: 20-30 minutos" -ForegroundColor Gray
Write-Host "   Presiona Ctrl+C para detener (se guardará el progreso)`n" -ForegroundColor Yellow

# Crear directorio de logs si no existe
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" -Force | Out-Null
}

# Ejecutar training con output a archivo
$logFile = "logs/phase1_training_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"

try {
    python src/scripts/execute_phase1_baseline.py 2>&1 | Tee-Object -FilePath $logFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Entrenamiento completado exitosamente!" -ForegroundColor Green
        Write-Host "   Log guardado en: $logFile" -ForegroundColor Cyan
    }
    else {
        Write-Host "`n⚠️  Entrenamiento terminó con código de salida: $LASTEXITCODE" -ForegroundColor Yellow
        Write-Host "   Revisa el log: $logFile" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "`n❌ Error durante el entrenamiento: $_" -ForegroundColor Red
    Write-Host "   Log guardado en: $logFile" -ForegroundColor Cyan
}

Write-Host "`n📊 Verificando resultados guardados..." -ForegroundColor Cyan
if (Test-Path "src/ml/results") {
    Get-ChildItem "src/ml/results" -File | ForEach-Object {
        Write-Host "   ✓ $($_.Name)" -ForegroundColor Green
    }
}

Write-Host ""
