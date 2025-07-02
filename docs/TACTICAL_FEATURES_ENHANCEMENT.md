# Tactical Features Enhancement Guide

## Problem
The `score_diff` and `error_label` features have very low representation (~10%) in exported datasets because they require separate tactical analysis that is often not executed.

## Solutions

### 1. Integrated Processing (Recommended for New Data)
For processing new games with both features and tactics in one step:

```bash
# Process personal games with full tactical analysis
python src/scripts/generate_features_with_tactics.py --source personal --max-games 1000

# Process elite games
python src/scripts/generate_features_with_tactics.py --source elite --max-games 500
```

**Pros:** Complete coverage, single step, automatically registers analyzed games
**Cons:** Slower (10-100x), resource intensive

### 2. Lightweight Estimation (Recommended for Large Datasets)
For quick approximation of tactical features:

```bash
# Add estimated tactical features to personal dataset
python src/scripts/estimate_tactical_features.py --source personal --limit 10000

# Add to all sources
python src/scripts/estimate_tactical_features.py --limit 50000
```

**Pros:** Very fast (~100x faster), good coverage
**Cons:** Approximate values, not engine-precise

### 3. Enhanced Batch Analysis (Recommended for Existing Data)
For processing existing features with better efficiency:

```bash
# Analyze games missing tactical data (avoids reprocessing)
python src/scripts/enhanced_tactical_analysis.py --source personal --max-games 1000

# Force reprocess all games (ignores analyzed_tacticals table)
python src/scripts/enhanced_tactical_analysis.py --source personal --force-reprocess
```

**Pros:** Engine-accurate, batched for efficiency, tracks analyzed games
**Cons:** Still resource intensive

**Note:** This script automatically updates the `analyzed_tacticals` table to track which games have been processed, preventing duplicate work on subsequent runs.

## Workflow Recommendations

### For Personal Datasets (<5,000 games):
1. Use **Enhanced Batch Analysis** for existing data
2. Use **Integrated Processing** for new data

```bash
# Process existing personal games
python src/scripts/enhanced_tactical_analysis.py --source personal --max-games 5000

# Check coverage
python src/scripts/export_features_dataset_parallel.py --source personal
```

### For Large Datasets (>10,000 games):
1. Use **Lightweight Estimation** for initial coverage
2. Use **Enhanced Batch Analysis** for high-value subsets

```bash
# Quick estimation for all
python src/scripts/estimate_tactical_features.py --source elite --limit 50000

# Precise analysis for recent games
python src/scripts/enhanced_tactical_analysis.py --source elite --max-games 1000
```

### For Mixed Approach:
1. Lightweight estimation for bulk coverage
2. Precise analysis for specific games/players

```bash
# Bulk estimation
python src/scripts/estimate_tactical_features.py --source personal

# Precise analysis for specific players (would need filtering enhancement)
python src/scripts/enhanced_tactical_analysis.py --source personal --max-games 500
```

## Expected Results

| Method         | Coverage | Speed     | Accuracy | Use Case            |
| -------------- | -------- | --------- | -------- | ------------------- |
| Integrated     | 60-80%   | Slow      | High     | New data processing |
| Lightweight    | 95-100%  | Very Fast | Medium   | Bulk datasets       |
| Enhanced Batch | 60-80%   | Medium    | High     | Existing data       |

## Performance Tips

1. **Start small**: Test with `--max-games 100` first
2. **Monitor resources**: Tactical analysis is CPU/memory intensive
3. **Use source filtering**: Process one source at a time
4. **Batch processing**: Let enhanced batch analysis handle memory management
5. **Mixed strategy**: Use lightweight for bulk + precise for important subsets

## Troubleshooting

### Low Coverage After Tactical Analysis
- Check that Stockfish is properly installed
- Verify games have valid PGN format
- Some positions are skipped (opening moves, low complexity)

### Performance Issues
- Reduce max-games parameter
- Use fewer parallel workers
- Consider lightweight estimation instead

### Memory Issues
- Process smaller batches
- Use enhanced batch analysis (auto-manages memory)
- Clear Docker containers between runs

## Validation

After running any method, validate the results:

```bash
# Export and check coverage
python src/scripts/export_features_dataset_parallel.py --source personal

# Check in Python
python -c "
import pandas as pd
df = pd.read_parquet('/app/src/data/export/personal/features.parquet')
total = len(df)
with_score = df['score_diff'].notna().sum()
print(f'Coverage: {with_score}/{total} ({with_score/total*100:.1f}%)')
"
```

## Architecture Notes

### Repository Pattern Implementation
All tactical analysis scripts have been refactored to use the repository pattern with SQLAlchemy ORM:

- **No Hardcoded SQL**: All database queries use repository methods instead of raw SQL strings
- **Type Safety**: SQLAlchemy provides better type checking and IDE support
- **Maintainability**: Database logic is centralized in repository classes
- **Testability**: Repository methods can be easily mocked for unit testing

### Key Repository Methods Used:
- `features_repo.get_features_missing_tactical_data()` - Gets features needing tactical analysis
- `analyzed_repo.get_coverage_by_source()` - Gets analysis coverage statistics
- `analyzed_repo.save_analyzed_tactical_hash()` - Registers analyzed games
- `features_repo.get_unanalyzed_game_ids()` - Gets games that need analysis

### Database Tracking

## Database Tracking

### analyzed_tacticals Table
The system tracks which games have been analyzed for tactics in the `analyzed_tacticals` table:

```sql
-- Check which games have been analyzed
SELECT COUNT(*) as analyzed_games FROM analyzed_tacticals;

-- Check analysis coverage by source
SELECT g.source, 
       COUNT(DISTINCT g.game_id) as total_games,
       COUNT(DISTINCT at.game_id) as analyzed_games,
       ROUND(COUNT(DISTINCT at.game_id) * 100.0 / COUNT(DISTINCT g.game_id), 2) as coverage_pct
FROM games g
LEFT JOIN analyzed_tacticals at ON g.game_id = at.game_id
GROUP BY g.source;
```

### Benefits:
- **Prevents Duplicate Work**: Avoids reprocessing already analyzed games
- **Resume Processing**: Can safely restart interrupted analysis jobs
- **Progress Tracking**: Shows exactly how many games have been analyzed
- **Source-Specific Analysis**: Can track coverage per data source

### Manual Management:
```bash
# Clear analyzed_tacticals to force reprocessing (use with caution)
# python -c "from db.repository.analyzed_tacticals_repository import Analyzed_tacticalsRepository; repo = Analyzed_tacticalsRepository(); repo.clear_all()"

# Remove specific game from analyzed_tacticals to reprocess it
# python -c "from db.repository.analyzed_tacticals_repository import Analyzed_tacticalsRepository; repo = Analyzed_tacticalsRepository(); repo.remove_game('GAME_ID')"
```
