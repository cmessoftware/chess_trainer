import time
# modules/tactical_analysis.py
from modules.tactical_analysis_parallel import run_parallel_analysis_from_db

if __name__ == "__main__":
    print("Running parallel analysis...")
    start_time = time.time()
    run_parallel_analysis_from_db()
    end_time = time.time()
    print(f"Parallel analysis completed in {end_time - start_time:.2f} seconds.")
