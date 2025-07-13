# 🚀 ML Preprocessing Pipeline - Configuration & Usage Guide

## Overview

The ML preprocessing pipeline for Chess Trainer provides comprehensive data preparation capabilities for training machine learning models on chess game data. It handles multiple source types with specialized transformations and ensures data quality and consistency.

## Source Types & Configurations

### Source Categories

| Source Type   | Description                 | ELO Range            | Platform          | Standardization    |
| ------------- | --------------------------- | -------------------- | ----------------- | ------------------ |
| **personal**  | User's personal games       | Variable (1000-2200) | Mixed             | ✅ Required         |
| **novice**    | Beginner/intermediate games | 1200-2000            | Chess.com/Lichess | ✅ Required         |
| **elite**     | Expert level games          | >2000                | Chess.com/Lichess | ✅ Required         |
| **fide**      | Official tournament games   | >2000                | FIDE events       | ❌ Already standard |
| **stockfish** | Engine testing data         | N/A                  | Synthetic         | ❌ No ELO data      |

### Source-Specific Configurations

```python
source_configs = {
    "personal": {
        "elo_standardization": True,      # Mixed platforms need standardization
        "scaler_type": "standard",        # Standard scaling for mixed data
        "handle_outliers": True,          # Personal games may have outliers
        "platform_detection": "auto"     # Auto-detect from site field
    },
    
    "novice": {
        "elo_standardization": True,      # Platform-specific ratings
        "scaler_type": "robust",          # Robust to outliers in novice play
        "handle_outliers": True,          # Novice play more variable
        "special_handling": "conservative_play"
    },
    
    "elite": {
        "elo_standardization": True,      # High-level platform differences
        "scaler_type": "standard",        # Consistent high-level play
        "handle_outliers": False,         # Elite play generally consistent
        "special_handling": "tactical_depth"
    },
    
    "fide": {
        "elo_standardization": False,     # FIDE ratings are the standard
        "scaler_type": "standard",        # Official tournament consistency
        "handle_outliers": False,         # Official games well-regulated
        "special_handling": "tournament_context"
    },
    
    "stockfish": {
        "elo_standardization": False,     # No ELO data
        "scaler_type": "minmax",          # Bounded engine evaluations
        "handle_outliers": True,          # Engine testing may have extremes
        "special_handling": "score_clipping"
    }
}
```

## Pipeline Components

### 1. ELO Standardization

Addresses rating differences between platforms:

```python
# Lichess to FIDE-like conversion
lichess_standardized = (lichess_rating * 0.92) - 100

# Chess.com to FIDE-like conversion  
chesscom_standardized = (chesscom_rating * 1.02) + 50
```

**Rationale**: Lichess ratings are typically 100-150 points higher than FIDE equivalents, while Chess.com ratings are closer to FIDE standards.

### 2. Feature Categories

#### Numerical Continuous
- `material_balance`, `material_total`, `branching_factor`
- `self_mobility`, `opponent_mobility`, `score_diff`
- `move_number`, `num_pieces`

#### Numerical Binary  
- `has_castling_rights`, `is_repetition`, `is_low_mobility`
- `is_center_controlled`, `is_pawn_endgame`, `is_stockfish_test`

#### Categorical Ordinal
- `phase`: opening → middlegame → endgame
- `error_label`: ok → inaccuracy → mistake → blunder

#### Categorical Nominal
- `player_color`, `site`, `event`, `result`

#### ELO Features
- `white_elo`, `black_elo`, `standardized_elo`
- `elo_difference`, `elo_category`, `elo_advantage`

### 3. Missing Value Strategies

| Feature Type         | Strategy             | Rationale                     |
| -------------------- | -------------------- | ----------------------------- |
| Numerical Continuous | Median               | Robust to outliers            |
| Numerical Binary     | Most Frequent        | Preserves distribution        |
| Categorical Ordinal  | Most Frequent        | Maintains order relationships |
| Categorical Nominal  | Constant ("unknown") | Explicit missing indicator    |
| ELO Features         | Median               | Rating-specific handling      |
| Text Features        | Constant ("unknown") | Explicit missing marker       |

### 4. Derived Features

#### Mobility Features
```python
mobility_ratio = self_mobility / (opponent_mobility + 1)
mobility_advantage = self_mobility - opponent_mobility
total_mobility = self_mobility + opponent_mobility
```

#### Material Features
```python
material_per_piece = material_total / (num_pieces + 1)
```

#### Position Complexity
```python
complexity_score = branching_factor * num_pieces
```

#### Score-based Features
```python
score_diff_abs = abs(score_diff)
is_losing_position = (score_diff < -100)
is_winning_position = (score_diff > 100)
```

#### ELO-based Features
```python
elo_squared = standardized_elo ** 2
elo_log = log(standardized_elo + 1)
is_favorite = (player_elo > opponent_elo)
```

## Advanced Feature Engineering

### Temporal Features
- `year`, `month`, `day_of_week`, `quarter`
- `is_weekend`, `is_holiday_season`

### Sequence Features (by game)
- `score_diff_prev`, `score_diff_change`, `score_diff_trend`
- `momentum_positive`, `momentum_streak`

### Opponent Features
- `elo_difference_abs`, `elo_gap_category`
- `is_favorite`, `elo_advantage`

### Opening Features
- `is_opening_phase`, `opening_length`
- `early_castling`

### Tactical Features
- `has_pin`, `has_fork`, `has_skewer`, etc.
- `tactical_density`, `tactical_complexity`

### Endgame Features
- `king_activity_endgame`, `pawn_endgame_advantage`
- `endgame_proximity`

### Positional Features
- `mobility_dominance`, `piece_activity_index`
- `positional_pressure`

## Usage Examples

### Basic Single Source Processing

```python
from modules.ml_preprocessing import create_source_specific_preprocessor

# Load your data
df = load_chess_data_from_db(source_type="elite")

# Create source-specific preprocessor
preprocessor = create_source_specific_preprocessor("elite")

# Preprocess data
df_processed = preprocessor.fit_transform(df, source_type="elite")

# Prepare for ML training
X_train, X_val, X_test, y_train, y_val, y_test = preprocessor.prepare_train_test_split(
    df_processed, 
    target_column="error_label"
)
```

### Multi-Source Processing

```python
from modules.ml_preprocessing import preprocess_multiple_sources

# Load data from multiple sources
source_data = {
    "novice": load_chess_data("novice"),
    "elite": load_chess_data("elite"), 
    "personal": load_chess_data("personal")
}

# Process all sources together
df_combined, processing_report = preprocess_multiple_sources(
    source_data, 
    target_column="error_label"
)
```

### Command Line Usage

```bash
# Process all sources individually
python src/scripts/prepare_ml_datasets.py --all-sources --max-samples 10000

# Process specific source
python src/scripts/prepare_ml_datasets.py --source elite --max-samples 5000

# Create combined dataset
python src/scripts/prepare_ml_datasets.py --combined --output-dir datasets/ml_ready

# Quick personal model preparation
python src/scripts/prepare_ml_datasets.py --source personal --quick-mode
```

### Testing the Pipeline

```bash
# Run full test suite
python src/scripts/test_ml_preprocessing.py

# Test specific source
python src/scripts/test_ml_preprocessing.py --source elite --verbose
```

## Data Quality Validation

The pipeline includes comprehensive quality validation:

### Quality Metrics
- Missing value percentage
- Duplicate row detection
- Data type consistency
- Memory usage analysis
- Feature correlation analysis

### Source-Specific Validations
- ELO range validation per source type
- Platform detection accuracy
- Feature distribution consistency
- Outlier detection and handling

## Performance Characteristics

### Processing Speed
- **Small datasets** (1K samples): ~0.1-0.5 seconds
- **Medium datasets** (10K samples): ~1-5 seconds  
- **Large datasets** (100K samples): ~10-50 seconds

### Memory Usage
- Raw data: ~50-100 MB per 10K samples
- Processed data: ~100-200 MB per 10K samples (with derived features)

### Scalability
- Supports batch processing for large datasets
- Memory-efficient chunk processing available
- Parallel processing for multi-source workflows

## Output Formats

### Datasets
- **Parquet**: Optimized for ML workflows, preserves data types
- **CSV**: Human-readable, compatible with most tools

### Files Generated
- `{source}_ml_dataset_{timestamp}.parquet`
- `{source}_train_{timestamp}.parquet`
- `{source}_val_{timestamp}.parquet`
- `{source}_test_{timestamp}.parquet`
- `ml_preprocessing_report_{timestamp}.json`

### Processing Reports
Comprehensive JSON reports including:
- Processing statistics
- Quality metrics
- Configuration used
- Feature engineering summary
- Performance benchmarks

## Integration with Existing Pipeline

### Database Integration
- Uses existing `FeaturesRepository` and `GamesRepository`
- Maintains compatibility with PostgreSQL schema
- Leverages existing feature generation infrastructure

### Compatibility
- Works with existing `generate_features_parallel.py`
- Integrates with EDA notebooks
- Compatible with training scripts

## Best Practices

### For Personal Models
1. Use `personal` source type with auto-platform detection
2. Enable outlier handling for variable skill levels
3. Apply comprehensive feature engineering
4. Use stratified splits by ELO category

### For Research/Analysis
1. Use `elite` or `fide` sources for consistency
2. Disable outlier handling to preserve authentic data
3. Document preprocessing steps for reproducibility
4. Include source distribution in model evaluation

### For Production Models
1. Combine multiple sources for robustness
2. Validate preprocessing pipeline thoroughly
3. Monitor data drift over time
4. Maintain preprocessing version control

## Troubleshooting

### Common Issues

#### Missing ELO Data
```python
# Handle sources without ELO information
if source_type == "stockfish":
    # Skip ELO-based features
    pass
```

#### Platform Detection Errors
```python
# Manually specify platform if auto-detection fails
df_processed = preprocessor.standardize_elo(df, platform="chess.com")
```

#### Memory Issues with Large Datasets
```python
# Use chunked processing
chunk_size = 10000
for chunk in pd.read_sql(query, con=connection, chunksize=chunk_size):
    processed_chunk = preprocessor.transform(chunk)
```

#### Inconsistent Feature Names
```python
# Get ML-ready columns after preprocessing
ml_columns = preprocessor.get_feature_importance_ready_columns(df_processed)
```

## Environment Configuration

### Required Environment Variables
```bash
CHESS_TRAINER_DB_URL="postgresql://user:pass@host:port/db"
ML_DATASETS_OUTPUT_PATH="datasets/ml_ready"
MAX_WORKERS=4
FEATURES_PER_CHUNK=500
```

### Dependencies
```txt
pandas>=1.5.0
numpy>=1.20.0  
scikit-learn>=1.0.0
psycopg2>=2.8.0
```

## Version History

- **v1.0**: Initial implementation with basic preprocessing
- **v1.1**: Added ELO standardization and source-specific configs
- **v1.2**: Comprehensive feature engineering integration
- **v1.3**: Multi-source processing and performance optimization

---

*This pipeline represents the complete implementation of the 30% missing ML preprocessing functionality for Chess Trainer Issue #66.*
