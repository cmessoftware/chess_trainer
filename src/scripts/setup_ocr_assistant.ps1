#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Asistente interactivo para instalar Tesseract OCR
    
.DESCRIPTION
    Guía paso a paso para instalar Tesseract con verificación automática
    y apertura de páginas de descarga en el navegador.
    
.EXAMPLE
    .\setup_ocr_assistant.ps1
#>

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  ASISTENTE DE INSTALACIÓN OCR - CHESS TRAINER                  ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$ErrorActionPreference = "Continue"

# Función para verificar instalación
function Test-TesseractInstalled {
    try {
        $null = Get-Command tesseract -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}

# Función para mostrar estado
function Show-Status {
    param($item, $status)
    $icon = if ($status) { "✅" } else { "❌" }
    $color = if ($status) { "Green" } else { "Red" }
    Write-Host "  $icon $item" -ForegroundColor $color
}

# Verificar estado actual
Write-Host "🔍 VERIFICACIÓN DEL SISTEMA`n" -ForegroundColor Yellow

# 1. Tesseract
$hasTesseract = Test-TesseractInstalled
Show-Status "Tesseract OCR" $hasTesseract

# 2. Poppler
try {
    $null = Get-Command pdftoppm -ErrorAction Stop
    $hasPoppler = $true
}
catch {
    $hasPoppler = $false
}
Show-Status "Poppler (pdf2image)" $hasPoppler

# 3. Python packages
$pythonExe = "C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe"
try {
    $packages = & $pythonExe -c "import pytesseract, pdf2image, PIL; print('OK')" 2>&1
    $hasPythonPkgs = $packages -contains "OK"
}
catch {
    $hasPythonPkgs = $false
}
Show-Status "Python packages (pytesseract, pdf2image, pillow)" $hasPythonPkgs

Write-Host ""

# Si todo está instalado, terminar
if ($hasTesseract -and $hasPoppler -and $hasPythonPkgs) {
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "✅ ¡TODO YA ESTÁ INSTALADO!" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Green
    
    Write-Host "💡 Puedes procesar los PDFs escaneados ahora:`n" -ForegroundColor Yellow
    Write-Host "   $pythonExe src/scripts/init_chess_rag.py`n" -ForegroundColor Cyan
    exit 0
}

# Si falta Tesseract, guiar instalación
if (-not $hasTesseract) {
    Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Red
    Write-Host "⚠️  TESSERACT OCR NO ESTÁ INSTALADO" -ForegroundColor Red
    Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Red
    
    Write-Host "📋 PASOS DE INSTALACIÓN:`n" -ForegroundColor Yellow
    
    Write-Host "1️⃣  Abriré la página de descarga en tu navegador..." -ForegroundColor White
    Write-Host "    Descarga: tesseract-ocr-w64-setup-5.x.x.exe (~80MB)`n" -ForegroundColor Gray
    
    $response = Read-Host "¿Abrir página de descarga ahora? (S/n)"
    if ($response -eq "" -or $response -eq "S" -or $response -eq "s") {
        Start-Process "https://github.com/UB-Mannheim/tesseract/wiki"
        Write-Host "✅ Página abierta en el navegador`n" -ForegroundColor Green
    }
    
    Write-Host "2️⃣  Ejecuta el instalador descargado:" -ForegroundColor White
    Write-Host "    - Ruta: C:\Program Files\Tesseract-OCR (por defecto)" -ForegroundColor Gray
    Write-Host "    - ✅ Marca 'Additional language data'" -ForegroundColor Gray
    Write-Host "    - ✅ Selecciona: Spanish (spa) + English (eng)" -ForegroundColor Gray
    Write-Host "    - ✅ Agregar al PATH del sistema`n" -ForegroundColor Gray
    
    Write-Host "3️⃣  Después de instalar:" -ForegroundColor White
    Write-Host "    - Cierra esta ventana de PowerShell" -ForegroundColor Gray
    Write-Host "    - Abre una NUEVA ventana de PowerShell" -ForegroundColor Gray
    Write-Host "    - Ejecuta: .\setup_ocr_assistant.ps1 nuevamente`n" -ForegroundColor Gray
    
    Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
    
    $manualPath = Read-Host "¿Ya instalaste Tesseract y quieres agregarlo al PATH manualmente? (s/N)"
    if ($manualPath -eq "s" -or $manualPath -eq "S") {
        Write-Host "`n🔧 Agregando Tesseract al PATH...`n" -ForegroundColor Yellow
        
        $tesseractPath = "C:\Program Files\Tesseract-OCR"
        if (Test-Path "$tesseractPath\tesseract.exe") {
            try {
                $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
                if ($machinePath -notlike "*$tesseractPath*") {
                    [System.Environment]::SetEnvironmentVariable(
                        "Path",
                        "$machinePath;$tesseractPath",
                        "Machine"
                    )
                    Write-Host "✅ Tesseract agregado al PATH del sistema" -ForegroundColor Green
                }
                
                # Actualizar sesión actual
                $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
                Write-Host "✅ PATH actualizado en sesión actual`n" -ForegroundColor Green
                
                # Verificar
                if (Test-TesseractInstalled) {
                    $version = tesseract --version 2>&1 | Select-Object -First 1
                    Write-Host "✅ Tesseract detectado: $version`n" -ForegroundColor Green
                }
                else {
                    Write-Host "⚠️  Cierra y reabre PowerShell para que tome efecto`n" -ForegroundColor Yellow
                }
            }
            catch {
                Write-Host "❌ Error agregando al PATH: $($_.Exception.Message)`n" -ForegroundColor Red
            }
        }
        else {
            Write-Host "❌ No se encontró tesseract.exe en: $tesseractPath`n" -ForegroundColor Red
            Write-Host "   Verifica que Tesseract esté instalado correctamente`n" -ForegroundColor Yellow
        }
    }
}

# Resumen final
Write-Host "`n═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📚 DOCUMENTACIÓN COMPLETA" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
Write-Host "Lee la guía completa en:" -ForegroundColor White
Write-Host "  INSTALL_TESSERACT_GUIDE.md`n" -ForegroundColor Cyan

if ($hasTesseract) {
    Write-Host "✅ Sistema listo para procesar PDFs con OCR`n" -ForegroundColor Green
}
else {
    Write-Host "⏳ Después de instalar Tesseract, ejecuta:" -ForegroundColor Yellow
    Write-Host "  $pythonExe src/scripts/init_chess_rag.py`n" -ForegroundColor Cyan
}
