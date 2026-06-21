param(
    [string]$Player,
    [int]$MaxGames = 0,
    [string]$Output = "./course_data.sqlite",
    [string]$EnvFile = "../../.env",
    [switch]$Merge,
    [switch]$Replace,
    [ValidateSet(
        "Beginner",
        "Intermediate",
        "Advanced Amateur",
        "Expert",
        "Master Candidate",
        "Master+"
    )]
    [string]$SkillGroup,
    [int]$PlayerEloMin = 0,
    [int]$PlayerEloMax = 0,
    [switch]$EitherSideElo
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

$env:OPENBLAS_NUM_THREADS = "1"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

$migrateArgs = @(".\migrate_to_sqlite.py", "--env-file", (Resolve-Path $EnvFile))

if (-not [string]::IsNullOrWhiteSpace($Player)) {
    $migrateArgs += @("--player", $Player)
}

if ($MaxGames -gt 0) {
    $migrateArgs += @("--max-games", $MaxGames)
}

$migrateArgs += @("--export-chunk-size", 300)

if (-not [string]::IsNullOrWhiteSpace($SkillGroup)) {
    $migrateArgs += @("--skill-group", $SkillGroup)
    if (-not $EitherSideElo) {
        $migrateArgs += "--exclusive-elo-band"
    }
}

if ($EitherSideElo) {
    $migrateArgs += "--either-side-elo"
}

if ($PlayerEloMin -gt 0) {
    $migrateArgs += @("--player-elo-min", $PlayerEloMin)
}

if ($PlayerEloMax -gt 0) {
    $migrateArgs += @("--player-elo-max", $PlayerEloMax)
}

$useMerge = $Merge -or (
    -not $Replace -and
    -not $PSBoundParameters.ContainsKey('Merge') 
)
if ($useMerge) {
    $migrateArgs += "--merge"
}

$migrateArgs += @("--output", $Output)

$filterParts = @()
if (-not [string]::IsNullOrWhiteSpace($Player)) { $filterParts += "player='$Player'" }
if ($MaxGames -gt 0) { $filterParts += "max_games=$MaxGames" }
if (-not [string]::IsNullOrWhiteSpace($SkillGroup)) { $filterParts += "skill_group='$SkillGroup'" }
if (-not [string]::IsNullOrWhiteSpace($SkillGroup) -and -not $EitherSideElo) {
    $filterParts += "exclusive_elo"
}
if ($PlayerEloMin -gt 0 -or $PlayerEloMax -gt 0) {
    $filterParts += "elo=$PlayerEloMin-$PlayerEloMax"
}
if ($useMerge) { $filterParts += "merge" } else { $filterParts += "replace" }
$filterSummary = if ($filterParts.Count -gt 0) { $filterParts -join ", " } else { "all games (no player filter)" }

Write-Output "Ejecutando migracion ($filterSummary)..."
& $pythonExe @migrateArgs
exit $LASTEXITCODE
