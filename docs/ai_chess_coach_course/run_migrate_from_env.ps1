param(
    [string]$Player,
    [string]$Output = "./course_data.sqlite",
    [string]$EnvFile = "../../.env"
)

$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

if (-not (Test-Path $EnvFile)) {
    Write-Error "No se encontro el archivo .env en: $EnvFile"
    exit 1
}

# Carga variables del .env al proceso actual
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match '^\s*([^#=]+)=(.*)$') {
        $name = $matches[1].Trim()
        $value = $matches[2].Trim().Trim('"')
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

if ([string]::IsNullOrWhiteSpace($env:CHESS_TRAINER_DB_URL)) {
    Write-Error "CHESS_TRAINER_DB_URL no esta configurada despues de cargar .env"
    exit 1
}

$pythonExe = "C:/Users/sergiosal/miniforge3/envs/chess_trainer/python.exe"
if (-not (Test-Path $pythonExe)) {
    Write-Error "No se encontro Python del entorno chess_trainer en: $pythonExe"
    exit 1
}

Write-Output "CHESS_TRAINER_DB_URL cargada correctamente."
Write-Output "Ejecutando migracion para player '$Player'..."

& $pythonExe .\migrate_to_sqlite.py --player $Player --output $Output
exit $LASTEXITCODE
