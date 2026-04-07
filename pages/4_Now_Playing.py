"""Now Playing — player controls, queue and recently played analysis."""

import pandas as pd
import streamlit as st

from src.spotify_client import (
    get_spotify_client,
    fetch_currently_playing,
    fetch_recently_played,
    fetch_queue,
    fetch_devices,
    player_play,
    player_pause,
    player_next,
    player_previous,
)
from src.theme import inject_premium_css, SPOTIFY_GREEN, base_layout
from src.sidebar import render_sidebar_player

import plotly.graph_objects as go

st.set_page_config(
    page_title="Now Playing — SpotifyAnalytics",
    page_icon=":material/headphones:",
    layout="wide",
)
inject_premium_css()

st.title(":material/headphones: Now Playing")

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

sp = get_spotify_client()

if sp is not None:
    render_sidebar_player(sp)

if sp is None:
    st.info(
        ":material/lock: Conecta tu cuenta de Spotify desde "
        "**Mi Perfil** para usar el reproductor.",
        icon=":material/lock:",
    )
    st.stop()

# ---------------------------------------------------------------------------
# Currently Playing — Hero section
# ---------------------------------------------------------------------------

currently = fetch_currently_playing(sp)

if currently:
    with st.container(border=True):
        col_info, col_embed = st.columns([1, 2])
        with col_info:
            if currently.get("is_playing"):
                st.caption(":material/play_circle: REPRODUCIENDO")
            else:
                st.caption(":material/pause_circle: EN PAUSA")

            st.markdown(f"### {currently['track_name']}")
            st.caption(f"{currently['artist']} — {currently['album']}")

            # Progress
            if currently.get("duration_ms") and currently.get("progress_ms"):
                progress = currently["progress_ms"] / currently["duration_ms"]
                elapsed = currently["progress_ms"] // 1000
                total = currently["duration_ms"] // 1000
                st.progress(progress)
                st.caption(
                    f"{elapsed // 60}:{elapsed % 60:02d} / "
                    f"{total // 60}:{total % 60:02d}"
                )

        with col_embed:
            track_id = currently.get("track_id", "")
            if track_id:
                import streamlit.components.v1 as components
                embed_html = (
                    f'<iframe src="https://open.spotify.com/embed/track/{track_id}'
                    f'?theme=0" width="100%" height="152" frameBorder="0" '
                    f'allow="autoplay; clipboard-write; encrypted-media; '
                    f'fullscreen; picture-in-picture" loading="lazy" '
                    f'style="border-radius:12px"></iframe>'
                )
                components.html(embed_html, height=160)

    # Player controls
    st.space("small")
    col_prev, col_play, col_next, col_device = st.columns([1, 1, 1, 3])
    with col_prev:
        if st.button(":material/skip_previous: Anterior", use_container_width=True):
            player_previous(sp)
            st.rerun()
    with col_play:
        if currently.get("is_playing"):
            if st.button(":material/pause: Pausar", use_container_width=True):
                player_pause(sp)
                st.rerun()
        else:
            if st.button(":material/play_arrow: Play", use_container_width=True, type="primary"):
                player_play(sp)
                st.rerun()
    with col_next:
        if st.button(":material/skip_next: Siguiente", use_container_width=True):
            player_next(sp)
            st.rerun()
    with col_device:
        devices = fetch_devices(sp)
        if devices:
            active = [d for d in devices if d["is_active"]]
            device_name = active[0]["name"] if active else "Sin dispositivo"
            st.caption(f":material/devices: {device_name}")
        else:
            st.caption(":material/warning: No hay dispositivos activos. Abre Spotify en algún dispositivo.")

else:
    with st.container(border=True):
        st.markdown("### :material/music_off: Nada reproduciéndose")
        st.caption(
            "Abre Spotify en tu ordenador o móvil y reproduce algo. "
            "Luego recarga esta página."
        )
        devices = fetch_devices(sp)
        if devices:
            st.caption(
                f":material/devices: Dispositivos detectados: "
                f"{', '.join(d['name'] for d in devices)}"
            )
        if st.button(":material/refresh: Recargar", type="primary"):
            st.rerun()

# ---------------------------------------------------------------------------
# Queue
# ---------------------------------------------------------------------------

st.space("medium")
st.subheader(":material/queue_music: Cola de reproducción")

queue = fetch_queue(sp)

if queue:
    queue_data = []
    for i, item in enumerate(queue, start=1):
        queue_data.append({
            "Pos": i,
            "Cover": item.get("album_cover_url", ""),
            "Track": item.get("track_name", ""),
            "Artista": item.get("artist", ""),
        })

    queue_df = pd.DataFrame(queue_data)

    col_config = {
        "Pos": st.column_config.NumberColumn("Pos", width=50),
        "Track": st.column_config.TextColumn("Track"),
        "Artista": st.column_config.TextColumn("Artista"),
    }
    if any(queue_df["Cover"].astype(bool)):
        col_config["Cover"] = st.column_config.ImageColumn("Cover", width=50)

    st.dataframe(
        queue_df,
        use_container_width=True,
        hide_index=True,
        column_config=col_config,
    )
else:
    st.caption(":material/info: La cola está vacía o no hay reproducción activa.")

# ---------------------------------------------------------------------------
# Recently Played — Analysis
# ---------------------------------------------------------------------------

st.space("medium")
st.subheader(":material/history: Escuchas recientes")

recent_df = fetch_recently_played(sp)

if recent_df.empty:
    st.caption(":material/info: No se pudieron obtener las escuchas recientes.")
    st.stop()

# Display recent tracks
tracks_display = recent_df[
    [c for c in ["track_name", "artist", "album", "album_cover_url", "played_at"]
     if c in recent_df.columns]
].copy()

if "played_at" in tracks_display.columns:
    tracks_display["played_at"] = tracks_display["played_at"].dt.strftime("%d/%m %H:%M")

col_config_recent = {
    "track_name": st.column_config.TextColumn("Track"),
    "artist": st.column_config.TextColumn("Artista"),
    "album": st.column_config.TextColumn("Álbum"),
    "played_at": st.column_config.TextColumn("Reproducido"),
}
if "album_cover_url" in tracks_display.columns:
    col_config_recent["album_cover_url"] = st.column_config.ImageColumn("Cover", width=50)

st.dataframe(
    tracks_display,
    use_container_width=True,
    hide_index=True,
    column_config=col_config_recent,
)

# ---------------------------------------------------------------------------
# Recently Played — Listening patterns
# ---------------------------------------------------------------------------

if "played_at" in recent_df.columns and not recent_df["played_at"].isna().all():
    st.space("small")

    col_hour, col_genre = st.columns(2)

    with col_hour:
        st.markdown("**:material/schedule: ¿Cuándo escuchas más?**")
        recent_df["hour"] = recent_df["played_at"].dt.hour
        hour_counts = recent_df.groupby("hour").size().reindex(
            range(24), fill_value=0
        ).reset_index()
        hour_counts.columns = ["hour", "count"]

        fig_hour = go.Figure(go.Bar(
            x=hour_counts["hour"],
            y=hour_counts["count"],
            marker=dict(color=SPOTIFY_GREEN, cornerradius=4),
            hovertemplate="Hora: %{x}:00<br>Escuchas: %{y}<extra></extra>",
        ))
        fig_hour.update_layout(
            xaxis_title="Hora del día",
            yaxis_title="Escuchas",
            xaxis=dict(dtick=2),
            **base_layout(),
        )
        st.plotly_chart(fig_hour, use_container_width=True)

    with col_genre:
        st.markdown("**:material/music_note: Artistas más escuchados recientemente**")
        top_recent = (
            recent_df["artist"]
            .value_counts()
            .head(10)
            .reset_index()
        )
        top_recent.columns = ["artist", "count"]

        fig_artists = go.Figure(go.Bar(
            x=top_recent["count"],
            y=top_recent["artist"],
            orientation="h",
            marker=dict(color=SPOTIFY_GREEN, cornerradius=4),
            hovertemplate="<b>%{y}</b><br>Escuchas: %{x}<extra></extra>",
        ))
        fig_artists.update_layout(
            xaxis_title="Escuchas",
            yaxis=dict(autorange="reversed"),
            **base_layout(),
        )
        st.plotly_chart(fig_artists, use_container_width=True)
