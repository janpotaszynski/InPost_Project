import json
import pandas as pd
from pathlib import Path

COUNTRIES = ['AT', 'BE', 'DE', 'DK', 'ES', 'FI', 'FR', 'GB', 'HU', 'IT', 'LU', 'NL', 'PL', 'PT', 'SE']

FUNCTIONS = [
    'allegro_courier_collect', 'allegro_courier_reverse_return_send', 'allegro_courier_send',
    'allegro_letter_reverse_return_send', 'allegro_letter_send', 'allegro_parcel_collect',
    'allegro_parcel_reverse_return_send', 'allegro_parcel_send', 'cross_network_parcel_collect',
    'cross_network_parcel_send', 'parcel', 'parcel_collect', 'parcel_reverse_return_send',
    'parcel_send', 'standard_courier_reverse_return_send', 'standard_courier_send',
    'cool_parcel_collect', 'standard_courier_collect', 'standard_letter_collect',
    'standard_letter_send', 'allegro_letter_collect', 'laundry_collect',
]

PAYMENT_TYPES = {
    '0': 'Payments are not supported',
    '1': 'Cash payment at the point',
    '2': 'Payment by card in the machine',
    '3': 'Payment by cash and card',
}

PHYSICAL_TYPES = ['None', 'bankopaczkomaty', 'bloqit', 'classic', 'legacy', 'modular', 'newfm', 'next', 'pickuphero', 'screenless']


def parse_point(point: dict) -> dict:
    location = point.get('location') or {}
    functions = set(point.get('functions') or [])
    raw_payment = point.get('payment_type') or {}
    payment_key = next(iter(raw_payment), None)
    physical = str(point.get('physical_type')) if point.get('physical_type') is not None else 'None'

    row = {
        'name': point.get('name'),
        'type': ', '.join(point.get('type') or []),
        'status': point.get('status'),
        'longitude': location.get('longitude'),
        'latitude': location.get('latitude'),
        'location_type': point.get('location_type'),
        'payment_available': point.get('payment_available'),
        'payment_type': PAYMENT_TYPES.get(payment_key) if payment_key else None,
        'location_247': point.get('location_247'),
        'easy_access_zone': point.get('easy_access_zone'),
        'physical_type': physical if physical in PHYSICAL_TYPES else None,
        'print_in_store': point.get('print_in_store'),
    }

    for func in FUNCTIONS:
        row[func] = func in functions

    return row


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
        for func in FUNCTIONS:
            if func in df.columns:
                df[func] = df[func].astype('boolean')
        out_path = data_dir / f'{country}.parquet'
        df.to_parquet(out_path, index=False)
        print(f'{country}: {len(rows)} points -> {out_path}')


if __name__ == '__main__':
    main()
