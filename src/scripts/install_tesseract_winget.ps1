#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Instalación rápida de Tesseract OCR usando winget
    
.DESCRIPTION
    Utiliza Windows Package Manager (winget) para instalar Tesseract OCR.
    winget viene preinstalado en Windows 10/11 modernas.
    
.EXAMPLE
    .\install_tesseract_winget.ps1
#>

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "📸 INSTALACIÓN DE TESSERACT OCR" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# Verificar si winget está disponible
Write-Host "🔍 Verificando winget..." -ForegroundColor Yellow
try {
    $null = Get-Command winget -ErrorAction Stop
    Write-Host "✅ winget está disponible" -ForegroundColor Green
}
catch {
    Write-Host "❌ winget no está disponible" -ForegroundColor Red
    Write-Host "`n⚠️  SOLUCIÓN ALTERNATIVA:" -ForegroundColor Yellow
    Write-Host "   1. Instalación manual desde:" -ForegroundColor White
    Write-Host "      https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
    Write-Host "   2. Descarga: tesseract-ocr-w64-setup-5.x.x.exe" -ForegroundColor White
    Write-Host "   3. Ejecuta el instalador con opciones por defecto`n" -ForegroundColor White
    exit 1
}

# Verificar si Tesseract ya está instalado
Write-Host "`n🔍 Verificando instalación existente..." -ForegroundColor Yellow
$tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
if (Test-Path $tesseractPath) {
    Write-Host "✅ Tesseract ya está instalado" -ForegroundColor Green
    $version = & $tesseractPath --version 2>&1 | Select-Object -First 1
    Write-Host "   Versión: $version" -ForegroundColor White
    Write-Host "`n💡 No es necesario reinstalar`n" -ForegroundColor Yellow
    exit 0
}

# Instalar Tesseract con winget
Write-Host "`n📦 Instalando Tesseract OCR con winget..." -ForegroundColor Yellow
Write-Host "   (Esto puede tomar 1-2 minutos)`n" -ForegroundColor White

try {
    winget install --id UB-Mannheim.TesseractOCR --accept-package-agreements --accept-source-agreements
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Tesseract instalado exitosamente" -ForegroundColor Green
        
        # Verificar instalación
        if (Test-Path $tesseractPath) {
            $version = & $tesseractPath --version 2>&1 | Select-Object -First 1
            Write-Host "   Versión: $version" -ForegroundColor White
            
            # Verificar idiomas
            $tessdataPath = "C:\Program Files\Tesseract-OCR\tessdata"
            Write-Host "`n📚 Verificando idiomas instalados:" -ForegroundColor Yellow
            
            if (Test-Path "$tessdataPath\eng.traineddata") {
                Write-Host "   ✅ Inglés (eng)" -ForegroundColor Green
            }
            else {
                Write-Host "   ❌ Inglés (eng) NO instalado" -ForegroundColor Red
            }
            
            if (Test-Path "$tessdataPath\spa.traineddata") {
                Write-Host "   ✅ Español (spa)" -ForegroundColor Green
            }
            else {
                Write-Host "   ⚠️  Español (spa) NO instalado" -ForegroundColor Yellow
                Write-Host "`n   📋 Para agregar español:" -ForegroundColor Cyan
                Write-Host "      1. Descarga spa.traineddata desde:" -ForegroundColor White
                Write-Host "         https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata" -ForegroundColor Cyan
                Write-Host "      2. Copia el archivo a: $tessdataPath`n" -ForegroundColor White
            }
            
            # Actualizar PATH (no reiniciar PowerShell necesario)
            Write-Host "`n🔄 Actualizando PATH en la sesión actual..." -ForegroundColor Yellow
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            Write-Host "✅ PATH actualizado" -ForegroundColor Green
            
            Write-Host "`n========================================" -ForegroundColor Cyan
            Write-Host "✅ INSTALACIÓN COMPLETA" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Cyan
            Write-Host "`n💡 Siguiente paso:" -ForegroundColor Yellow
            Write-Host "   python src/scripts/init_chess_rag.py`n" -ForegroundColor Cyan
        }
        else {
            Write-Host "`n⚠️  Tesseract instalado pero no encontrado en la ruta esperada" -ForegroundColor Yellow
            Write-Host "   Reinicia PowerShell e intenta nuevamente`n" -ForegroundColor White
        }
    }
    else {
        Write-Host "`n❌ Error durante la instalación" -ForegroundColor Red
        Write-Host "   Código de salida: $LASTEXITCODE`n" -ForegroundColor White
    }
}
catch {
    Write-Host "`n❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n📋 INSTALACIÓN MANUAL:" -ForegroundColor Cyan
    Write-Host "   https://github.com/UB-Mannheim/tesseract/wiki`n" -ForegroundColor White
}
