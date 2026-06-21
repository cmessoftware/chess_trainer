# Creates a new branch from origin/main with the current tree, excluding GitHub >100 MB files.
# Usage: .\scripts\git\create_clean_feature_branch.ps1

param(
    [string]$SourceBranch = "feature/04_ml_training",
    [string]$TargetBranch = "feature/04_ml_training_clean",
    [string]$BaseBranch = "origin/main"
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

$excludePaths = @(
    "docs/ai_chess_coach_course/course_data.sqlite",
    "backups/chess_trainer_db_backup_20260617_102149.sql",
    "backups/chess_trainer_old_volume_20260603_210049.dump",
    "backups"
)

Write-Host "Fetching origin..."
git fetch origin

if (git show-ref --verify --quiet "refs/heads/$TargetBranch") {
    Write-Error "Branch $TargetBranch already exists."
}

Write-Host "Creating $TargetBranch from $BaseBranch..."
git checkout -b $TargetBranch $BaseBranch

Write-Host "Copying tree from $SourceBranch..."
git checkout $SourceBranch -- .

foreach ($path in $excludePaths) {
    if (Test-Path $path) {
        Remove-Item -Recurse -Force $path -ErrorAction SilentlyContinue
    }
    git rm -r --cached --ignore-unmatch $path 2>$null | Out-Null
}

$gitignoreExtra = @"

# Large local data (never commit — GitHub 100 MB limit)
docs/ai_chess_coach_course/course_data.sqlite
backups/
backups/*.sql
backups/*.dump
"@
if (-not (Select-String -Path ".gitignore" -Pattern "docs/ai_chess_coach_course/course_data.sqlite" -Quiet)) {
    Add-Content -Path ".gitignore" -Value $gitignoreExtra
}

git add -A
git commit -m "feat: ML training, SHAP, and Kaggle competition (clean branch, no large data files)"

Write-Host "OK. Push with: git push -u origin $TargetBranch"
