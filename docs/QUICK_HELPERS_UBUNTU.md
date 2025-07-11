# Quick Helpers for Ubuntu/Container Environment

## Overview
`quick-helpers.sh` is the bash equivalent of `quick-helpers.ps1`, designed to work in Ubuntu environments and inside Docker containers.

## Installation & Usage

### 1. Inside Docker Container
```bash
# Copy the script into the container (if needed)
docker-compose cp quick-helpers.sh notebooks:/notebooks/

# Enter the container
docker-compose exec notebooks bash

# Make executable and load
chmod +x /notebooks/quick-helpers.sh
source /notebooks/quick-helpers.sh
```

### 2. Host Ubuntu System
```bash
# Make executable
chmod +x quick-helpers.sh

# Load commands for current session
source ./quick-helpers.sh

# Install permanently in bash profile
auto_install
```

### 3. From Host System (Managing Containers)
```bash
# Load commands for current session
source ./quick-helpers.sh

# Use any command (they will work from host)
dev      # Setup development environment
ml       # Run ML pipeline test
sync     # Sync code to containers
```

## Key Differences from PowerShell Version

### Browser Opening
- **PowerShell**: Uses `Start-Process` to open URLs
- **Bash**: Uses `xdg-open` (Linux) or `open` (macOS), falls back to displaying URL

### Path Handling
- **PowerShell**: Uses `Join-Path` and Windows-style paths
- **Bash**: Uses standard Unix path concatenation with `/`

### Color Output
- **PowerShell**: Uses `-ForegroundColor` parameter
- **Bash**: Uses ANSI escape codes for colors

### Function Naming
- **PowerShell**: Uses `auto-install` (with hyphen)
- **Bash**: Uses `auto_install` (with underscore, as hyphens are not allowed in bash function names)

## Core Commands (Same as PowerShell)

### 🔥 Most Used
- `ml` - Complete ML pipeline test
- `tac` - Test tactical features
- `sync` - Sync source code
- `dev` - Setup complete environment

### ⚡ Instant Access
- `j` - Open Jupyter (localhost:8888)
- `m` - Open MLflow (localhost:5000)
- `a` - Open Streamlit App (localhost:8501)
- `b` - Enter bash in container

### 🚀 Services
- `up` - Start all services
- `down` - Stop all services
- `reset` - Restart all services
- `st` - Show status

## Testing
```bash
# Run the test script
chmod +x test-helpers.sh
./test-helpers.sh
```

## Cross-Platform Workflow

You can use both scripts depending on your environment:

1. **Windows Development**: Use `quick-helpers.ps1`
2. **Container Work**: Use `quick-helpers.sh`
3. **Linux/macOS**: Use `quick-helpers.sh`

Both scripts provide identical functionality, just adapted for their respective environments.
