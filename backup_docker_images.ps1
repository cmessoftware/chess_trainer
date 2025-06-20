# Carpeta base donde guardar los backups
$backupBasePath = "C:\DockerImageBackups"

# Crear carpeta con fecha actual
$dateFolder = Get-Date -Format "yyyy-MM-dd_HH-mm"
$backupFolder = Join-Path $backupBasePath $dateFolder
New-Item -ItemType Directory -Force -Path $backupFolder | Out-Null

# Obtener lista de imágenes
$images = docker images --format "{{.Repository}}:{{.Tag}}" | Where-Object { $_ -ne "<none>:<none>" }

if ($images.Count -eq 0) {
    Write-Host "⚠️ No hay imágenes para respaldar."
    exit
}

# Respaldar cada imagen
foreach ($image in $images) {
    # Limpiar caracteres inválidos para el nombre de archivo
    $safeName = ($image -replace "[\\/:*?""<>|]", "_")
    $outputPath = Join-Path $backupFolder "$safeName.tar"

    Write-Host "💾 Guardando imagen $image..."
    docker save -o $outputPath $image
}

Write-Host "✅ Backup completado. Imágenes guardadas en: $backupFolder"
