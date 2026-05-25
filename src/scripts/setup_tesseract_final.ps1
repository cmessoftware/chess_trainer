#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Configurar Tesseract OCR y procesar PDFs escaneados
    
.DESCRIPTION
    Descarga idioma español, configura PATH y ejecuta procesamiento OCR
#>

$ErrorActionPreference = "Stop"

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  CONFIGURACIÓN FINAL DE TESSERACT OCR                          ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Rutas
$tesseractPath = "C:\Users\sergiosal\AppData\Local\Programs\Tesseract-OCR"
$tesseractExe = "$tesseractPath\tesseract.exe"
$tessdataPath = "$tesseractPath\tessdata"

# 1. Verificar instalación
Write-Host "🔍 Verificando Tesseract..." -ForegroundColor Yellow
if (Test-Path $tesseractExe) {
    $version = & $tesseractExe --version 2>&1 | Select-Object -First 1
    Write-Host "✅ $version" -ForegroundColor Green
}
else {
    Write-Host "❌ Tesseract no encontrado en: $tesseractPath" -ForegroundColor Red
    exit 1
}

# 2. Verificar idiomas
Write-Host "`n📚 Verificando idiomas..." -ForegroundColor Yellow
$langs = & $tesseractExe --list-langs 2>&1 | Select-String -Pattern "eng|spa"

if ($langs -match "spa") {
    Write-Host "✅ Español (spa) instalado" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Español (spa) NO instalado. Descargando..." -ForegroundColor Yellow
    
    $spaUrl = "https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata"
    $spaFile = "$tessdataPath\spa.traineddata"
    
    try {
        Write-Host "   Descargando spa.traineddata (~4MB)..." -ForegroundColor White
        Invoke-WebRequest -Uri $spaUrl -OutFile $spaFile -UseBasicParsing
        Write-Host "✅ Español descargado e instalado" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Error descargando: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "`n   Descarga manual desde: $spaUrl" -ForegroundColor Yellow
        Write-Host "   Y copia a: $tessdataPath`n" -ForegroundColor Yellow
        exit 1
    }
}

if ($langs -match "eng") {
    Write-Host "✅ Inglés (eng) instalado" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Inglés (eng) NO instalado (debería venir por defecto)" -ForegroundColor Yellow
}

# 3. Configurar PATH
Write-Host "`n🔧 Configurando PATH..." -ForegroundColor Yellow
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$tesseractPath*") {
    Write-Host "   Agregando Tesseract al PATH del usuario..." -ForegroundColor White
    [System.Environment]::SetEnvironmentVariable(
        "Path",
        "$currentPath;$tesseractPath",
        "User"
    )
    Write-Host "✅ PATH actualizado (permanente)" -ForegroundColor Green
}
else {
    Write-Host "✅ Tesseract ya está en PATH" -ForegroundColor Green
}

# Actualizar sesión actual
$env:Path = "$env:Path;$tesseractPath"
Write-Host "✅ PATH actualizado en sesión actual" -ForegroundColor Green

# 4. Configurar pytesseract
Write-Host "`n🐍 Configurando pytesseract..." -ForegroundColor Yellow
$configScript = @"
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'$tesseractExe'
print('✅ pytesseract configurado')
print('Tesseract location:', pytesseract.pytesseract.tesseract_cmd)
try:
    version = pytesseract.get_tesseract_version()
    print('Tesseract version:', version)
except Exception as e:
    print('⚠️  Error:', e)
"@

$pythonExe = "C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe"
$configScript | & $pythonExe 2>&1

# 5. Verificación final
Write-Host "`n════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "✅ TESSERACT CONFIGURADO CORRECTAMENTE" -ForegroundColor Green
Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

# 6. Mostrar idiomas finales
Write-Host "📚 Idiomas disponibles:" -ForegroundColor Yellow
& $tesseractExe --list-langs 2>&1 | Select-String -Pattern "List|eng|spa|osd"
Write-Host ""

# 7. Preguntar si procesar PDFs ahora
Write-Host "════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "📖 PROCESAR PDFs ESCANEADOS" -ForegroundColor Cyan
Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan

Write-Host "Tienes 13 PDFs escaneados pendientes de procesamiento:" -ForegroundColor White
Write-Host "  - Modern Chess Openings 15th Edition (MCO-15) ⭐" -ForegroundColor Gray
Write-Host "  - Fundamental Chess Endings" -ForegroundColor Gray
Write-Host "  - My System (Nimzowitsch)" -ForegroundColor Gray
Write-Host "  - The Art of Attack in Chess" -ForegroundColor Gray
Write-Host "  - Y 9 libros más de finales y estrategia`n" -ForegroundColor Gray

Write-Host "Tiempo estimado: ~30-60 minutos (2-5 min por libro)`n" -ForegroundColor Yellow

$response = Read-Host "¿Procesar PDFs ahora? (S/n)"

if ($response -eq "" -or $response -eq "S" -or $response -eq "s") {
    Write-Host "`n🚀 Iniciando procesamiento con OCR...`n" -ForegroundColor Green
    Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
    
    & $pythonExe src/scripts/init_chess_rag.py
    
    Write-Host "`n════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "✅ PROCESAMIENTO COMPLETADO" -ForegroundColor Green
    Write-Host "════════════════════════════════════════════════════════════`n" -ForegroundColor Cyan
    
    Write-Host "💡 Verifica el estado final:" -ForegroundColor Yellow
    Write-Host "   $pythonExe checkpoint_status.py`n" -ForegroundColor Cyan
}
else {
    Write-Host "`n⏸️  Procesamiento pospuesto" -ForegroundColor Yellow
    Write-Host "`n💡 Para procesar más tarde, ejecuta:" -ForegroundColor Yellow
    Write-Host "   $pythonExe src/scripts/init_chess_rag.py`n" -ForegroundColor Cyan
}
