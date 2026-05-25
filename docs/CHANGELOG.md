# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.1.138] - 2026-05-25

### Added
- **🎓 AI Engineering Course** (PR #95) - New learning material in `docs/courses/`:
  - AI Engineer roadmap with phase-by-phase learning plan
  - Three Jupyter notebooks: architecture overview, feature pipeline, dataset builder
  - SQLite migration script for portable course data
- **📊 Course Data Access Layer** (PR #97, #98) - Portable SQLAlchemy-based data layer:
  - `docs/courses/data_access/features_repository.py` - SQLAlchemy repository with SQLite default and optional PostgreSQL via `CHESS_COURSE_DB_URL`
  - `docs/courses/data_access/notebook_data_helper.py` - Helper utilities for notebooks
  - `docs/courses/dataset/build_training_dataset.py` - Standalone dataset builder module
  - `tests/docs_courses/test_course_data_access.py` - Test suite for data access layer
  - `tests/docs_courses/test_build_training_dataset.py` - Test suite for dataset builder
- **🗺️ AI Chess Coach Roadmap** (PR #98) - Phase 1–2 feature list at `docs/ai_chess_coach/roadmap/02-phase-1-2-feature-list.md`
- **📚 ML Theory & Analysis Docs** (PR #93) - New documentation organized by category:
  - `docs/ml_theory/ML_THEORETICAL_FRAMEWORK.md`
  - `docs/ml_analysis/ML_CURRENT_STATE_ANALYSIS.md`, `PAGES_ARCHITECTURE_ANALYSIS.md`, `ISSUE_21_COMPLETION_REPORT.md`
  - `docs/devops/DATASETS_VOLUMES_CONFIG.md`, `DOCKER_DEVELOPMENT_STRATEGY.md`, `MLFLOW_POSTGRES_INTEGRATION.md`
- **🔧 Copilot Instructions** (PR #94) - `.github/copilot-instructions.md` with project conventions
- **📋 Tesseract Setup Guide** - `INSTALL_TESSERACT_GUIDE.md` for OCR prerequisites

### Changed
- **🏷️ Project Renamed** (PR #93) - Project renamed from ChessTrainer to **CHESSINSIGHTAI** in README and description
- **📁 Docs Reorganization** (PR #99) - AI Coach and OCR docs moved into `docs/ai_chess_coach/`:
  - `AI_CHESS_COACH_TESTING_GUIDE.md`, `AI_COACH_CHECKLIST.md`, `AI_COACH_IMPLEMENTATION_GUIDE.md`, `AI_COACH_QUICKSTART.md`, `OCR_SETUP_GUIDE.md`
- **📓 Course Notebooks Updated** (PR #97, #98) - Notebooks aligned to use new portable data layer and normalized entry points
- **🗄️ Alembic Migrations** (PR #94) - Added multiple new schema migrations: batch tracking, users table, SHAP analysis tables, views, and merge heads

### Fixed
- **📐 Course README Placeholders** (PR #97) - Normalized script entry points and clarified placeholder values

### Technical Details
- **Version**: v0.1.138
- **PRs merged**: #93, #94, #95, #97, #98, #99
- **Branch**: `main`
- **Date range**: 2026-05-17 to 2026-05-25

---

## [v0.1.109] - 2026-01-30

### Added
- **📚 Modern Documentation Overhaul** - Complete update of project documentation
  - Updated main README.md with React 19 + TypeScript + Vite architecture
  - Comprehensive tech stack documentation (Frontend/Backend/ML/Development Tools)
  - Modern quick start guide with React development workflow
  - Professional development experience documentation

### Changed
- **📖 README.md Major Update** - Aligned with current technology stack:
  - ❌ **Removed**: Outdated Streamlit references (no longer used)
  - ✅ **Added**: Complete React + FastAPI architecture documentation
  - ✅ **Enhanced**: Development workflow and setup instructions
  - ✅ **Updated**: Access points and benefits of current architecture

- **🌐 README_es.md Complete Synchronization** - Spanish documentation fully updated:
  - Synchronized with English version (v0.1.107 → v0.1.109)
  - Updated from elite-only to all skill levels chess training approach
  - Added modern development stack section with detailed descriptions
  - Fixed all documentation references and added new organizational sections

- **📋 Documentation Links Verification** - Comprehensive audit and corrections:
  - Fixed broken documentation references (README_es.md, VERSION_BASE.md paths)
  - Added new sections: Training & Studies System, Development & Setup Guides
  - Enhanced documentation index with proper categorization
  - Updated changelog with detailed v0.1.107 release notes

### Technical Details
- **Commit**: `a8401c3` - Documentation modernization and React stack alignment
- **Version Update**: `5ea1443` - Automated version bump to v0.1.109
- **Languages**: English and Spanish documentation fully synchronized
- **Impact**: Ready for new developers with accurate modern setup instructions

---

## [v0.1.107] - 2026-01-16

### Added
- **🤖 Complete ML Prediction System** - Comprehensive MLflow-integrated prediction pipeline
  - ML prediction guide (PREDICCIONES_FIABLES_MLFLOW.md)
  - 6-phase ML development roadmap with detailed technical specifications
  - Extended EDA analysis notebooks with MLflow integration
  - Real user analysis scripts with tactical pattern detection

- **🎓 Training & Study System** - Complete personalized chess training infrastructure
  - PGN study system documentation (ESTUDIOS_PGN_SISTEMA_COMPLETO.md)
  - Training system with resource management (TRAINING_SYSTEM_COMPLETE.md)
  - Advanced study generators with ML personalization
  - Training manager with progress tracking and concrete exercise generation
  - 4,242 games analyzed, 39,180 tactical positions processed

- **⚛️ Frontend SPRINT 1** - React-based database browser and ML integration
  - Database Connector component for PostgreSQL integration
  - Games Browser page with pagination, filtering, and PGN export
  - Enhanced PGN upload with comprehensive error handling
  - Updated main navigation with new modules and improved UX

- **🚀 Backend ML APIs** - Complete API ecosystem for chess analysis
  - FastAPI error classifier API with JWT authentication
  - Flask survivorship analysis API for bias detection
  - ML pipeline implementation (phases 1-6) with MLflow tracking
  - External validation and model calibration systems
  - Training recommender system with personalized suggestions

- **📊 Data Acquisition & Analysis Tools**
  - Enhanced Chess.com downloaders with retry logic and rate limiting
  - User recommendation system based on ML pattern analysis
  - Database investigation and maintenance automation tools
  - Quick training access system with progress tracking

### Changed
- **🏗️ Project Structure Reorganization**
  - Moved all scripts to `src/scripts/` for better organization
  - Created `training/` and `reports/` directories for output management
  - Cleaned up temporary and duplicate files across the project
  - Reorganized documentation structure with clear categorization

- **📚 Enhanced Documentation**
  - Frontend Roadmap with 4-phase React development plan
  - Personalized chess studies tutorial with step-by-step guides
  - MLflow-PostgreSQL integration guide for production deployment
  - Survivorship bias analysis module documentation

### Fixed
- **🔧 Frontend Stability** - Fixed dotenv imports across all frontend components
- **🗄️ Database Integration** - Resolved PostgreSQL connection issues in browser components
- **📤 PGN Export** - Enhanced error handling for large dataset exports

### Technical Details
- **Commit**: `d679114` - ML prediction system and training management
- **Frontend Commit**: `e228da3` - Database browser and ML integration
- **Major Achievement**: Complete end-to-end ML pipeline with React frontend
- **Files Changed**: 134 files, +8,108 additions, -11,600 deletions
- **Production Ready**: Database browser, ML-powered study generation, comprehensive API backend

---

## [Unreleased] - Current Development (Jan 30, 2026)

### Added
- **🎨 Modern Tech Stack Documentation** - Updated README with current React + Vite + FastAPI architecture
- **🔗 Documentation Links Verification** - Comprehensive audit and correction of all documentation references
- **📚 Enhanced Documentation Index** - New sections for Training & Studies System and Development guides
- **⚛️ Frontend Architecture Details** - Complete React 19 + TypeScript + Material-UI stack documentation
- **🚀 FastAPI Backend Documentation** - Updated backend architecture with JWT auth and PostgreSQL integration

### Changed
- **📖 README.md Major Overhaul** - Completely updated to reflect current technology stack:
  - ❌ **Removed**: Outdated Streamlit references (no longer used)
  - ✅ **Added**: React 19 + Vite frontend documentation
  - ✅ **Updated**: FastAPI backend with modern architecture details
  - ✅ **Enhanced**: Development workflow and setup instructions
- **🔗 Fixed Documentation Links** - Corrected all broken references:
  - `./README_es.md` → `./docs/README_es.md`
  - `./VERSION_BASE.md` → `./docs/VERSION_BASE.md`
  - `./VERSION_BASE_es.md` → `./docs/VERSION_BASE_es.md`
- **📋 Reorganized Documentation Sections** - New categories:
  - **Training & Studies System** - PGN studies, training resources, custom tutorials
  - **Development & Setup Guides** - Environment setup, API testing, architecture updates

### Improved
- **🎯 Quick Start Guide** - Updated with modern React + FastAPI development workflow
- **🏗️ Architecture Overview** - Detailed frontend/backend architecture diagrams and data flow
- **💻 Tech Stack Details** - Comprehensive technology descriptions with emojis and context
- **📊 Implementation Status** - Real-time project status with current priorities
- **🔄 Development Workflow** - Updated commands for frontend (npm) and backend (uvicorn) development

### Technical Details
- **Current Version**: v0.1.107-d679114
- **Frontend**: React 19 + TypeScript + Vite + Material-UI + React Query
- **Backend**: FastAPI + PostgreSQL + MLflow + JWT Authentication
- **Major Focus**: Documentation accuracy and modern development experience
- **Next Steps**: Complete dashboard implementation and user management features

---

## [v0.1.102] - 2025-12-29

### Added
- **📁 Documentation Structure Reorganization** - Created comprehensive docs/ directory structure
- **📊 Technical Roadmap** - Added 6-phase development roadmap with current project status analysis
- **🎨 Mermaid Architecture Diagram** - Complete system architecture visualization with component status
- **🛠️ Mermaid to JPG Converter** - Python script for converting Mermaid diagrams to images
- **📚 Complete Documentation Suite**:
  - MLflow PostgreSQL Integration Guide
  - Reliable Predictions with MLflow (Spanish)
  - ELO Standardization Technical Guide
  - Issue #21 Completion Report
  - Docker Development Strategy
  - Datasets Volumes Configuration
  - Git LFS Setup Guide

### Changed
- **📖 README.md Updated** - All documentation links now point to organized docs/ directory
- **🔧 Mermaid Script Path** - Updated to use new roadmap location in docs/
- **📊 Project Status Assessment** - Comprehensive analysis showing Phase 1 at 75% completion

### Technical Details
- **Current Version**: v0.1.102-67b6ca6
- **Major Focus**: Documentation organization and Phase 1 ML pipeline completion planning
- **Architecture**: Full system diagram with color-coded component status
- **Next Steps**: Complete Phase 1 baseline model implementation

---

## [v0.1.101] - 2025-10-02

### Added
- **🤖 ML Issues Generator** - Automated ML issue creation system
- **📋 ML Issues JSON** - Structured ML workflow issue tracking
- **📓 ML Workflow Notebook** - Base notebook for ML experiments

### Changed
- **📝 README Updates** - Enhanced ML workflow documentation
- **🔢 Version Management** - Automated version updates

---

## [v0.1.100] - 2025-09-10

### Added
- **✅ Issue #67 Completion** - Complete ML Analysis Implementation
- **📊 Enhanced Analytics** - Comprehensive dataset analysis capabilities

### Technical Details
- **Commit**: `67b6ca6` - ML Analysis Implementation milestone
- **Major Achievement**: Core ML functionality completed

---

## [v0.1.99] - 2025-07-13

### Fixed
- **🔧 Import Pipeline** - Fixed import_pgn_parallel.py functionality
- **📖 Documentation** - Updated README.md and VERSION files

---

## [v0.1.92-v0.1.98] - 2025-07-11 to 2025-07-12

### Added
- **🎯 Issue #21 Completion** - ELO Standardization System fully implemented
- **📊 Real Datasets Analysis** - Comprehensive ML analysis functionality
- **🧹 Project Cleanup** - Removed duplicate directories and documentation

### Changed
- **📝 README Updates** - Marked ML core issues #67 and #68 as completed
- **🗂️ File Organization** - Clean duplicated src directories

### Technical Details
- **Major Milestone**: ELO Standardization System 100% complete
- **Database**: PostgreSQL integration optimized
- **Analysis**: Real datasets ML functionality enhanced

---

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
