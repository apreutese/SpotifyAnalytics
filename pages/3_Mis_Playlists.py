"""Mis Playlists — analyse and compare your own Spotify playlists."""

import streamlit as st

from src.data_loader import get_global_dataframe
from src.spotify_client import (
    get_spotify_client,
    fetch_user_playlists,
    fetch_playlist_tracks,
    enrich_liked_with_hf,
)
from src.kpis_playlists import (
    kpi_playlist_genres,
    kpi_playlist_audio_dna,
    kpi_playlist_timeline,
    kpi_playlist_summary,
)
from src.charts_playlists import (
    chart_playlist_genres,
    chart_playlist_audio_dna,
    chart_compare_playlists,
    chart_playlist_timeline,
)
from src.theme import inject_premium_css
from src.sidebar import render_sidebar_player

st.set_page_config(
    page_title="Mis Playlists — SpotifyAnalytics",
    page_icon=":material/queue_music:",
    layout="wide",
)
inject_premium_css()

st.title(":material/queue_music: Mis Playlists")

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

sp = get_spotify_client()

if sp is not None:
    render_sidebar_player(sp)

if sp is None:
    st.info(
        ":material/lock: Conecta tu cuenta de Spotify desde "
        "**Mi Perfil** para analizar tus playlists.",
        icon=":material/lock:",
    )
    st.stop()

# ---------------------------------------------------------------------------
# Load global data for enrichment
# ---------------------------------------------------------------------------

hf_df, _ = get_global_dataframe()

# ---------------------------------------------------------------------------
# Fetch playlists
# ---------------------------------------------------------------------------

playlists_df = fetch_user_playlists(sp)

if playlists_df.empty:
    st.caption(":material/info: No se encontraron playlists en tu cuenta.")
    st.stop()

# Filter to only user-owned playlists (we can only get items for those)
try:
    from src.spotify_client import fetch_user_profile
    user_profile = fetch_user_profile(sp)
    user_id = user_profile.get("id", "")
    own_playlists = playlists_df[playlists_df["owner_id"] == user_id].copy()
    if own_playlists.empty:
        own_playlists = playlists_df.copy()
except Exception:
    own_playlists = playlists_df.copy()

# ---------------------------------------------------------------------------
# Mode selector: Individual analysis vs Comparator
# ---------------------------------------------------------------------------

mode = st.radio(
    "Modo",
    [":material/search: Análisis individual", ":material/compare_arrows: Comparar playlists"],
    horizontal=True,
    label_visibility="collapsed",
)

st.space("small")

# ---------------------------------------------------------------------------
# Helper: analyse a single playlist
# ---------------------------------------------------------------------------


def _analyse_playlist(playlist_id: str, playlist_name: str) -> dict | None:
    """Fetch, enrich and compute KPIs for a playlist.

    Returns:
        Dict with keys: tracks_df, summary, genres, dna, timeline.
        None if the playlist has no tracks.
    """
    cache_key = f"pl_tracks_{playlist_id}"
    if cache_key in st.session_state and not st.session_state[cache_key].empty:
        tracks_df = st.session_state[cache_key]
    else:
        tracks_df = fetch_playlist_tracks(sp, playlist_id)
        if not tracks_df.empty:
            st.session_state[cache_key] = tracks_df

    if tracks_df.empty:
        return None

    enriched = enrich_liked_with_hf(tracks_df, hf_df)

    return {
        "tracks_df": enriched,
        "summary": kpi_playlist_summary(enriched),
        "genres": kpi_playlist_genres(enriched),
        "dna": kpi_playlist_audio_dna(enriched),
        "timeline": kpi_playlist_timeline(enriched),
        "name": playlist_name,
    }


# ---------------------------------------------------------------------------
# Individual analysis
# ---------------------------------------------------------------------------

if "Análisis individual" in mode:
    playlist_options = {
        row["playlist_id"]: f"{row['name']}  ({row['total_tracks']} tracks)"
        for _, row in own_playlists.iterrows()
    }
    selected_id = st.selectbox(
        "Selecciona una playlist",
        options=list(playlist_options.keys()),
        format_func=lambda x: playlist_options[x],
    )

    if selected_id:
        selected_name = own_playlists.loc[
            own_playlists["playlist_id"] == selected_id, "name"
        ].iloc[0]
        analysis = _analyse_playlist(selected_id, selected_name)

        if analysis is None:
            st.caption(":material/info: Esta playlist no tiene tracks.")
            st.stop()

        # Summary metrics
        s = analysis["summary"]
        with st.container(horizontal=True):
            st.metric("Tracks", f"{s['total_tracks']:,}", border=True)
            st.metric("Duración", f"{s['total_duration_min']:.0f} min", border=True)
            st.metric("Artistas", f"{s['unique_artists']:,}", border=True)
            st.metric("Géneros", f"{s['unique_genres']:,}", border=True)

        st.space("small")

        # KPIs
        col_left, col_right = st.columns(2)

        with col_left:
            # PL1 — Genres
            if not analysis["genres"].empty:
                tab_chart, tab_table = st.tabs(
                    [":material/donut_small: Gráfico", ":material/table: Tabla"]
                )
                with tab_chart:
                    st.plotly_chart(
                        chart_playlist_genres(analysis["genres"]),
                        use_container_width=True,
                    )
                with tab_table:
                    st.dataframe(analysis["genres"], use_container_width=True, hide_index=True)
            else:
                st.caption(":material/info: No hay datos de género para esta playlist.")

        with col_right:
            # PL2 — Audio DNA
            if not analysis["dna"].empty:
                tab_chart, tab_table = st.tabs(
                    [":material/radar: Radar", ":material/table: Tabla"]
                )
                with tab_chart:
                    st.plotly_chart(
                        chart_playlist_audio_dna(analysis["dna"], selected_name),
                        use_container_width=True,
                    )
                with tab_table:
                    st.dataframe(analysis["dna"], use_container_width=True, hide_index=True)
            else:
                st.caption(
                    ":material/info: No hay suficientes coincidencias con el "
                    "dataset global para generar el radar."
                )

        # PL3 — Timeline
        if not analysis["timeline"].empty:
            tab_chart, tab_table = st.tabs(
                [":material/timeline: Timeline", ":material/table: Tabla"]
            )
            with tab_chart:
                st.plotly_chart(
                    chart_playlist_timeline(analysis["timeline"]),
                    use_container_width=True,
                )
            with tab_table:
                st.dataframe(analysis["timeline"], use_container_width=True, hide_index=True)

        # Playlist embed player
        st.space("small")
        st.subheader(":material/headphones: Reproductor")

        import streamlit.components.v1 as components
        playlist_embed = (
            f'<iframe src="https://open.spotify.com/embed/playlist/{selected_id}'
            f'?theme=0" width="100%" height="352" frameBorder="0" '
            f'allow="autoplay; clipboard-write; encrypted-media; '
            f'fullscreen; picture-in-picture" loading="lazy" '
            f'style="border-radius:12px"></iframe>'
        )
        components.html(playlist_embed, height=362)

        # Track list
        st.space("small")
        st.subheader(":material/library_music: Tracks")

        tracks_display = analysis["tracks_df"][
            [c for c in ["track_name", "artist", "album", "album_cover_url"]
             if c in analysis["tracks_df"].columns]
        ].copy()

        if "album_cover_url" in tracks_display.columns:
            st.dataframe(
                tracks_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "album_cover_url": st.column_config.ImageColumn("Cover", width=60),
                    "track_name": st.column_config.TextColumn("Track"),
                    "artist": st.column_config.TextColumn("Artista"),
                    "album": st.column_config.TextColumn("Álbum"),
                },
            )
        else:
            st.dataframe(tracks_display, use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Comparator
# ---------------------------------------------------------------------------

elif "Comparar" in mode:
    st.caption("Selecciona dos playlists propias para comparar su ADN musical.")

    col_a, col_b = st.columns(2)

    playlist_names = {
        row["playlist_id"]: row["name"]
        for _, row in own_playlists.iterrows()
    }
    playlist_ids = list(playlist_names.keys())

    with col_a:
        id_a = st.selectbox(
            "Playlist A",
            options=playlist_ids,
            format_func=lambda x: playlist_names[x],
            key="cmp_a",
        )
    with col_b:
        id_b = st.selectbox(
            "Playlist B",
            options=playlist_ids,
            format_func=lambda x: playlist_names[x],
            key="cmp_b",
            index=min(1, len(playlist_ids) - 1),
        )

    if id_a and id_b:
        if id_a == id_b:
            st.caption(":material/warning: Selecciona dos playlists diferentes.")
            st.stop()

        analysis_a = _analyse_playlist(id_a, playlist_names[id_a])
        analysis_b = _analyse_playlist(id_b, playlist_names[id_b])

        if analysis_a is None or analysis_b is None:
            st.caption(":material/info: Una de las playlists no tiene tracks.")
            st.stop()

        # Summary comparison
        st.space("small")
        sa, sb = analysis_a["summary"], analysis_b["summary"]
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(f"**{playlist_names[id_a]}**")
            with st.container(horizontal=True):
                st.metric("Tracks", f"{sa['total_tracks']:,}", border=True)
                st.metric("Artistas", f"{sa['unique_artists']:,}", border=True)
                st.metric("Géneros", f"{sa['unique_genres']:,}", border=True)
        with col_m2:
            st.markdown(f"**{playlist_names[id_b]}**")
            with st.container(horizontal=True):
                st.metric("Tracks", f"{sb['total_tracks']:,}", border=True)
                st.metric("Artistas", f"{sb['unique_artists']:,}", border=True)
                st.metric("Géneros", f"{sb['unique_genres']:,}", border=True)

        # Playlist embeds side by side
        import streamlit.components.v1 as components

        st.space("small")
        emb_a, emb_b = st.columns(2)
        with emb_a:
            components.html(
                f'<iframe src="https://open.spotify.com/embed/playlist/{id_a}'
                f'?theme=0" width="100%" height="352" frameBorder="0" '
                f'allow="autoplay; clipboard-write; encrypted-media; '
                f'fullscreen; picture-in-picture" loading="lazy" '
                f'style="border-radius:12px"></iframe>',
                height=362,
            )
        with emb_b:
            components.html(
                f'<iframe src="https://open.spotify.com/embed/playlist/{id_b}'
                f'?theme=0" width="100%" height="352" frameBorder="0" '
                f'allow="autoplay; clipboard-write; encrypted-media; '
                f'fullscreen; picture-in-picture" loading="lazy" '
                f'style="border-radius:12px"></iframe>',
                height=362,
            )

        # Radar comparison
        st.space("small")
        dna_a, dna_b = analysis_a["dna"], analysis_b["dna"]
        if not dna_a.empty and not dna_b.empty:
            st.plotly_chart(
                chart_compare_playlists(
                    dna_a, dna_b,
                    playlist_names[id_a], playlist_names[id_b],
                ),
                use_container_width=True,
            )
        else:
            st.caption(
                ":material/info: No hay suficientes datos de audio features "
                "para generar la comparación."
            )

        # Shared artists
        st.space("small")
        st.subheader(":material/group: Artistas compartidos")

        df_a = analysis_a["tracks_df"]
        df_b = analysis_b["tracks_df"]
        artists_a = set(df_a["artist"].dropna().unique())
        artists_b = set(df_b["artist"].dropna().unique())
        shared = artists_a & artists_b

        if shared:
            st.caption(f"{len(shared)} artistas en común")

            # Build artist info: image, track counts per playlist
            artist_info: list[dict] = []
            for artist_name in sorted(shared):
                rows_a = df_a[df_a["artist"] == artist_name]
                rows_b = df_b[df_b["artist"] == artist_name]
                # Use first album cover as representative image
                img = None
                if "album_cover_url" in df_a.columns:
                    imgs = rows_a["album_cover_url"].dropna()
                    if not imgs.empty:
                        img = imgs.iloc[0]
                if img is None and "album_cover_url" in df_b.columns:
                    imgs = rows_b["album_cover_url"].dropna()
                    if not imgs.empty:
                        img = imgs.iloc[0]
                artist_info.append({
                    "name": artist_name,
                    "img": img,
                    "count_a": len(rows_a),
                    "count_b": len(rows_b),
                })

            # Render as cards in a 3-column grid
            for row_start in range(0, len(artist_info), 3):
                cols = st.columns(3)
                for col_idx, col in enumerate(cols):
                    idx = row_start + col_idx
                    if idx >= len(artist_info):
                        break
                    info = artist_info[idx]
                    with col:
                        with st.container(border=True):
                            c_img, c_info = st.columns([1, 3])
                            with c_img:
                                if info["img"]:
                                    st.image(info["img"], width=56)
                                else:
                                    st.markdown(":material/person:")
                            with c_info:
                                st.markdown(f"**{info['name']}**")
                                st.caption(
                                    f"{info['count_a']} tracks en A · "
                                    f"{info['count_b']} tracks en B"
                                )
        else:
            st.caption("No hay artistas compartidos entre estas playlists.")
