import streamlit as st

from src.data_loader import get_global_dataframe
from src.kpis_global import (
    kpi_top_genres,
    kpi_genre_dna,
    kpi_popularity_correlation,
    kpi_sentiment_by_year,
    kpi_popularity_distribution,
)
from src.charts_global import (
    chart_top_genres,
    chart_genre_dna,
    chart_popularity_correlation,
    chart_sentiment_by_year,
    chart_popularity_distribution,
)
from src.theme import inject_premium_css

st.set_page_config(page_title="Global — SpotifyAnalytics", page_icon=":material/public:", layout="wide")
inject_premium_css()

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

df, match_rate = get_global_dataframe()
has_year: bool = "year" in df.columns

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header(":material/filter_list: Filtros")

    all_genres = sorted(df["genre"].dropna().unique().tolist())
    selected_genres: list[str] = st.multiselect(
        "Género(s)", options=all_genres, default=[], placeholder="Todos los géneros",
    )

    pop_min, pop_max = int(df["popularity"].min()), int(df["popularity"].max())
    pop_range: tuple[int, int] = st.slider(
        "Rango de popularidad", min_value=pop_min, max_value=pop_max,
        value=(pop_min, pop_max),
    )

    if has_year:
        years_available = sorted(df["year"].dropna().astype(int).unique().tolist())
        year_range = st.select_slider(
            "Año", options=years_available,
            value=(years_available[0], years_available[-1]),
        )
    else:
        year_range = None

    only_explicit: bool = st.checkbox("Solo explícitas", value=False)

# ---------------------------------------------------------------------------
# Apply filters
# ---------------------------------------------------------------------------

filtered = df.copy()

if selected_genres:
    filtered = filtered[filtered["genre"].isin(selected_genres)]

filtered = filtered[
    (filtered["popularity"] >= pop_range[0])
    & (filtered["popularity"] <= pop_range[1])
]

if has_year and year_range is not None:
    filtered = filtered[
        filtered["year"].between(year_range[0], year_range[1])
    ]

if only_explicit:
    filtered = filtered[filtered["explicit"] == True]  # noqa: E712

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title(":material/public: Análisis Global")

with st.container(horizontal=True):
    st.metric("Tracks filtrados", f"{len(filtered):,}", border=True)
    st.metric("Artistas", f"{filtered['artist'].nunique():,}", border=True)
    st.metric("Géneros", f"{filtered['genre'].nunique():,}", border=True)

if filtered.empty:
    st.warning("No hay datos con los filtros seleccionados.", icon=":material/warning:")
    st.stop()

# ---------------------------------------------------------------------------
# G1 — Top Géneros
# ---------------------------------------------------------------------------

st.space("small")
st.subheader(":material/category: G1 · Top Géneros")

df_genres = kpi_top_genres(filtered)

tab_chart, tab_table = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
with tab_chart:
    st.plotly_chart(chart_top_genres(df_genres), width="stretch")
with tab_table:
    st.dataframe(df_genres, hide_index=True, width="stretch")

st.space("small")

# ---------------------------------------------------------------------------
# G2 — ADN Musical por Género
# ---------------------------------------------------------------------------

st.subheader(":material/graphic_eq: G2 · ADN Musical por Género")

genre_options = sorted(filtered["genre"].dropna().unique().tolist())
selected_genre = st.selectbox(
    "Selecciona un género para el radar", options=genre_options,
    index=0 if genre_options else None,
)

if selected_genre:
    df_dna = kpi_genre_dna(filtered, selected_genre)
    if not df_dna.empty:
        tab_chart2, tab_table2 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
        with tab_chart2:
            st.plotly_chart(
                chart_genre_dna(df_dna, selected_genre), width="stretch",
            )
        with tab_table2:
            st.dataframe(df_dna, hide_index=True, width="stretch")
    else:
        st.info("Sin datos para este género.", icon=":material/info:")

st.space("small")

# ---------------------------------------------------------------------------
# G3 — Popularidad vs Features
# ---------------------------------------------------------------------------

st.subheader(":material/scatter_plot: G3 · Popularidad vs Audio Features")

corr_df = kpi_popularity_correlation(filtered)

tab_chart3, tab_table3 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
with tab_chart3:
    st.plotly_chart(chart_popularity_correlation(corr_df), width="stretch")
with tab_table3:
    st.dataframe(corr_df, width="stretch")

st.space("small")

# ---------------------------------------------------------------------------
# G4 — Sentimiento Temporal / Distribución de Popularidad (fallback)
# ---------------------------------------------------------------------------

df_sentiment = kpi_sentiment_by_year(filtered) if has_year else None

if df_sentiment is not None and len(df_sentiment) > 1:
    st.subheader(":material/timeline: G4 · Sentimiento Musical por Década")

    tab_chart4, tab_table4 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
    with tab_chart4:
        st.plotly_chart(chart_sentiment_by_year(df_sentiment), width="stretch")
    with tab_table4:
        st.dataframe(df_sentiment, hide_index=True, width="stretch")
else:
    st.subheader(":material/equalizer: G4 · Distribución de Popularidad")

    df_dist = kpi_popularity_distribution(filtered)

    tab_chart4, tab_table4 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
    with tab_chart4:
        st.plotly_chart(
            chart_popularity_distribution(df_dist), width="stretch",
        )
    with tab_table4:
        st.dataframe(df_dist, hide_index=True, width="stretch")

# ---------------------------------------------------------------------------
# G5 — Top 100 Playlist Player
# ---------------------------------------------------------------------------

st.space("small")
st.subheader(":material/headphones: G5 · Top 100 más populares")

top100 = (
    filtered
    .dropna(subset=["track_id"])
    .nlargest(100, "popularity")
    [["track_id", "track_name", "artist", "duration_ms"]]
    .copy()
)

# Add album_cover_url placeholder (HF dataset doesn't have cover art)
if "album_cover_url" not in top100.columns:
    top100["album_cover_url"] = None

if not top100.empty:
    from src.components.playlist_player import render_playlist
    from src.spotify_auth import get_access_token

    _token = get_access_token()
    render_playlist(
        top100,
        mode="sdk" if _token else "embed",
        title="Top 100 — Más Populares",
        key="global_top100",
        token=_token,
    )
