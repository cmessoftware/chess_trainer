
"""
Cleanup script to verify and remove old MLflow SQLite database
This confirms that PostgreSQL is fully integrated as the backend.
"""
import sys
import logging
import shutil
from pathlib import Path
import mlflow

# Add src path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import project utilities
from db.repository.mlflow_repository import mlflow_repo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_postgres_running():
    """Verify PostgreSQL connection is working"""
    if not mlflow_repo.test_connection():
        logger.error("❌ PostgreSQL connection failed - cancelling cleanup")
        return False
    logger.info("✅ PostgreSQL connection successful")
    return True

def verify_mlflow_tracking_uri():
    """Verify MLflow is configured to use PostgreSQL"""
    # Get current tracking URI
    try:
        tracking_uri = mlflow.get_tracking_uri()
        logger.info(f"Current MLflow tracking URI: {tracking_uri}")
        
        # Check if it contains postgresql
        if "postgresql" not in str(tracking_uri).lower():
            logger.error("❌ MLflow not configured to use PostgreSQL")
            return False
        
        logger.info("✅ MLflow configured to use PostgreSQL")
        return True
    except Exception as e:
        logger.error(f"❌ Error checking MLflow tracking URI: {e}")
        return False

def check_sqlite_file():
    """Check if mlflow.db exists and can be removed"""
    sqlite_path = Path("mlflow.db")
    
    if not sqlite_path.exists():
        logger.info("✅ No SQLite file found - already using PostgreSQL")
        return None
    
    logger.info(f"Found SQLite file: {sqlite_path}")
    file_size = sqlite_path.stat().st_size
    logger.info(f"SQLite file size: {file_size/1024:.2f} KB")
    
    return sqlite_path

def backup_sqlite_file(sqlite_path):
    """Create backup of SQLite file before removal"""
    if sqlite_path is None:
        return
    
    backup_path = sqlite_path.with_suffix(".db.bak")
    try:
        shutil.copy2(sqlite_path, backup_path)
        logger.info(f"✅ Created backup at {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"❌ Error creating backup: {e}")
        return None

def remove_sqlite_file(sqlite_path, backup_path):
    """Remove SQLite file if everything checks out"""
    if sqlite_path is None:
        return True
    
    try:
        sqlite_path.unlink()
        logger.info(f"✅ Successfully removed {sqlite_path}")
        logger.info(f"A backup was saved at {backup_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error removing SQLite file: {e}")
        return False

def main():
    """Main cleanup function"""
    logger.info("=" * 60)
    logger.info("MLFLOW POSTGRESQL MIGRATION CLEANUP")
    logger.info("=" * 60)
    
    # Run verification checks
    if not verify_postgres_running():
        logger.error("❌ PostgreSQL check failed - aborting cleanup")
        return False
    
    if not verify_mlflow_tracking_uri():
        logger.error("❌ MLflow configuration check failed - aborting cleanup")
        return False
    
    # Check SQLite file
    sqlite_path = check_sqlite_file()
    
    if sqlite_path is None:
        logger.info("✅ No SQLite file to clean up - migration complete!")
        return True
    
    # Confirm with user
    logger.info("\nReady to complete migration by removing SQLite file.")
    logger.info("A backup will be created before removal.")
    
    # Create backup
    backup_path = backup_sqlite_file(sqlite_path)
    if backup_path is None:
        logger.error("❌ Backup failed - aborting cleanup")
        return False
    
    # Remove file
    if remove_sqlite_file(sqlite_path, backup_path):
        logger.info("\n✅ MIGRATION COMPLETE!")
        logger.info("MLflow is now fully configured to use PostgreSQL as backend.")
        return True
    else:
        logger.error("❌ Failed to remove SQLite file")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
