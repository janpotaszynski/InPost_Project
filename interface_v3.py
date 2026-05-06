import json
from pathlib import Path

import numpy as np
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
    "Custom":                        None,
}

# Short aliases used in custom formulas → actual column names
SHORTCUTS = {
    "total":   "parcel_machines",
    "nonstop": "parcel_machines_247",
    "easy":    "parcel_machines_easy_access",
    "indoor":  "parcel_machines_indoor",
    "outdoor": "parcel_machines_outdoor",
    "pop":     "population",
}

DATA_DIR = Path("data")


@st.cache_data
def load_geojson(filename: str) -> dict:
    with open(DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data
def load_data(filename: str) -> pd.DataFrame:
    return pd.read_parquet(DATA_DIR / filename)


def eval_formula(df: pd.DataFrame, formula: str) -> pd.Series:
    """Evaluate a user formula using shortcut column names."""
    rename = {col: alias for alias, col in SHORTCUTS.items()}
    eval_df = df[list(SHORTCUTS.values())].rename(columns=rename).astype(float)
    result = eval_df.eval(formula)
    return result.replace([np.inf, -np.inf], np.nan)


def build_map(
    geojson: dict,
    df: pd.DataFrame,
    color_values: pd.Series,
    hover_label: str,
    is_float: bool = False,
) -> go.Figure:
    fmt = ".4g" if is_float else ","
    fig = go.Figure(go.Choropleth(
        geojson=geojson,
        locations=df["terc"].astype(str),
        featureidkey="properties.terc",
        z=color_values,
        colorscale="YlOrRd",
        text=df["name"],
        customdata=color_values.values.reshape(-1, 1),
        hovertemplate=(
            "<b>%{text}</b><br>"
            + hover_label + ": %{customdata[0]:" + fmt + "}"
            + "<extra></extra>"
        ),
        colorbar=dict(title=hover_label, thickness=15, len=0.6),
        marker_line_color="white",
        marker_line_width=0.5,
    ))
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, height=650)
    return fig


# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.header("Options")

level      = st.sidebar.selectbox("Administrative level", list(LEVELS.keys()))
stat_label = st.sidebar.selectbox("Statistic", list(STATS.keys()))

st.sidebar.markdown("---")
st.sidebar.markdown("**Formula shortcuts**")
st.sidebar.markdown(
    "| Shortcut | Statistic |\n"
    "|----------|-----------|\n"
    "| `total`   | Parcel machines (total) |\n"
    "| `nonstop` | Parcel machines 24/7 |\n"
    "| `easy`    | Parcel machines – easy access |\n"
    "| `indoor`  | Parcel machines – indoor |\n"
    "| `outdoor` | Parcel machines – outdoor |\n"
    "| `pop`     | Population |\n"
)

# ── Main ───────────────────────────────────────────────────────────────────
st.title("Poland – InPost & Population Statistics")

geojson_file, data_file = LEVELS[level]

for path in [DATA_DIR / geojson_file, DATA_DIR / data_file]:
    if not path.exists():
        st.error(f"Missing file: {path.name}. Run fetch and combine scripts first.")
        st.stop()

geojson = load_geojson(geojson_file)
df      = load_data(data_file)

if stat_label == "Custom":
    formula = st.text_input(
        "Formula",
        placeholder="e.g. (total + 3*easy) / pop",
        help="Use shortcuts listed in the sidebar. Arithmetic operators: + - * / ** ()",
    )

    if not formula.strip():
        st.info("Enter a formula above to render the map.")
        st.stop()

    try:
        color_values = eval_formula(df, formula)
    except Exception as e:
        st.error(f"Formula error: {e}")
        st.stop()

    fig = build_map(geojson, df, color_values, hover_label=formula, is_float=True)

else:
    stat_col     = STATS[stat_label]
    color_values = pd.to_numeric(df[stat_col], errors="coerce")
    fig = build_map(geojson, df, color_values, hover_label=stat_label, is_float=False)

st.plotly_chart(fig, use_container_width=True)
