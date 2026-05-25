# ELO Standardization Guide

## Overview

This guide describes the ELO standardization system implemented in Chess Trainer to normalize player ratings across different sources and time periods.

## Problem Statement

Chess ratings come from different sources:
- **Lichess**: Typically higher ratings
- **Chess.com**: More conservative ratings  
- **FIDE**: Official ratings, often lower
- **Historical games**: Rating inflation over time

## Solution: ELO Standardization

### Standardization Formula

```python
standardized_elo = ((original_elo - source_mean) / source_std) * target_std + target_mean
```

### Parameters by Source

```python
STANDARDIZATION_PARAMS = {
    'lichess': {'mean': 1500, 'std': 350, 'target_mean': 1400, 'target_std': 300},
    'chess_com': {'mean': 1200, 'std': 280, 'target_mean': 1400, 'target_std': 300},
    'fide': {'mean': 1800, 'std': 200, 'target_mean': 1400, 'target_std': 300},
    'personal': {'mean': 1350, 'std': 250, 'target_mean': 1400, 'target_std': 300}
}
```

## Implementation

### Database Schema

```sql
ALTER TABLE games ADD COLUMN elo_standardized INTEGER;
ALTER TABLE games ADD COLUMN opponent_elo_standardized INTEGER;
```

### Python Implementation

```python
class EloStandardizer:
    def __init__(self):
        self.params = STANDARDIZATION_PARAMS
    
    def standardize_elo(self, elo: int, source: str) -> int:
        """Standardize ELO rating based on source"""
        if source not in self.params:
            return elo
        
        params = self.params[source]
        standardized = (
            (elo - params['mean']) / params['std']
        ) * params['target_std'] + params['target_mean']
        
        return max(800, min(2800, int(standardized)))  # Clamp to reasonable range
```

### Batch Update Script

```python
#!/usr/bin/env python3

from src.modules.elo_standardization import EloStandardizer
from src.db.repository.games_repository import GamesRepository

def update_standardized_elos():
    standardizer = EloStandardizer()
    repo = GamesRepository()
    
    games = repo.get_all_games()
    
    for game in games:
        # Standardize player ELO
        std_elo = standardizer.standardize_elo(
            game.elo, 
            game.source or 'personal'
        )
        
        # Standardize opponent ELO
        std_opp_elo = standardizer.standardize_elo(
            game.opponent_elo, 
            game.source or 'personal'
        )
        
        # Update database
        repo.update_standardized_elos(
            game.id, 
            std_elo, 
            std_opp_elo
        )
```

## Validation

### Distribution Analysis

```python
import matplotlib.pyplot as plt
import seaborn as sns

def plot_elo_distributions(games_df):
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Original ELOs by source
    sns.boxplot(data=games_df, x='source', y='elo', ax=axes[0,0])
    axes[0,0].set_title('Original ELO Distribution by Source')
    
    # Standardized ELOs by source
    sns.boxplot(data=games_df, x='source', y='elo_standardized', ax=axes[0,1])
    axes[0,1].set_title('Standardized ELO Distribution by Source')
    
    # Before/after histograms
    games_df['elo'].hist(ax=axes[1,0], alpha=0.7, label='Original')
    games_df['elo_standardized'].hist(ax=axes[1,1], alpha=0.7, label='Standardized')
    
    plt.tight_layout()
    plt.show()
```

### Quality Metrics

```python
def calculate_standardization_metrics(df):
    metrics = {}
    
    for source in df['source'].unique():
        source_data = df[df['source'] == source]
        
        metrics[source] = {
            'original_mean': source_data['elo'].mean(),
            'original_std': source_data['elo'].std(),
            'standardized_mean': source_data['elo_standardized'].mean(),
            'standardized_std': source_data['elo_standardized'].std(),
            'count': len(source_data)
        }
    
    return metrics
```

## Usage in ML Pipeline

### Feature Engineering

```python
def extract_elo_features(game):
    features = {
        'player_elo_std': game.elo_standardized,
        'opponent_elo_std': game.opponent_elo_standardized,
        'elo_difference_std': game.elo_standardized - game.opponent_elo_standardized,
        'elo_tier': get_elo_tier(game.elo_standardized)
    }
    return features

def get_elo_tier(elo):
    if elo < 1000: return 'beginner'
    elif elo < 1300: return 'novice'
    elif elo < 1600: return 'intermediate'
    elif elo < 1900: return 'advanced'
    elif elo < 2200: return 'expert'
    else: return 'master'
```

### Model Training

```python
# Use standardized ELOs for consistent training
X = features_df[['player_elo_std', 'opponent_elo_std', 'elo_difference_std', ...]]
y = features_df['error_label']

model = LogisticRegression()
model.fit(X, y)
```

## Monitoring

### Drift Detection

```python
def detect_elo_drift(recent_games, historical_mean=1400, threshold=50):
    recent_mean = recent_games['elo_standardized'].mean()
    drift = abs(recent_mean - historical_mean)
    
    if drift > threshold:
        print(f"⚠️ ELO drift detected: {drift:.1f} points")
        return True
    return False
```

### Update Frequency

- **Initial setup**: Run full standardization
- **Daily updates**: Standardize new games
- **Monthly review**: Check for parameter drift
- **Quarterly analysis**: Update standardization parameters

## References

- [ELO Standardization Implementation](../src/modules/elo_standardization.py)
- [Games Repository](../src/db/repository/games_repository.py)
- [Feature Engineering Guide](../notebooks/4-chess_trainer_analysis_extended_eda.ipynb)
