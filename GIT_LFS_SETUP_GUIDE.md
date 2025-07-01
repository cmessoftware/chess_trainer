# Git LFS Setup Guide for Chess Trainer

## Overview

This project uses **Git Large File Storage (LFS)**## 📊 Best Practices for Large Datasets

### **Files that should NOT be in the repository:**
- **Large compressed files** (*.zip, *.gz, *.tar): Use external storage services or APIs
- **Massive raw datasets** (*.pgn): Use Lichess/Chess.com APIs for on-demand downloads
- **Temporary files**: Generate locally as needed

### **When to use LFS for notebooks:**
- **Notebooks >1MB**: Especially those with extensive outputs
- **EDA notebooks**: With large visualizations and analysis results
- **ML analysis notebooks**: With model outputs and performance metrics
- **Research notebooks**: With comprehensive statistical analysis

### **Recommended use of external sources:**
```bash
# Download datasets from Lichess
curl "https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.bz2"

# Use Chess.com API
curl "https://api.chess.com/pub/player/{username}/games/{YYYY}/{MM}"
```to efficiently manage large datasets, notebooks, and model files. Git LFS replaces large files with text pointers inside Git, while storing the file contents on a remote server.

## 📋 Files Tracked by Git LFS

The following file types are automatically tracked by Git LFS:

### **Machine Learning Models**
- `*.pkl` - Trained machine learning models
- `*.h5` - Keras/TensorFlow model files
- `*.joblib` - Scikit-learn serialized models
- `*.model` - Generic model files

### **Processed Datasets**
- `*.parquet` - Processed feature datasets
- `*.csv` - Large CSV datasets

### **Notebooks with Large Outputs**
- `*.ipynb` - Jupyter notebooks with analysis and models
  - **Especially important for**: EDA notebooks, ML analysis, large visualizations
  - **Threshold**: Notebooks >1MB should use LFS

### **Files NOT Tracked by LFS** (Excluded for Efficiency)
- `*.zip`, `*.gz`, `*.tar` - Compressed files (use external sources)
- `*.pgn` - Raw chess game files (use lichess/chess.com APIs)
- `*.png`, `*.jpg` - Images (kept small and manageable)

## 🚀 Quick Setup

### 1. Install Git LFS
```bash
# On Ubuntu/Debian
apt-get install git-lfs

# On macOS
brew install git-lfs

# On Windows
# Download from: https://git-lfs.github.io/
```

### 2. Initialize Git LFS
```bash
git lfs install
```

### 3. Clone Repository
```bash
git clone https://github.com/cmessoftware/chess_trainer.git
cd chess_trainer
```

### 4. Pull LFS Files
```bash
git lfs pull
```

## 🐳 Docker Environment

The Docker environment automatically handles Git LFS:

### **Build & Run Notebooks Container**
```bash
# Build the notebooks container
docker-compose build notebooks

# Run with full repository access
docker-compose up notebooks
```

The `dockerfile.notebooks` includes:
- ✅ Git LFS installation and configuration
- ✅ Full repository access at `/chess_trainer`
- ✅ Automatic LFS file pulling
- ✅ JupyterLab with complete dataset access

## � Best Practices for Large Datasets

### **Files that should NOT be in the repository:**
- **Large compressed files** (*.zip, *.gz, *.tar): Use external storage services or APIs
- **Massive raw datasets** (*.pgn): Use Lichess/Chess.com APIs for on-demand download
- **Temporary files**: Generate locally as needed

### **Recommended use of external sources:**
```bash
# Download datasets from Lichess
curl "https://database.lichess.org/standard/lichess_db_standard_rated_2024-01.pgn.bz2"

# Use Chess.com API
curl "https://api.chess.com/pub/player/{username}/games/{YYYY}/{MM}"
```

### **Recommended structure:**
```
datasets/
├── export/           # Processed datasets (parquet, csv) → LFS
├── models/           # Trained models (pkl, h5) → LFS  
├── notebooks/        # Analysis (ipynb) → LFS (optional)
└── scripts/          # Download scripts → Normal Git
```

## �📊 Working with Large Files

### **Check LFS Status**
```bash
# See which files are tracked by LFS
git lfs track

# Check LFS file status
git lfs status

# List all LFS files
git lfs ls-files
```

### **Adding New Large Files**
```bash
# Track new file types
git lfs track "*.new_extension"

# Add and commit
git add .gitattributes
git add your_large_file.extension
git commit -m "Add large file with LFS"
```

### **Pull Specific LFS Files**
```bash
# Pull only specific files
git lfs pull --include="*.ipynb"

# Pull excluding certain files
git lfs pull --exclude="*.zip"
```

## 🔧 Configuration Details

### **Current .gitattributes Configuration**
```
# Machine Learning Models
*.pkl filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.joblib filter=lfs diff=lfs merge=lfs -text
*.model filter=lfs diff=lfs merge=lfs -text

# Processed Datasets
*.parquet filter=lfs diff=lfs merge=lfs -text
*.csv filter=lfs diff=lfs merge=lfs -text

# Notebooks with large outputs
*.ipynb filter=lfs diff=lfs merge=lfs -text
```

### **Docker Configuration**
The `dockerfile.notebooks` is optimized for LFS:
- **WORKDIR**: `/chess_trainer` (full repository access)
- **Git LFS**: Pre-installed and configured
- **Auto-pull**: LFS files downloaded on container start
- **GitHub CLI**: Available for authentication

## 🚨 Troubleshooting

### **LFS Files Not Downloading**
```bash
# Force pull all LFS files
git lfs pull --all

# Check LFS remote
git lfs env
```

### **Authentication Issues**
```bash
# Configure Git credentials
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Use GitHub CLI for authentication
gh auth login
```

### **Container Issues**
```bash
# Rebuild container with latest LFS config
docker-compose build --no-cache notebooks

# Check container LFS status
docker-compose exec notebooks git lfs status
```

## 📈 Performance Benefits

- **Repository Size**: ~10MB (vs ~70MB without LFS)
- **Clone Speed**: 5x faster initial clones
- **Bandwidth**: Only downloads needed files
- **History**: Clean Git history without binary diffs

## 🔗 Related Documentation

- [Dataset Volumes Configuration](./DATASETS_VOLUMES_CONFIG.md)
- [Development Setup](./README.md#development-setup)
- [Docker Configuration](./README.md#docker-usage)

---

*For more information about Git LFS, visit: https://git-lfs.github.io/*
