# CHESS TRAINER - Versión: v0.1.51-7633ef4

# Chess Trainer (stable base version)

This project allows you to analyze and tactically train chess games using data science and interactive visualization.

## Features

- Generation of datasets from PGN files
- Tactical enrichment with Stockfish
- Error classification with automatic labels (`error_label`)
- Exploration and visualization with Streamlit and notebooks
- Training of supervised models for error prediction
- Logging and history of predictions

## Requirements

- Python 3.8+
- streamlit
- pandas, seaborn, matplotlib
- python-chess
- scikit-learn
- Stockfish 

## Structure

See the [`README.md`](./README.md) file for the complete project structure.

## Quick usage

### Docker Setup (Recommended)

#### Windows Users - One-Command Setup:
```powershell
.\build_up_clean_all.ps1
```

#### 🎯 Benefits of PowerShell Automation:
- **Complete Environment Setup**: Builds and starts all containers with one command
- **Cross-Platform Compatibility**: Native Windows PowerShell support without Unix permission requirements
- **Automatic Cleanup**: Removes unused Docker images to optimize disk usage
- **Service Integration**: Starts both main application and Jupyter notebooks containers
- **Background Operation**: Containers run detached for continuous development workflow
- **Error Reduction**: Automated sequence minimizes manual configuration mistakes

#### Manual Docker Setup:
```bash
docker-compose build
docker-compose up -d
```

### Local Development:
```bash
# Run the main interface
streamlit run app.py (In development)

# Generate datasets
cd /app/src/pipeline
./run_pipeline.sh interactive
```

## Credits

Developed by cmessoftware as part of their practical work for the Data Science Diploma.
