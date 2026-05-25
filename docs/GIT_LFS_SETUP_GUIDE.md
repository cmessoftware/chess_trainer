# Git LFS Setup Guide - Chess Trainer

## Overview

Git Large File Storage (LFS) is essential for the Chess Trainer project due to large datasets, ML models, and binary artifacts. This guide covers setup, configuration, and best practices.

## Why Git LFS?

Chess Trainer handles large files:
- **📊 Datasets**: Parquet files (>100MB)
- **🤖 ML Models**: Trained models (>50MB) 
- **🖼️ Images**: Architecture diagrams, plots
- **📁 Artifacts**: Compressed PGN archives

## Installation

### Windows
```powershell
# Using Git for Windows (includes LFS)
winget install Git.Git

# Or install separately
winget install GitLFS.GitLFS

# Verify installation
git lfs version
```

### Linux/macOS
```bash
# Ubuntu/Debian
sudo apt-get install git-lfs

# macOS
brew install git-lfs

# CentOS/RHEL
sudo yum install git-lfs
```

## Project Setup

### Initialize LFS

```bash
# Enable LFS in repository
git lfs install

# Track large file types
git lfs track "*.parquet"
git lfs track "*.pkl"
git lfs track "*.joblib"
git lfs track "*.h5"
git lfs track "*.zip"
git lfs track "*.tar.gz"
git lfs track "*.jpg"
git lfs track "*.png"
git lfs track "*.pdf"

# Commit .gitattributes
git add .gitattributes
git commit -m "Configure Git LFS tracking"
```

### Current .gitattributes

```bash
# Chess Trainer - Git LFS Configuration

# Datasets
*.parquet filter=lfs diff=lfs merge=lfs -text
*.csv filter=lfs diff=lfs merge=lfs -text
*.json filter=lfs diff=lfs merge=lfs -text

# ML Models
*.pkl filter=lfs diff=lfs merge=lfs -text
*.joblib filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.pb filter=lfs diff=lfs merge=lfs -text
*.onnx filter=lfs diff=lfs merge=lfs -text

# Archives
*.zip filter=lfs diff=lfs merge=lfs -text
*.tar.gz filter=lfs diff=lfs merge=lfs -text
*.7z filter=lfs diff=lfs merge=lfs -text

# Images
*.jpg filter=lfs diff=lfs merge=lfs -text
*.jpeg filter=lfs diff=lfs merge=lfs -text
*.png filter=lfs diff=lfs merge=lfs -text
*.gif filter=lfs diff=lfs merge=lfs -text
*.pdf filter=lfs diff=lfs merge=lfs -text

# Database dumps
*.sql filter=lfs diff=lfs merge=lfs -text
*.dump filter=lfs diff=lfs merge=lfs -text
```

## Usage Workflow

### Adding Large Files

```bash
# Add large dataset
cp large_dataset.parquet data/
git add data/large_dataset.parquet
git commit -m "Add large dataset via LFS"

# Verify LFS tracking
git lfs ls-files
```

### Checking LFS Status

```bash
# View tracked files
git lfs ls-files

# Check which files will be tracked
git lfs track

# View LFS status
git lfs status
```

### Pushing/Pulling with LFS

```bash
# Push (uploads LFS files)
git push origin main

# Pull with LFS files
git lfs pull

# Clone with LFS
git clone https://github.com/user/chess_trainer.git
cd chess_trainer
git lfs pull
```

## File Management

### Current LFS Files in Project

```bash
# Check current LFS files
$ git lfs ls-files

architecture.jpg
data/datasets/chess_games_unified.parquet
data/datasets/chess_games_sample.parquet
mlruns/models/model.pkl
notebooks/correlation_matrix_cleaned.png
```

### File Size Monitoring

```bash
# Find large files (>10MB)
find . -size +10M -type f

# Check repository size
du -sh .git/

# LFS storage usage
git lfs fsck
```

### Migrating Existing Large Files

```bash
# Migrate files already in Git to LFS
git lfs migrate import --include="*.parquet,*.pkl"

# Verify migration
git lfs ls-files

# Force push (rewrites history)
git push --force-with-lease origin main
```

## Best Practices

### File Organization

```bash
# Recommended directory structure
data/
  raw/                    # Raw datasets (LFS)
  processed/             # Processed datasets (LFS)
  external/              # External data sources (LFS)

models/
  trained/               # Trained models (LFS)
  checkpoints/           # Model checkpoints (LFS)
  artifacts/             # Model artifacts (LFS)

notebooks/
  figures/               # Generated plots (LFS)
  exports/               # Notebook exports (LFS)
```

### Gitignore Configuration

```bash
# .gitignore - Exclude temporary large files

# Temporary datasets
*.tmp
*.temp

# Jupyter checkpoints
.ipynb_checkpoints/

# MLflow artifacts (use LFS for important ones)
mlruns/*/artifacts/*
!mlruns/*/artifacts/*.pkl
!mlruns/*/artifacts/*.joblib

# Cache files
__pycache__/
*.pyc
.cache/
```

### Performance Optimization

```bash
# Configure LFS for better performance
git config lfs.concurrent 8
git config lfs.batch true

# Skip LFS during shallow clones (CI/CD)
git clone --depth 1 --filter=blob:none <url>
GIT_LFS_SKIP_SMUDGE=1 git clone <url>
```

## Automation Scripts

### LFS Health Check

```bash
#!/bin/bash
# scripts/check_lfs_health.sh

echo "🔍 Git LFS Health Check"
echo "====================="

# Check LFS installation
if ! command -v git-lfs &> /dev/null; then
    echo "❌ Git LFS not installed"
    exit 1
fi

# Check LFS tracking
echo "📊 Tracked file types:"
git lfs track

# Check large files not in LFS
echo "⚠️ Large files not in LFS:"
find . -size +10M -type f ! -path './.git/*' ! -path './mlruns/*' | while read file; do
    if ! git lfs ls-files | grep -q "$file"; then
        echo "  $file ($(du -h "$file" | cut -f1))"
    fi
done

echo "✅ Health check complete"
```

### Automated LFS Setup

```powershell
# scripts/setup_lfs.ps1

Write-Host "🚀 Setting up Git LFS for Chess Trainer" -ForegroundColor Green

# Check if LFS is installed
if (!(Get-Command git-lfs -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git LFS not found. Installing..." -ForegroundColor Red
    winget install GitLFS.GitLFS
}

# Initialize LFS
git lfs install

# Track file types
$fileTypes = @(
    "*.parquet", "*.pkl", "*.joblib", "*.h5", 
    "*.zip", "*.tar.gz", "*.jpg", "*.png", "*.pdf"
)

foreach ($type in $fileTypes) {
    git lfs track $type
    Write-Host "📎 Tracking $type" -ForegroundColor Yellow
}

# Commit .gitattributes
git add .gitattributes
git commit -m "Configure Git LFS for Chess Trainer"

Write-Host "✅ Git LFS setup complete!" -ForegroundColor Green
```

## Troubleshooting

### Common Issues

#### 1. "This exceeds GitHub's file size limit"

```bash
# File was added before LFS tracking
git rm --cached large_file.parquet
git lfs track "*.parquet"
git add large_file.parquet
git commit -m "Move large file to LFS"
```

#### 2. LFS files not downloading

```bash
# Force download LFS files
git lfs pull

# Or specific files
git lfs pull --include="*.parquet"
```

#### 3. Bandwidth limit exceeded

```bash
# Check LFS quota
git lfs fsck

# Use Git LFS cache
GIT_LFS_SKIP_SMUDGE=1 git clone <url>
cd repo
git lfs pull
```

#### 4. Large .git directory

```bash
# Clean LFS cache
git lfs prune

# Remove old LFS objects
git lfs prune --recent
```

### Diagnostic Commands

```bash
# LFS configuration
git lfs env

# LFS logs
git lfs logs last

# Verify LFS integrity
git lfs fsck

# Check tracking patterns
git lfs track --list
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/ci.yml
name: CI with LFS

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
      with:
        lfs: true
    
    - name: Setup Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python -m pytest tests/
```

### Docker Integration

```dockerfile
# Dockerfile with LFS
FROM python:3.11-slim

# Install Git LFS
RUN apt-get update && \
    apt-get install -y git git-lfs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clone repository with LFS
RUN git lfs install
COPY . .
RUN git lfs pull

# Continue with application setup...
```

## Monitoring and Maintenance

### Regular Maintenance Tasks

```bash
# Weekly cleanup
git lfs prune --recent

# Monthly health check
./scripts/check_lfs_health.sh

# Quarterly review
git lfs fsck
du -sh .git/lfs/
```

### Storage Monitoring

```python
# scripts/monitor_lfs.py
import subprocess
import json

def get_lfs_info():
    result = subprocess.run(['git', 'lfs', 'fsck'], 
                          capture_output=True, text=True)
    
    info = {
        'total_files': len(subprocess.run(['git', 'lfs', 'ls-files'], 
                          capture_output=True, text=True).stdout.strip().split('\n')),
        'git_dir_size': subprocess.run(['du', '-sh', '.git/'], 
                       capture_output=True, text=True).stdout.split()[0]
    }
    
    return info

if __name__ == '__main__':
    info = get_lfs_info()
    print(json.dumps(info, indent=2))
```

## References

- [Git LFS Documentation](https://git-lfs.github.io/)
- [GitHub LFS Guide](https://docs.github.com/en/repositories/working-with-files/managing-large-files)
- [Project Setup Script](../scripts/setup_lfs.ps1)
- [LFS Configuration](../.gitattributes)

---

**Document Version**: 1.0  
**Last Updated**: December 29, 2025  
**Maintained by**: Chess Trainer Development Team
