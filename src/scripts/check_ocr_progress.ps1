#!/usr/bin/env pwsh
# Script para verificar el progreso del procesamiento OCR

Write-Host "`n════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📊 ESTADO DEL PROCESAMIENTO OCR" -ForegroundColor Yellow
Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

# Verificar proceso Python
$pythonProcess = Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.WorkingSet64 -gt 100MB }

if ($pythonProcess) {
    Write-Host "✅ Proceso OCR activo" -ForegroundColor Green
    Write-Host "   PID: $($pythonProcess.Id)" -ForegroundColor Gray
    Write-Host "   CPU: $([math]::Round($pythonProcess.CPU, 2))s" -ForegroundColor Gray
    Write-Host "   Memoria: $([math]::Round($pythonProcess.WorkingSet64 / 1MB))MB`n" -ForegroundColor Gray
}
else {
    Write-Host "⚠️  No hay procesos OCR activos`n" -ForegroundColor Yellow
}

# Verificar checkpoint
$checkpointFile = "data/chess_books/processing_checkpoint.json"
if (Test-Path $checkpointFile) {
    $checkpoint = Get-Content $checkpointFile -Raw | ConvertFrom-Json
    $processed = $checkpoint.processed_books.Count
    
    Write-Host "📚 Libros procesados:" -ForegroundColor White
    Write-Host "   Total: $processed libros" -ForegroundColor Cyan
    
    # Mostrar últimos 5 libros procesados
    Write-Host "`n   Últimos procesados:" -ForegroundColor White
    $checkpoint.processed_books.Keys | Select-Object -Last 5 | ForEach-Object {
        $book = $checkpoint.processed_books.$_
        Write-Host "   • $_ ($($book.chunks) chunks)" -ForegroundColor Gray
    }
}
else {
    Write-Host "⚠️  No se encontró archivo checkpoint`n" -ForegroundColor Yellow
}

# Instrucciones
Write-Host "`n════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "💡 Comandos útiles:" -ForegroundColor White
Write-Host "   • Ver este resumen: .\check_ocr_progress.ps1" -ForegroundColor Gray
Write-Host "   • Ver logs en tiempo real: Ejecutar en nueva terminal" -ForegroundColor Gray
Write-Host "   • Detener proceso: Stop-Process -Id <PID>" -ForegroundColor Gray
Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
