# ==============================================================================
# Chess Trainer - Unified Docker Management Script for Windows
# ==============================================================================
# This script provides complete Docker environment management for Windows users
# Combines build, start, cleanup, and backup functionality in one script
# ==============================================================================

param(
    [switch]$BuildOnly,
    [switch]$StartOnly,
    [switch]$Backup,
    [switch]$Clean,
    [switch]$Stop,
    [switch]$Status,
    [switch]$Help
)

function Show-Help {
    Write-Host @"
🔧 Chess Trainer - Docker Management Script

USAGE:
    .\build_up_clean_all.ps1 [OPTIONS]

OPTIONS:
    (no params)     🚀 Full setup: Build + Start + Clean (default)
    -BuildOnly      🔨 Only build containers
    -StartOnly      ▶️  Only start existing containers  
    -Backup         💾 Backup all Docker images
    -Clean          🧹 Clean unused Docker images and volumes
    -Stop           ⏹️  Stop all containers
    -Status         📊 Show container status
    -Help           ❓ Show this help

EXAMPLES:
    .\build_up_clean_all.ps1                # Full setup
    .\build_up_clean_all.ps1 -BuildOnly     # Just build
    .\build_up_clean_all.ps1 -Backup        # Backup images
    .\build_up_clean_all.ps1 -Status        # Check status

"@
}

function Build-Containers {
    Write-Host "🚀 Construyendo imagen chess_trainer..." -ForegroundColor Green
    docker-compose build chess_trainer
    
    Write-Host "🚀 Construyendo imagen notebooks..." -ForegroundColor Green
    docker-compose build notebooks
    
    Write-Host "✅ Imágenes construidas exitosamente!" -ForegroundColor Green
}

function Start-Containers {
    Write-Host "▶️ Levantando contenedores..." -ForegroundColor Cyan
    docker-compose up -d chess_trainer notebooks
    Write-Host "✅ Contenedores iniciados!" -ForegroundColor Green
}

function Stop-Containers {
    Write-Host "⏹️ Deteniendo contenedores..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✅ Contenedores detenidos!" -ForegroundColor Green
}

function Clean-Docker {
    Write-Host "🧹 Limpiando imágenes no utilizadas..." -ForegroundColor Yellow
    docker image prune -a -f
    
    Write-Host "🧹 Limpiando volúmenes no utilizados..." -ForegroundColor Yellow
    docker volume prune -f
    
    Write-Host "✅ Limpieza completada!" -ForegroundColor Green
}

function Backup-Images {
    # Crear carpeta de backup con fecha
    $backupBasePath = "C:\DockerImageBackups"
    $dateFolder = Get-Date -Format "yyyy-MM-dd_HH-mm"
    $backupFolder = Join-Path $backupBasePath $dateFolder
    New-Item -ItemType Directory -Force -Path $backupFolder | Out-Null
    
    Write-Host "💾 Creando backup de imágenes Docker..." -ForegroundColor Magenta
    Write-Host "📁 Carpeta de backup: $backupFolder" -ForegroundColor Gray
    
    # Obtener imágenes del proyecto
    $images = docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { 
        $_ -match "chess_trainer" -or $_ -match "postgres" -or $_ -match "jupyter"
    }
    
    if ($images.Count -eq 0) {
        Write-Host "⚠️ No hay imágenes relacionadas con chess_trainer para respaldar." -ForegroundColor Yellow
        return
    }
    
    foreach ($image in $images) {
        $safeName = ($image -replace "[\\/:*?""<>|]", "_")
        $outputPath = Join-Path $backupFolder "$safeName.tar"
        
        Write-Host "💾 Guardando imagen $image..." -ForegroundColor Gray
        docker save -o $outputPath $image
    }
    
    Write-Host "✅ Backup completado. Imágenes guardadas en: $backupFolder" -ForegroundColor Green
}

function Show-Status {
    Write-Host "📊 Estado de contenedores Chess Trainer:" -ForegroundColor Cyan
    Write-Host "============================================" -ForegroundColor Gray
    
    # Mostrar contenedores activos
    $runningContainers = docker ps --filter "name=chess_trainer" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    if ($runningContainers) {
        Write-Host $runningContainers
    }
    else {
        Write-Host "❌ No hay contenedores chess_trainer ejecutándose" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "🐳 Todas las imágenes Docker:" -ForegroundColor Cyan
    docker images --filter "reference=chess_trainer*" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"
}

# ==============================================================================
# MAIN EXECUTION
# ==============================================================================

if ($Help) {
    Show-Help
    exit 0
}

if ($Status) {
    Show-Status
    exit 0
}

if ($Stop) {
    Stop-Containers
    exit 0
}

if ($Clean) {
    Clean-Docker
    exit 0
}

if ($Backup) {
    Backup-Images
    exit 0
}

if ($BuildOnly) {
    Build-Containers
    exit 0
}

if ($StartOnly) {
    Start-Containers
    Show-Status
    exit 0
}

# DEFAULT: Full setup (Build + Start + Clean)
Write-Host "🚀 Chess Trainer - Configuración completa de Docker" -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Gray

Build-Containers
Start-Containers  
Clean-Docker
Show-Status

Write-Host ""
Write-Host "🎉 ¡Configuración completa! Los contenedores están listos para usar." -ForegroundColor Green
Write-Host "📖 Para ver más opciones, ejecuta: .\build_up_clean_all.ps1 -Help" -ForegroundColor Gray
