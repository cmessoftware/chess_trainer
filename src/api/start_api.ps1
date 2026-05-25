# Script PowerShell para iniciar el servicio FastAPI

Write-Host "🚀 Iniciando Chess Error Level Classifier API..." -ForegroundColor Green

# Cambiar al directorio del servicio
Set-Location -Path $PSScriptRoot

# Crear entorno virtual si no existe
if (-not (Test-Path "venv")) {
    Write-Host "📦 Creando entorno virtual..." -ForegroundColor Yellow
    python -m venv venv
}

# Activar entorno virtual
Write-Host "✅ Activando entorno virtual..." -ForegroundColor Green
& .\venv\Scripts\Activate.ps1

# Instalar dependencias
Write-Host "📋 Instalando dependencias..." -ForegroundColor Yellow
pip install -r requirements_api.txt

# Iniciar el servicio
Write-Host "🌐 Iniciando servidor en http://localhost:8000" -ForegroundColor Green
Write-Host "📖 Documentación disponible en http://localhost:8000/docs" -ForegroundColor Cyan

uvicorn chess_error_classifier_api:app --host 0.0.0.0 --port 8000 --reload