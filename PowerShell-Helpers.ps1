# Chess Trainer Development Helpers
# Add these functions to your PowerShell profile for enhanced productivity

# =============================================================================
# CONTAINER MANAGEMENT
# =============================================================================

function Start-ChessTrainer {
    """Start all Chess Trainer services"""
    Write-Host "🚀 Starting Chess Trainer services..." -ForegroundColor Green
    docker-compose up -d
    Write-Host "✅ Services started. Access points:" -ForegroundColor Green
    Write-Host "   🎯 Streamlit App: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "   📊 Jupyter Lab:   http://localhost:8888" -ForegroundColor Cyan
    Write-Host "   📈 MLflow UI:     http://localhost:5000" -ForegroundColor Cyan
}

function Stop-ChessTrainer {
    """Stop all Chess Trainer services"""
    Write-Host "🛑 Stopping Chess Trainer services..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "✅ Services stopped" -ForegroundColor Green
}

function Restart-ChessTrainer {
    """Clean restart of all services"""
    Write-Host "🔄 Restarting Chess Trainer services..." -ForegroundColor Blue
    docker-compose down
    docker-compose up -d
    Write-Host "✅ Services restarted" -ForegroundColor Green
}

function Show-ChessTrainerStatus {
    """Show status of all services"""
    Write-Host "📊 Chess Trainer Services Status:" -ForegroundColor Blue
    docker-compose ps
}

# =============================================================================
# ML DEVELOPMENT SHORTCUTS
# =============================================================================

function Test-MLPipeline {
    """Test the ML preprocessing pipeline in container"""
    Write-Host "🧪 Testing ML Pipeline..." -ForegroundColor Blue
    
    # Sync latest code
    docker-compose cp "src/" notebooks:/notebooks/src/
    
    # Run validation
    docker-compose exec notebooks python /notebooks/validate_ml_pipeline_fixed.py
    
    Write-Host "✅ ML Pipeline test completed" -ForegroundColor Green
}

function Test-TacticalFeatures {
    """Test tactical features preprocessing with MLflow validation"""
    Write-Host "🎯 Testing Tactical Features..." -ForegroundColor Blue
    
    # Sync code and run test
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose cp "test_tactical_preprocessing.py" notebooks:/notebooks/
    docker-compose cp "simple_ml_test.py" notebooks:/notebooks/
    
    # Run preprocessing test
    Write-Host "🧪 Running preprocessing validation..." -ForegroundColor Cyan
    docker-compose exec notebooks python /notebooks/test_tactical_preprocessing.py
    
    # Run ML integration test  
    Write-Host "📈 Running MLflow integration test..." -ForegroundColor Cyan
    docker-compose exec notebooks python /notebooks/simple_ml_test.py
    
    Write-Host "✅ Tactical features test completed" -ForegroundColor Green
}

function Open-Jupyter {
    """Open Jupyter Lab in browser"""
    Write-Host "📊 Opening Jupyter Lab..." -ForegroundColor Blue
    Start-Process "http://localhost:8888"
}

function Open-MLflow {
    """Open MLflow UI in browser"""
    Write-Host "📈 Opening MLflow UI..." -ForegroundColor Blue
    Start-Process "http://localhost:5000"
}

# Importamos las funciones de MLflow con PostgreSQL
. "$PSScriptRoot\mlflow-helpers.ps1"

function Open-StreamlitApp {
    """Open Streamlit app in browser"""
    Write-Host "🎯 Opening Streamlit App..." -ForegroundColor Blue
    Start-Process "http://localhost:8501"
}

# =============================================================================
# CONTAINER INTERACTION
# =============================================================================

function Enter-NotebooksContainer {
    """Enter the notebooks container with bash"""
    Write-Host "🐳 Entering notebooks container..." -ForegroundColor Blue
    docker-compose exec notebooks bash
}

function Enter-AppContainer {
    """Enter the main app container with bash"""
    Write-Host "🐳 Entering app container..." -ForegroundColor Blue
    docker-compose exec chess_trainer bash
}

function Run-InContainer {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Command,
        [string]$Service = "notebooks"
    )
    """Run a command in the specified container"""
    Write-Host "⚡ Running in $Service container: $Command" -ForegroundColor Yellow
    docker-compose exec $Service $Command
}

function Python-InContainer {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Script,
        [string]$Service = "notebooks"
    )
    """Run a Python script in container"""
    Write-Host "🐍 Running Python script: $Script" -ForegroundColor Blue
    
    # Sync source code first
    docker-compose cp "src/" ${Service}:/notebooks/src/
    
    # Run the script
    docker-compose exec $Service python $Script
}

# =============================================================================
# FILE SYNCHRONIZATION
# =============================================================================

function Sync-ToContainer {
    param(
        [Parameter(Mandatory = $true)]
        [string]$LocalPath,
        [Parameter(Mandatory = $true)]
        [string]$ContainerPath,
        [string]$Service = "notebooks"
    )
    """Sync files to container"""
    Write-Host "📁 Syncing $LocalPath to $Service:$ContainerPath" -ForegroundColor Cyan
    docker-compose cp $LocalPath ${Service}:$ContainerPath
    Write-Host "✅ Sync completed" -ForegroundColor Green
}

function Sync-FromContainer {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ContainerPath,
        [Parameter(Mandatory = $true)]
        [string]$LocalPath,
        [string]$Service = "notebooks"
    )
    """Sync files from container"""
    Write-Host "📁 Syncing $Service:$ContainerPath to $LocalPath" -ForegroundColor Cyan
    docker-compose cp ${Service}:$ContainerPath $LocalPath
    Write-Host "✅ Sync completed" -ForegroundColor Green
}

function Sync-SourceCode {
    """Sync all source code to containers"""
    Write-Host "📦 Syncing source code to containers..." -ForegroundColor Blue
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose cp "src/" chess_trainer:/app/src/
    Write-Host "✅ Source code synced" -ForegroundColor Green
}

# =============================================================================
# LOGGING AND MONITORING
# =============================================================================

function Show-ContainerLogs {
    param(
        [string]$Service = "notebooks",
        [int]$Lines = 50
    )
    """Show container logs"""
    Write-Host "📋 Showing last $Lines lines from $Service..." -ForegroundColor Blue
    docker-compose logs --tail=$Lines -f $Service
}

function Show-AllLogs {
    """Show logs from all services"""
    Write-Host "📋 Showing logs from all services..." -ForegroundColor Blue
    docker-compose logs -f
}

function Monitor-Resources {
    """Monitor Docker resource usage"""
    Write-Host "📊 Docker Resource Usage:" -ForegroundColor Blue
    docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
}

# =============================================================================
# MAINTENANCE
# =============================================================================

function Clean-Docker {
    """Clean up Docker resources"""
    Write-Host "🧹 Cleaning Docker resources..." -ForegroundColor Yellow
    docker-compose down
    docker system prune -f
    docker volume prune -f
    Write-Host "✅ Docker cleanup completed" -ForegroundColor Green
}

function Update-Dependencies {
    """Update dependencies in containers"""
    Write-Host "📦 Updating dependencies..." -ForegroundColor Blue
    docker-compose exec notebooks pip install --upgrade -r /notebooks/requirements.txt
    Write-Host "✅ Dependencies updated" -ForegroundColor Green
}

# =============================================================================
# GIT WORKFLOW HELPERS
# =============================================================================

function Quick-Commit {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )
    """Quick commit with automated staging"""
    Write-Host "📝 Quick commit: $Message" -ForegroundColor Blue
    git add .
    git commit -m $Message
    Write-Host "✅ Committed successfully" -ForegroundColor Green
}

function Push-Branch {
    """Push current branch to origin"""
    $branch = git branch --show-current
    Write-Host "🚀 Pushing branch: $branch" -ForegroundColor Blue
    git push -u origin $branch
    Write-Host "✅ Branch pushed successfully" -ForegroundColor Green
}

# =============================================================================
# SHORTCUTS ALIASES
# =============================================================================

# Quick aliases for common commands
Set-Alias -Name ct-start -Value Start-ChessTrainer
Set-Alias -Name ct-stop -Value Stop-ChessTrainer
Set-Alias -Name ct-restart -Value Restart-ChessTrainer
Set-Alias -Name ct-status -Value Show-ChessTrainerStatus
Set-Alias -Name ct-test -Value Test-MLPipeline
Set-Alias -Name ct-tactical -Value Test-TacticalFeatures
Set-Alias -Name ct-jupyter -Value Open-Jupyter
Set-Alias -Name ct-mlflow -Value Open-MLflow
Set-Alias -Name ct-app -Value Open-StreamlitApp
Set-Alias -Name ct-bash -Value Enter-NotebooksContainer
Set-Alias -Name ct-logs -Value Show-ContainerLogs
Set-Alias -Name ct-sync -Value Sync-SourceCode
Set-Alias -Name ct-clean -Value Clean-Docker

# Display help
function Show-ChessTrainerHelp {
    Write-Host @"
🎯 Chess Trainer Development Helpers
=====================================

📦 CONTAINER MANAGEMENT:
  ct-start       Start all services
  ct-stop        Stop all services  
  ct-restart     Restart all services
  ct-status      Show services status

🧪 ML DEVELOPMENT:
  ct-test        Test ML pipeline
  ct-tactical    Test tactical features
  ct-sync        Sync source code

🌐 BROWSER ACCESS:
  ct-jupyter     Open Jupyter Lab
  ct-mlflow      Open MLflow UI
  ct-app         Open Streamlit App

🐳 CONTAINER ACCESS:
  ct-bash        Enter notebooks container
  ct-logs        Show container logs

🧹 MAINTENANCE:
  ct-clean       Clean Docker resources

📝 EXAMPLES:
  ct-start                           # Start all services
  ct-test                           # Test ML pipeline
  Run-InContainer "pip list"        # Run command in container
  Python-InContainer "/notebooks/script.py"  # Run Python script
  Sync-ToContainer "data/" "/notebooks/data/" # Sync files

Type 'Show-ChessTrainerHelp' anytime to see this help.
"@ -ForegroundColor Green
}

Write-Host "✅ Chess Trainer development helpers loaded!" -ForegroundColor Green
Write-Host "Type 'Show-ChessTrainerHelp' for available commands." -ForegroundColor Cyan
