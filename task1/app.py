import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="UFO Sightings Dashboard", layout="wide")

st.title("Interactive UFO Sightings Dashboard")
st.markdown(
    "Explore how UFO sightings vary by **time of day**, **country**, and **shape**."
)

df = pd.read_csv("ufo.csv", header=None, low_memory=False)

df.columns = [
    "datetime",
    "city",
    "state",
    "country",
    "shape",
    "duration_seconds",
    "duration_text",
    "comments",
    "date_posted",
    "latitude",
    "longitude",
]

# -----------------------------
# Clean data
# -----------------------------
df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")
df["hour"] = df["datetime"].dt.hour
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
df["duration_seconds"] = pd.to_numeric(df["duration_seconds"], errors="coerce")

# Clean text fields a little
df["city"] = df["city"].astype(str).str.title()
df["state"] = df["state"].astype(str).str.upper()
df["country"] = df["country"].astype(str).str.lower()
df["shape"] = df["shape"].astype(str).str.lower()


df = df.dropna(subset=["datetime", "hour", "country",
               "shape", "latitude", "longitude"])

# Optional: remove blank-like text values
df = df[
    (df["country"].str.strip() != "")
    & (df["shape"].str.strip() != "")
    & (df["city"].str.strip() != "")
]


st.info(
    "Insight: UFO sightings peak during evening hours (around 20:00–22:00), "
    "with the majority occurring in the United States. Certain shapes like "
    "'light' and 'triangle' are reported most frequently."
)

# -----------------------------
# Sidebar filters
# -----------------------------
st.sidebar.header("Filters")

countries = sorted(df["country"].dropna().unique().tolist())
selected_countries = st.sidebar.multiselect(
    "Select country",
    countries,
    default=countries
)

shapes = sorted(df["shape"].dropna().unique().tolist())
selected_shapes = st.sidebar.multiselect(
    "Select shape",
    shapes,
    default=shapes
)

min_duration = int(df["duration_seconds"].dropna().min())
max_duration = int(df["duration_seconds"].dropna().max())
default_max = min(max_duration, 600)

duration_range = st.sidebar.slider(
    "Duration (seconds)",
    min_value=min_duration,
    max_value=max_duration,
    value=(min_duration, default_max),
)

selected_country_focus = st.sidebar.selectbox(
    "Focus on one country (for deeper analysis)",
    options=["All"] + countries
)

# -----------------------------
# Apply filters
# -----------------------------
filtered_df = df[
    (df["country"].isin(selected_countries))
    & (df["shape"].isin(selected_shapes))
    & (df["duration_seconds"] >= duration_range[0])
    & (df["duration_seconds"] <= duration_range[1])
]

if selected_country_focus != "All":
    filtered_df = filtered_df[filtered_df["country"] == selected_country_focus]


st.subheader("Overview")
st.write(f"Total sightings in current selection: **{len(filtered_df):,}**")

if filtered_df.empty:
    st.warning(
        "No data matches your current filters. Try selecting more countries, shapes, or a wider duration range.")
    st.stop()

# -----------------------------
# Row 1: Hour + Country charts
# -----------------------------
col1, col2 = st.columns(2)

with col1:
    hour_counts = (
        filtered_df.groupby("hour")
        .size()
        .reset_index(name="count")
        .sort_values("hour")
    )

    fig_hour = px.bar(
        hour_counts,
        x="hour",
        y="count",
        title="Sightings by Hour of Day (Peak in Evening Hours)",
        labels={"hour": "Hour of day", "count": "Number of sightings"},
    )
    fig_hour.update_layout(xaxis=dict(dtick=1))
    st.plotly_chart(fig_hour, use_container_width=True)

with col2:
    country_counts = (
        filtered_df.groupby("country")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(10)
    )

    fig_country = px.bar(
        country_counts,
        x="country",
        y="count",
        title="Top Countries by UFO Sightings (US Dominates)",
        labels={"country": "Country", "count": "Number of sightings"},
    )
    st.plotly_chart(fig_country, use_container_width=True)

# -----------------------------
# Map section
# -----------------------------
st.subheader("Geographical Distribution of UFO Sightings")

map_df = filtered_df.dropna(subset=["latitude", "longitude"]).copy()

if not map_df.empty:

    center_lat = map_df["latitude"].mean()
    center_lon = map_df["longitude"].mean()

    if selected_country_focus != "All":
        zoom_level = 4.5
    elif len(selected_countries) == 1:
        zoom_level = 4
    else:
        zoom_level = 1.5

    fig_map = px.scatter_map(
        map_df,
        lat="latitude",
        lon="longitude",
        color="shape",
        hover_name="city",
        hover_data={
            "state": True,
            "country": True,
            "shape": True,
            "duration_text": True,
            "comments": True,
            "latitude": False,
            "longitude": False,
        },
        title="Geographical Distribution of UFO Sightings",
        zoom=zoom_level,
        height=650,
    )

    fig_map.update_layout(
        map_style="open-street-map",
        map=dict(
            center=dict(lat=center_lat, lon=center_lon),
            zoom=zoom_level,
        ),
        margin={"r": 0, "t": 50, "l": 0, "b": 0},
        legend_title_text="Shape",
    )

    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("No map data available for the current selection.")

# -----------------------------
# Shape chart
# -----------------------------
shape_counts = (
    filtered_df.groupby("shape")
    .size()
    .reset_index(name="count")
    .sort_values("count", ascending=False)
    .head(10)
)

fig_shape = px.bar(
    shape_counts,
    x="shape",
    y="count",
    title="Most Common UFO Shapes (Light & Triangle Most Frequent)",
    labels={"shape": "Shape", "count": "Number of sightings"},
)

st.plotly_chart(fig_shape, use_container_width=True)


st.subheader("Sample Sightings in Current Selection")
st.dataframe(
    filtered_df[["datetime", "city", "state",
                 "country", "shape", "duration_text"]]
    .sort_values("datetime", ascending=False)
    .head(20),
    use_container_width=True
)
