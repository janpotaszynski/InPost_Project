import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(layout="wide", page_title="Poland Map")

LEVELS = {
    "Voivodeships": "poland.voivodeships.json",
    "Counties": "poland.counties.json",
    "Municipalities": "poland.municipalities.json",
}

DATA_DIR = Path("data")


@st.cache_data
def load_geojson(filename: str) -> dict:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def build_map(geojson: dict) -> px.choropleth:
    rows = [{"terc": f["properties"]["terc"], "name": f["properties"]["name"]} for f in geojson["features"]]
    df = pd.DataFrame(rows)
    df["value"] = 1

    fig = px.choropleth(
        df,
        geojson=geojson,
        locations="terc",
        featureidkey="properties.terc",
        color="value",
        color_continuous_scale=[[0, "#a8c8f0"], [1, "#a8c8f0"]],
        hover_name="name",
        hover_data={"value": False, "terc": False},
    )
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        coloraxis_showscale=False,
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        height=800,
    )
    fig.update_traces(marker_line_color="white", marker_line_width=0.5)
    return fig


st.title("Poland Administrative Boundaries")

level = st.sidebar.selectbox(
    "Administrative level",
    list(LEVELS.keys()),
    help="Choose the level of administrative division to display",
)

missing = not (DATA_DIR / LEVELS[level]).exists()
if missing:
    st.error(f"GeoJSON file not found. Run `python fetch_poland.py` first.")
    st.stop()

geojson = load_geojson(LEVELS[level])
fig = build_map(geojson)
st.plotly_chart(fig, use_container_width=True)
