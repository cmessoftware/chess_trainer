param(
    [string]$Output = "./course_data.sqlite",
    [string]$EnvFile = "../../.env",
    [string]$ManifestPath = "./data/datasets/balanced_import_manifest.json",
    [switch]$Replace
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$env:OPENBLAS_NUM_THREADS = "1"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"

# 10,000 games — exclusive ELO bands (avg white/black). Quotas match PG availability.
$groups = @(
    @{ Name = "Beginner";          Min = 600;  Max = 1199; MaxGames = 2300; Description = "Beginner (<1200)" }
    @{ Name = "Intermediate";      Min = 1200; Max = 1599; MaxGames = 3810; Description = "Intermediate (1200-1599)" }
    @{ Name = "Advanced Amateur";  Min = 1600; Max = 1999; MaxGames = 986;  Description = "Advanced Amateur (1600-1999)" }
    @{ Name = "Expert";            Min = 2000; Max = 2199; MaxGames = 1404; Description = "Expert (2000-2199)" }
    @{ Name = "Master Candidate";  Min = 2200; Max = 2399; MaxGames = 1000; Description = "Master Candidate (2200-2399)" }
    @{ Name = "Master+";           Min = 2400; Max = 3000; MaxGames = 500;  Description = "Master+ (2400+)" }
)

$targetGames = 0
foreach ($group in $groups) { $targetGames += $group.MaxGames }
$manifestEntries = @()
$firstCall = $true

Write-Output "Balanced course import (exclusive ELO bands, no source filter)"
Write-Output "  target games : $targetGames"
Write-Output "  assignment   : average(white_elo, black_elo) -> one band per game"
Write-Output "  output       : $Output"
Write-Output ""

foreach ($group in $groups) {
    Write-Output "=== $($group.Name) | ELO $($group.Min)-$($group.Max) | max_games=$($group.MaxGames) ==="

    $invokeArgs = @{
        MaxGames     = $group.MaxGames
        SkillGroup   = $group.Name
        PlayerEloMin = $group.Min
        PlayerEloMax = $group.Max
        Output       = $Output
        EnvFile      = $EnvFile
        Merge        = $true
    }

    if ($Replace -and $firstCall) {
        $invokeArgs.Remove("Merge")
        $invokeArgs["Replace"] = $true
        $firstCall = $false
    }

    try {
        & "$PSScriptRoot/run_migrate_from_env.ps1" @invokeArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Import failed for group '$($group.Name)' (exit $LASTEXITCODE)"
            exit $LASTEXITCODE
        }
    }
    catch {
        Write-Error "Exception: $($_.Exception.Message)"
        Write-Error $_.ScriptStackTrace
        exit 1
    }

    $manifestEntries += [ordered]@{
        skill_group             = $group.Name
        skill_group_description = $group.Description
        elo_min                 = $group.Min
        elo_max                 = $group.Max
        max_games               = $group.MaxGames
        exclusive_elo_band      = $true
        exported_at             = (Get-Date).ToString("o")
    }
    Write-Output ""
}

$skillGroupCatalog = @(
    foreach ($group in $groups) {
        [ordered]@{
            name        = $group.Name
            description = $group.Description
            elo_min     = $group.Min
            elo_max     = $group.Max
            max_games   = $group.MaxGames
        }
    }
)

$manifest = [ordered]@{
    generated_at        = (Get-Date).ToString("o")
    output              = [System.IO.Path]::GetFullPath($Output)
    target_games        = $targetGames
    elo_assignment      = "exclusive_average"
    skill_groups        = $skillGroupCatalog
    batches             = $manifestEntries
}

$manifestFile = Join-Path $PSScriptRoot $ManifestPath
$manifestDir = Split-Path $manifestFile -Parent
if (-not (Test-Path $manifestDir)) {
    New-Item -ItemType Directory -Path $manifestDir -Force | Out-Null
}

$manifest | ConvertTo-Json -Depth 6 | Set-Content -Path $manifestFile -Encoding UTF8
Write-Output "Manifest written to: $manifestFile"
Write-Output "Balanced import complete ($targetGames games requested)."
