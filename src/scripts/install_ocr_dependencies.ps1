#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Instalar Tesseract OCR y Poppler para procesamiento de PDFs escaneados
    
.DESCRIPTION
    Instala las dependencias necesarias para OCR:
    - Tesseract OCR (motor de reconocimiento de texto)
    - Poppler (utilidades PDF para pdf2image)
    
.EXAMPLE
    .\install_ocr_dependencies.ps1
    .\install_ocr_dependencies.ps1 -SkipTesseract  # Solo instalar Poppler
#>

param(
    [switch]$SkipTesseract,
    [switch]$SkipPoppler
)

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "📸 INSTALACI�N DE DEPENDENCIAS OCR" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# Verificar si Chocolatey está instalado
function Test-Chocolatey {
    try {
        $null = Get-Command choco -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

# Instalar Tesseract OCR
if (-not $SkipTesseract) {
    Write-Host "🔍 Verificando Tesseract OCR..." -ForegroundColor Yellow
    
    # Verificar si ya está instalado
    $tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"
    if (Test-Path $tesseractPath) {
        Write-Host "✅ Tesseract ya está instalado en: $tesseractPath" -ForegroundColor Green
        
        # Verificar versión
        $version = & $tesseractPath --version 2>&1 | Select-Object -First 1
        Write-Host "   Versión: $version" -ForegroundColor White
    }
    else {
        Write-Host "❌ Tesseract no está instalado" -ForegroundColor Red
        
        if (Test-Chocolatey) {
            Write-Host "`n📦 Instalando Tesseract con Chocolatey..." -ForegroundColor Yellow
            choco install tesseract -y
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Tesseract instalado exitosamente" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Error instalando Tesseract con Chocolatey" -ForegroundColor Red
            }
        }
        else {
            Write-Host "`n⚠️  Chocolatey no está instalado" -ForegroundColor Yellow
            Write-Host "`n📋 INSTALACIÓN MANUAL DE TESSERACT:" -ForegroundColor Cyan
            Write-Host "   1. Descarga el instalador desde:" -ForegroundColor White
            Write-Host "      https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor Cyan
            Write-Host "   2. Ejecuta el instalador y sigue las instrucciones" -ForegroundColor White
            Write-Host "   3. Asegúrate de agregar Tesseract al PATH del sistema" -ForegroundColor White
            Write-Host "   4. Reinicia PowerShell después de instalar`n" -ForegroundColor White
        }
    }
    
    # Verificar idiomas instalados
    if (Test-Path $tesseractPath) {
        $tessdataPath = "C:\Program Files\Tesseract-OCR\tessdata"
        if (Test-Path "$tessdataPath\spa.traineddata") {
            Write-Host "   ✅ Idioma español (spa) instalado" -ForegroundColor Green
        }
        else {
            Write-Host "   ⚠️  Idioma español (spa) NO instalado" -ForegroundColor Yellow
            Write-Host "      Descarga desde: https://github.com/tesseract-ocr/tessdata" -ForegroundColor Cyan
        }
        
        if (Test-Path "$tessdataPath\eng.traineddata") {
            Write-Host "   ✅ Idioma inglés (eng) instalado" -ForegroundColor Green
        }
    }
}

# Instalar Poppler
if (-not $SkipPoppler) {
    Write-Host "`n🔍 Verificando Poppler..." -ForegroundColor Yellow
    
    # Verificar si pdftoppm está en el PATH
    try {
        $null = Get-Command pdftoppm -ErrorAction Stop
        $popplerPath = (Get-Command pdftoppm).Source
        Write-Host "✅ Poppler ya está instalado" -ForegroundColor Green
        Write-Host "   Ubicación: $popplerPath" -ForegroundColor White
    }
    catch {
        Write-Host "❌ Poppler no está instalado" -ForegroundColor Red
        
        if (Test-Chocolatey) {
            Write-Host "`n📦 Instalando Poppler con Chocolatey..." -ForegroundColor Yellow
            choco install poppler -y
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✅ Poppler instalado exitosamente" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Error instalando Poppler con Chocolatey" -ForegroundColor Red
            }
        }
        else {
            Write-Host "`n📋 INSTALACIÓN MANUAL DE POPPLER:" -ForegroundColor Cyan
            Write-Host "   1. Descarga desde:" -ForegroundColor White
            Write-Host "      https://github.com/oschwartz10612/poppler-windows/releases/" -ForegroundColor Cyan
            Write-Host "   2. Extrae el archivo ZIP a una ubicación (ej: C:\poppler)" -ForegroundColor White
            Write-Host "   3. Agrega el directorio bin al PATH del sistema" -ForegroundColor White
            Write-Host "      Ejemplo: C:\poppler\Library\bin" -ForegroundColor Cyan
            Write-Host "   4. Reinicia PowerShell después de agregar al  PATH`n" -ForegroundColor White
        }
    }
}

# Verificación final
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "📊 VERIFICACIÓN FINAL" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$allOk = $true

# Verificar Tesseract
if (-not $SkipTesseract) {
    if (Test-Path "C:\Program Files\Tesseract-OCR\tesseract.exe") {
        Write-Host "✅ Tesseract: Instalado" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Tesseract: NO instalado" -ForegroundColor Red
        $allOk = $false
    }
}

# Verificar Poppler
if (-not $SkipPoppler) {
    try {
        $null = Get-Command pdftoppm -ErrorAction Stop
        Write-Host "✅ Poppler: Instalado" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Poppler: NO instalado" -ForegroundColor Red
        $allOk = $false
    }
}

# Verificar paquetes Python
Write-Host "`n🐍 Verificando paquetes Python..." -ForegroundColor Yellow

$pythonPackages = @("pytesseract", "pdf2image", "pillow")
foreach ($pkg in $pythonPackages) {
    try {
        $result = pip show $pkg 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ $pkg instalado" -ForegroundColor Green
        }
        else {
            Write-Host "   ❌ $pkg NO instalado" -ForegroundColor Red
            $allOk = $false
        }
    }
    catch {
        Write-Host "   ❌ $pkg NO instalado" -ForegroundColor Red
        $allOk = $false
    }
}

# Resultado final
Write-Host "`n========================================" -ForegroundColor Cyan
if ($allOk) {
    Write-Host "✅ TODAS LAS DEPENDENCIAS INSTALADAS" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "`n💡 Siguiente paso:" -ForegroundColor Yellow
    Write-Host "   Ejecuta: python src/scripts/init_chess_rag.py" -ForegroundColor Cyan
    Write-Host "   Los PDFs escaneados se procesarán automáticamente con OCR`n" -ForegroundColor White
}
else {
    Write-Host "⚠️  ALGUNAS DEPENDENCIAS FALTANTES" -ForegroundColor Yellow
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "`n📋 Revisa los errores arriba y completa la instalación manual" -ForegroundColor White
    Write-Host "   Luego reinicia PowerShell y vuelve a ejecutar este script`n" -ForegroundColor White
}
