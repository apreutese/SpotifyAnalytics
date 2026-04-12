"""Demo Perfil Spotify — personal stats from local CSVs (no OAuth required)."""

import pandas as pd
import streamlit as st

from src.personal_loader import (
    load_my_liked_songs,
    load_my_top_tracks,
    load_my_top_artists,
    has_personal_data,
)
from src.kpis_personal import (
    kpi_saved_timeline,
    kpi_release_decades,
    kpi_explicit_ratio,
    kpi_top_albums,
    kpi_top_artists,
)
from src.charts_personal import (
    chart_saved_timeline,
    chart_release_decades,
    chart_explicit_ratio,
    chart_top_albums,
    chart_top_artists,
)
from src.theme import inject_premium_css

st.set_page_config(
    page_title="Demo Perfil — SpotifyAnalytics",
    page_icon=":material/person:",
    layout="wide",
)
inject_premium_css()

st.title(":material/person: Demo Perfil Spotify")
st.caption(
    "Datos personales exportados previamente (snapshot estático). "
    "Sin conexión a Spotify necesaria."
)

# ---------------------------------------------------------------------------
# Check data availability
# ---------------------------------------------------------------------------

if not has_personal_data():
    st.warning(
        "No se encontraron CSVs personales en `data/`. "
        "Ejecuta `python scripts/export_personal_data.py` para generarlos.",
        icon=":material/warning:",
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
# Load data from CSVs
# ---------------------------------------------------------------------------

liked_df = load_my_liked_songs(enriched=True)
top_artists_df = load_my_top_artists(time_range=time_range)

if liked_df is None or liked_df.empty:
    st.warning("No se encontraron canciones guardadas en los CSVs.", icon=":material/warning:")
    st.stop()

if top_artists_df is None:
    top_artists_df = pd.DataFrame()

# Apply date filter
if date_filter and len(date_filter) == 2:
    start_date, end_date = date_filter
    if "added_at" in liked_df.columns:
        liked_df = liked_df[
            (liked_df["added_at"].dt.date >= start_date)
            & (liked_df["added_at"].dt.date <= end_date)
        ]

# ---------------------------------------------------------------------------
# Metrics row
# ---------------------------------------------------------------------------

n_albums = liked_df["album"].nunique() if "album" in liked_df.columns else 0
total_min = round(liked_df["duration_ms"].dropna().sum() / 60_000) if "duration_ms" in liked_df.columns else 0

with st.container(horizontal=True):
    st.metric("Canciones guardadas", f"{len(liked_df):,}", border=True)
    st.metric("Artistas únicos", f"{liked_df['artist'].nunique():,}", border=True)
    st.metric("Álbumes", f"{n_albums:,}", border=True)
    st.metric("Duración total", f"{total_min:,} min", border=True)

# ---------------------------------------------------------------------------
# P1 — Timeline de Guardados
# ---------------------------------------------------------------------------

st.space("small")
st.subheader(":material/schedule: P1 · Timeline de canciones guardadas")

df_timeline = kpi_saved_timeline(liked_df)

if not df_timeline.empty:
    tab_c1, tab_t1 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
    with tab_c1:
        st.plotly_chart(chart_saved_timeline(df_timeline), use_container_width=True)
    with tab_t1:
        st.dataframe(df_timeline, hide_index=True, use_container_width=True)
else:
    st.info("Sin datos de timeline.", icon=":material/info:")

st.space("small")

# ---------------------------------------------------------------------------
# P2 — Décadas de Lanzamiento
# ---------------------------------------------------------------------------

st.subheader(":material/calendar_month: P2 · Décadas de lanzamiento")

df_decades = kpi_release_decades(liked_df)

if not df_decades.empty:
    tab_c2, tab_t2 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
    with tab_c2:
        st.plotly_chart(chart_release_decades(df_decades), use_container_width=True)
    with tab_t2:
        st.dataframe(df_decades, hide_index=True, use_container_width=True)
else:
    st.info("Sin datos de fecha de lanzamiento.", icon=":material/info:")

st.space("small")

# ---------------------------------------------------------------------------
# P3 & P4 — Explicit vs Clean + Top Álbumes (side by side)
# ---------------------------------------------------------------------------

col_left, col_right = st.columns(2)

with col_left:
    st.subheader(":material/explicit: P3 · Explicit vs Clean")
    df_explicit = kpi_explicit_ratio(liked_df)
    if not df_explicit.empty:
        tab_c3, tab_t3 = st.tabs([":material/donut_small: Gráfico", ":material/table: Tabla"])
        with tab_c3:
            st.plotly_chart(chart_explicit_ratio(df_explicit), use_container_width=True)
        with tab_t3:
            st.dataframe(df_explicit, hide_index=True, use_container_width=True)
    else:
        st.info("Sin datos de explicit.", icon=":material/info:")

with col_right:
    st.subheader(":material/album: P4 · Álbumes más repetidos")
    df_albums = kpi_top_albums(liked_df)
    if not df_albums.empty:
        tab_c4, tab_t4 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
        with tab_c4:
            st.plotly_chart(chart_top_albums(df_albums), use_container_width=True)
        with tab_t4:
            display_cols = [c for c in ["album_cover_url", "album", "count"] if c in df_albums.columns]
            col_cfg = {
                "album": st.column_config.TextColumn("Álbum"),
                "count": st.column_config.NumberColumn("Tracks"),
            }
            if "album_cover_url" in display_cols:
                col_cfg["album_cover_url"] = st.column_config.ImageColumn("Portada", width=60)
            st.dataframe(df_albums[display_cols], hide_index=True, use_container_width=True, column_config=col_cfg)
    else:
        st.info("Sin datos de álbumes.", icon=":material/info:")

st.space("small")

# ---------------------------------------------------------------------------
# P5 — Mis Top Artists
# ---------------------------------------------------------------------------

st.subheader(":material/star: P5 · Mis top artistas")

df_top = kpi_top_artists(liked_df, top_artists_df)

if not df_top.empty:
    tab_c5, tab_t5 = st.tabs([":material/bar_chart: Gráfico", ":material/table: Tabla"])
    with tab_c5:
        st.plotly_chart(chart_top_artists(df_top), use_container_width=True)
    with tab_t5:
        display_cols_p5 = [
            c for c in ["artist_image_url", "artist", "liked_count", "top_rank"]
            if c in df_top.columns
        ]
        col_config_p5 = {
            "artist": st.column_config.TextColumn("Artista"),
            "liked_count": st.column_config.NumberColumn("Canciones guardadas"),
            "top_rank": st.column_config.NumberColumn("Ranking Top"),
        }
        if "artist_image_url" in display_cols_p5:
            col_config_p5["artist_image_url"] = st.column_config.ImageColumn("Foto", width=60)
        st.dataframe(
            df_top[display_cols_p5],
            hide_index=True,
            use_container_width=True,
            column_config=col_config_p5,
        )
else:
    st.info("Sin datos de artistas.", icon=":material/info:")

st.space("small")

# ---------------------------------------------------------------------------
# P6 — Mis Top Tracks
# ---------------------------------------------------------------------------

st.subheader(":material/music_note: P6 · Mis top tracks")

top_tracks_df = load_my_top_tracks(time_range=time_range)

if top_tracks_df is not None and not top_tracks_df.empty:
    from src.components.playlist_player import render_playlist
    from src.spotify_auth import get_access_token

    _token = get_access_token()
    render_playlist(
        top_tracks_df,
        mode="sdk" if _token else "embed",
        title=f"Top Tracks — {time_label}",
        key=f"demo_top_tracks_{time_range}",
        token=_token,
    )
else:
    st.info("Sin datos de top tracks.", icon=":material/info:")
