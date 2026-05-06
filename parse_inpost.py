import json
from pathlib import Path

import pandas as pd

COUNTRIES = ["AT", "BE", "DE", "DK", "ES", "FI", "FR", "GB", "HU", "IT", "LU", "NL", "PL", "PT", "SE"]
DATA_DIR = Path("data")


def _parse_point(raw: dict) -> dict:
    loc = raw.get("location") or {}
    return {
        "name":             raw.get("name"),
        "latitude":         loc.get("latitude"),
        "longitude":        loc.get("longitude"),
        "location_247":     raw.get("location_247"),
        "easy_access_zone": raw.get("easy_access_zone"),
        "location_type":    raw.get("location_type"),
    }


def main() -> None:
    source = DATA_DIR / "inpost_points.json"

    if not source.exists():
        missing = [c for c in COUNTRIES if not (DATA_DIR / f"{c}.parquet").exists()]
        if not missing:
            print("Skipping parse_inpost (all country parquets already exist)")
        else:
            print(f"Skipping parse_inpost — {source} not found. Run fetch_inpost.py first.")
        return

    with open(source, encoding="utf-8") as f:
        points = json.load(f)

    by_country: dict[str, list] = {c: [] for c in COUNTRIES}
    for point in points:
        country = point.get("country")
        if country in by_country:
            by_country[country].append(_parse_point(point))

    for country, rows in by_country.items():
        out_path = DATA_DIR / f"{country}.parquet"
        if out_path.exists():
            print(f"  Skipping {country} (already exists)")
            continue
        pd.DataFrame(rows).to_parquet(out_path, index=False)
        print(f"  {country}: {len(rows)} points -> {out_path}")


if __name__ == "__main__":
    main()
