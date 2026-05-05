import json
import pandas as pd
from pathlib import Path

COUNTRIES = ['AT', 'BE', 'DE', 'DK', 'ES', 'FI', 'FR', 'GB', 'HU', 'IT', 'LU', 'NL', 'PL', 'PT', 'SE']


def parse_point(point: dict) -> dict:
    location = point.get('location') or {}
    return {
        'name': point.get('name'),
        'latitude': location.get('latitude'),
        'longitude': location.get('longitude'),
        'location_247': point.get('location_247'),
        'easy_access_zone': point.get('easy_access_zone'),
        'location_type': point.get('location_type'),
    }


def main():
    data_dir = Path('data')

    with open(data_dir / 'inpost_points.json', encoding='utf-8') as f:
        points = json.load(f)

    by_country: dict[str, list] = {c: [] for c in COUNTRIES}

    for point in points:
        country = point.get('country')
        if country in by_country:
            by_country[country].append(parse_point(point))

    for country, rows in by_country.items():
        df = pd.DataFrame(rows)
        out_path = data_dir / f'{country}.parquet'
        df.to_parquet(out_path, index=False)
        print(f'{country}: {len(rows)} points -> {out_path}')


if __name__ == '__main__':
    main()
