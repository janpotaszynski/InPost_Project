import geopandas as gpd
import pandas as pd
from pathlib import Path

DATA = Path("data")

LEVELS = [
    ("voivodeships",   "poland.voivodeships.json",  "voivodeship_data.parquet"),
    ("counties",       "poland.counties.json",       "county_data.parquet"),
    ("municipalities", "poland.municipalities.json", "municipality_data.parquet"),
]


def load_inpost_points() -> gpd.GeoDataFrame:
    pl = pd.read_parquet(DATA / "PL.parquet")
    return gpd.GeoDataFrame(
        pl,
        geometry=gpd.points_from_xy(pl["longitude"], pl["latitude"]),
        crs="EPSG:4326",
    )


def load_population(level_name: str) -> pd.DataFrame:
    pop = pd.read_parquet(DATA / f"populations_{level_name}.parquet")
    return (
        pop.sort_values("population", ascending=False)
        .drop_duplicates(subset="name_match", keep="first")
        [["name_match", "population"]]
    )


def aggregate_inpost(points: gpd.GeoDataFrame, polygons: gpd.GeoDataFrame) -> pd.DataFrame:
    polys = polygons[["terc", "name", "geometry"]].rename(columns={"name": "unit_name"})
    joined = gpd.sjoin(points, polys, how="left", predicate="within")
    joined = joined.dropna(subset=["terc"])

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

    for col in ["parcel_machines_247", "parcel_machines_easy_access", "parcel_machines_indoor", "parcel_machines_outdoor"]:
        agg[col] = agg[col].astype(int)

    return agg


def build_level(level_name: str, geojson_file: str, out_file: str, points: gpd.GeoDataFrame) -> None:
    print(f"\n{level_name}")

    polygons = gpd.read_file(DATA / geojson_file)
    pop = load_population(level_name)

    agg = aggregate_inpost(points, polygons)
    print(f"  Spatial join done: {len(agg)} units with points (of {len(polygons)} total)")

    result = polygons[["terc", "name"]].merge(agg, on=["terc", "name"], how="left")

    for col in ["parcel_machines", "parcel_machines_247", "parcel_machines_easy_access", "parcel_machines_indoor", "parcel_machines_outdoor"]:
        result[col] = result[col].fillna(0).astype(int)

    result = result.merge(pop, left_on="name", right_on="name_match", how="left").drop(columns=["name_match"])

    matched = result["population"].notna().sum()
    print(f"  Population matched: {matched} / {len(result)} units")

    out_path = DATA / out_file
    result.to_parquet(out_path, index=False)
    print(f"  Saved {len(result)} rows -> {out_path}")


def main():
    print("Loading InPost Poland points...")
    points = load_inpost_points()
    print(f"  {len(points)} points loaded")

    for level_name, geojson_file, out_file in LEVELS:
        build_level(level_name, geojson_file, out_file, points)

    print("\nDone.")


if __name__ == "__main__":
    main()
