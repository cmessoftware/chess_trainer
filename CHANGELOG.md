# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
### Changed  
### Deprecated
### Removed
### Fixed
### Security

-->
