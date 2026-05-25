# Script de prueba para verificar campos nuevos en SHAP API
# Ejecutar: .\test_shap_new_fields_simple.ps1

Write-Host "`n🔍 Test de SHAP API - Campos Nuevos (move_san, move_uci, fen, player_color)`n" -ForegroundColor Cyan

# 1. Obtener token
Write-Host "1️⃣ Obteniendo token..." -ForegroundColor Yellow
try {
    $loginBody = @{
        username = "admin"
        password = "admin123"
    } | ConvertTo-Json
    
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
        -Method POST `
        -ContentType "application/json" `
        -Body $loginBody `
        -ErrorAction Stop
    
    $token = $loginResponse.access_token
    Write-Host "   ✅ Token obtenido correctamente" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Error obteniendo token: $_" -ForegroundColor Red
    exit 1
}

# 2. Consultar SHAP values
Write-Host "`n2️⃣ Consultando SHAP values..." -ForegroundColor Yellow
try {
    $gameId = "5daf60d3cfe938edbe083c9bd584b6a62b27c1068d927cf3d35875479f4006bb"
    $headers = @{
        Authorization = "Bearer $token"
    }
    
    $shapValues = Invoke-RestMethod -Uri "http://localhost:8000/api/analysis/shap/game/$gameId`?move_number=10" `
        -Method GET `
        -Headers $headers `
        -ErrorAction Stop
    
    Write-Host "   ✅ SHAP values obtenidos: $($shapValues.Count) registros" -ForegroundColor Green
}
catch {
    Write-Host "   ❌ Error consultando SHAP: $_" -ForegroundColor Red
    exit 1
}

# 3. Verificar campos nuevos
Write-Host "`n3️⃣ Verificando campos nuevos..." -ForegroundColor Yellow

$firstValue = $shapValues[0]
$fieldsToCheck = @('move_san', 'move_uci', 'fen', 'player_color')
$allFieldsPresent = $true

foreach ($field in $fieldsToCheck) {
    if ($firstValue.PSObject.Properties.Name -contains $field) {
        $value = $firstValue.$field
        if ($null -eq $value) {
            Write-Host "   ⚠️  $field : PRESENTE pero NULL (requiere regeneración)" -ForegroundColor Yellow
        }
        else {
            Write-Host "   ✅ $field : $value" -ForegroundColor Green
        }
    }
    else {
        Write-Host "   ❌ $field : CAMPO NO EXISTE en la respuesta" -ForegroundColor Red
        $allFieldsPresent = $false
    }
}

# 4. Mostrar ejemplo completo
Write-Host "`n4️⃣ Ejemplo de registro SHAP:" -ForegroundColor Yellow
Write-Host ($firstValue | ConvertTo-Json -Depth 3) -ForegroundColor Cyan

# 5. Resumen
Write-Host "`n📊 RESUMEN:" -ForegroundColor Cyan
if ($allFieldsPresent) {
    Write-Host "✅ Todos los campos nuevos están presentes en la API" -ForegroundColor Green
    
    $nullCount = 0
    foreach ($field in $fieldsToCheck) {
        if ($null -eq $firstValue.$field) {
            $nullCount++
        }
    }
    
    if ($nullCount -gt 0) {
        Write-Host "⚠️  Hay $nullCount campos con valores NULL" -ForegroundColor Yellow
        Write-Host "   Para poblarlos, ejecuta:" -ForegroundColor Yellow
        Write-Host "   1. DELETE /api/analysis/{analysis_id}" -ForegroundColor White
        Write-Host "   2. POST /api/analysis/shap con game_id" -ForegroundColor White
    }
    else {
        Write-Host "🎉 Todos los campos tienen datos!" -ForegroundColor Green
    }
}
else {
    Write-Host "❌ Faltan campos en la API - revisar endpoint" -ForegroundColor Red
}

Write-Host ""
