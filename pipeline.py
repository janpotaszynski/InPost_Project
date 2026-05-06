import subprocess
import sys
from pathlib import Path

STEPS = [
    # "fetch_inpost.py",
    "parse_inpost.py",
    "fetch_boundaries.py",
    "fetch_populations.py",
    "build_dataset.py",
]


def main() -> None:
    Path("data").mkdir(exist_ok=True)
    for script in STEPS:
        print(f"─── {script} ───")
        subprocess.run([sys.executable, script], check=True)
        print()


if __name__ == "__main__":
    main()
