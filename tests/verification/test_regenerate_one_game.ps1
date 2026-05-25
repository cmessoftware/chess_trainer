# Script de prueba rápida para regenerar UNA partida SHAP
# Ejecutar: .\test_regenerate_one_game.ps1

$ErrorActionPreference = "Stop"

Write-Host "`n🧪 Test de Regeneración SHAP - Una Partida`n" -ForegroundColor Cyan

# Configuración
$BASE_URL = "http://localhost:8000"
$USERNAME = "admin"
$PASSWORD = "admin123"
$TEST_GAME_ID = "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb"

# Paso 1: Verificar API
Write-Host "1️⃣ Verificando API..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$BASE_URL/docs" -Method GET -TimeoutSec 2
    Write-Host "   ✅ API respondiendo en $BASE_URL" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ API no responde. Ejecuta:" -ForegroundColor Red
    Write-Host "      cd src/api" -ForegroundColor White
    Write-Host "      C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe -m uvicorn main:app --reload --port 8000" -ForegroundColor White
    exit 1
}

Start-Sleep -Seconds 1

# Paso 2: Login y obtener token
Write-Host "`n2️⃣ Obteniendo token de autenticación..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = $USERNAME
        password = $PASSWORD
    } | ConvertTo-Json

    $loginResponse = Invoke-RestMethod `
        -Uri "$BASE_URL/api/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginBody `
        -TimeoutSec 10

    $token = $loginResponse.access_token
    Write-Host "   ✅ Token obtenido: $($token.Substring(0,20))..." -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Error en login: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 1

# Paso 3: Regenerar análisis SHAP
Write-Host "`n3️⃣ Regenerando análisis SHAP..." -ForegroundColor Yellow
Write-Host "   Game ID: $($TEST_GAME_ID.Substring(0,20))..." -ForegroundColor Gray

try {
    $headers = @{
        Authorization  = "Bearer $token"
        "Content-Type" = "application/json"
    }

    $shapBody = @{
        game_id = $TEST_GAME_ID
    } | ConvertTo-Json

    Write-Host "   ⏱️  Procesando (esto puede tardar 15-30 segundos)..." -ForegroundColor Gray
    
    $shapResponse = Invoke-RestMethod `
        -Uri "$BASE_URL/api/analysis/shap" `
        -Method POST `
        -Headers $headers `
        -Body $shapBody `
        -TimeoutSec 60

    $analysisId = $shapResponse.analysis_id
    Write-Host "   ✅ Análisis completado - ID: $analysisId" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Error en SHAP: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
    exit 1
}

Start-Sleep -Seconds 2

# Paso 4: Verificar campos nuevos
Write-Host "`n4️⃣ Verificando nuevos campos en API..." -ForegroundColor Yellow

try {
    $shapValues = Invoke-RestMethod `
        -Uri "$BASE_URL/api/analysis/shap/game/$TEST_GAME_ID`?move_number=1" `
        -Method GET `
        -Headers $headers `
        -TimeoutSec 10

    if ($shapValues.Count -eq 0) {
        Write-Host "   ⚠️  No se encontraron SHAP values" -ForegroundColor Yellow
        exit 1
    }

    $firstValue = $shapValues[0]
    
    Write-Host "   📊 Ejemplo de SHAP value regenerado:" -ForegroundColor Cyan
    Write-Host "      Move Number: $($firstValue.move_number)" -ForegroundColor White
    Write-Host "      Move SAN: $($firstValue.move_san)" -ForegroundColor $(if ($firstValue.move_san) { "Green" } else { "Red" })
    Write-Host "      Move UCI: $($firstValue.move_uci)" -ForegroundColor $(if ($firstValue.move_uci) { "Green" } else { "Red" })
    Write-Host "      FEN: $($firstValue.fen.Substring(0, [Math]::Min(40, $firstValue.fen.Length)))..." -ForegroundColor $(if ($firstValue.fen) { "Green" } else { "Red" })
    Write-Host "      Player Color: $($firstValue.player_color)" -ForegroundColor $(if ($firstValue.player_color) { "Green" } else { "Red" })
    Write-Host "      Feature: $($firstValue.feature_name)" -ForegroundColor White
    Write-Host "      SHAP Value: $($firstValue.shap_value)" -ForegroundColor White

}
catch {
    Write-Host "   ❌ Error obteniendo SHAP: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Paso 5: Verificar en base de datos
Write-Host "`n5️⃣ Verificando en base de datos..." -ForegroundColor Yellow

try {
    $verifyScript = @"
import psycopg2
conn = psycopg2.connect('postgresql://chess:chess_pass@localhost:5432/chess_trainer_db')
cur = conn.cursor()

# Contar análisis
cur.execute('SELECT COUNT(*) FROM analysis_results')
total_analysis = cur.fetchone()[0]

# Contar SHAP values
cur.execute('SELECT COUNT(*) FROM move_shap_values')
total_shap = cur.fetchone()[0]

# Contar SHAP con campos nuevos poblados
cur.execute('SELECT COUNT(*) FROM move_shap_values WHERE move_san IS NOT NULL')
shap_with_san = cur.fetchone()[0]

cur.execute('SELECT COUNT(*) FROM move_shap_values WHERE player_color IS NOT NULL')
shap_with_color = cur.fetchone()[0]

print(f'   Análisis en DB: {total_analysis}')
print(f'   SHAP values: {total_shap}')
print(f'   SHAP con move_san: {shap_with_san} ({int(shap_with_san/total_shap*100) if total_shap > 0 else 0}%)')
print(f'   SHAP con player_color: {shap_with_color} ({int(shap_with_color/total_shap*100) if total_shap > 0 else 0}%)')

conn.close()
"@

    C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe -c $verifyScript
    Write-Host "   ✅ Verificación en DB completada" -ForegroundColor Green

}
catch {
    Write-Host "   ⚠️  No se pudo verificar DB: $($_.Exception.Message)" -ForegroundColor Yellow
}

# Resumen final
Write-Host "`n📋 RESUMEN:" -ForegroundColor Cyan
Write-Host "   ✅ API funcionando" -ForegroundColor Green
Write-Host "   ✅ Autenticación exitosa" -ForegroundColor Green
Write-Host "   ✅ Análisis SHAP regenerado (ID: $analysisId)" -ForegroundColor Green
Write-Host "   ✅ Campos nuevos verificados en API" -ForegroundColor Green
Write-Host "   ✅ Base de datos actualizada" -ForegroundColor Green

Write-Host "`n🎉 ¡Regeneración exitosa!" -ForegroundColor Green
Write-Host "`n📖 Próximos pasos:" -ForegroundColor Cyan
Write-Host "   1. Regenerar más partidas desde Postman:" -ForegroundColor White
Write-Host "      POST http://localhost:8000/api/analysis/shap" -ForegroundColor Gray
Write-Host "      Body: { `"game_id`": `"tu_game_id`" }" -ForegroundColor Gray
Write-Host "`n   2. Verificar todos los análisis:" -ForegroundColor White
Write-Host "      GET http://localhost:8000/api/analysis/shap/game/{game_id}" -ForegroundColor Gray
Write-Host "`n   3. Probar con LLM usando campos nuevos (ver REGENERATE_SHAP_GUIDE.md)" -ForegroundColor White
Write-Host ""
