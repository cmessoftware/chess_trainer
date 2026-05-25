#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Backup completo de la base de datos PostgreSQL del proyecto Chess Trainer

.DESCRIPTION
    Crea un backup completo de la base de datos chess_trainer_db usando pg_dump
    desde el contenedor Docker de PostgreSQL.

.PARAMETER BackupName
    Nombre descriptivo para el backup (opcional, por defecto usa timestamp)

.EXAMPLE
    .\backup_database.ps1
    .\backup_database.ps1 -BackupName "pre_phase2"
#>

param(
    [string]$BackupName = ""
)

# Colores
$Green = "Green"
$Cyan = "Cyan"
$Yellow = "Yellow"
$Red = "Red"

Write-Host "`n========================================" -ForegroundColor $Cyan
Write-Host "  🔒 BACKUP DE BASE DE DATOS" -ForegroundColor $Cyan
Write-Host "========================================`n" -ForegroundColor $Cyan

# Crear directorio de backups
if (-not (Test-Path "backups")) {
    New-Item -ItemType Directory -Path "backups" | Out-Null
    Write-Host "✅ Directorio 'backups' creado`n" -ForegroundColor $Green
}

# Generar nombre del archivo
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
if ($BackupName) {
    $backup_file = "backups\chess_trainer_db_${BackupName}_${timestamp}.sql"
}
else {
    $backup_file = "backups\chess_trainer_db_backup_${timestamp}.sql"
}

Write-Host "📊 Configuración:" -ForegroundColor $Yellow
Write-Host "   • Base de datos: chess_trainer_db" -ForegroundColor White
Write-Host "   • Usuario: chess" -ForegroundColor White
Write-Host "   • Archivo: $backup_file" -ForegroundColor White
Write-Host "   • Fecha: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -ForegroundColor White

# Verificar que PostgreSQL esté corriendo
Write-Host "🔍 Verificando contenedor PostgreSQL..." -ForegroundColor $Cyan
$containerName = docker ps --filter "name=postgres" --format "{{.Names}}" 2>$null | Select-Object -First 1

if (-not $containerName) {
    Write-Host "❌ Contenedor PostgreSQL no está corriendo" -ForegroundColor $Red
    Write-Host "   Iniciando servicios...`n" -ForegroundColor $Yellow
    docker-compose up -d postgres
    Start-Sleep -Seconds 5
    $containerName = docker ps --filter "name=postgres" --format "{{.Names}}" 2>$null | Select-Object -First 1
}

if ($containerName) {
    Write-Host "✅ Contenedor encontrado: $containerName`n" -ForegroundColor $Green
    
    # Ejecutar backup
    Write-Host "🔄 Ejecutando pg_dump..." -ForegroundColor $Cyan
    docker exec $containerName pg_dump -U chess chess_trainer_db > $backup_file 2>&1
    
    # Verificar resultado
    if (Test-Path $backup_file) {
        $fileSize = (Get-Item $backup_file).Length
        
        if ($fileSize -gt 1000) {
            $sizeMB = [math]::Round($fileSize / 1MB, 2)
            
            Write-Host "`n========================================" -ForegroundColor $Green
            Write-Host "  ✅ BACKUP COMPLETADO" -ForegroundColor $Green
            Write-Host "========================================`n" -ForegroundColor $Green
            
            Write-Host "📁 Ubicación:" -ForegroundColor $Yellow
            Write-Host "   $backup_file`n" -ForegroundColor White
            
            Write-Host "📦 Tamaño:" -ForegroundColor $Yellow
            Write-Host "   $sizeMB MB`n" -ForegroundColor White
            
            Write-Host "🔄 Para restaurar:" -ForegroundColor $Cyan
            Write-Host "   docker exec -i $containerName psql -U chess -d chess_trainer_db < $backup_file`n" -ForegroundColor Gray
            
            # Listar todos los backups
            Write-Host "📋 Backups disponibles:" -ForegroundColor $Yellow
            Get-ChildItem -Path "backups" -Filter "*.sql" | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | ForEach-Object {
                $size = [math]::Round($_.Length / 1MB, 2)
                Write-Host "   • $($_.Name) ($size MB)" -ForegroundColor Gray
            }
            Write-Host ""
            
        }
        else {
            Write-Host "`n❌ Backup falló (archivo muy pequeño)" -ForegroundColor $Red
            Write-Host "   Contenido del error:`n" -ForegroundColor $Yellow
            Get-Content $backup_file
        }
    }
    else {
        Write-Host "`n❌ No se pudo crear el archivo de backup" -ForegroundColor $Red
    }
}
else {
    Write-Host "❌ No se pudo iniciar el contenedor PostgreSQL" -ForegroundColor $Red
    exit 1
}
