# ⚡ CHESS TRAINER - ULTRA-OPTIMIZED COMMANDS
# Load with: . .\quick-helpers.ps1
# Your daily workflow in super-fast commands!

# =======================================    Write-Host "   📊 Jupyter: http://localhost:8889" -ForegroundColor Cyan=====================================
# 🎯 AUTO-CONFIGURATION
# =============================================================================

# Auto-detect project root and set global variables
$global:CHESS_TRAINER_ROOT = $PWD.Path
$global:CHESS_TRAINER_SRC = Join-Path $CHESS_TRAINER_ROOT "src"

# Quick navigation function
function ct {
    """Quick navigate to chess trainer root"""
    Set-Location $global:CHESS_TRAINER_ROOT
    Write-Host "📁 Navigated to chess trainer root" -ForegroundColor Cyan
}

# Helper function to ensure we're in the right directory
function Ensure-ProjectDirectory {
    if (-not (Test-Path "docker-compose.yml")) {
        if (Test-Path $global:CHESS_TRAINER_ROOT) {
            Set-Location $global:CHESS_TRAINER_ROOT
            Write-Host "📁 Switched to project directory: $global:CHESS_TRAINER_ROOT" -ForegroundColor Cyan
        }
        else {
            Write-Host "❌ Error: Not in chess_trainer directory and can't find project root!" -ForegroundColor Red
            Write-Host "💡 Run this from the chess_trainer directory or use 'ct' to navigate there first" -ForegroundColor Yellow
            return $false
        }
    }
    return $true
}

# =============================================================================
# 🔥 CORE ML WORKFLOW (Most used - Super optimized)
# =============================================================================

# Import MLflow helpers
. "$PSScriptRoot\mlflow-helpers.ps1"

function mlinit {
    """Initialize MLflow with PostgreSQL"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Initialize-MLflow
}

function mlanalyze {
    """🔬 Quick ML analysis of all datasets (NON-DESTRUCTIVE)"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🚀 Running ML analysis on all chess datasets..." -ForegroundColor Green
    Write-Host "⚠️ Non-destructive mode: Only reading existing data" -ForegroundColor Yellow
    Analyze-ChessDatasets
}

function elostd {
    """📊 Quick ELO standardization test"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "📊 Testing ELO standardization..." -ForegroundColor Green
    Test-ELOStandardization
}

function cmplevels {
    """🎯 Compare error patterns across player levels"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🎯 Comparing player level error patterns..." -ForegroundColor Green
    Compare-PlayerLevels
}

function mlexp {
    param (
        [string]$ExperimentName = "chess_error_prediction",
        [string]$ModelType = "RandomForest"
    )
    """Run an ML experiment with MLflow tracking"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Run-MLExperiment -ExperimentName $ExperimentName -ModelType $ModelType
}

function mltest {
    """Test MLflow PostgreSQL integration"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🔬 Testing MLflow PostgreSQL integration..." -ForegroundColor Blue
    docker-compose cp "src/" mlflow:/mlflow/src/
    docker-compose exec mlflow python /mlflow/src/ml/test_mlflow_postgres_integration.py
    Write-Host "✅ MLflow integration test completed" -ForegroundColor Green
}

function mlclean {
    """Clean up old MLflow SQLite file"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Cleanup-MLflowSQLite
}

function mltrain {
    """Train chess error prediction model"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Train-ChessErrorModel
}

function mlpredict {
    param (
        [string]$FEN = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        [string]$Move = "e2e4"
    )
    """Test chess move prediction"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Test-ChessPrediction -FEN $FEN -Move $Move
}

function ml {
    """Complete ML pipeline test with sync"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🧪 ML Pipeline Test..." -ForegroundColor Blue
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose exec notebooks python /notebooks/validate_ml_pipeline_fixed.py
    Write-Host "✅ ML test completed" -ForegroundColor Green
}

function tac {
    """Test tactical features specifically"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🎯 Tactical Features Test..." -ForegroundColor Blue
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose cp "test_tactical_preprocessing.py" notebooks:/notebooks/
    docker-compose exec notebooks python /notebooks/test_tactical_preprocessing.py
    Write-Host "✅ Tactical test completed" -ForegroundColor Green
}

function sync {
    """Sync essential source code to containers (optimized)"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🔄 Syncing code (optimized)..." -ForegroundColor Blue
    
    # Sync only essential directories to notebooks
    $essentialDirs = @("ml", "modules", "scripts")
    foreach ($dir in $essentialDirs) {
        if (Test-Path "src/$dir") {
            docker-compose cp "src/$dir" notebooks:/notebooks/src/
            Write-Host "   📁 Synced src/$dir to notebooks" -ForegroundColor Gray
        }
    }
    
    # Sync complete src to app container (needed for full functionality)
    docker-compose cp "src/" chess_trainer:/app/src/
    Write-Host "   📁 Synced complete src to app" -ForegroundColor Gray
    
    Write-Host "✅ Smart sync completed" -ForegroundColor Green
}

function sync-ml {
    """Sync only ML-related code to notebooks"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🧠 Syncing ML code only..." -ForegroundColor Blue
    
    $mlDirs = @("ml", "modules")
    foreach ($dir in $mlDirs) {
        if (Test-Path "src/$dir") {
            docker-compose cp "src/$dir" notebooks:/notebooks/src/
            Write-Host "   🧠 Synced src/$dir" -ForegroundColor Gray
        }
    }
    
    Write-Host "✅ ML sync completed" -ForegroundColor Green
}

function sync-app {
    """Sync only app-related code"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🎯 Syncing app code..." -ForegroundColor Blue
    
    $appDirs = @("pages", "modules", "scripts")
    foreach ($dir in $appDirs) {
        if (Test-Path "src/$dir") {
            docker-compose cp "src/$dir" chess_trainer:/app/src/
            Write-Host "   🎯 Synced src/$dir to app" -ForegroundColor Gray
        }
    }
    
    Write-Host "✅ App sync completed" -ForegroundColor Green
}

function sync-scripts {
    """Sync only scripts directory"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "📝 Syncing scripts..." -ForegroundColor Blue
    
    if (Test-Path "src/scripts") {
        docker-compose cp "src/scripts" notebooks:/notebooks/src/
        docker-compose cp "src/scripts" chess_trainer:/app/src/
        Write-Host "✅ Scripts synced" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️ src/scripts not found" -ForegroundColor Yellow
    }
}

function test {
    """Quick test with auto-sync"""
    if (-not (Ensure-ProjectDirectory)) { return }
    sync
    docker-compose exec notebooks python /notebooks/validate_ml_pipeline_fixed.py
}

# =============================================================================
# ⚡ INSTANT ACCESS (1-2 letters - Lightning fast)
# =============================================================================

function j { 
    # Get current token and open Jupyter with it
    $logs = docker-compose logs notebooks --tail 50
    $tokenLine = $logs | Select-String -Pattern "127.0.0.1:8888.*token=" | Select-Object -Last 1
    if ($tokenLine) {
        $url = $tokenLine.Line -replace '.*http://', 'http://'
        $url = $url -replace '\s.*$', ''
        $url = $url -replace '127\.0\.0\.1', 'localhost'
        $url = $url -replace ':8888', ':8889'
        Write-Host "🚀 Opening Jupyter: $url" -ForegroundColor Green
        Start-Process $url
    }
    else {
        Write-Host "⚠️  Jupyter not running. Starting services..." -ForegroundColor Yellow
        up
        Start-Sleep 3
        j  # Retry
    }
}
function m { Start-Process "http://localhost:5000" }     # MLflow  
function a { Start-Process "http://localhost:8501" }     # Streamlit App
function b { docker-compose exec notebooks bash }        # Bash

# =============================================================================
# 🚀 CONTAINER LIFECYCLE (Super fast)
# =============================================================================

function up { 
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🚀 Starting services..." -ForegroundColor Blue
    docker-compose up -d
    Write-Host "✅ All services running" -ForegroundColor Green
    Write-Host "   🎯 App: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "   📊 Jupyter: http://localhost:8889" -ForegroundColor Cyan
    Write-Host "   📈 MLflow: http://localhost:5000" -ForegroundColor Cyan
}

function down { 
    if (-not (Ensure-ProjectDirectory)) { return }
    docker-compose down
    Write-Host "🛑 Services stopped" -ForegroundColor Yellow
}

function reset {
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🔄 Resetting services..." -ForegroundColor Blue
    docker-compose down
    docker-compose up -d
    Write-Host "✅ Services reset" -ForegroundColor Green
}

function st { 
    if (-not (Ensure-ProjectDirectory)) { return }
    docker-compose ps 
}  # Status

# =============================================================================
# 🏗️ SELECTIVE CONTAINER BUILD (Optimized for development)
# =============================================================================

function build-app {
    """Build only chess_trainer container (lightweight, fast)"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🏗️ Building chess_trainer container only..." -ForegroundColor Blue
    docker-compose build chess_trainer
    Write-Host "✅ Chess trainer app container built!" -ForegroundColor Green
    Write-Host "💡 Run 'up-app' to start only the app services" -ForegroundColor Cyan
}

function build-notebooks {
    """Build only notebooks container (heavy ML dependencies)"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🏗️ Building notebooks container (this may take a while)..." -ForegroundColor Blue
    docker-compose build notebooks
    Write-Host "✅ Notebooks container built!" -ForegroundColor Green
    Write-Host "💡 Run 'up-ml' to start ML services" -ForegroundColor Cyan
}

function build-all {
    """Build all containers from scratch"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🏗️ Building all containers from scratch..." -ForegroundColor Blue
    docker-compose build
    Write-Host "✅ All containers built!" -ForegroundColor Green
    Write-Host "💡 Run 'up' to start all services" -ForegroundColor Cyan
}

function up-app {
    """Start only app-related services (chess_trainer, mlflow, postgres)"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🚀 Starting app services only..." -ForegroundColor Blue
    docker-compose up -d chess_trainer mlflow postgres
    Write-Host "✅ App services running" -ForegroundColor Green
    Write-Host "   🎯 App: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "   📈 MLflow: http://localhost:5000" -ForegroundColor Cyan
    Write-Host "💡 Run 'up-ml' to also start Jupyter notebooks" -ForegroundColor Yellow
}

function up-ml {
    """Start all services including notebooks (complete ML environment)"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🚀 Starting all services (including ML notebooks)..." -ForegroundColor Blue
    docker-compose up -d
    Write-Host "✅ Complete ML environment running" -ForegroundColor Green
    Write-Host "   🎯 App: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "   📊 Jupyter: http://localhost:8889" -ForegroundColor Cyan
    Write-Host "   📈 MLflow: http://localhost:5000" -ForegroundColor Cyan
}

# =============================================================================
# 🧪 DEVELOPMENT WORKFLOW
# =============================================================================

function dev {
    """Complete development environment setup"""
    if (-not (Ensure-ProjectDirectory)) { return }
    Write-Host "🔧 Setting up development environment..." -ForegroundColor Blue
    docker-compose up -d
    Start-Sleep -Seconds 3
    sync
    Write-Host "✅ Development ready!" -ForegroundColor Green
    Write-Host "Commands: ml (test) | j (jupyter) | m (mlflow) | a (app)" -ForegroundColor Cyan
}

function commit {
    param([string]$msg = "Quick update")
    git add .
    git commit -m $msg
    Write-Host "✅ Committed: $msg" -ForegroundColor Green
}

function push {
    $branch = git branch --show-current
    git push -u origin $branch
    Write-Host "🚀 Pushed branch: $branch" -ForegroundColor Green
}

function pull {
    git pull
    Write-Host "📥 Pulled latest changes" -ForegroundColor Green
}

# =============================================================================
# 📊 MONITORING & DEBUGGING
# =============================================================================

function logs { docker-compose logs -f notebooks }
function logsml { docker-compose logs -f mlflow }
function logsapp { docker-compose logs -f chess_trainer }

function clean {
    Write-Host "🧹 Cleaning Docker resources..." -ForegroundColor Yellow
    docker-compose down
    docker system prune -f
    Write-Host "✅ Cleaned" -ForegroundColor Green
}

function perf {
    """Show container performance"""
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# =============================================================================
# 🎯 ML-SPECIFIC TOOLS
# =============================================================================

function install {
    """Install Python package in notebook container"""
    param([string]$package)
    docker-compose exec notebooks pip install $package
    Write-Host "✅ Installed: $package" -ForegroundColor Green
}

function python {
    """Interactive Python in container"""
    docker-compose exec notebooks python -i
}

function notebook {
    """Execute specific notebook"""
    param([string]$name = "ml_workflow_integrated.ipynb")
    Write-Host "📓 Executing notebook: $name" -ForegroundColor Blue
    docker-compose exec notebooks jupyter nbconvert --execute --to notebook --inplace /notebooks/$name
    Write-Host "✅ Notebook executed" -ForegroundColor Green
}

function run {
    """Run any Python script in container"""
    param([string]$script)
    if (-not $script) {
        Write-Host "Usage: run script.py" -ForegroundColor Yellow
        return
    }
    sync
    docker-compose exec notebooks python /notebooks/$script
}

# =============================================================================
# 🔧 UTILITIES
# =============================================================================

function token {
    """Get current Jupyter token"""
    Write-Host "🔍 Getting Jupyter token..." -ForegroundColor Blue
    $logs = docker-compose logs notebooks --tail 50
    $tokenLine = $logs | Select-String -Pattern "127.0.0.1:8888.*token=" | Select-Object -Last 1
    if ($tokenLine) {
        $url = $tokenLine.Line -replace '.*http://', 'http://'
        $url = $url -replace '\s.*$', ''
        $url = $url -replace '127\.0\.0\.1', 'localhost'
        $url = $url -replace ':8888', ':8889'
        Write-Host "🎯 Current Jupyter URL:" -ForegroundColor Green
        Write-Host "$url" -ForegroundColor Cyan
        
        # Extract just the token
        if ($url -match 'token=([a-f0-9]+)') {
            Write-Host "🔑 Token: $($matches[1])" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "⚠️  No token found. Make sure notebooks container is running." -ForegroundColor Red
        Write-Host "Try running: up" -ForegroundColor Yellow
    }
}

function edit {
    """Edit file and auto-sync if in src/"""
    param([string]$file)
    if (-not $file) {
        Write-Host "Usage: edit filename" -ForegroundColor Yellow
        return
    }
    code $file
    if ($file -like "src/*") { 
        Write-Host "📝 File in src/, will sync after edit" -ForegroundColor Cyan
    }
}

function backup {
    """Quick backup of current work"""
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    git add .
    git commit -m "backup: $timestamp"
    Write-Host "💾 Backup created: $timestamp" -ForegroundColor Green
}

function branch {
    """Create and switch to new branch"""
    param([string]$name)
    if (-not $name) {
        Write-Host "Current branch: $(git branch --show-current)" -ForegroundColor Cyan
        git branch
        return
    }
    git checkout -b $name
    Write-Host "🌿 Created and switched to branch: $name" -ForegroundColor Green
}

function auto-install {
    """Install quick-helpers permanently in PowerShell profile"""
    $currentPath = Get-Location
    $profileContent = @"
# ⚡ CHESS TRAINER - Auto-load optimized commands
if (Test-Path "$currentPath\quick-helpers.ps1") {
    . "$currentPath\quick-helpers.ps1"
}
"@
    
    if (-not (Test-Path $PROFILE)) {
        New-Item -ItemType File -Path $PROFILE -Force | Out-Null
    }
    
    Add-Content -Path $PROFILE -Value $profileContent
    Write-Host "✅ Chess Trainer commands installed in PowerShell profile!" -ForegroundColor Green
    Write-Host "🔄 Restart PowerShell or run: . `$PROFILE" -ForegroundColor Cyan
}

# =============================================================================
# 📋 INFORMATION & HELP
# =============================================================================

function help {
    Write-Host @"
⚡ CHESS TRAINER - OPTIMIZED COMMANDS
====================================

🔥 CORE WORKFLOW (Most used):
  ml        Complete ML pipeline test
  tac       Test tactical features  
  test      Quick test with sync
  sync      Sync essential code (optimized)
  sync-ml   Sync only ML code to notebooks
  sync-app  Sync only app code  
  sync-scripts  Sync only scripts

⚡ INSTANT ACCESS (1 letter):
  j         Jupyter Lab (localhost:8889)
  m         MLflow UI (localhost:5000)  
  a         Streamlit App (localhost:8501)
  b         Bash in container

🚀 SERVICES:
  up        Start all services
  up-app    Start only app services (fast)
  up-ml     Start all services including notebooks
  down      Stop all services
  reset     Restart all services  
  st        Show status

🏗️ SELECTIVE BUILD (Optimized):
  build-app       Build only chess_trainer container (fast)
  build-notebooks Build only notebooks container (heavy)
  build-all       Build all containers from scratch

🧪 DEVELOPMENT:
  dev       Setup complete environment
  commit    Git commit with message
  push      Push current branch
  pull      Pull latest changes
  branch    Create/switch branch

📊 MONITORING:
  logs      Notebook container logs
  logsml    MLflow container logs
  logsapp   App container logs
  perf      Container performance
  clean     Clean Docker resources

🎯 ML TOOLS:
  mlinit      Initialize MLflow with PostgreSQL
  mltrain     Train chess error prediction model  
  mlpredict   Test chess move prediction
  mltest      Test MLflow PostgreSQL integration
  mlclean     Clean old MLflow SQLite file
  mlexp       Run ML experiment
  install     Install Python package
  python      Interactive Python
  notebook    Execute Jupyter notebook
  run         Run Python script

🔧 UTILITIES:
  token        Get Jupyter token/URL
  edit         Edit file (auto-sync src/)
  backup       Quick git backup  
  auto-install Install commands permanently
  help         Show this help

WORKFLOW EXAMPLES:
  # Quick app development (fastest):
  build-app && up-app
  
  # Full ML development:
  build-all && up-ml
  
  # Just changed app code:
  build-app && reset
  
  # Daily workflow:
  dev && ml && j
  
OPTIMIZATION TIPS:
  - Use 'build-app' for faster builds when only changing app code
  - Use 'up-app' to start lightweight services for app development  
  - Use 'up-ml' only when you need notebooks/ML features
  - 'build-notebooks' takes longer but has all ML dependencies
  
"@ -ForegroundColor Green
}

function info {
    """Show current project status"""
    Write-Host "🎯 CHESS TRAINER PROJECT STATUS" -ForegroundColor Blue
    Write-Host "================================" -ForegroundColor Blue
    Write-Host "📁 Directory: $(Get-Location)" -ForegroundColor Cyan
    Write-Host "🌿 Branch: $(git branch --show-current)" -ForegroundColor Cyan
    Write-Host "📊 Git Status:" -ForegroundColor Cyan
    git status --short
    Write-Host "`n🐳 Docker Services:" -ForegroundColor Cyan
    docker-compose ps
    Write-Host "`n⚡ Quick Commands: ml | tac | j | m | a" -ForegroundColor Yellow
}

# =============================================================================
# 🎉 STARTUP
# =============================================================================

Write-Host "⚡ CHESS TRAINER OPTIMIZED COMMANDS LOADED!" -ForegroundColor Green
Write-Host "Type 'help' for all commands or 'info' for project status" -ForegroundColor Cyan
Write-Host "Quick start: dev | ml | j | m | a | b" -ForegroundColor Yellow

# 🔬 ML Real Datasets Analysis
function Analyze-RealDatasets {
    <#
    .SYNOPSIS
        🔬 Quick analysis of real chess datasets
    .DESCRIPTION
        Run comprehensive ML analysis comparing elite, fide, novice, personal, and stockfish datasets
    #>
    Write-Host "🔬 Running Real Datasets Analysis..." -ForegroundColor Cyan
    Invoke-RealDatasetsAnalysis
}
