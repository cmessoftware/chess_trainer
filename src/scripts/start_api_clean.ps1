# Script para limpiar e iniciar el API de Chess Trainer
# Ejecutar: .\start_api_clean.ps1

$ErrorActionPreference = "Continue"

Write-Host "`n🚀 Iniciando Chess Trainer API (limpio)`n" -ForegroundColor Cyan

# Paso 1: Limpiar jobs de PowerShell
Write-Host "1️⃣ Limpiando jobs de PowerShell..." -ForegroundColor Yellow
Get-Job | Stop-Job -ErrorAction SilentlyContinue
Get-Job | Remove-Job -ErrorAction SilentlyContinue
Write-Host "   ✅ Jobs limpiados" -ForegroundColor Green

# Paso 2: Detener procesos Python
Write-Host "`n2️⃣ Deteniendo procesos Python..." -ForegroundColor Yellow
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    $pythonProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ $($pythonProcs.Count) proceso(s) Python detenido(s)" -ForegroundColor Green
    Start-Sleep -Seconds 2
}
else {
    Write-Host "   ℹ️  No hay procesos Python corriendo" -ForegroundColor Gray
}

# Paso 3: Liberar puerto 8000
Write-Host "`n3️⃣ Verificando puerto 8000..." -ForegroundColor Yellow
$port8000 = netstat -ano | Select-String ":8000.*LISTENING"
if ($port8000) {
    $pid = ($port8000[0] -split '\s+')[-1]
    Write-Host "   🔍 Puerto 8000 ocupado por PID: $pid" -ForegroundColor Yellow
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    Write-Host "   ✅ Puerto 8000 liberado" -ForegroundColor Green
}
else {
    Write-Host "   ✅ Puerto 8000 libre" -ForegroundColor Green
}

# Paso 4: Verificar PostgreSQL
Write-Host "`n4️⃣ Verificando PostgreSQL..." -ForegroundColor Yellow
try {
    $pgCheck = docker exec chess_trainer-postgres-1 pg_isready -U chess 2>&1
    if ($pgCheck -like "*accepting connections*") {
        Write-Host "   ✅ PostgreSQL está corriendo" -ForegroundColor Green
    }
    else {
        Write-Host "   ⚠️  PostgreSQL puede no estar disponible" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "   ⚠️  No se pudo verificar PostgreSQL" -ForegroundColor Yellow
}

# Paso 5: Iniciar API
Write-Host "`n5️⃣ Iniciando API en puerto 8000..." -ForegroundColor Yellow
Write-Host "   📂 Directorio: c:\Users\sergiosal\source\repos\chess_trainer\src\api" -ForegroundColor Gray

$startScript = {
    Set-Location "c:\Users\sergiosal\source\repos\chess_trainer\src\api"
    $env:PYTHONPATH = "C:\Users\sergiosal\source\repos\chess_trainer\src"
    & C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
}

$job = Start-Job -ScriptBlock $startScript
Write-Host "   ⏳ Esperando inicio del servidor..." -ForegroundColor Gray
Start-Sleep -Seconds 6

# Paso 6: Verificar que está corriendo
Write-Host "`n6️⃣ Verificando API..." -ForegroundColor Yellow
$maxAttempts = 5
$attempt = 0
$apiRunning = $false

while ($attempt -lt $maxAttempts -and -not $apiRunning) {
    $attempt++
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/docs" -Method GET -TimeoutSec 2 -ErrorAction Stop
        $apiRunning = $true
        Write-Host "   ✅ API respondiendo correctamente!" -ForegroundColor Green
    }
    catch {
        Write-Host "   ⏳ Intento $attempt/$maxAttempts..." -ForegroundColor Gray
        Start-Sleep -Seconds 2
    }
}

if ($apiRunning) {
    Write-Host "`n🎉 API iniciado exitosamente!" -ForegroundColor Green
    Write-Host "`n📍 URLs disponibles:" -ForegroundColor Cyan
    Write-Host "   🌐 Docs interactivos: http://localhost:8000/docs" -ForegroundColor White
    Write-Host "   📖 ReDoc: http://localhost:8000/redoc" -ForegroundColor White
    Write-Host "   ❤️  Health check: http://localhost:8000/health" -ForegroundColor White
    
    Write-Host "`n🔄 El servidor está corriendo con reload automático" -ForegroundColor Cyan
    Write-Host "   Job ID: $($job.Id)" -ForegroundColor Gray
    Write-Host "`n💡 Comandos útiles:" -ForegroundColor Cyan
    Write-Host "   Ver logs:    Receive-Job -Id $($job.Id) -Keep" -ForegroundColor White
    Write-Host "   Detener:     Stop-Job -Id $($job.Id); Remove-Job -Id $($job.Id)" -ForegroundColor White
    
    Write-Host "`n🧪 Ahora puedes ejecutar:" -ForegroundColor Cyan
    Write-Host "   .\tests\verification\test_regenerate_one_game.ps1" -ForegroundColor Green
    
}
else {
    Write-Host "`n❌ El API no respondió después de $maxAttempts intentos" -ForegroundColor Red
    Write-Host "`n📋 Ver logs del job:" -ForegroundColor Yellow
    Receive-Job -Id $job.Id
    Write-Host "`n💡 Intenta iniciar manualmente:" -ForegroundColor Cyan
    Write-Host "   cd src/api" -ForegroundColor White
    Write-Host "   C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe -m uvicorn main:app --reload --port 8000" -ForegroundColor White
}

Write-Host ""
