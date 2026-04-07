import pandas as pd
import streamlit as st

from src.data_loader import get_global_dataframe
from src.spotify_client import (
    get_spotify_client,
    fetch_liked_songs,
    fetch_top_artists,
    enrich_liked_with_hf,
)
from src.kpis_personal import (
    build_artist_genres,
    kpi_my_genres,
    kpi_saved_timeline,
    kpi_my_audio_dna,
    kpi_genre_distribution,
    kpi_top_artists,
)
from src.charts_personal import (
    chart_my_genres,
    chart_saved_timeline,
    chart_my_audio_dna,
    chart_genre_distribution,
    chart_top_artists,
)

st.set_page_config(page_title="Mi Perfil — SpotifyAnalytics", page_icon=":material/person:", layout="wide")

st.title(":material/person: Mi Perfil")

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

sp = get_spotify_client()

if sp is None:
    st.info(
        "Conecta tu cuenta de Spotify para ver tus estadísticas personales. "
        "Si el botón de arriba no funciona, ejecuta `python auth.py` en terminal.",
        icon=":material/login:",
    )
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

TIME_RANGE_MAP: dict[str, str] = {
    "Corto plazo (~4 semanas)": "short_term",
    "Medio plazo (~6 meses)": "medium_term",
    "Largo plazo (varios años)": "long_term",
}

with st.sidebar:
    st.header(":material/filter_list: Filtros")

    time_label = st.radio(
        "Período Top Artists",
        options=list(TIME_RANGE_MAP.keys()),
        index=1,
    )
    time_range: str = TIME_RANGE_MAP[time_label]

    date_filter = st.date_input(
        "Rango de fechas (canciones guardadas)",
        value=[],
        help="Filtra liked songs por fecha de guardado",
    )

# ---------------------------------------------------------------------------
# Fetch data
# ---------------------------------------------------------------------------

hf_df, _ = get_global_dataframe()

liked_df = fetch_liked_songs(sp)
top_artists_df = fetch_top_artists(sp, time_range=time_range)

if liked_df.empty:
    st.warning("No se encontraron canciones guardadas en tu biblioteca.", icon=":material/warning:")
    st.stop()

# Apply date filter
if date_filter and len(date_filter) == 2:
    start_date, end_date = date_filter
    liked_df = liked_df[
        (liked_df["added_at"].dt.date >= start_date)
        & (liked_df["added_at"].dt.date <= end_date)
    ]

# Enrich with HF audio features
enriched_df = enrich_liked_with_hf(liked_df, hf_df)

# Build artist genres from top_artists + HF data (0 extra API calls)
artist_genres = build_artist_genres(top_artists_df, enriched_df)

# ---------------------------------------------------------------------------
# Metrics row
# ---------------------------------------------------------------------------

with st.container(horizontal=True):
    st.metric("Canciones guardadas", f"{len(liked_df):,}", border=True)
    st.metric("Artistas únicos", f"{liked_df['artist'].nunique():,}", border=True)
    n_genres = len(set(g for gs in artist_genres.values() for g in gs))
    st.metric("Géneros", f"{n_genres:,}", border=True)

# ---------------------------------------------------------------------------
# P1 — Mis Géneros
# ---------------------------------------------------------------------------

st.space("small")
st.subheader(":material/category: P1 · Mis Géneros")

df_my_genres = kpi_my_genres(liked_df, artist_genres)

if not df_my_genres.empty:
    tab_chart, tab_table = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
    with tab_chart:
        st.plotly_chart(chart_my_genres(df_my_genres), width="stretch")
    with tab_table:
        st.dataframe(df_my_genres, hide_index=True, width="stretch")
else:
    st.info("No se encontraron géneros para tus artistas.", icon=":material/info:")

st.space("small")

# ---------------------------------------------------------------------------
# P2 — Timeline de Guardados
# ---------------------------------------------------------------------------

st.subheader(":material/schedule: P2 · Timeline de canciones guardadas")

df_timeline = kpi_saved_timeline(liked_df)

if not df_timeline.empty:
    tab_chart2, tab_table2 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
    with tab_chart2:
        st.plotly_chart(chart_saved_timeline(df_timeline), width="stretch")
    with tab_table2:
        st.dataframe(df_timeline, hide_index=True, width="stretch")
else:
    st.info("Sin datos de timeline.", icon=":material/info:")

st.space("small")

# ---------------------------------------------------------------------------
# P3 — Mi ADN Musical / Distribución de Géneros (fallback)
# ---------------------------------------------------------------------------

df_dna = kpi_my_audio_dna(enriched_df)

if df_dna is not None:
    st.subheader(":material/graphic_eq: P3 · Mi ADN musical")

    tab_chart3, tab_table3 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
    with tab_chart3:
        st.plotly_chart(chart_my_audio_dna(df_dna), width="stretch")
    with tab_table3:
        st.dataframe(df_dna, hide_index=True, width="stretch")
else:
    st.subheader(":material/donut_small: P3 · Distribución de géneros")
    st.caption("Menos de 20 canciones coinciden con el dataset global — mostrando géneros en su lugar.")

    df_genre_dist = kpi_genre_distribution(artist_genres)
    if not df_genre_dist.empty:
        tab_chart3, tab_table3 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
        with tab_chart3:
            st.plotly_chart(
                chart_genre_distribution(df_genre_dist), width="stretch",
            )
        with tab_table3:
            st.dataframe(df_genre_dist, hide_index=True, width="stretch")
    else:
        st.info("Sin datos de géneros.", icon=":material/info:")

st.space("small")

# ---------------------------------------------------------------------------
# P4 — Mis Top Artists
# ---------------------------------------------------------------------------

st.subheader(":material/star: P4 · Mis top artistas")

df_top = kpi_top_artists(liked_df, top_artists_df)

if not df_top.empty:
    tab_chart4, tab_table4 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
    with tab_chart4:
        st.plotly_chart(chart_top_artists(df_top), width="stretch")
    with tab_table4:
        st.dataframe(df_top, hide_index=True, width="stretch")
else:
    st.info("Sin datos de artistas.", icon=":material/info:")
