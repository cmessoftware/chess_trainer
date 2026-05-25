#!/usr/bin/env python3
"""
Script para verificar el estado de las tablas de la base de datos.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import text

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Load environment variables
load_dotenv()

# Import required modules
from db.session import get_session

def check_tables():
    """Check the state of database tables."""
    print("=" * 60)
    print("DATABASE TABLE STATUS")
    print("=" * 60)
    
    try:
        session = get_session()
        
        # Check each table
        tables_to_check = [
            'alembic_version',
            'games', 
            'features',
            'analyzed_tacticals',
            'studies',
            'study_positions',
            'processed_features'
        ]
        
        for table_name in tables_to_check:
            try:
                result = session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).fetchone()
                count = result[0] if result else 0
                print(f"{table_name:20s}: {count:>8,} rows")
            except Exception as e:
                print(f"{table_name:20s}: ERROR - {str(e)[:50]}")
        
        session.close()
        
    except Exception as e:
        print(f"Database connection error: {e}")
    
    print("=" * 60)

if __name__ == "__main__":
    check_tables()
