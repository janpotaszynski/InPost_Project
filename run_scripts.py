import subprocess
import sys
import os
from pathlib import Path

def run_scripts():
    # 1. Define and create the directory
    output_dir = "data"
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    print(f"--- Directory '{output_dir}' is ready ---\n")

    # 2. List of files to run in order
    scripts = [
        "fetch_inpost.py",
        "create_country_tables.py",
        "fetch_poland.py",
        "fetch_populations.py",
        "combine_poland_data.py"
    ]

    for script in scripts:
        print(f"--- Starting: {script} ---")
        try:
            # sys.executable ensures it uses the same Python environment
            subprocess.run([sys.executable, script], check=True)
            print(f"--- Finished: {script} ---\n")
        except subprocess.CalledProcessError as e:
            print(f"Error: {script} failed with exit code {e.returncode}")
            break

if __name__ == "__main__":
    run_scripts()