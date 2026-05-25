#!/usr/bin/env python3
"""
Script simple para contar features.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Load environment variables
load_dotenv()

# Import required modules
from db.repository.features_repository import FeaturesRepository

def main():
    """Main function."""
    print("Checking features count...")
    
    try:
        features_repo = FeaturesRepository()
        features = features_repo.get_all()
        count = len(features)
        print(f"Total features in database: {count:,}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
