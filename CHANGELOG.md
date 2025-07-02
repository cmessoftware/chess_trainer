# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.61] - 2025-07-02

### Added
- **Parameter Consistency** - Unified command-line parameter naming across all tactical analysis scripts:
  - Changed `--limit` to `--max-games` in `estimate_tactical_features.py` for consistency with other scripts
  - Updated pipeline `run_pipeline.sh` to handle `--max-games` parameter correctly
  - Enhanced parameter documentation and examples in help output
- **Pipeline Integration** - Complete integration of tactical analysis tools into main pipeline:
  - All tactical analysis commands now properly integrated and tested
  - Improved error handling and user feedback
  - Enhanced documentation with clear examples for each command

### Fixed
- **Parameter Naming Inconsistency** - Resolved inconsistent parameter naming between scripts:
  - `estimate_tactical_features.py` now uses `--max-games` instead of `--limit`
  - Pipeline parameter passing now correctly handles all tactical analysis options
  - Updated help documentation to reflect consistent parameter usage
- **Process Control** - Enhanced process management and cleanup in tactical analysis:
  - Improved signal handling and graceful shutdowns
  - Better timeout management for long-running processes
  - Robust cleanup of background processes and resources

## [v0.1.59] - 2025-07-01

### Added
- **Tactical Features Enhancement Suite** - Comprehensive tools to increase score_diff and error_label coverage in datasets:
  - `src/scripts/enhanced_tactical_analysis.py` - Optimized batch tactical analysis with analyzed_tacticals tracking
  - `src/scripts/estimate_tactical_features.py` - Lightweight tactical feature estimation for fast coverage
  - `src/scripts/generate_features_with_tactics.py` - Integrated feature generation with tactical analysis
  - `src/scripts/test_tactical_analysis.py` - Test suite for tactical analysis functionality
  - `docs/TACTICAL_FEATURES_ENHANCEMENT.md` - Complete guide for improving tactical feature coverage
- **Database Tracking** - Enhanced tracking of analyzed games:
  - Automatic registration in analyzed_tacticals table to prevent duplicate work
  - Coverage reporting by source and feature type
  - Resume capability for interrupted analysis jobs
- **Performance Optimizations** - Multiple strategies for different use cases:
  - Lightweight estimation: ~100x faster with ~95% coverage (approximate values)
  - Enhanced batch processing: Memory-managed analysis with proper tracking
  - Integrated processing: Single-step feature generation with tactical analysis

### Fixed
- **Tactical Analysis Tracking** - Resolved missing analyzed_tacticals table updates in batch processing
- **Coverage Reporting** - Added comprehensive reporting of tactical feature coverage by source
- **Memory Management** - Improved batch processing to handle large datasets efficiently

### Documentation
- **Analysis Conclusion** - Identified root cause of low tactical feature representation (<10%)
- **Solution Strategies** - Documented three approaches for different dataset sizes and requirements
- **Performance Guidelines** - Clear recommendations for optimal processing strategies
- **Root Cause Analysis** - Created comprehensive analysis document: `docs/TACTICAL_FEATURES_LOW_COVERAGE_ANALYSIS.md`
- **Documentation Integration** - Added documentation section to README.md and README_es.md with links to all analysis guides

## [v0.1.57] - 2025-07-01

### Added
- **Export Dataset Test Suite Integration** - Integrated comprehensive testing infrastructure into main test runner:
  - Added `--export-dataset` option to main `tests/run_tests.sh` test runner
  - Unified test interface supporting coverage, HTML reports, and parallel execution
  - Syntax validation for `export_features_dataset_parallel.py` script
  - Integrated 18 export functionality tests and 13 repository tests into main testing framework
- **Test Runner Enhancement** - Enhanced main test runner with export dataset support:
  - Centralized test management with consistent command-line interface
  - Standardized reporting formats across all test categories
  - Better maintainability and CI/CD integration through single entry point

### Changed
- **Test Infrastructure** - Consolidated test execution into unified runner system
- **Documentation** - Updated test documentation to reflect integration with main test runner

### Removed
- **Legacy Test Runner** - Removed redundant standalone `run_export_dataset_tests.sh` script
  - All functionality now available through main test runner
  - Simplified maintenance with single test entry point

### Fixed
- **Repository Test Mocking** - Resolved DataFrame mock call count issues in repository export tests  
- **Test Isolation** - Improved test independence and reduced brittleness in mocking pandas operations
- **Export Logic Validation** - Comprehensive testing of filter application, error handling, and edge cases

## [v0.1.53] - 2025-07-01

### Added
- **PostgreSQL Optimization** - Enhanced database configuration and utilities for improved performance
- **Docker Git LFS Support** - Proper gnupg installation and enhanced Git LFS integration
- **Windows Setup Guide** - Comprehensive setup documentation for Windows environments
- **Git LFS Setup Documentation** - Complete guide for large file storage configuration

### Changed
- **Requirements Management** - Updated requirements across all environments (app, notebooks, tests)
- **Documentation Localization** - Enhanced Spanish documentation (architecture_es.md, VERSION_BASE_es.md)
- **Pipeline Scripts** - Improved database management tools and pipeline utilities
- **Test Infrastructure** - Enhanced test suite with PostgreSQL migration support

### Enhanced
- **Feature Generation** - Improved parallel processing capabilities
- **UI Components** - Updated elite_explorer, elite_stats, and export_exercises interfaces
- **DevOps Scripts** - Added Docker management scripts (manage-docker.ps1/.bat)
- **Version Management** - Enhanced commit automation and version control systems

### Fixed
- **Database Migration** - Resolved PostgreSQL migration issues
- **Docker Optimization** - Improved container build and deployment processes
- **Test Framework** - Comprehensive testing framework implementation

## [v0.1.44] - 2025-07-01

### Added
- **Export Dataset Test Suite** - Comprehensive testing infrastructure for export_features_dataset functionality:
  - `tests/test_export_features_dataset.py` - 18 unit, integration, and performance tests for export script
  - `tests/test_features_repository_export.py` - 13 unit tests for FeaturesRepository export logic
  - `tests/run_export_dataset_tests.sh` - Custom test runner with categorized execution
  - `tests/EXPORT_DATASET_TESTS.md` - Complete test suite documentation
  - `tests/pytest_export.ini` - Dedicated pytest configuration for export tests
- **Test Categories** - Organized test execution by type:
  - Unit tests: Fast, isolated function testing with mocked dependencies
  - Integration tests: Component interaction and data flow verification
  - Performance tests: Large dataset handling and parallel processing
- **Test Infrastructure** - Enhanced test automation and reporting:
  - HTML and JUnit XML test reports with timestamps
  - Test summary generation with coverage area documentation
  - Parallel test execution support for performance validation

### Fixed
- **Repository Test Mocking** - Resolved DataFrame mock call count issues in repository export tests
- **Test Isolation** - Improved test independence and reduced brittleness in mocking pandas operations
- **Export Logic Validation** - Comprehensive testing of filter application, error handling, and edge cases

## [v0.1.43] - 2025-06-30

### Added
- **Documentation Structure Enhancement** - Comprehensive documentation improvements addressing issue #62
- **Spanish Language Documentation** - Complete Spanish versions for all major documentation files:
  - `src/architecture_es.md` - System architecture diagram and explanations in Spanish
  - `tests/README_es.md` - Complete testing guide with runner documentation in Spanish
  - `DATASETS_VOLUMES_CONFIG_es.md` - Docker volumes configuration for dataset sharing in Spanish
- **Documentation Index** - Organized navigation structure replacing requirements sections in both VERSION_BASE files
- **Docker Installation References** - Clear references to automatic dependency installation via:
  - `Dockerfile` - Main application container setup
  - `dockerfile.notebooks` - Jupyter environment setup
  - `requirements.txt` - Complete Python dependencies
  - `docker-compose.yml` - Container orchestration

### Changed
- **VERSION_BASE Files Restructured** - Documentation index now serves as primary navigation replacing basic requirements section
- **Cross-Reference Enhancement** - Better organization and linking between English and Spanish documentation versions
- **Issue Management Optimization** - Removed #MIGRATED-TODO keys from English version to prevent duplicate GitHub issues

### Fixed
- **Docker Build Issues** - Resolved pytest package installation error in Dockerfile (issue #62)
- **Documentation Organization** - Logical categorization into Core Documentation, Configuration, Architecture, Testing, and Reports sections

### Technical Details
- **Commit**: `6f8d69b6fa66173cf4e4e13d385fc061fef7ca02`
- **Author**: Sergio Salanitri
- **Date**: Mon Jun 30 15:06:47 2025 -0300
- **Branch**: `62-compartir-datasets-ente-containers`

---

## Previous Versions

### [v0.1.42] - 2025-06-30
- **Fixed Docker build**: Remove pytest packages from apt-get install
- **Resolved build error**: 'E: Unable to locate package pytest'
- **Technical Details**: Commit `e6619b7` - Fixes #62, moved pytest packages to pip installation

### [v0.1.41] - 2025-06-30
- **Git LFS Configuration**: Added Docker Git LFS support and selective volume sharing
- **Docker Updates**: Enhanced dockerfile and dockerfile.notebooks with proper Git LFS installation
- **Documentation**: Created comprehensive dataset volume sharing documentation
- **Windows Support**: Added Windows setup guide and LFS usage documentation
- **Volume Sharing**: Updated docker-compose.yml for selective export/models sharing between containers

### [v0.1.40] - 2025-06-30
- **Source Parameter Support**: Added source parameter in feature generation process (issue #59)
- **Testing Enhancements**: Associated tests for source parameter functionality
- **Feature Filtering**: Added filter by source in generate_feature process (issue #56)
- **Bug Fixes**: Fixed max-games control failure

### [v0.1.39] - 2025-06-29
- **PostgreSQL Migration**: Migrated entire system from SQLite to PostgreSQL
- **Testing Suite**: Added comprehensive tests for analyze_tactics_parallel
- **Requirements Update**: Updated requirements.txt with all references (app, notebooks, and tests)
- **Pipeline Improvements**: Enhanced analyze_tactics process with fixes and optimizations

### [v0.1.38] - 2025-06-26
- **Git LFS Setup**: Configured Git LFS for large files and processed games
- **Performance**: Optimized storage for large dataset files

## Major Releases

### [v0.2] - 2025-06-14
- **Major Version Update**: New stable version with enhanced features
- **Commit**: `09eacce` - Significant system improvements and optimizations

### [v0.1] - 2025-05-31  
- **Initial Stable Release**: Backend stabilization and core functionality
- **Training Dataset**: Successfully generating training_dataset.csv
- **Commit**: `30f47e3` - First stable version with working training dataset generation

## Recent Feature Development (June 2025)

### Dataset and Source Management
- **Multi-source Support**: Enhanced support for multiple datasets (issue #8)
- **Source Filtering**: Improved feature generation with source-based filtering
- **Data Processing**: Optimized pipeline for different data sources

### Infrastructure and DevOps  
- **Docker Optimization**: Complete containerization with Git LFS support
- **PostgreSQL Migration**: Full database migration from SQLite to PostgreSQL
- **Volume Sharing**: Intelligent dataset sharing between containers
- **Testing Framework**: Comprehensive test suite implementation

### Documentation and Localization
- **Bilingual Documentation**: Complete Spanish translations for all major docs
- **Architecture Documentation**: Detailed system architecture diagrams
- **Testing Guides**: Comprehensive testing documentation and runner guides
- **Installation Automation**: Docker-first approach with automatic dependency management

<!-- Template for future entries:

## [Unreleased]

### Added
- **Export Dataset Unit Tests** - Comprehensive test suite for export_features_dataset_parallel functionality
  - `tests/test_export_features_dataset.py` - Main export functionality tests (25+ test cases)
  - `tests/test_features_repository_export.py` - Repository layer tests (15+ test cases)
  - `tests/run_export_dataset_tests.sh` - Dedicated test runner with categorized execution
  - `tests/EXPORT_DATASET_TESTS.md` - Complete testing documentation
  - **Test Categories**: Unit tests, Integration tests, Performance tests
  - **Coverage Areas**: Export functions, file formats, filters, error handling, parallel processing
  - **Mock Strategies**: Database layer, file system, parallel processing
  - **Performance Benchmarks**: Small to large dataset handling validation

### Changed
- **Repository Pattern Enforcement** - Eliminated all hardcoded SQL queries:
  - Refactored `test_tactical_analysis.py` to use repository methods instead of raw SQL
  - Refactored `estimate_tactical_features.py` to use `get_features_missing_tactical_data()` method
  - Added `get_features_missing_tactical_data()` method to FeaturesRepository for tactical analysis queries
  - All tactical analysis scripts now exclusively use SQLAlchemy ORM and repository pattern
  - Improved type safety, maintainability, and testability of database operations

### Deprecated
### Removed
### Fixed
### Security

-->
