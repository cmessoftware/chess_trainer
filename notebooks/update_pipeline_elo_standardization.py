#!/usr/bin/env python3
"""
Update Data Pipeline with ELO Standardization

This script updates existing datasets to include standardized ELO ratings,
ensuring consistency across all chess platforms and data sources.

Author: Chess Trainer Project  
Issue: #21 (ELO Standardization)
Date: 2025-07-12
"""

import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import tempfile
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

try:
    from elo_standardization import ELOStandardizer, ELOPlatform
except ImportError:
    # Try local import
    from ml.elo_standardization import ELOStandardizer, ELOPlatform

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataPipelineUpdater:
    """Updates existing data pipeline with ELO standardization"""
    
    def __init__(self, data_base_path: str = "/notebooks/data"):
        self.data_base_path = Path(data_base_path)
        self.standardizer = ELOStandardizer()
        self.results = {
            "files_processed": 0,
            "games_updated": 0,
            "elos_standardized": 0,
            "processing_log": []
        }
    
    def find_dataset_files(self) -> List[Path]:
        """Find all dataset files that need ELO standardization"""
        dataset_files = []
        
        # Search common locations
        search_paths = [
            self.data_base_path / "export",
            self.data_base_path / "processed", 
            self.data_base_path / "games",
            Path("/notebooks/datasets/export"),
            Path("/notebooks/datasets/processed")
        ]
        
        for search_path in search_paths:
            if search_path.exists():
                logger.info(f"🔍 Searching in: {search_path}")
                
                # Look for Parquet files
                parquet_files = list(search_path.glob("**/*.parquet"))
                dataset_files.extend(parquet_files)
                
                # Look for CSV files 
                csv_files = list(search_path.glob("**/*.csv"))
                dataset_files.extend(csv_files)
        
        logger.info(f"📁 Found {len(dataset_files)} dataset files")
        return dataset_files
    
    def backup_file(self, file_path: Path) -> Path:
        """Create backup of original file"""
        backup_path = file_path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_path.suffix}")
        
        try:
            import shutil
            shutil.copy2(file_path, backup_path)
            logger.info(f"💾 Created backup: {backup_path.name}")
            return backup_path
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            raise
    
    def update_dataset_file(self, file_path: Path) -> Dict[str, Any]:
        """Update a single dataset file with standardized ELO ratings"""
        file_result = {
            "file": str(file_path),
            "original_rows": 0,
            "updated_rows": 0,
            "new_columns": [],
            "errors": []
        }
        
        try:
            logger.info(f"🔬 Processing: {file_path.name}")
            
            # Load dataset
            if file_path.suffix.lower() == '.parquet':
                df = pd.read_parquet(file_path)
            elif file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path)
            else:
                file_result["errors"].append(f"Unsupported file format: {file_path.suffix}")
                return file_result
            
            file_result["original_rows"] = len(df)
            logger.info(f"📊 Loaded {len(df)} rows, {len(df.columns)} columns")
            
            # Check if standardization is needed
            has_elo_columns = any(col in df.columns for col in ['white_elo', 'black_elo'])
            has_standardized = any(col in df.columns for col in ['standardized_white_elo', 'standardized_black_elo'])
            
            if not has_elo_columns:
                logger.info(f"⏭️ Skipping {file_path.name} - no ELO columns found")
                file_result["errors"].append("No ELO columns found")
                return file_result
            
            if has_standardized:
                logger.info(f"⏭️ Skipping {file_path.name} - already has standardized ELO columns")
                file_result["errors"].append("Already has standardized ELO columns")
                return file_result
            
            # Create backup
            backup_path = self.backup_file(file_path)
            
            # Apply ELO standardization
            logger.info(f"⚙️ Applying ELO standardization...")
            df_standardized = self.standardizer.standardize_dataframe_elos(df)
            
            # Check what was added
            new_columns = [col for col in df_standardized.columns if col not in df.columns]
            file_result["new_columns"] = new_columns
            file_result["updated_rows"] = len(df_standardized)
            
            # Save updated dataset
            if file_path.suffix.lower() == '.parquet':
                df_standardized.to_parquet(file_path, index=False)
            else:
                df_standardized.to_csv(file_path, index=False)
            
            logger.info(f"✅ Updated {file_path.name} with {len(new_columns)} new columns")
            
            # Get statistics
            standardization_stats = self.standardizer.get_statistics()
            self.results["elos_standardized"] += standardization_stats["conversions_performed"]
            
            # Validation
            validation = self.standardizer.validate_standardization(df_standardized)
            file_result["validation"] = validation
            
            return file_result
            
        except Exception as e:
            error_msg = f"Error processing {file_path.name}: {e}"
            logger.error(f"❌ {error_msg}")
            file_result["errors"].append(error_msg)
            return file_result
    
    def update_all_datasets(self) -> Dict[str, Any]:
        """Update all found datasets with ELO standardization"""
        logger.info("🚀 Starting data pipeline ELO standardization update...")
        
        dataset_files = self.find_dataset_files()
        
        if not dataset_files:
            logger.warning("⚠️ No dataset files found")
            return self.results
        
        # Process each file
        for file_path in dataset_files:
            file_result = self.update_dataset_file(file_path)
            self.results["processing_log"].append(file_result)
            
            if not file_result["errors"]:
                self.results["files_processed"] += 1
                self.results["games_updated"] += file_result["updated_rows"]
        
        # Summary
        self.results["success_rate"] = (
            self.results["files_processed"] / max(1, len(dataset_files)) * 100
        )
        
        logger.info(f"✅ Pipeline update completed!")
        logger.info(f"📊 Files processed: {self.results['files_processed']}/{len(dataset_files)}")
        logger.info(f"📊 Games updated: {self.results['games_updated']}")
        logger.info(f"📊 ELOs standardized: {self.results['elos_standardized']}")
        
        return self.results
    
    def generate_report(self) -> str:
        """Generate a detailed report of the pipeline update"""
        report = []
        report.append("=" * 80)
        report.append("🏆 ELO STANDARDIZATION PIPELINE UPDATE REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        report.append(f"📊 SUMMARY:")
        report.append(f"   • Files processed: {self.results['files_processed']}")
        report.append(f"   • Games updated: {self.results['games_updated']}")
        report.append(f"   • ELOs standardized: {self.results['elos_standardized']}")
        report.append(f"   • Success rate: {self.results.get('success_rate', 0):.1f}%")
        report.append("")
        
        # Detailed results
        report.append(f"📋 DETAILED RESULTS:")
        for i, file_result in enumerate(self.results['processing_log'], 1):
            file_name = Path(file_result['file']).name
            report.append(f"   {i}. {file_name}")
            
            if file_result['errors']:
                report.append(f"      ❌ Errors: {', '.join(file_result['errors'])}")
            else:
                report.append(f"      ✅ Rows: {file_result['original_rows']} -> {file_result['updated_rows']}")
                report.append(f"      ➕ New columns: {', '.join(file_result['new_columns'])}")
                
                if 'validation' in file_result:
                    validation = file_result['validation']
                    report.append(f"      📈 Standardized ELOs: {validation['standardized_white_count']} white, {validation['standardized_black_count']} black")
            report.append("")
        
        # Standardization statistics
        standardization_stats = self.standardizer.get_statistics()
        report.append(f"📈 STANDARDIZATION STATISTICS:")
        report.append(f"   • Conversions performed: {standardization_stats['conversions_performed']}")
        report.append(f"   • Invalid ratings found: {standardization_stats['invalid_ratings_found']}")
        report.append(f"   • Platforms processed: {', '.join(standardization_stats['platforms_processed'])}")
        report.append(f"   • Success rate: {standardization_stats['success_rate']:.1f}%")
        report.append("")
        
        report.append("=" * 80)
        report.append("✅ ELO standardization pipeline update completed successfully!")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Main execution function"""
    print("🚀 Starting ELO Standardization Pipeline Update...")
    print("⚠️ This will modify existing dataset files (backups will be created)")
    
    # Initialize updater
    updater = DataPipelineUpdater()
    
    try:
        # Update all datasets
        results = updater.update_all_datasets()
        
        # Generate and print report
        report = updater.generate_report()
        print(report)
        
        # Save report to file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"/tmp/elo_standardization_report_{timestamp}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"📄 Report saved to: {report_file}")
        
        return 0 if results['files_processed'] > 0 else 1
        
    except Exception as e:
        logger.error(f"❌ Pipeline update failed: {e}")
        print(f"\n❌ Pipeline update failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
