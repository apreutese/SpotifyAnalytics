"""Mis Playlists — analyse and compare your own Spotify playlists."""

import streamlit as st

from src.spotify_auth import get_spotify_client
from src.spotify_data import (
    fetch_user_playlists,
    fetch_playlist_tracks,
)
from src.kpis_playlists import (
    kpi_playlist_timeline,
    kpi_playlist_summary,
)
from src.kpis_personal import (
    kpi_release_decades,
    kpi_explicit_ratio,
    kpi_top_albums,
)
from src.charts_playlists import chart_playlist_timeline
from src.charts_personal import (
    chart_release_decades,
    chart_explicit_ratio,
    chart_top_albums,
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
# Fetch playlists
# ---------------------------------------------------------------------------

playlists_df = fetch_user_playlists(sp)

if playlists_df.empty:
    st.caption(":material/info: No se encontraron playlists en tu cuenta.")
    st.stop()

# Filter to only user-owned playlists (we can only get items for those)
try:
    from src.spotify_data import fetch_user_profile
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
# Helper: fetch and compute KPIs for a single playlist
# ---------------------------------------------------------------------------


def _analyse_playlist(playlist_id: str, playlist_name: str) -> dict | None:
    """Fetch and compute KPIs for a playlist.

    Returns:
        Dict with keys: tracks_df, summary, decades, explicit, albums, timeline.
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

    return {
        "tracks_df": tracks_df,
        "summary": kpi_playlist_summary(tracks_df),
        "decades": kpi_release_decades(tracks_df),
        "explicit": kpi_explicit_ratio(tracks_df),
        "albums": kpi_top_albums(tracks_df, top_n=10),
        "timeline": kpi_playlist_timeline(tracks_df),
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
            st.metric("Álbumes", f"{s['unique_albums']:,}", border=True)

        st.space("small")

        # KPIs — Decades + Explicit side by side
        col_left, col_right = st.columns(2)

        with col_left:
            if not analysis["decades"].empty:
                tab_c, tab_t = st.tabs(
                    [":material/calendar_month: Décadas", ":material/table: Tabla"]
                )
                with tab_c:
                    st.plotly_chart(
                        chart_release_decades(analysis["decades"]),
                        use_container_width=True,
                    )
                with tab_t:
                    st.dataframe(analysis["decades"], use_container_width=True, hide_index=True)
            else:
                st.caption(":material/info: Sin datos de fecha de lanzamiento.")

        with col_right:
            if not analysis["explicit"].empty:
                tab_c, tab_t = st.tabs(
                    [":material/explicit: Explicit", ":material/table: Tabla"]
                )
                with tab_c:
                    st.plotly_chart(
                        chart_explicit_ratio(analysis["explicit"]),
                        use_container_width=True,
                    )
                with tab_t:
                    st.dataframe(analysis["explicit"], use_container_width=True, hide_index=True)
            else:
                st.caption(":material/info: Sin datos de explicit.")

        # Top Albums
        if not analysis["albums"].empty:
            tab_c, tab_t = st.tabs(
                [":material/album: Álbumes", ":material/table: Tabla"]
            )
            with tab_c:
                st.plotly_chart(
                    chart_top_albums(analysis["albums"]),
                    use_container_width=True,
                )
            with tab_t:
                st.dataframe(analysis["albums"], use_container_width=True, hide_index=True)

        # Timeline
        if not analysis["timeline"].empty:
            tab_c, tab_t = st.tabs(
                [":material/timeline: Timeline", ":material/table: Tabla"]
            )
            with tab_c:
                st.plotly_chart(
                    chart_playlist_timeline(analysis["timeline"]),
                    use_container_width=True,
                )
            with tab_t:
                st.dataframe(analysis["timeline"], use_container_width=True, hide_index=True)

        # Playlist player (track list + SDK player for Premium)
        st.space("small")
        st.subheader(":material/headphones: Reproductor")

        from src.components.playlist_player import render_playlist
        from src.spotify_auth import get_access_token

        playlist_tracks = analysis["tracks_df"]
        _token = get_access_token()
        render_playlist(
            playlist_tracks,
            mode="sdk" if _token else "embed",
            title=selected_name,
            key=f"pl_{selected_id}",
            token=_token,
        )


# ---------------------------------------------------------------------------
# Comparator
# ---------------------------------------------------------------------------

elif "Comparar" in mode:
    st.caption("Selecciona dos playlists para comparar sus estadísticas.")

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
                st.metric("Álbumes", f"{sa['unique_albums']:,}", border=True)
        with col_m2:
            st.markdown(f"**{playlist_names[id_b]}**")
            with st.container(horizontal=True):
                st.metric("Tracks", f"{sb['total_tracks']:,}", border=True)
                st.metric("Artistas", f"{sb['unique_artists']:,}", border=True)
                st.metric("Álbumes", f"{sb['unique_albums']:,}", border=True)

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
