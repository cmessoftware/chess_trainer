"""Quick script to run orchestrated tests."""
import subprocess
import sys

def run_tests():
    """Run all orchestrated tests."""
    tests = [
        "tests/ai_coach/orchestrated/test_planner_service.py",
        "tests/ai_coach/orchestrated/test_executor_service.py",
        "tests/ai_coach/orchestrated/test_memory_service.py",
        "tests/ai_coach/orchestrated/test_integration.py"
    ]
    
    cmd = [
        sys.executable,
        "-m",
        "pytest"
    ] + tests + [
        "-v",
        "--tb=short",
        "-m", "unit or integration",
        "--color=yes"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=r"c:\Users\sergiosal\source\repos\chess_trainer")
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
