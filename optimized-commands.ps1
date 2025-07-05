# OPTIMIZED CHESS TRAINER COMMANDS
# Specific optimizations for your most-used workflows

# =============================================================================
# 🔥 SUPER-FAST ML TESTING (Your most used commands)
# =============================================================================

function ml {
    """Single command for complete ML testing pipeline"""
    Write-Host "🧪 Running complete ML test..." -ForegroundColor Blue
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose cp "test_tactical_preprocessing.py" notebooks:/notebooks/
    docker-compose exec notebooks python /notebooks/validate_ml_pipeline_fixed.py
}

function tac {
    """Test tactical features only"""
    Write-Host "🎯 Testing tactical features..." -ForegroundColor Blue
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose cp "test_tactical_preprocessing.py" notebooks:/notebooks/
    docker-compose exec notebooks python /notebooks/test_tactical_preprocessing.py
}

function sync {
    """Sync all source code instantly"""
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose cp "src/" chess_trainer:/app/src/
    Write-Host "✅ Code synced" -ForegroundColor Green
}

# =============================================================================
# ⚡ INSTANT SERVICE ACCESS (1-letter commands)
# =============================================================================

function j { Start-Process "http://localhost:8888" }     # Jupyter
function m { Start-Process "http://localhost:5000" }     # MLflow
function a { Start-Process "http://localhost:8501" }     # App
function b { docker-compose exec notebooks bash }        # Bash

# =============================================================================
# 🚀 CONTAINER LIFECYCLE (Super fast)
# =============================================================================

function up { 
    docker-compose up -d
    Write-Host "🚀 All services up" -ForegroundColor Green
}

function down { 
    docker-compose down
    Write-Host "🛑 All services down" -ForegroundColor Yellow
}

function reset {
    docker-compose down
    docker-compose up -d
    Write-Host "🔄 Services reset" -ForegroundColor Blue
}

function st { docker-compose ps }  # Status

# =============================================================================
# 🧪 DEVELOPMENT WORKFLOW SHORTCUTS
# =============================================================================

function dev {
    """Complete development environment setup"""
    Write-Host "🔧 Setting up development environment..." -ForegroundColor Blue
    docker-compose up -d
    sync
    Write-Host "✅ Development ready!" -ForegroundColor Green
    Write-Host "Access: j (Jupyter) | m (MLflow) | a (App)" -ForegroundColor Cyan
}

function test {
    """Run quick ML test with latest code"""
    sync
    docker-compose exec notebooks python /notebooks/validate_ml_pipeline_fixed.py
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
    Write-Host "🚀 Pushed $branch" -ForegroundColor Green
}

# =============================================================================
# 📊 MONITORING & DEBUGGING (Optimized)
# =============================================================================

function logs { docker-compose logs -f notebooks }
function logs-ml { docker-compose logs -f mlflow }
function logs-app { docker-compose logs -f chess_trainer }

function clean {
    docker-compose down
    docker system prune -f
    Write-Host "🧹 Cleaned" -ForegroundColor Yellow
}

# =============================================================================
# 🎯 ML-SPECIFIC SHORTCUTS (Your Daily Tools)
# =============================================================================

function notebook {
    """Quick access to specific notebook"""
    param([string]$name = "ml_workflow_integrated.ipynb")
    docker-compose exec notebooks jupyter nbconvert --execute --to notebook --inplace /notebooks/$name
}

function install {
    """Install package in notebook container"""
    param([string]$package)
    docker-compose exec notebooks pip install $package
    Write-Host "✅ Installed $package" -ForegroundColor Green
}

function python {
    """Interactive Python in container"""
    docker-compose exec notebooks python -i
}

# =============================================================================
# 🔧 FILE OPERATIONS (Streamlined)
# =============================================================================

function edit {
    """Edit file and sync to container"""
    param([string]$file)
    code $file
    if ($file -like "src/*") { sync }
}

function run {
    """Run any Python script in container"""
    param([string]$script)
    sync
    docker-compose exec notebooks python /notebooks/$script
}

# =============================================================================
# 📈 PERFORMANCE MONITORING
# =============================================================================

function perf {
    """Show container performance"""
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

function space {
    """Show disk usage"""
    docker system df
}

# =============================================================================
# 🎉 HELP SYSTEM
# =============================================================================

function help {
    Write-Host @"
🎯 CHESS TRAINER - OPTIMIZED COMMANDS
====================================

🔥 CORE ML TESTING:
  ml        Complete ML pipeline test
  tac       Test tactical features
  test      Quick test with sync
  sync      Sync source code

⚡ INSTANT ACCESS (1-letter):
  j         Jupyter Lab
  m         MLflow UI  
  a         Streamlit App
  b         Bash in container

🚀 SERVICES:
  up        Start all services
  down      Stop all services  
  reset     Restart all services
  st        Show status

🧪 DEVELOPMENT:
  dev       Setup complete environment
  commit    Quick git commit
  push      Push current branch
  
📊 MONITORING:
  logs      Show notebook logs
  perf      Container performance
  clean     Clean Docker resources

🔧 UTILITIES:
  install   Install Python package
  python    Interactive Python
  run       Run script in container
  
Type any command to execute!
"@ -ForegroundColor Green
}

# Display startup message
Write-Host "⚡ CHESS TRAINER OPTIMIZED COMMANDS LOADED!" -ForegroundColor Green
Write-Host "Type 'help' for command list or use:" -ForegroundColor Cyan
Write-Host "  dev  - Setup everything" -ForegroundColor Yellow  
Write-Host "  ml   - Test ML pipeline" -ForegroundColor Yellow
Write-Host "  j/m/a - Open Jupyter/MLflow/App" -ForegroundColor Yellow
