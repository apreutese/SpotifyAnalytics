"""Shared sidebar components: mini-player and user profile."""

import streamlit as st


def render_sidebar_player(sp=None) -> None:
    """Render a mini-player in the sidebar if the user is authenticated.

    Args:
        sp: Authenticated Spotify client. If None, attempts to get one
            silently (without showing login button).
    """
    from src.spotify_client import (
        fetch_currently_playing,
        fetch_user_profile,
        player_play,
        player_pause,
        player_next,
        player_previous,
    )

    if sp is None:
        return

    with st.sidebar:
        st.space("small")

        # User profile at top of sidebar — compact badge
        try:
            profile = fetch_user_profile(sp)
            name = profile.get("display_name", "Usuario")
            img_url = profile.get("image_url", "")
            if img_url:
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px">'
                    f'<img src="{img_url}" '
                    f'style="width:32px;height:32px;border-radius:50%;object-fit:cover">'
                    f'<span style="font-weight:600;font-size:0.9rem">{name}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption(f":material/person: **{name}**")
        except Exception:
            pass

        st.divider()

        # Mini player
        try:
            currently = fetch_currently_playing(sp)
        except Exception:
            currently = None

        if currently:
            st.caption(":material/headphones: NOW PLAYING")

            # Track info
            track_name = currently.get("track_name", "")
            artist = currently.get("artist", "")
            track_id = currently.get("track_id", "")

            if currently.get("album_cover_url"):
                st.image(currently["album_cover_url"], width=180)

            st.markdown(f"**{track_name}**")
            st.caption(artist)

            # Progress bar
            if currently.get("duration_ms") and currently.get("progress_ms"):
                progress = currently["progress_ms"] / currently["duration_ms"]
                st.progress(progress)

            # Controls
            col_p, col_pp, col_n = st.columns(3)
            with col_p:
                if st.button(":material/skip_previous:", key="sb_prev", use_container_width=True):
                    player_previous(sp)
                    st.rerun()
            with col_pp:
                if currently.get("is_playing"):
                    if st.button(":material/pause:", key="sb_pause", use_container_width=True):
                        player_pause(sp)
                        st.rerun()
                else:
                    if st.button(":material/play_arrow:", key="sb_play", use_container_width=True):
                        player_play(sp)
                        st.rerun()
            with col_n:
                if st.button(":material/skip_next:", key="sb_next", use_container_width=True):
                    player_next(sp)
                    st.rerun()

            # Link to Now Playing page
            st.page_link(
                "pages/4_Now_Playing.py",
                label="Abrir Now Playing",
                icon=":material/open_in_new:",
            )
        else:
            st.caption(":material/music_off: Sin reproducción activa")

        st.divider()
