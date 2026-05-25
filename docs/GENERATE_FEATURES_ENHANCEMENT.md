# Generate Features Parallel Script - Source Filtering Enhancement

## Summary

Enhanced the `/app/src/scripts/generate_features_parallel.py` script to support source-based filtering for chess game feature generation.

## New Features Added

### ✅ **Source-Based Filtering**
- **New `--source` parameter** to filter games by source
- **Support for multiple sources**: lichess, chess.com, elite_games, etc.
- **Automatic source validation** through existing repository methods

### ✅ **Enhanced Command-Line Interface**
- **Improved argument parsing** with proper type checking
- **Detailed help documentation** with usage examples
- **Better parameter validation** and error reporting

### ✅ **Optimized Processing Logic**
- **Intelligent game selection** using `get_games_by_pagination_not_analyzed()`
- **Automatic exclusion of processed games** to avoid duplicate work
- **Better progress tracking** with detailed chunk-level reporting

### ✅ **Improved Error Handling & Logging**
- **Comprehensive statistics tracking** (processed, skipped, errors)
- **Better error reporting** with context and traceback information
- **Progress indicators** for chunk processing

## Usage Examples

### Basic Usage
```bash
# Generate features for all games (max 1000)
python src/scripts/generate_features_parallel.py

# Generate features for specific number of games
python src/scripts/generate_features_parallel.py --max-games 500
```

### Source-Specific Processing
```bash
# Process only Lichess games
python src/scripts/generate_features_parallel.py --source lichess --max-games 1000

# Process only Chess.com games  
python src/scripts/generate_features_parallel.py --source chess.com --max-games 2000

# Process only elite games
python src/scripts/generate_features_parallel.py --source elite_games --max-games 100
```

### Help & Documentation
```bash
# Show help with all available options
python src/scripts/generate_features_parallel.py --help
```

## Technical Improvements

### **Database Integration**
- **PostgreSQL compatibility** maintained from previous migration
- **Efficient querying** using source-aware repository methods
- **Transaction safety** with proper rollback handling

### **Performance Optimization**
- **Smart game selection** excludes already processed games upfront
- **Reduced database calls** by loading processed hashes once per chunk
- **Better memory management** with chunk-based processing

### **Code Quality**
- **Comprehensive documentation** with usage examples at file header
- **Better variable naming** and code organization
- **Enhanced logging** with emoji indicators for better readability

## Configuration Options

### Environment Variables
- `CHESS_TRAINER_DB_URL`: PostgreSQL connection URL
- `MAX_WORKERS`: Number of parallel workers (default: 4)
- `FEATURES_PER_CHUNK`: Games per processing chunk (default: 500)

### Command-Line Arguments
- `--max-games`: Maximum number of games to process
- `--source`: Filter games by source (optional)

## Sample Output

```
🚀 Starting parallel feature generation...
📋 Parameters:
   - Max games: 1000
   - Source filter: lichess
   - Max workers: 4
   - Features per chunk: 500

🔍 Starting feature generation process...
📋 Filtering by source: lichess
🎯 Maximum games to process: 1000
📊 Already processed games: 150

📥 Retrieved 500 games (total: 500)
📥 Retrieved 500 games (total: 1000)
🔍 No more games available. Retrieved 1000 games total.

🧩 Total chunks to process: 2
📊 Total games to process: 1000

⏳ Processing chunk 1/2...
🎯 Processing game ID: abc123...
   Magnus Carlsen vs Hikaru Nakamura
📊 Game abc123 generated 45 features
✅ Game abc123 processed and features saved.
📈 Chunk completed - Processed: 480, Skipped: 15, Errors: 5
✅ Completed chunk 1/2

⏳ Processing chunk 2/2...
📈 Chunk completed - Processed: 475, Skipped: 20, Errors: 5
✅ Completed chunk 2/2

✅ Parallel feature generation completed.
```

## Files Modified

### Main Script
- `/app/src/scripts/generate_features_parallel.py`
  - Added source filtering capability
  - Enhanced command-line interface
  - Improved error handling and logging
  - Added comprehensive documentation

### Dependencies
- Uses existing `GamesRepository.get_games_by_pagination_not_analyzed()` method
- Maintains compatibility with PostgreSQL database migration
- Leverages existing feature generation infrastructure

## Benefits

1. **🎯 Targeted Processing**: Process games from specific sources only
2. **⚡ Efficiency**: Automatic exclusion of already processed games
3. **📊 Better Monitoring**: Detailed progress tracking and statistics
4. **🔧 Flexibility**: Configurable processing parameters
5. **🛡️ Reliability**: Improved error handling and recovery
6. **📖 Usability**: Comprehensive documentation and help system

## Compatibility

- ✅ **PostgreSQL**: Full compatibility with existing database setup
- ✅ **Parallel Processing**: Maintains multi-worker architecture
- ✅ **Existing Features**: All original functionality preserved
- ✅ **Repository Pattern**: Uses existing repository classes
- ✅ **Environment Configuration**: Respects existing environment variables

**Status: ENHANCEMENT COMPLETED SUCCESSFULLY** 🎉

The script now supports source-based filtering while maintaining all existing functionality and improving overall performance and usability.

---
*Enhanced: June 29, 2025*
*Source Filtering for Parallel Feature Generation*
