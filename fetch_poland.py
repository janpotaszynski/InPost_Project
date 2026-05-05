import requests
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/jusuff/PolandGeoJson/main/data"
FILES = [
    "poland.voivodeships.json",
    "poland.counties.json",
    "poland.municipalities.json",
]


def main():
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    for filename in FILES:
        url = f"{BASE_URL}/{filename}"
        print(f"Fetching {filename}...")
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        out_path = data_dir / filename
        out_path.write_bytes(response.content)
        print(f"  Saved to {out_path}")


if __name__ == "__main__":
    main()
