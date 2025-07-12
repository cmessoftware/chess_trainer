#!/usr/bin/env python3
"""
Quick runner for the ML datasets analysis - NON-DESTRUCTIVE
"""
import os
import sys
import subprocess
from pathlib import Path


def run_analysis_in_container():
    """Run the analysis script inside the notebooks container"""
    print("🚀 Running ML datasets analysis in container...")
    print("⚠️ This is completely NON-DESTRUCTIVE - only reads existing data")

    # Check if we're in the right directory
    if not Path("docker-compose.yml").exists():
        print("❌ Please run this from the project root directory")
        return 1

    # Copy the analysis script to the container and run it
    commands = [
        # Ensure the notebooks container is running
        "docker-compose up -d notebooks",
        # Copy the analysis script
        "docker cp src/ml/analyze_real_datasets.py chess_trainer-notebooks-1:/notebooks/",
        # Run the analysis
        "docker-compose exec notebooks python /notebooks/analyze_real_datasets.py",
    ]

    for cmd in commands:
        print(f"📋 Running: {cmd}")
        try:
            result = subprocess.run(cmd, shell=True, check=True, capture_output=False)
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {cmd}")
            print(f"Error: {e}")
            return 1

    print("✅ Analysis completed successfully")
    return 0


def run_analysis_local():
    """Run the analysis script locally"""
    print("🚀 Running ML datasets analysis locally...")
    print("⚠️ This is completely NON-DESTRUCTIVE - only reads existing data")

    script_path = Path(__file__).parent / "analyze_real_datasets.py"

    if not script_path.exists():
        print(f"❌ Analysis script not found: {script_path}")
        return 1

    try:
        # Run the script
        result = subprocess.run([sys.executable, str(script_path)], check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"❌ Analysis failed: {e}")
        return 1


if __name__ == "__main__":
    print("🔬 Chess Datasets ML Analysis Runner")
    print("Choose execution mode:")
    print("1. Run in Docker container (recommended)")
    print("2. Run locally")

    choice = input("Enter choice (1 or 2): ").strip()

    if choice == "1":
        exit_code = run_analysis_in_container()
    elif choice == "2":
        exit_code = run_analysis_local()
    else:
        print("❌ Invalid choice")
        exit_code = 1

    sys.exit(exit_code)
