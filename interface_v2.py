import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(layout="wide", page_title="Poland InPost Stats")

LEVELS = {
    "Voivodeships":   ("poland.voivodeships.json",  "voivodeship_data.parquet"),
    "Counties":       ("poland.counties.json",       "county_data.parquet"),
    "Municipalities": ("poland.municipalities.json", "municipality_data.parquet"),
}

STATS = {
    "Parcel machines (total)":       "parcel_machines",
    "Parcel machines 24/7":          "parcel_machines_247",
    "Parcel machines – easy access": "parcel_machines_easy_access",
    "Parcel machines – indoor":      "parcel_machines_indoor",
    "Parcel machines – outdoor":     "parcel_machines_outdoor",
    "Population":                    "population",
}

DATA_DIR = Path("data")


@st.cache_data
def load_geojson(filename: str) -> dict:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_data(filename: str) -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / filename)


def build_map(geojson: dict, df: pd.DataFrame, stat_col: str, stat_label: str) -> go.Figure:
    color_values = pd.to_numeric(df[stat_col], errors="coerce")

    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=df["terc"].astype(str),
        featureidkey="properties.terc",
        z=color_values,
        colorscale="YlOrRd",
        text=df["name"],
        customdata=df[[stat_col]].values,
        hovertemplate="<b>%{text}</b><br>" + stat_label + ": %{customdata[0]:,}<extra></extra>",
        colorbar=dict(title=stat_label, thickness=15, len=0.6),
        marker_line_color="white",
        marker_line_width=0.5,
    ))

    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=800,
    )
    return fig


st.title("Poland – InPost & Population Statistics")

st.sidebar.header("Options")

level = st.sidebar.selectbox("Administrative level", list(LEVELS.keys()))
stat_label = st.sidebar.selectbox("Statistic", list(STATS.keys()))
stat_col = STATS[stat_label]

geojson_file, data_file = LEVELS[level]

for path in [DATA_DIR / geojson_file, DATA_DIR / data_file]:
    if not path.exists():
        st.error(f"Missing file: {path.name}. Run fetch and combine scripts first.")
        st.stop()

geojson = load_geojson(geojson_file)
df = load_data(data_file)

fig = build_map(geojson, df, stat_col, stat_label)
st.plotly_chart(fig, use_container_width=True)
