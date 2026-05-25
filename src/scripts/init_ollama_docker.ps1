#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Inicializar Ollama en Docker con modelos
.DESCRIPTION
    Script para levantar Ollama en Docker y descargar los modelos necesarios
.EXAMPLE
    .\init_ollama_docker.ps1
    .\init_ollama_docker.ps1 -DevOnly  # Solo modelo de desarrollo
#>

param(
    [switch]$DevOnly
)

Write-Host "`n🚀 Iniciando Ollama en Docker..." -ForegroundColor Cyan

# 0. Verificar que Docker está corriendo
Write-Host "`n🔍 Verificando Docker Desktop..." -ForegroundColor Yellow
try {
    $dockerVersion = docker version --format '{{.Server.Version}}' 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker no responde"
    }
    Write-Host "✅ Docker Desktop corriendo (versión $dockerVersion)" -ForegroundColor Green
}
catch {
    Write-Host "`n❌ ERROR: Docker Desktop no está corriendo" -ForegroundColor Red
    Write-Host "`n📋 Pasos para solucionar:" -ForegroundColor Yellow
    Write-Host "   1. Inicia Docker Desktop desde el menú de Windows" -ForegroundColor White
    Write-Host "   2. Espera a que el ícono de Docker en la bandeja esté estable" -ForegroundColor White
    Write-Host "   3. Verifica con: docker ps" -ForegroundColor White
    Write-Host "   4. Vuelve a ejecutar este script" -ForegroundColor White
    Write-Host "`n"
    exit 1
}

# 1. Levantar servicio Ollama
Write-Host "`n📦 Levantando contenedor Ollama..." -ForegroundColor Yellow
docker-compose up -d ollama

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error al iniciar Ollama en Docker" -ForegroundColor Red
    exit 1
}

Write-Host "⏳ Esperando que Ollama esté listo..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 2. Verificar que Ollama está corriendo
try {
    $response = Invoke-WebRequest -Uri "http://localhost:11434/api/version" -Method GET -TimeoutSec 5
    Write-Host "✅ Ollama está corriendo" -ForegroundColor Green
}
catch {
    Write-Host "❌ Error: Ollama no está respondiendo" -ForegroundColor Red
    Write-Host "   Verifica los logs: docker-compose logs ollama" -ForegroundColor Yellow
    exit 1
}

# 3. Descargar modelo de desarrollo
Write-Host "`n📥 Descargando modelo llama3.2:3b (desarrollo)..." -ForegroundColor Yellow
docker exec chess_trainer_ollama ollama pull llama3.2:3b

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Modelo llama3.2:3b descargado" -ForegroundColor Green
}
else {
    Write-Host "⚠️ Error descargando llama3.2:3b" -ForegroundColor Yellow
}

# 4. Descargar modelo de producción (solo si no es DevOnly)
if (-not $DevOnly) {
    Write-Host "`n📥 Descargando modelo llama3.1:8b (producción)..." -ForegroundColor Yellow
    docker exec chess_trainer_ollama ollama pull llama3.1:8b
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Modelo llama3.1:8b descargado" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️ Error descargando llama3.1:8b" -ForegroundColor Yellow
    }
}

# 5. Listar modelos instalados
Write-Host "`n📋 Modelos instalados:" -ForegroundColor Cyan
docker exec chess_trainer_ollama ollama list

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "✅ OLLAMA CONFIGURADO CORRECTAMENTE EN DOCKER" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan

Write-Host "`n📊 Información:" -ForegroundColor Yellow
Write-Host "   🔗 URL: http://localhost:11434" -ForegroundColor White
Write-Host "   📦 Container: chess_trainer_ollama" -ForegroundColor White
Write-Host "   💾 Volume: ollama_data" -ForegroundColor White

Write-Host "`n💡 Comandos útiles:" -ForegroundColor Yellow
Write-Host "   Ver logs:        docker-compose logs -f ollama" -ForegroundColor White
Write-Host "   Listar modelos:  docker exec chess_trainer_ollama ollama list" -ForegroundColor White
Write-Host "   Ejecutar modelo: docker exec -it chess_trainer_ollama ollama run llama3.2:3b" -ForegroundColor White
Write-Host "   Detener:         docker-compose stop ollama" -ForegroundColor White

Write-Host "`n🔧 Variables de entorno para Python:" -ForegroundColor Yellow
Write-Host "   OLLAMA_BASE_URL=http://localhost:11434" -ForegroundColor Cyan

Write-Host "`n"
