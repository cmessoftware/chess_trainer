# ⚡ CHESS TRAINER - ULTRA-OPTIMIZED COMMANDS
# Load with: . .\quick-helpers.ps1
# Your daily workflow in super-fast commands!

# =============================================================================
# 🔥 CORE ML WORKFLOW (Most used - Super optimized)
# =============================================================================

function ml {
    """Complete ML pipeline test with sync"""
    Write-Host "🧪 ML Pipeline Test..." -ForegroundColor Blue
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose exec notebooks python /notebooks/validate_ml_pipeline_fixed.py
    Write-Host "✅ ML test completed" -ForegroundColor Green
}

function tac {
    """Test tactical features specifically"""
    Write-Host "🎯 Tactical Features Test..." -ForegroundColor Blue
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose cp "test_tactical_preprocessing.py" notebooks:/notebooks/
    docker-compose exec notebooks python /notebooks/test_tactical_preprocessing.py
    Write-Host "✅ Tactical test completed" -ForegroundColor Green
}

function sync {
    """Sync all source code to containers"""
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose cp "src/" chess_trainer:/app/src/
    Write-Host "✅ Code synced" -ForegroundColor Green
}

function test {
    """Quick test with auto-sync"""
    sync
    docker-compose exec notebooks python /notebooks/validate_ml_pipeline_fixed.py
}

# =============================================================================
# ⚡ INSTANT ACCESS (1-2 letters - Lightning fast)
# =============================================================================

function j { Start-Process "http://localhost:8888" }     # Jupyter
function m { Start-Process "http://localhost:5000" }     # MLflow  
function a { Start-Process "http://localhost:8501" }     # Streamlit App
function b { docker-compose exec notebooks bash }        # Bash

# =============================================================================
# 🚀 CONTAINER LIFECYCLE (Super fast)
# =============================================================================

function up { 
    Write-Host "🚀 Starting services..." -ForegroundColor Blue
    docker-compose up -d
    Write-Host "✅ All services running" -ForegroundColor Green
    Write-Host "   🎯 App: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "   📊 Jupyter: http://localhost:8888" -ForegroundColor Cyan
    Write-Host "   📈 MLflow: http://localhost:5000" -ForegroundColor Cyan
}

function down { 
    docker-compose down
    Write-Host "🛑 Services stopped" -ForegroundColor Yellow
}

function reset {
    Write-Host "🔄 Resetting services..." -ForegroundColor Blue
    docker-compose down
    docker-compose up -d
    Write-Host "✅ Services reset" -ForegroundColor Green
}

function st { docker-compose ps }  # Status

# =============================================================================
# 🧪 DEVELOPMENT WORKFLOW
# =============================================================================

function dev {
    """Complete development environment setup"""
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
  sync      Sync source code

⚡ INSTANT ACCESS (1 letter):
  j         Jupyter Lab (localhost:8888)
  m         MLflow UI (localhost:5000)  
  a         Streamlit App (localhost:8501)
  b         Bash in container

🚀 SERVICES:
  up        Start all services
  down      Stop all services
  reset     Restart all services  
  st        Show status

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
  install   Install Python package
  python    Interactive Python
  notebook  Execute Jupyter notebook
  run       Run Python script

🔧 UTILITIES:
  edit      Edit file (auto-sync src/)
  backup    Quick git backup
  help      Show this help

EXAMPLES:
  dev               # Setup everything
  ml                # Test ML pipeline  
  commit "fix bug"  # Quick commit
  install pandas    # Install package
  run test.py       # Run script
  
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
Write-Host "Quick start: dev | ml | j | m | a" -ForegroundColor Yellow
