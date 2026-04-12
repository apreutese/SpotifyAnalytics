"""Mi Perfil — live personal stats via OAuth (requires Spotify connection)."""

import pandas as pd
import streamlit as st

from src.spotify_auth import get_spotify_client, get_access_token
from src.spotify_data import (
    fetch_liked_songs,
    fetch_top_artists,
    fetch_top_tracks,
    fetch_user_profile,
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
from src.sidebar import render_sidebar_player

st.set_page_config(
    page_title="Mi Perfil — SpotifyAnalytics",
    page_icon=":material/person:",
    layout="wide",
)
inject_premium_css()

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

sp = get_spotify_client()

if sp is not None:
    render_sidebar_player(sp)

if sp is None:
    st.info(
        ":material/lock: Conecta tu cuenta de Spotify para ver tu perfil en vivo.",
        icon=":material/lock:",
    )
    st.stop()

# ---------------------------------------------------------------------------
# User profile header
# ---------------------------------------------------------------------------

profile = fetch_user_profile(sp)

col_avatar, col_greeting = st.columns([1, 11])
with col_avatar:
    if profile.get("image_url"):
        st.image(profile["image_url"], width=72)
    else:
        st.markdown("### :material/person:")
with col_greeting:
    st.title(f":material/person: {profile['display_name']}")
    st.caption("Tu perfil musical en tiempo real")

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
        "Período Top Artists / Tracks",
        options=list(TIME_RANGE_MAP.keys()),
        index=1,
    )
    time_range: str = TIME_RANGE_MAP[time_label]

# ---------------------------------------------------------------------------
# Fetch data (cached in session_state for the current session)
# ---------------------------------------------------------------------------

if "mi_perfil_liked" not in st.session_state:
    st.session_state["mi_perfil_liked"] = fetch_liked_songs(sp)
liked_df = st.session_state["mi_perfil_liked"]

ta_key = f"mi_perfil_top_artists_{time_range}"
if ta_key not in st.session_state:
    st.session_state[ta_key] = fetch_top_artists(sp, time_range=time_range)
top_artists_df = st.session_state[ta_key]

tt_key = f"mi_perfil_top_tracks_{time_range}"
if tt_key not in st.session_state:
    st.session_state[tt_key] = fetch_top_tracks(sp, time_range=time_range)
top_tracks_df = st.session_state[tt_key]

if liked_df is None or liked_df.empty:
    st.warning("No se encontraron canciones guardadas.", icon=":material/warning:")
    st.stop()

if top_artists_df is None:
    top_artists_df = pd.DataFrame()

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
# P6 — Mis Top Tracks (with SDK player)
# ---------------------------------------------------------------------------

st.subheader(":material/music_note: P6 · Mis top tracks")

if top_tracks_df is not None and not top_tracks_df.empty:
    from src.components.playlist_player import render_playlist

    _token = get_access_token()
    render_playlist(
        top_tracks_df,
        mode="sdk" if _token else "embed",
        title=f"Top Tracks — {time_label}",
        key=f"mi_perfil_top_tracks_{time_range}",
        token=_token,
    )
else:
    st.info("Sin datos de top tracks.", icon=":material/info:")
