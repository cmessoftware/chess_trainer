# Test endpoint de notificaciones con un token válido

Write-Host "🔍 Obteniendo token de login..." -ForegroundColor Cyan

# Login para obtener token válido
$loginBody = @{
    username = "admin"
    password = "admin123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/auth/login" -Method POST -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access_token
    Write-Host "✅ Token obtenido: $($token.Substring(0,30))..." -ForegroundColor Green
    Write-Host ""
    
    # Decodificar el token (payload)
    $tokenParts = $token.Split('.')
    $payload = $tokenParts[1]
    # Agregar padding si es necesario
    while ($payload.Length % 4 -ne 0) {
        $payload += "="
    }
    $payloadBytes = [Convert]::FromBase64String($payload)
    $payloadJson = [System.Text.Encoding]::UTF8.GetString($payloadBytes)
    Write-Host "📋 Payload del token:" -ForegroundColor Yellow
    Write-Host $payloadJson -ForegroundColor Gray
    Write-Host ""
    
    # Probar endpoint de notificaciones
    Write-Host "🔔 Probando endpoint de notificaciones..." -ForegroundColor Cyan
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type"  = "application/json"
    }
    
    $notificationsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/features/notifications" -Method GET -Headers $headers
    
    Write-Host "✅ Notificaciones obtenidas:" -ForegroundColor Green
    Write-Host "   Total: $($notificationsResponse.Count)" -ForegroundColor White
    
    if ($notificationsResponse.Count -gt 0) {
        Write-Host ""
        Write-Host "📝 Primera notificación:" -ForegroundColor Yellow
        $notificationsResponse[0] | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Gray
    }
    
}
catch {
    Write-Host "❌ Error:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response body: $responseBody" -ForegroundColor Gray
    }
}
