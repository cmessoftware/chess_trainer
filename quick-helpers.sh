#!/bin/bash

# ⚡ CHESS TRAINER - ULTRA-OPTIMIZED COMMANDS (Ubuntu/Container Version)
# Load with: source ./quick-helpers.sh
# Your daily workflow in super-fast commands!

# =============================================================================
# 🎯 AUTO-CONFIGURATION
# =============================================================================

# Auto-detect project root and set global variables
export CHESS_TRAINER_ROOT="${PWD}"
export CHESS_TRAINER_SRC="${CHESS_TRAINER_ROOT}/src"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Quick navigation function
ct() {
    """Quick navigate to chess trainer root"""
    cd "${CHESS_TRAINER_ROOT}"
    echo -e "${CYAN}📁 Navigated to chess trainer root${NC}"
}

# Helper function to ensure we're in the right directory
ensure_project_directory() {
    if [[ ! -f "docker-compose.yml" ]]; then
        if [[ -d "${CHESS_TRAINER_ROOT}" ]]; then
            cd "${CHESS_TRAINER_ROOT}"
            echo -e "${CYAN}📁 Switched to project directory: ${CHESS_TRAINER_ROOT}${NC}"
        else
            echo -e "${RED}❌ Error: Not in chess_trainer directory and can't find project root!${NC}"
            echo -e "${YELLOW}💡 Run this from the chess_trainer directory or use 'ct' to navigate there first${NC}"
            return 1
        fi
    fi
    return 0
}

# =============================================================================
# 🔥 CORE ML WORKFLOW (Most used - Super optimized)
# =============================================================================

ml() {
    """Complete ML pipeline test with sync"""
    ensure_project_directory || return 1
    echo -e "${BLUE}🧪 ML Pipeline Test...${NC}"
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose exec notebooks python /notebooks/validate_ml_pipeline_fixed.py
    echo -e "${GREEN}✅ ML test completed${NC}"
}

tac() {
    """Test tactical features specifically"""
    ensure_project_directory || return 1
    echo -e "${BLUE}🎯 Tactical Features Test...${NC}"
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose cp "test_tactical_preprocessing.py" notebooks:/notebooks/
    docker-compose exec notebooks python /notebooks/test_tactical_preprocessing.py
    echo -e "${GREEN}✅ Tactical test completed${NC}"
}

sync() {
    """Sync all source code to containers"""
    ensure_project_directory || return 1
    docker-compose cp "src/" notebooks:/notebooks/src/
    docker-compose cp "src/" chess_trainer:/app/src/
    echo -e "${GREEN}✅ Code synced${NC}"
}

test() {
    """Quick test with auto-sync"""
    ensure_project_directory || return 1
    sync
    docker-compose exec notebooks python /notebooks/validate_ml_pipeline_fixed.py
}

# =============================================================================
# ⚡ INSTANT ACCESS (1-2 letters - Lightning fast)
# =============================================================================

j() { 
    if command -v xdg-open > /dev/null; then
        xdg-open "http://localhost:8888"
    elif command -v open > /dev/null; then
        open "http://localhost:8888"
    else
        echo -e "${CYAN}🔗 Jupyter: http://localhost:8888${NC}"
    fi
}

m() { 
    if command -v xdg-open > /dev/null; then
        xdg-open "http://localhost:5000"
    elif command -v open > /dev/null; then
        open "http://localhost:5000"
    else
        echo -e "${CYAN}🔗 MLflow: http://localhost:5000${NC}"
    fi
}

a() { 
    if command -v xdg-open > /dev/null; then
        xdg-open "http://localhost:8501"
    elif command -v open > /dev/null; then
        open "http://localhost:8501"
    else
        echo -e "${CYAN}🔗 Streamlit App: http://localhost:8501${NC}"
    fi
}

b() { docker-compose exec notebooks bash; }

# =============================================================================
# 🚀 CONTAINER LIFECYCLE (Super fast)
# =============================================================================

up() {
    ensure_project_directory || return 1
    echo -e "${BLUE}🚀 Starting services...${NC}"
    docker-compose up -d
    echo -e "${GREEN}✅ All services running${NC}"
    echo -e "${CYAN}   🎯 App: http://localhost:8501${NC}"
    echo -e "${CYAN}   📊 Jupyter: http://localhost:8888${NC}"
    echo -e "${CYAN}   📈 MLflow: http://localhost:5000${NC}"
}

down() {
    ensure_project_directory || return 1
    docker-compose down
    echo -e "${YELLOW}🛑 Services stopped${NC}"
}

reset() {
    ensure_project_directory || return 1
    echo -e "${BLUE}🔄 Resetting services...${NC}"
    docker-compose down
    docker-compose up -d
    echo -e "${GREEN}✅ Services reset${NC}"
}

st() {
    ensure_project_directory || return 1
    docker-compose ps
}

# =============================================================================
# 🧪 DEVELOPMENT WORKFLOW
# =============================================================================

dev() {
    """Complete development environment setup"""
    ensure_project_directory || return 1
    echo -e "${BLUE}🔧 Setting up development environment...${NC}"
    docker-compose up -d
    sleep 3
    sync
    echo -e "${GREEN}✅ Development ready!${NC}"
    echo -e "${CYAN}Commands: ml (test) | j (jupyter) | m (mlflow) | a (app)${NC}"
}

commit() {
    local msg="${1:-Quick update}"
    git add .
    git commit -m "$msg"
    echo -e "${GREEN}✅ Committed: $msg${NC}"
}

push() {
    local branch=$(git branch --show-current)
    git push -u origin "$branch"
    echo -e "${GREEN}🚀 Pushed branch: $branch${NC}"
}

pull() {
    git pull
    echo -e "${GREEN}📥 Pulled latest changes${NC}"
}

# =============================================================================
# 📊 MONITORING & DEBUGGING
# =============================================================================

logs() { docker-compose logs -f notebooks; }
logsml() { docker-compose logs -f mlflow; }
logsapp() { docker-compose logs -f chess_trainer; }

clean() {
    echo -e "${YELLOW}🧹 Cleaning Docker resources...${NC}"
    docker-compose down
    docker system prune -f
    echo -e "${GREEN}✅ Cleaned${NC}"
}

perf() {
    """Show container performance"""
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# =============================================================================
# 🎯 ML-SPECIFIC TOOLS
# =============================================================================

install() {
    """Install Python package in notebook container"""
    local package="$1"
    if [[ -z "$package" ]]; then
        echo -e "${YELLOW}Usage: install <package_name>${NC}"
        return 1
    fi
    docker-compose exec notebooks pip install "$package"
    echo -e "${GREEN}✅ Installed: $package${NC}"
}

python() {
    """Interactive Python in container"""
    docker-compose exec notebooks python -i
}

notebook() {
    """Execute specific notebook"""
    local name="${1:-ml_workflow_integrated.ipynb}"
    echo -e "${BLUE}📓 Executing notebook: $name${NC}"
    docker-compose exec notebooks jupyter nbconvert --execute --to notebook --inplace "/notebooks/$name"
    echo -e "${GREEN}✅ Notebook executed${NC}"
}

run() {
    """Run any Python script in container"""
    local script="$1"
    if [[ -z "$script" ]]; then
        echo -e "${YELLOW}Usage: run script.py${NC}"
        return 1
    fi
    sync
    docker-compose exec notebooks python "/notebooks/$script"
}

# =============================================================================
# 🔧 UTILITIES
# =============================================================================

edit() {
    """Edit file and auto-sync if in src/"""
    local file="$1"
    if [[ -z "$file" ]]; then
        echo -e "${YELLOW}Usage: edit filename${NC}"
        return 1
    fi
    
    # Try different editors in order of preference
    if command -v code > /dev/null; then
        code "$file"
    elif command -v nano > /dev/null; then
        nano "$file"
    elif command -v vim > /dev/null; then
        vim "$file"
    else
        echo -e "${RED}No suitable editor found (code, nano, vim)${NC}"
        return 1
    fi
    
    if [[ "$file" == src/* ]]; then
        echo -e "${CYAN}📝 File in src/, will sync after edit${NC}"
    fi
}

backup() {
    """Quick backup of current work"""
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    git add .
    git commit -m "backup: $timestamp"
    echo -e "${GREEN}💾 Backup created: $timestamp${NC}"
}

branch() {
    """Create and switch to new branch"""
    local name="$1"
    if [[ -z "$name" ]]; then
        echo -e "${CYAN}Current branch: $(git branch --show-current)${NC}"
        git branch
        return 0
    fi
    git checkout -b "$name"
    echo -e "${GREEN}🌿 Created and switched to branch: $name${NC}"
}

auto_install() {
    """Install quick-helpers permanently in bash profile"""
    local current_path=$(pwd)
    local profile_file=""
    
    # Determine which profile file to use
    if [[ -f "$HOME/.bashrc" ]]; then
        profile_file="$HOME/.bashrc"
    elif [[ -f "$HOME/.bash_profile" ]]; then
        profile_file="$HOME/.bash_profile"
    elif [[ -f "$HOME/.profile" ]]; then
        profile_file="$HOME/.profile"
    else
        profile_file="$HOME/.bashrc"
        touch "$profile_file"
    fi
    
    local profile_content="
# ⚡ CHESS TRAINER - Auto-load optimized commands
if [[ -f \"$current_path/quick-helpers.sh\" ]]; then
    source \"$current_path/quick-helpers.sh\"
fi"
    
    echo "$profile_content" >> "$profile_file"
    echo -e "${GREEN}✅ Chess Trainer commands installed in $profile_file!${NC}"
    echo -e "${CYAN}🔄 Restart terminal or run: source $profile_file${NC}"
}

# =============================================================================
# 📋 INFORMATION & HELP
# =============================================================================

help() {
    cat << 'EOF'
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
  edit         Edit file (auto-sync src/)
  backup       Quick git backup  
  auto_install Install commands permanently
  help         Show this help

EXAMPLES:
  dev               # Setup everything
  ml                # Test ML pipeline  
  commit "fix bug"  # Quick commit
  install pandas    # Install package
  run test.py       # Run script
  
EOF
}

info() {
    """Show current project status"""
    echo -e "${BLUE}🎯 CHESS TRAINER PROJECT STATUS${NC}"
    echo -e "${BLUE}================================${NC}"
    echo -e "${CYAN}📁 Directory: $(pwd)${NC}"
    echo -e "${CYAN}🌿 Branch: $(git branch --show-current)${NC}"
    echo -e "${CYAN}📊 Git Status:${NC}"
    git status --short
    echo -e "\n${CYAN}🐳 Docker Services:${NC}"
    docker-compose ps
    echo -e "\n${YELLOW}⚡ Quick Commands: ml | tac | j | m | a${NC}"
}

# =============================================================================
# 🎉 STARTUP
# =============================================================================

echo -e "${GREEN}⚡ CHESS TRAINER OPTIMIZED COMMANDS LOADED!${NC}"
echo -e "${CYAN}Type 'help' for all commands or 'info' for project status${NC}"
echo -e "${YELLOW}Quick start: dev | ml | j | m | a${NC}"
