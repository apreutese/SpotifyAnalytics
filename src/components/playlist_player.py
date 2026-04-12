"""Playlist player component: Spotify-like track list + embed player.

Two modes:
- **embed** (CSV pages): Spotify oEmbed iframe, no OAuth needed.
- **sdk** (OAuth pages): Web Playback SDK — full playback, requires Premium.

Usage:
    from src.components.playlist_player import render_playlist
    render_playlist(tracks_df, mode="embed", key="global_top100")
    render_playlist(tracks_df, mode="sdk", key="now_pl", token="BQ...")
"""

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ---------------------------------------------------------------------------
# Premium playlist CSS
# ---------------------------------------------------------------------------

_PLAYLIST_CSS: str = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@500;700&family=DM+Sans:wght@400;500;600&display=swap');

.pl-container {
    background: #0d0d0d;
    border-radius: 12px;
    padding: 0;
    font-family: 'DM Sans', sans-serif;
    overflow: hidden;
}

.pl-header {
    padding: 20px 24px 12px;
    display: flex;
    align-items: center;
    gap: 12px;
}

.pl-header-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.25rem;
    font-weight: 700;
    color: #f0f0f0;
    margin: 0;
}

.pl-header-count {
    font-size: 0.8rem;
    color: #888;
    margin: 0;
}

.pl-list {
    max-height: 420px;
    overflow-y: auto;
    scrollbar-width: thin;
    scrollbar-color: #333 transparent;
}

.pl-track {
    display: flex;
    align-items: center;
    padding: 8px 24px;
    gap: 14px;
    cursor: pointer;
    transition: background 0.2s ease;
    border-left: 3px solid transparent;
    position: relative;
}

.pl-track:hover {
    background: rgba(212, 168, 83, 0.08);
}

.pl-track.active {
    background: rgba(212, 168, 83, 0.12);
    border-left-color: #D4A853;
}

.pl-track.active::before {
    content: '';
    position: absolute;
    left: -3px;
    top: 0;
    bottom: 0;
    width: 3px;
    background: #D4A853;
    box-shadow: 0 0 8px rgba(212, 168, 83, 0.4);
}

.pl-num {
    width: 28px;
    font-size: 0.85rem;
    color: #888;
    text-align: center;
    flex-shrink: 0;
}

.pl-track.active .pl-num {
    color: #D4A853;
    font-weight: 600;
}

.pl-art {
    width: 44px;
    height: 44px;
    border-radius: 4px;
    object-fit: cover;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.4);
}

.pl-info {
    flex: 1;
    min-width: 0;
    overflow: hidden;
}

.pl-name {
    font-size: 0.9rem;
    font-weight: 500;
    color: #f0f0f0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin: 0;
}

.pl-track.active .pl-name {
    font-family: 'Playfair Display', serif;
    color: #D4A853;
    font-weight: 700;
}

.pl-artist {
    font-size: 0.78rem;
    color: #999;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin: 0;
}

.pl-dur {
    font-size: 0.78rem;
    color: #777;
    flex-shrink: 0;
    font-variant-numeric: tabular-nums;
}

.pl-embed-wrap {
    padding: 8px 16px 16px;
}
</style>
"""

# Default placeholder artwork
_NO_ART: str = (
    "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' "
    "width='44' height='44' viewBox='0 0 44 44'%3E"
    "%3Crect width='44' height='44' fill='%23222'/%3E"
    "%3Ctext x='50%25' y='54%25' dominant-baseline='middle' "
    "text-anchor='middle' fill='%23555' font-size='18'%3E"
    "%E2%99%AA%3C/text%3E%3C/svg%3E"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_duration(ms: int | float | None) -> str:
    """Convert milliseconds to m:ss string."""
    if ms is None or pd.isna(ms):
        return "--:--"
    total_sec = int(ms) // 1000
    return f"{total_sec // 60}:{total_sec % 60:02d}"


def _build_track_html(
    idx: int,
    track_id: str,
    name: str,
    artist: str,
    art_url: str | None,
    duration_ms: int | float | None,
    is_active: bool,
    *,
    sdk_mode: bool = False,
) -> str:
    """Build HTML for a single track row."""
    cls = "pl-track active" if is_active else "pl-track"
    art = art_url if art_url and isinstance(art_url, str) and art_url.startswith("http") else _NO_ART
    dur = _format_duration(duration_ms)
    # Sanitize text
    name_safe = str(name).replace("<", "&lt;").replace(">", "&gt;").replace("'", "&#39;")
    artist_safe = str(artist).replace("<", "&lt;").replace(">", "&gt;").replace("'", "&#39;")

    if sdk_mode:
        onclick = f"playTrack('spotify:track:{track_id}')"
    else:
        onclick = ""

    return (
        f'<div class="{cls}" data-id="{track_id}" '
        f'onclick="{onclick}">'
        f'  <span class="pl-num">{idx}</span>'
        f'  <img class="pl-art" src="{art}" alt="">'
        f'  <div class="pl-info">'
        f'    <p class="pl-name">{name_safe}</p>'
        f'    <p class="pl-artist">{artist_safe}</p>'
        f'  </div>'
        f'  <span class="pl-dur">{dur}</span>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# SDK player builder
# ---------------------------------------------------------------------------


def _build_sdk_player_html(token: str, track_uris: list[str], selected_uri: str) -> str:
    """Build HTML/JS for the Spotify Web Playback SDK player.

    Args:
        token: Spotify access token with `streaming` scope.
        track_uris: List of spotify:track:ID URIs.
        selected_uri: The URI to start playing.

    Returns:
        Full HTML string with embedded SDK player (no track list).
    """
    uris_js = ", ".join(f'"{u}"' for u in track_uris)
    return f"""
    <div id="sdk-root">
      <div class="sdk-status" id="sdk-status">Conectando al reproductor…</div>
    </div>

    <script src="https://sdk.scdn.co/spotify-player.js"></script>
    <script>
      const TOKEN = "{token}";
      const TRACK_URIS = [{uris_js}];
      let SELECTED_URI = "{selected_uri}";
      let deviceId = null;
      let player = null;

      function formatMs(ms) {{
        const s = Math.floor(ms / 1000);
        return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0');
      }}

      const SVG_PREV = '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6V6zm3.5 6 8.5 6V6l-8.5 6z"/></svg>';
      const SVG_PLAY = '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7L8 5z"/></svg>';
      const SVG_PAUSE = '<svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>';
      const SVG_NEXT = '<svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>';

      function renderPlayer(state) {{
        const track = state.track_window.current_track;
        const art = track.album.images[0]?.url || '';
        const root = document.getElementById('sdk-root');
        root.innerHTML = `
          <div class="sdk-player">
            ${{art ? `<img src="${{art}}" width="56" height="56" style="border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,.4)">` : ''}}
            <div class="sdk-info">
              <div class="sdk-track">${{track.name}}</div>
              <div class="sdk-artist">${{track.artists.map(a => a.name).join(', ')}}</div>
            </div>
            <div class="sdk-controls">
              <button class="sdk-btn" onclick="player.previousTrack()">${{SVG_PREV}}</button>
              <button class="sdk-btn play" id="sdk-toggle" onclick="player.togglePlay()">
                ${{state.paused ? SVG_PLAY : SVG_PAUSE}}
              </button>
              <button class="sdk-btn" onclick="player.nextTrack()">${{SVG_NEXT}}</button>
            </div>
          </div>
          <div class="sdk-progress" id="sdk-progress" onclick="seekTo(event)">
            <div class="sdk-progress-bar" id="sdk-bar" style="width:${{(state.position/state.duration*100).toFixed(1)}}%"></div>
          </div>
          <div class="sdk-time">
            <span id="sdk-elapsed">${{formatMs(state.position)}}</span>
            <span>${{formatMs(state.duration)}}</span>
          </div>
        `;
      }}

      function seekTo(e) {{
        const rect = e.currentTarget.getBoundingClientRect();
        const pct = (e.clientX - rect.left) / rect.width;
        player.getCurrentState().then(s => {{
          if (s) player.seek(Math.floor(pct * s.duration));
        }});
      }}

      // Progress updater
      setInterval(() => {{
        if (!player) return;
        player.getCurrentState().then(s => {{
          if (!s || s.paused) return;
          const bar = document.getElementById('sdk-bar');
          const elapsed = document.getElementById('sdk-elapsed');
          if (bar) bar.style.width = (s.position / s.duration * 100).toFixed(1) + '%';
          if (elapsed) elapsed.textContent = formatMs(s.position);
        }});
      }}, 500);

      window.onSpotifyWebPlaybackSDKReady = () => {{
        player = new Spotify.Player({{
          name: 'SpotifyAnalytics Player',
          getOAuthToken: cb => cb(TOKEN),
          volume: 0.5
        }});

        player.addListener('ready', ({{ device_id }}) => {{
          deviceId = device_id;
          document.getElementById('sdk-status').textContent = 'Reproductor listo';
          playTrack(SELECTED_URI);
        }});

        player.addListener('not_ready', () => {{
          document.getElementById('sdk-status').textContent = 'Dispositivo desconectado';
        }});

        player.addListener('player_state_changed', state => {{
          if (state) {{
            renderPlayer(state);
            updateHighlight(state.track_window.current_track.uri);
          }}
        }});

        player.addListener('initialization_error', ({{ message }}) => {{
          document.getElementById('sdk-status').innerHTML =
            '<span style="color:#e74c3c">Error: ' + message + '</span>';
        }});

        player.addListener('authentication_error', ({{ message }}) => {{
          document.getElementById('sdk-status').innerHTML =
            '<span style="color:#e74c3c">Auth error — ¿tienes Premium? ' + message + '</span>';
        }});

        player.connect();
      }};

      function updateHighlight(uri) {{
        const trackId = uri ? uri.replace('spotify:track:', '') : '';
        document.querySelectorAll('.pl-track').forEach(el => {{
          el.classList.toggle('active', el.getAttribute('data-id') === trackId);
        }});
      }}

      function playTrack(uri) {{
        if (!deviceId) return;
        const idx = TRACK_URIS.indexOf(uri);
        updateHighlight(uri);
        fetch('https://api.spotify.com/v1/me/player/play?device_id=' + deviceId, {{
          method: 'PUT',
          headers: {{ 'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ uris: TRACK_URIS, offset: {{ position: Math.max(idx, 0) }} }})
        }});
      }}
    </script>
    """


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


_SDK_CSS: str = """
<style>
  .sdk-player {
    background: #0d0d0d;
    border-radius: 12px;
    padding: 16px 20px;
    display: flex;
    align-items: center;
    gap: 16px;
  }
  .sdk-info { flex: 1; min-width: 0; }
  .sdk-track { color: #f0f0f0; font-size: 0.95rem; font-weight: 600;
               white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .sdk-artist { color: #999; font-size: 0.8rem; margin-top: 2px;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .sdk-controls { display: flex; align-items: center; gap: 4px; }
  .sdk-btn {
    background: none; border: none; color: #f0f0f0;
    cursor: pointer; padding: 8px; border-radius: 50%;
    transition: color 0.2s, background 0.2s;
    display: inline-flex; align-items: center; justify-content: center;
    width: 40px; height: 40px;
  }
  .sdk-btn:hover { color: #D4A853; background: rgba(212,168,83,0.12); }
  .sdk-btn.play { color: #D4A853; width: 48px; height: 48px; }
  .sdk-progress {
    width: 100%; height: 4px; background: #333; border-radius: 2px;
    margin-top: 12px; overflow: hidden; cursor: pointer;
  }
  .sdk-progress-bar {
    height: 100%; background: #D4A853; border-radius: 2px;
    transition: width 0.3s linear;
  }
  .sdk-time { display: flex; justify-content: space-between;
              color: #777; font-size: 0.7rem; margin-top: 4px;
              font-variant-numeric: tabular-nums; }
  .sdk-status { color: #D4A853; font-size: 0.75rem; text-align: center;
                padding: 24px; }
</style>
"""


def render_playlist(
    tracks_df: pd.DataFrame,
    *,
    mode: str = "embed",
    title: str = "Playlist",
    key: str = "playlist",
    max_tracks: int = 100,
    embed_height: int = 80,
    token: str | None = None,
) -> str | None:
    """Render a Spotify-like playlist with an embed or SDK player.

    Args:
        tracks_df: DataFrame with at least [track_id, track_name, artist].
            Optional: album_cover_url, duration_ms.
        mode: 'embed' (CSV pages, preview) or 'sdk' (Premium, full playback).
        title: Display title above the list.
        key: Unique Streamlit key prefix for session state.
        max_tracks: Max tracks to render in the list.
        embed_height: Height of the Spotify embed iframe in px.
        token: Spotify access token (required for mode='sdk').

    Returns:
        The currently selected track_id, or None if no tracks.
    """
    if tracks_df is None or tracks_df.empty:
        st.caption(":material/info: No hay tracks para mostrar.")
        return None

    required_cols = {"track_id", "track_name", "artist"}
    if not required_cols.issubset(tracks_df.columns):
        st.error(f"El DataFrame necesita columnas: {required_cols}")
        return None

    df = tracks_df.head(max_tracks).copy()

    # Session state for selected track
    state_key = f"pl_selected_{key}"
    if state_key not in st.session_state:
        st.session_state[state_key] = df.iloc[0]["track_id"]

    selected_id = st.session_state[state_key]
    use_sdk = mode == "sdk" and token and selected_id

    # --- SDK mode: unified HTML (list + player in one iframe) ---
    if use_sdk:
        track_rows = []
        for idx, (_, row) in enumerate(df.iterrows(), start=1):
            tid = row["track_id"]
            track_rows.append(_build_track_html(
                idx=idx,
                track_id=tid,
                name=row["track_name"],
                artist=row["artist"],
                art_url=row.get("album_cover_url"),
                duration_ms=row.get("duration_ms"),
                is_active=False,
                sdk_mode=True,
            ))

        list_html = "\n".join(track_rows)
        count = len(df)
        track_uris = [f"spotify:track:{tid}" for tid in df["track_id"].values]
        selected_uri = f"spotify:track:{selected_id}"
        sdk_player_js = _build_sdk_player_html(token, track_uris, selected_uri)

        full_html = f"""
        {_PLAYLIST_CSS}
        {_SDK_CSS}
        <div class="pl-container">
          <div class="pl-header">
            <div>
              <p class="pl-header-title">{title}</p>
              <p class="pl-header-count">{count} tracks</p>
            </div>
          </div>
          <div class="pl-list">
            {list_html}
          </div>
          <div class="pl-embed-wrap">
            {sdk_player_js}
          </div>
        </div>
        """
        total_height = min(count * 62 + 80, 520) + 200
        components.html(full_html, height=total_height, scrolling=True)
        return selected_id

    # --- Embed mode: selectbox + HTML list + embed iframe ---
    # Selectbox for track selection
    options = df["track_id"].tolist()
    labels = {
        row["track_id"]: f"{i}. {row['track_name']} — {row['artist']}"
        for i, (_, row) in enumerate(df.iterrows(), start=1)
    }
    default_idx = 0
    if selected_id in options:
        default_idx = options.index(selected_id)

    new_selected = st.selectbox(
        "Seleccionar track",
        options=options,
        index=default_idx,
        format_func=lambda x: labels.get(x, x),
        key=f"{key}_selectbox",
        label_visibility="collapsed",
    )
    if new_selected and str(new_selected) != str(selected_id):
        st.session_state[state_key] = new_selected
        selected_id = new_selected

    # Build HTML track list (read-only, no onclick)
    track_rows = []
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        tid = row["track_id"]
        is_active = str(tid) == str(selected_id)
        track_rows.append(_build_track_html(
            idx=idx,
            track_id=tid,
            name=row["track_name"],
            artist=row["artist"],
            art_url=row.get("album_cover_url"),
            duration_ms=row.get("duration_ms"),
            is_active=is_active,
        ))

    list_html = "\n".join(track_rows)
    count = len(df)

    full_html = f"""
    {_PLAYLIST_CSS}
    <div class="pl-container">
      <div class="pl-header">
        <div>
          <p class="pl-header-title">{title}</p>
          <p class="pl-header-count">{count} tracks</p>
        </div>
      </div>
      <div class="pl-list">
        {list_html}
      </div>
    </div>
    """

    list_height = min(count * 62 + 80, 520)
    components.html(full_html, height=list_height, scrolling=False)

    # Embed player
    if selected_id:
        embed_html = (
            f'<iframe src="https://open.spotify.com/embed/track/{selected_id}'
            f'?theme=0" width="100%" height="{embed_height}" frameBorder="0" '
            f'allow="autoplay; clipboard-write; encrypted-media; '
            f'fullscreen; picture-in-picture" loading="lazy" '
            f'style="border-radius:12px"></iframe>'
        )
        components.html(embed_html, height=embed_height + 10)

    return selected_id
