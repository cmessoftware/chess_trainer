# Export Dataset Tests Documentation

## Overview

This document describes the comprehensive test suite for the `export_dataset` functionality in the chess trainer application. The tests ensure robust, reliable, and performant data export capabilities.

## Test Structure

### Test Files

1. **`test_export_features_dataset.py`**
   - Main functionality tests for the export scripts
   - Tests the public API and user-facing functions
   - Covers parallel processing and file I/O operations

2. **`test_features_repository_export.py`**
   - Database layer tests for the FeaturesRepository
   - Tests SQL query generation and data retrieval
   - Covers filter application and data formatting

3. **Test Runner Integration**
   - Fully integrated into main test runner system
   - Supports categorized execution and comprehensive reporting
   - Unified interface with other test categories

### Test Categories

#### 🔵 Unit Tests (`@pytest.mark.unit`)
- **Purpose**: Fast, isolated tests with mocked dependencies
- **Scope**: Individual functions and methods
- **Duration**: < 1 second per test
- **Coverage**: 
  - Function parameter validation
  - Error handling and edge cases
  - Data transformation logic
  - File format conversion

#### 🟢 Integration Tests (`@pytest.mark.integration`)
- **Purpose**: Component interaction verification
- **Scope**: Multi-layer data flow
- **Duration**: 1-10 seconds per test
- **Coverage**:
  - Database to file export pipeline
  - Parallel processing coordination
  - Real-world scenario simulation

#### 🟡 Performance Tests (`@pytest.mark.slow`)
- **Purpose**: Performance and scalability validation
- **Scope**: Large datasets and stress scenarios
- **Duration**: 10+ seconds per test
- **Coverage**:
  - Large dataset handling (1000+ records)
  - Memory usage optimization
  - Parallel processing efficiency

## Test Coverage Areas

### 1. Export Functions
- ✅ `export_features_to_dataset()` - Core export functionality
- ✅ `export_features_for_source()` - Single source export
- ✅ `export_all_sources_parallel()` - Parallel multi-source export

### 2. File Format Support
- ✅ Parquet format export and validation
- ✅ CSV format export and validation
- ✅ Invalid format handling
- ✅ File extension management

### 3. Filter Validation
- ✅ Source filtering (`elite`, `personal`, `novice`, etc.)
- ✅ ELO range filtering (min/max)
- ✅ Player name search (case-insensitive, partial match)
- ✅ Opening filtering (ECO codes and names)
- ✅ Game limit application
- ✅ Combined filter scenarios

### 4. Error Handling
- ✅ Database connection failures
- ✅ Invalid file paths
- ✅ Insufficient permissions
- ✅ Empty dataset scenarios
- ✅ Malformed data handling

### 5. Data Integrity
- ✅ Column selection verification
- ✅ Data type preservation
- ✅ NULL value handling
- ✅ Special character support
- ✅ Large dataset processing

### 6. Parallel Processing
- ✅ ProcessPoolExecutor integration
- ✅ Multi-source coordination
- ✅ Error propagation in parallel execution
- ✅ Resource cleanup and management

## Running the Tests

### Integrated Test Runner (Recommended)
The export dataset tests are integrated into the main test runner system:

```bash
# Navigate to tests directory
cd /app/tests

# Run all export dataset tests
bash run_tests.sh --export-dataset

# Run only unit tests
bash run_tests.sh --export-dataset --unit

# Run only integration tests  
bash run_tests.sh --export-dataset --integration

# Run with coverage report
bash run_tests.sh --export-dataset --coverage

# Run with HTML report generation
bash run_tests.sh --export-dataset --html-report

# Run with parallel execution
bash run_tests.sh --export-dataset --parallel
```



### Manual Pytest Execution
```bash
# Run with specific markers
pytest test_export_features_dataset.py -m unit
pytest test_features_repository_export.py -m integration

# Run with detailed output
pytest test_export_features_dataset.py -v --tb=long

# Run with coverage (if configured)
pytest test_export_features_dataset.py --cov=src/scripts/export_features_dataset_parallel
```

### Using Custom Configuration
```bash
# Use the export-specific pytest configuration
pytest -c pytest_export.ini test_export_features_dataset.py
```

## Test Fixtures and Mocks

### Key Fixtures
- `temp_export_dir`: Temporary directory for file operations
- `mock_features_repo`: Mocked FeaturesRepository instance
- `sample_dataframe`: Representative test data
- `mock_session_factory`: Database session mocking

### Mock Strategies
- **Database Layer**: Mock SQLAlchemy sessions and query results
- **File System**: Use temporary directories for safe testing
- **Parallel Processing**: Mock ProcessPoolExecutor for unit tests
- **External Dependencies**: Mock pandas operations for performance tests

## Assertions and Validations

### File Operations
```python
# Verify file creation
assert os.path.exists(expected_file_path)

# Validate file contents
exported_df = pd.read_parquet(file_path)
assert len(exported_df) == expected_row_count
assert list(exported_df.columns) == expected_columns
```

### Database Interactions
```python
# Verify repository method calls
mock_repo.get_features_with_filters.assert_called_once_with(
    source="elite",
    player_name="expected_player",
    # ... other expected parameters
)
```

### Data Quality
```python
# Check data integrity
assert df['game_id'].nunique() == expected_game_count
assert not df.isnull().any().any()  # No null values
assert df.dtypes['white_elo'] == 'int64'  # Correct data types
```

## Performance Benchmarks

### Expected Performance Metrics
- **Small datasets** (< 1000 records): < 2 seconds
- **Medium datasets** (1000-10000 records): < 10 seconds
- **Large datasets** (10000+ records): < 60 seconds
- **Parallel processing**: 2-4x speedup with multiple sources

### Memory Usage
- **Peak memory**: < 500MB for datasets up to 50,000 records
- **Memory growth**: Linear with dataset size
- **Cleanup**: All temporary files removed after tests

## Common Test Patterns

### Successful Export Test
```python
@pytest.mark.unit
def test_successful_export(self, temp_export_dir, mock_repo, sample_data):
    # Arrange
    mock_repo.get_features_with_filters.return_value = sample_data
    
    # Act
    export_features_to_dataset(source="elite", output_path=temp_output)
    
    # Assert
    assert os.path.exists(expected_file)
    exported_data = pd.read_parquet(expected_file)
    assert len(exported_data) == len(sample_data)
```

### Error Handling Test
```python
@pytest.mark.unit
def test_database_error_handling(self, mock_repo):
    # Arrange
    mock_repo.get_features_with_filters.side_effect = Exception("DB Error")
    
    # Act & Assert
    with pytest.raises(Exception, match="DB Error"):
        export_features_to_dataset(source="elite", output_path="/tmp/test")
```

### Integration Test
```python
@pytest.mark.integration
def test_full_export_pipeline(self, temp_dir, real_sample_data):
    # Test the complete export pipeline with realistic data
    # Verifies end-to-end functionality
```

## Troubleshooting

### Common Issues

1. **Test Database Connection**
   - Ensure PostgreSQL is running
   - Check `CHESS_TRAINER_DB_URL` environment variable
   - Verify test database has sample data

2. **File Permission Errors**
   - Use temporary directories for tests
   - Clean up test files after execution
   - Check disk space availability

3. **Mock Setup Issues**
   - Verify mock return values match expected types
   - Ensure all required methods are mocked
   - Check mock call assertions

### Debug Mode
```bash
# Run tests with verbose output and no capture
pytest test_export_features_dataset.py -v -s --tb=long

# Run single test with debugging
pytest test_export_features_dataset.py::TestExportFeaturesDataset::test_export_success -v -s
```

## Continuous Integration

### GitHub Actions Integration
```yaml
# Example CI configuration
- name: Run Export Dataset Tests
  run: |
    cd tests
    ./run_export_dataset_tests.sh --unit
    ./run_export_dataset_tests.sh --integration
```

### Test Reports
- **HTML Reports**: Detailed test results with navigation
- **JUnit XML**: CI/CD integration compatible format
- **Coverage Reports**: Code coverage analysis (when enabled)
- **Performance Reports**: Execution time and memory usage

## Contributing

### Adding New Tests
1. Follow existing naming conventions (`test_export_*`)
2. Use appropriate markers (`@pytest.mark.unit`, etc.)
3. Include comprehensive docstrings
4. Add both positive and negative test cases
5. Update this documentation

### Test Data Management
- Use fixtures for reusable test data
- Keep test data minimal but representative
- Clean up generated files in test teardown
- Use realistic but anonymized data

### Best Practices
- Write self-contained tests (no dependencies between tests)
- Use descriptive test names that explain the scenario
- Include edge cases and error conditions
- Mock external dependencies appropriately
- Verify both happy path and error scenarios

---

## Related Documentation
- [Main README](../README.md)
- [Testing Guide](README.md)
- [Dataset Configuration](../DATASETS_VOLUMES_CONFIG.md)
- [Architecture Documentation](../src/architecture.md)
