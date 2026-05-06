import requests
import json
import time
import numpy as np

def fetch_inpost_points():
    base_url = "https://api-global-points.easypack24.net/v1/points"
    points = []
    page = 1

    print("Rozpoczynam pobieranie danych...")

    while True:
        # Parametry zapytania: numer strony i liczba wyników na stronę (max 500)
        params = {
            'page': page,
            'per_page': 500
        }

        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status() # Rzuci błąd, jeśli status nie będzie 200

            data = response.json()
            items = data.get('items', [])

            if not items:
                break # Jeśli lista jest pusta, dotarliśmy do końca

            points.extend(items)
            print(f"Pobrano stronę {page}... (Łącznie punktów: {len(points)})")

            # Sprawdzenie czy jest kolejna strona w metadanych (jeśli API je udostępnia)
            # Jeśli nie, pętla przerwie się przy następnej pustej stronie
            if page >= data.get('total_pages', float('inf')):
                break

            page += 1
            # Krótka pauza, żeby nie przeciążyć serwera i nie dostać blokady (Rate Limiting)
            time.sleep(0.1)

        except requests.exceptions.RequestException as e:
            print(f"Wystąpił błąd podczas pobierania strony {page}: {e}")
            break

    return points

# Uruchomienie i zapis do pliku
if __name__ == "__main__":
    all_points = fetch_inpost_points()

    # Zapisujemy wszystko do pliku JSON
    with open("data/inpost_points.json", "w", encoding="utf-8") as f:
        json.dump(all_points, f, ensure_ascii=False, indent=4)

    print(f"\nGotowe! Pomyślnie pobrano {len(all_points)} punktów.")
    print("Dane zostały zapisane w pliku: inpost_points.json")
