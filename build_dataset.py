import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

DATA_DIR = Path("data")

LEVELS = [
    ("voivodeships",   "poland.voivodeships.json",  "voivodeship_data.parquet"),
    ("counties",       "poland.counties.json",       "county_data.parquet"),
    ("municipalities", "poland.municipalities.json", "municipality_data.parquet"),
]

# Mapping cause of differences between GeoJSON and GUS data
COUNTY_NAME_MAP = {
    "jeleniogórski": "karkonoski",
}
MUNICIPALITY_NAME_MAP = {
    "Słupia (Jędrzejowska)": "Słupia",
    "Sitkówka-Nowiny":       "Nowiny",
}
NAME_MAPS = {
    "counties":       COUNTY_NAME_MAP,
    "municipalities": MUNICIPALITY_NAME_MAP,
}

_YEAR_SUFFIX_RE = re.compile(r"\s+(?:od|do)\s+\d{4}.*$")


def load_inpost_points() -> gpd.GeoDataFrame:
    pl = pd.read_parquet(DATA_DIR / "PL.parquet")
    return gpd.GeoDataFrame(
        pl,
        geometry=gpd.points_from_xy(pl["longitude"], pl["latitude"]),
        crs="EPSG:4326",
    )


def load_population(level_name: str) -> pd.DataFrame:
    pop = pd.read_parquet(DATA_DIR / f"populations_{level_name}.parquet")

    if level_name == "counties":
        # Strip " od/do YYYY" year suffixes; keep current ("od") entries over historical ("do").
        pop["_is_historical"] = pop["name_match"].str.contains(r"\s+do\s+\d{4}", regex=True)
        pop["name_match"] = pop["name_match"].str.replace(_YEAR_SUFFIX_RE, "", regex=True).str.strip()
        return (
            pop.sort_values(["_is_historical", "population"], ascending=[True, False])
            .drop_duplicates(subset="name_match", keep="first")
            [["name_match", "population"]]
        )

    return (
        pop.sort_values("population", ascending=False)
        .drop_duplicates(subset="name_match", keep="first")
        [["name_match", "population"]]
    )


def aggregate_inpost(points: gpd.GeoDataFrame, polygons: gpd.GeoDataFrame) -> pd.DataFrame:
    polys = polygons[["terc", "name", "geometry"]].rename(columns={"name": "unit_name"})
    joined = gpd.sjoin(points, polys, how="left", predicate="within").dropna(subset=["terc"])

    agg = (
        joined.groupby(["terc", "unit_name"], sort=False)
        .agg(
            parcel_machines=("location_type", "count"),
            parcel_machines_247=("location_247", "sum"),
            parcel_machines_easy_access=("easy_access_zone", "sum"),
            parcel_machines_indoor=("location_type", lambda x: (x == "Indoor").sum()),
            parcel_machines_outdoor=("location_type", lambda x: (x == "Outdoor").sum()),
        )
        .reset_index()
        .rename(columns={"unit_name": "name"})
    )

    int_cols = ["parcel_machines_247", "parcel_machines_easy_access",
                "parcel_machines_indoor", "parcel_machines_outdoor"]
    agg[int_cols] = agg[int_cols].astype(int)
    return agg


def build_level(
    level_name: str,
    geojson_file: str,
    out_file: str,
    points: gpd.GeoDataFrame,
) -> None:
    print(f"\n{level_name}")

    polygons = gpd.read_file(DATA_DIR / geojson_file)
    pop = load_population(level_name)
    agg = aggregate_inpost(points, polygons)
    print(f"  Spatial join done: {len(agg)} units with points (of {len(polygons)} total)")

    result = polygons[["terc", "name"]].merge(agg, on=["terc", "name"], how="left")

    int_cols = ["parcel_machines", "parcel_machines_247", "parcel_machines_easy_access",
                "parcel_machines_indoor", "parcel_machines_outdoor"]
    result[int_cols] = result[int_cols].fillna(0).astype(int)

    name_map = NAME_MAPS.get(level_name, {})
    join_key = result["name"].replace(name_map) if name_map else result["name"]
    result = result.merge(pop, left_on=join_key, right_on="name_match", how="left").drop(columns=["name_match"])

    print(f"  Population matched: {result['population'].notna().sum()} / {len(result)} units")

    out_path = DATA_DIR / out_file
    result.to_parquet(out_path, index=False)
    print(f"  Saved {len(result)} rows -> {out_path}")


def main() -> None:
    print("Loading InPost Poland points...")
    points = load_inpost_points()
    print(f"  {len(points)} points loaded")

    for level_name, geojson_file, out_file in LEVELS:
        build_level(level_name, geojson_file, out_file, points)

    print("\nDone.")


if __name__ == "__main__":
    main()
