from pathlib import Path

import requests

BASE_URL = "https://raw.githubusercontent.com/jusuff/PolandGeoJson/main/data"
FILES = [
    "poland.voivodeships.json",
    "poland.counties.json",
    "poland.municipalities.json",
]


def main() -> None:
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    for filename in FILES:
        out_path = data_dir / filename
        if out_path.exists():
            print(f"  Skipping {filename} (already exists)")
            continue
        resp = requests.get(f"{BASE_URL}/{filename}", timeout=30)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)
        print(f"  Fetched {filename} -> {out_path}")


if __name__ == "__main__":
    main()
