#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Descarga e instala Tesseract OCR automáticamente
    
.DESCRIPTION
    Descarga el instalador de Tesseract desde GitHub y lo ejecuta
    de forma silenciosa con idiomas español e inglés.
    
.EXAMPLE
    .\install_tesseract_direct.ps1
#>

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "📸 INSTALACIÓN AUTOMÁTICA DE TESSERACT" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$ErrorActionPreference = "Stop"

# URLs y configuración
$downloadUrl = "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe"
$installerPath = "$env:TEMP\tesseract-installer.exe"
$tesseractPath = "C:\Program Files\Tesseract-OCR\tesseract.exe"

# Verificar instalación existente
Write-Host "🔍 Verificando instalación existente..." -ForegroundColor Yellow
if (Test-Path $tesseractPath) {
    Write-Host "✅ Tesseract ya está instalado" -ForegroundColor Green
    $version = & $tesseractPath --version 2>&1 | Select-Object -First 1
    Write-Host "   $version`n" -ForegroundColor White
    exit 0
}

# Descargar instalador
Write-Host "📥 Descargando Tesseract OCR 5.5..." -ForegroundColor Yellow
Write-Host "   URL: $downloadUrl" -ForegroundColor White
Write-Host "   (Esto puede tomar 1-2 minutos)`n" -ForegroundColor Gray

try {
    # Usar WebClient para mostrar progreso
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($downloadUrl, $installerPath)
    
    Write-Host "✅ Descarga completada" -ForegroundColor Green
    $fileSize = (Get-Item $installerPath).Length / 1MB
    Write-Host "   Tamaño: $([math]::Round($fileSize, 2)) MB`n" -ForegroundColor White
}
catch {
    Write-Host "❌ Error descargando: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`n📋 SOLUCIÓN MANUAL:" -ForegroundColor Yellow
    Write-Host "   1. Abre: https://github.com/UB-Mannheim/tesseract/wiki" -ForegroundColor White
    Write-Host "   2. Descarga: tesseract-ocr-w64-setup-5.x.x.exe" -ForegroundColor White
    Write-Host "   3. Ejecuta el instalador`n" -ForegroundColor White
    exit 1
}

# Ejecutar instalador
Write-Host "📦 Instalando Tesseract..." -ForegroundColor Yellow
Write-Host "   Instalación silenciosa con idiomas: eng, spa" -ForegroundColor White
Write-Host "   (Esto puede tomar 1-2 minutos)`n" -ForegroundColor Gray

try {
    # Instalador NSIS con parámetros silenciosos
    # /S = silent, /D = directorio de instalación
    $installArgs = "/S /D=C:\Program Files\Tesseract-OCR"
    $process = Start-Process -FilePath $installerPath -ArgumentList $installArgs -Wait -PassThru -NoNewWindow
    
    if ($process.ExitCode -eq 0) {
        Write-Host "✅ Instalación completada" -ForegroundColor Green
        
        # Verificar instalación
        if (Test-Path $tesseractPath) {
            $version = & $tesseractPath --version 2>&1 | Select-Object -First 1
            Write-Host "   $version" -ForegroundColor White
            
            # Verificar idiomas
            $tessdataPath = "C:\Program Files\Tesseract-OCR\tessdata"
            Write-Host "`n📚 Idiomas instalados:" -ForegroundColor Yellow
            
            $languages = @()
            Get-ChildItem "$tessdataPath\*.traineddata" | ForEach-Object {
                $lang = $_.BaseName
                $languages += $lang
                Write-Host "   ✅ $lang" -ForegroundColor Green
            }
            
            # Verificar español e inglés
            if ($languages -notcontains "spa") {
                Write-Host "`n⚠️  Falta idioma español (spa)" -ForegroundColor Yellow
                Write-Host "   Descargando spa.traineddata..." -ForegroundColor White
                
                $spaUrl = "https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata"
                $spaPath = "$tessdataPath\spa.traineddata"
                
                try {
                    Invoke-WebRequest -Uri $spaUrl -OutFile $spaPath
                    Write-Host "   ✅ Español descargado" -ForegroundColor Green
                }
                catch {
                    Write-Host "   ❌ Error descargando español: $($_.Exception.Message)" -ForegroundColor Red
                }
            }
            
            # Actualizar PATH
            Write-Host "`n🔄 Configurando PATH..." -ForegroundColor Yellow
            $machinePath = [System.Environment]::GetEnvironmentVariable("Path", "Machine")
            $tesseractDir = "C:\Program Files\Tesseract-OCR"
            
            if ($machinePath -notlike "*$tesseractDir*") {
                Write-Host "   Agregando Tesseract al PATH del sistema..." -ForegroundColor White
                [System.Environment]::SetEnvironmentVariable(
                    "Path",
                    "$machinePath;$tesseractDir",
                    "Machine"
                )
                Write-Host "   ✅ PATH actualizado (sistema)" -ForegroundColor Green
            }
            
            # Actualizar PATH en sesión actual
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
            Write-Host "   ✅ PATH actualizado (sesión actual)" -ForegroundColor Green
            
            Write-Host "`n========================================" -ForegroundColor Cyan
            Write-Host "✅ INSTALACIÓN EXITOSA" -ForegroundColor Green
            Write-Host "========================================" -ForegroundColor Cyan
            Write-Host "`n💡 Siguiente paso:" -ForegroundColor Yellow
            Write-Host "   python src/scripts/init_chess_rag.py" -ForegroundColor Cyan
            Write-Host "`n   Los 13 PDFs escaneados se procesarán con OCR`n" -ForegroundColor White
        }
        else {
            Write-Host "`n⚠️  Instalación completada pero ejecutable no encontrado" -ForegroundColor Yellow
            Write-Host "   Reinicia PowerShell e intenta: tesseract --version`n" -ForegroundColor White
        }
    }
    else {
        Write-Host "❌ Error durante la instalación (código: $($process.ExitCode))" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}
finally {
    # Limpiar instalador temporal
    if (Test-Path $installerPath) {
        Remove-Item $installerPath -Force
        Write-Host "`n🧹 Instalador temporal eliminado" -ForegroundColor Gray
    }
}
