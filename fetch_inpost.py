import json
import time
from pathlib import Path

import requests

BASE_URL = "https://api-global-points.easypack24.net/v1/points"
PER_PAGE = 500
OUTPUT = Path("data/inpost_points.json")


def fetch_all_points() -> list[dict]:
    points = []
    page = 1

    while True:
        resp = requests.get(BASE_URL, params={"page": page, "per_page": PER_PAGE})
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            break

        points.extend(items)
        print(f"  Page {page}: {len(points)} points total")

        if page >= data.get("total_pages", float("inf")):
            break

        page += 1
        time.sleep(0.1)

    return points


def main() -> None:
    if OUTPUT.exists():
        print(f"Skipping (already exists): {OUTPUT}")
        return

    OUTPUT.parent.mkdir(exist_ok=True)
    print("Fetching InPost points...")
    points = fetch_all_points()
    OUTPUT.write_text(json.dumps(points, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(points)} points -> {OUTPUT}")


if __name__ == "__main__":
    main()
