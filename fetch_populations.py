import re
import time
from pathlib import Path

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://bdl.stat.gov.pl/api/v1/data/by-variable/72305"
PAGE_SIZE = 100
TIMEOUT = 60
MAX_RETRIES = 5

LEVELS = {
    "voivodeships":    2,
    "counties":        5,
    "municipalities":  6,
}

_YEAR_SUFFIX_RE = re.compile(r"\s+(?:od|do)\s+\d{4}.*$")


def _session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=MAX_RETRIES,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    return s


def _normalize_name(name: str, level: str) -> str:
    if level == "counties":
        for prefix in ("Powiat m. st. ", "Powiat m. ", "Powiat "):
            if name.startswith(prefix):
                return name[len(prefix):]
    if level == "municipalities":
        name = name.removeprefix("M.st.")
        name = _YEAR_SUFFIX_RE.sub("", name).strip()
    return name


def fetch_level(level_name: str, unit_level: int) -> pd.DataFrame:
    session = _session()
    rows = []
    page = 0
    total = None

    while True:
        url = (
            f"{BASE_URL}"
            f"?unit-level={unit_level}"
            f"&page-size={PAGE_SIZE}"
            f"&page={page}"
        )

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = session.get(url, timeout=TIMEOUT)
                resp.raise_for_status()
                break
            except requests.exceptions.ReadTimeout:
                if attempt == MAX_RETRIES:
                    raise
                wait = 2 ** attempt
                print(f"    Timeout on page {page}, retrying in {wait}s ({attempt}/{MAX_RETRIES})...")
                time.sleep(wait)

        data = resp.json()

        if total is None:
            total = data["totalRecords"]
            pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
            print(f"  {level_name}: {total} records across {pages} pages")

        for result in data["results"]:
            values = result.get("values") or []
            if not values:
                continue
            latest = max(values, key=lambda v: v["year"])
            rows.append({
                "gus_id":     result["id"],
                "name":       result["name"],
                "name_match": _normalize_name(result["name"], level_name),
                "population": latest["val"],
                "year":       latest["year"],
            })

        fetched = page * PAGE_SIZE + len(data["results"])
        if fetched >= total:
            break

        page += 1
        if page % 10 == 0:
            print(f"    page {page} / {pages}...")
        time.sleep(0.2)

    return pd.DataFrame(rows)


def main() -> None:
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    for level_name, unit_level in LEVELS.items():
        out_path = data_dir / f"populations_{level_name}.parquet"
        if out_path.exists():
            print(f"Skipping {level_name} (already exists)")
            continue
        print(f"Fetching {level_name}...")
        df = fetch_level(level_name, unit_level)
        df.to_parquet(out_path, index=False)
        print(f"  Saved {len(df)} rows -> {out_path}")

    print("Done.")


if __name__ == "__main__":
    main()
