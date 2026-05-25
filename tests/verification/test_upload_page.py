#!/usr/bin/env python3
"""
Quick Test Script for Upload PGN Page
Tests the enhanced upload functionality
"""

import subprocess
import sys
import time
from pathlib import Path
import webbrowser

def main():
    print("🧪 Testing Upload PGN Page - Issue #74")
    print("=" * 50)
    
    # Check if test data exists
    test_data_dir = Path("test_data")
    if not test_data_dir.exists():
        print("❌ Test data directory not found")
        print("Creating test data...")
        test_data_dir.mkdir(exist_ok=True)
        
        # Create a simple test PGN
        test_pgn = test_data_dir / "simple_test.pgn"
        with open(test_pgn, "w") as f:
            f.write("""[Event "Test Game"]
[Site "Local"]
[Date "2025.07.05"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0
""")
        print(f"✅ Created test file: {test_pgn}")
    
    # Check test files
    pgn_files = list(test_data_dir.glob("*.pgn"))
    zip_files = list(test_data_dir.glob("*.zip"))
    
    print(f"\n📁 Test files available:")
    print(f"   PGN files: {len(pgn_files)}")
    for pgn in pgn_files:
        print(f"     - {pgn.name}")
    print(f"   ZIP files: {len(zip_files)}")
    for zip_file in zip_files:
        print(f"     - {zip_file.name}")
    
    print(f"\n🚀 Starting Upload PGN Page...")
    print(f"   Page will open at: http://localhost:8501")
    print(f"   Use Ctrl+C to stop the server")
    
    # Give user time to read
    time.sleep(2)
    
    try:
        # Start Streamlit
        result = subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "src/pages/upload_pgn.py",
            "--server.port", "8501",
            "--server.headless", "false"
        ], cwd=Path.cwd())
        
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Install Streamlit: pip install streamlit")
        print(f"   2. Check dependencies: pip install chess python-chess")
        print(f"   3. Verify environment variables in .env file")
        print(f"   4. Run manually: streamlit run src/pages/upload_pgn.py")

if __name__ == "__main__":
    main()
