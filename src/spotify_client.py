"""Spotify Web API client: OAuth + data fetching for personal page."""

import logging
import os
import time
from pathlib import Path

import pandas as pd
import spotipy
import streamlit as st
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCOPES: str = (
    "user-library-read user-top-read playlist-read-private "
    "user-read-playback-state user-modify-playback-state "
    "user-read-currently-playing user-read-recently-played "
    "user-read-private"
)
CACHE_PATH: Path = Path(__file__).resolve().parent.parent / ".spotify_cache"

CLIENT_ID: str = os.getenv("SPOTIFY_CLIENT_ID", "")
CLIENT_SECRET: str = os.getenv("SPOTIFY_CLIENT_SECRET", "")
REDIRECT_URI: str = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8501")


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------


def _get_oauth_manager() -> SpotifyOAuth:
    """Create a SpotifyOAuth manager."""
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPES,
        cache_path=str(CACHE_PATH),
        show_dialog=True,
    )


def get_spotify_client() -> spotipy.Spotify | None:
    """Authenticate via OAuth and return a Spotify client.

    Handles the OAuth flow within Streamlit using query params.

    Returns:
        Authenticated Spotify client or None if not authenticated.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        st.error(
            "Faltan credenciales de Spotify. "
            "Configura `SPOTIFY_CLIENT_ID` y `SPOTIFY_CLIENT_SECRET` en `.env`."
        )
        return None

    oauth = _get_oauth_manager()

    # Check for cached token
    token_info = oauth.get_cached_token()

    if token_info:
        return spotipy.Spotify(auth=token_info["access_token"])

    # Check for auth code in query params (redirect callback)
    query_params = st.query_params
    code = query_params.get("code")

    if code:
        try:
            token_info = oauth.get_access_token(code)
            st.query_params.clear()
            return spotipy.Spotify(auth=token_info["access_token"])
        except Exception as e:
            logger.error("OAuth token exchange failed: %s", e)
            st.error(f"Error de autenticación: {e}")
            return None

    # No token, no code → show login button
    auth_url = oauth.get_authorize_url()
    st.link_button("🔗 Conectar con Spotify", auth_url, type="primary")
    return None


def get_spotify_client_silent() -> spotipy.Spotify | None:
    """Try to get an authenticated Spotify client without showing UI.

    Unlike ``get_spotify_client()``, this will NOT render a login button
    if the user is not authenticated. Useful for pages that should
    gracefully degrade (e.g. Home).

    Returns:
        Authenticated Spotify client or None.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        return None

    oauth = _get_oauth_manager()
    token_info = oauth.get_cached_token()

    if token_info:
        return spotipy.Spotify(auth=token_info["access_token"])

    return None


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------


def fetch_liked_songs(sp: spotipy.Spotify, limit: int = 50) -> pd.DataFrame:
    """Fetch all liked songs from the user's library.

    Args:
        sp: Authenticated Spotify client.
        limit: Items per API page (max 50).

    Returns:
        DataFrame with liked song metadata.
    """
    tracks: list[dict] = []
    offset = 0

    with st.spinner("Obteniendo canciones guardadas…"):
        while True:
            results = sp.current_user_saved_tracks(limit=limit, offset=offset)
            items = results.get("items", [])
            if not items:
                break

            for item in items:
                track = item["track"]
                album = track.get("album", {})
                artists = track.get("artists", [])
                artist_name = artists[0]["name"] if artists else "Unknown"
                artist_id = artists[0]["id"] if artists else None

                album_images = album.get("images", [])

                tracks.append({
                    "track_id": track.get("id"),
                    "track_name": track.get("name"),
                    "artist": artist_name,
                    "artist_id": artist_id,
                    "album": album.get("name"),
                    "album_cover_url": album_images[0]["url"] if album_images else None,
                    "album_release_date": album.get("release_date"),
                    "duration_ms": track.get("duration_ms"),
                    "explicit": track.get("explicit"),
                    "added_at": item.get("added_at"),
                })

            offset += limit
            if offset >= results.get("total", 0):
                break

    df = pd.DataFrame(tracks)
    if not df.empty and "added_at" in df.columns:
        df["added_at"] = pd.to_datetime(df["added_at"])
    logger.info("Fetched %d liked songs", len(df))
    return df


def fetch_top_artists(
    sp: spotipy.Spotify,
    time_range: str = "medium_term",
    limit: int = 50,
) -> pd.DataFrame:
    """Fetch user's top artists.

    Args:
        sp: Authenticated Spotify client.
        time_range: One of 'short_term', 'medium_term', 'long_term'.
        limit: Number of artists (max 50).

    Returns:
        DataFrame with columns [artist_id, artist, genres, rank].
    """
    results = sp.current_user_top_artists(limit=limit, time_range=time_range)
    artists: list[dict] = []

    for i, item in enumerate(results.get("items", []), start=1):
        images = item.get("images", [])
        artists.append({
            "artist_id": item.get("id"),
            "artist": item.get("name"),
            "artist_image_url": images[0]["url"] if images else None,
            "genres": item.get("genres", []),
            "rank": i,
        })

    logger.info("Fetched %d top artists (%s)", len(artists), time_range)
    return pd.DataFrame(artists)


def fetch_artist_genres(
    sp: spotipy.Spotify,
    artist_ids: list[str],
) -> dict[str, list[str]]:
    """Fetch genres for a list of artist IDs.

    Tries the batch endpoint first (50 per request). If it returns 403
    (common in Spotify Development Mode), falls back to individual calls
    with a small delay to avoid rate limiting.

    Results are cached in ``st.session_state`` to avoid re-fetching on
    every Streamlit rerun.

    Args:
        sp: Authenticated Spotify client.
        artist_ids: List of artist IDs.

    Returns:
        Dict mapping artist_id → list of genres.
    """
    # Return cached result if available
    if "artist_genres_cache" in st.session_state:
        cache: dict[str, list[str]] = st.session_state["artist_genres_cache"]
        missing = [aid for aid in artist_ids if aid and aid not in cache]
        if not missing:
            return {aid: cache.get(aid, []) for aid in artist_ids if aid}
    else:
        cache = {}
        missing = list(set(aid for aid in artist_ids if aid))

    genres_map: dict[str, list[str]] = {}
    unique_ids = list(set(missing))

    if not unique_ids:
        st.session_state["artist_genres_cache"] = cache
        return {aid: cache.get(aid, []) for aid in artist_ids if aid}

    # --- Try batch endpoint first ---
    batch_ok = True
    with st.spinner(f"Obteniendo géneros de {len(unique_ids)} artistas…"):
        first_batch = unique_ids[:50]
        try:
            results = sp.artists(first_batch)
            for artist in results.get("artists", []):
                if artist:
                    genres_map[artist["id"]] = artist.get("genres", [])
        except Exception as e:
            logger.warning("Batch endpoint failed (falling back to individual): %s", e)
            batch_ok = False

        if batch_ok:
            # Batch works — continue with remaining batches
            for i in range(50, len(unique_ids), 50):
                batch = unique_ids[i : i + 50]
                try:
                    results = sp.artists(batch)
                    for artist in results.get("artists", []):
                        if artist:
                            genres_map[artist["id"]] = artist.get("genres", [])
                except Exception as e:
                    logger.warning("Failed to fetch artist batch %d: %s", i, e)
        else:
            # Fallback — individual calls with delay
            for idx, aid in enumerate(unique_ids):
                try:
                    artist = sp.artist(aid)
                    genres_map[aid] = artist.get("genres", [])
                except Exception as e:
                    logger.warning("Failed to fetch artist %s: %s", aid, e)
                    genres_map[aid] = []
                # Small delay every 5 calls to stay under rate limits
                if (idx + 1) % 5 == 0:
                    time.sleep(0.3)

    # Merge into cache and persist
    cache.update(genres_map)
    st.session_state["artist_genres_cache"] = cache

    return {aid: cache.get(aid, []) for aid in artist_ids if aid}


def enrich_liked_with_hf(
    liked_df: pd.DataFrame,
    hf_df: pd.DataFrame,
) -> pd.DataFrame:
    """Cross-reference liked songs with HF dataset to get audio features.

    Args:
        liked_df: DataFrame of liked songs.
        hf_df: Global HuggingFace DataFrame.

    Returns:
        Liked DataFrame enriched with audio features where available.
    """
    from src.data_loader import AUDIO_FEATURES

    hf_features = hf_df[["track_id"] + AUDIO_FEATURES + ["genre"]].copy()
    enriched = liked_df.merge(hf_features, on="track_id", how="left")

    matched = enriched[AUDIO_FEATURES[0]].notna().sum()
    logger.info("HF lookup: %d/%d liked songs matched", matched, len(enriched))

    return enriched


# ---------------------------------------------------------------------------
# User profile
# ---------------------------------------------------------------------------


def fetch_user_profile(sp: spotipy.Spotify) -> dict:
    """Fetch current user's profile (name, image, URI).

    Args:
        sp: Authenticated Spotify client.

    Returns:
        Dict with keys: display_name, image_url, uri, id.
    """
    me = sp.current_user()
    images = me.get("images", [])
    image_url = images[0]["url"] if images else None
    profile = {
        "display_name": me.get("display_name", "Usuario"),
        "image_url": image_url,
        "uri": me.get("uri", ""),
        "id": me.get("id", ""),
    }
    logger.info("Fetched profile for %s", profile["display_name"])
    return profile


# ---------------------------------------------------------------------------
# Playlists
# ---------------------------------------------------------------------------


def fetch_user_playlists(sp: spotipy.Spotify) -> pd.DataFrame:
    """Fetch all playlists owned by the current user.

    Args:
        sp: Authenticated Spotify client.

    Returns:
        DataFrame with columns [playlist_id, name, total_tracks, cover_url,
        description, owner_id].
    """
    playlists: list[dict] = []
    offset = 0

    with st.spinner("Obteniendo playlists…"):
        while True:
            results = sp.current_user_playlists(limit=50, offset=offset)
            items = results.get("items", [])
            if not items:
                break

            for item in items:
                images = item.get("images", [])
                # tracks field may be "tracks" or "items" (Feb 2026 API)
                tracks_obj = item.get("tracks") or item.get("items") or {}
                playlists.append({
                    "playlist_id": item.get("id"),
                    "name": item.get("name"),
                    "total_tracks": tracks_obj.get("total", 0),
                    "cover_url": images[0]["url"] if images else None,
                    "description": item.get("description", ""),
                    "owner_id": item.get("owner", {}).get("id", ""),
                })

            offset += 50
            if offset >= results.get("total", 0):
                break

    logger.info("Fetched %d playlists", len(playlists))
    return pd.DataFrame(playlists)


def fetch_playlist_tracks(
    sp: spotipy.Spotify,
    playlist_id: str,
) -> pd.DataFrame:
    """Fetch all tracks from a user's playlist.

    Args:
        sp: Authenticated Spotify client.
        playlist_id: Spotify playlist ID.

    Returns:
        DataFrame with track metadata similar to fetch_liked_songs.
    """
    tracks: list[dict] = []
    offset = 0

    with st.spinner("Obteniendo tracks de la playlist…"):
        while True:
            results = sp.playlist_items(
                playlist_id, limit=100, offset=offset,
                fields="items(added_at,track(id,name,duration_ms,explicit,"
                       "artists(id,name),album(name,release_date,images))),"
                       "total",
            )
            items = results.get("items", [])
            if not items:
                break

            for item in items:
                track = item.get("track")
                if not track or not track.get("id"):
                    continue
                album = track.get("album", {})
                artists = track.get("artists", [])
                artist_name = artists[0]["name"] if artists else "Unknown"
                artist_id = artists[0]["id"] if artists else None
                album_images = album.get("images", [])

                tracks.append({
                    "track_id": track.get("id"),
                    "track_name": track.get("name"),
                    "artist": artist_name,
                    "artist_id": artist_id,
                    "album": album.get("name"),
                    "album_release_date": album.get("release_date"),
                    "album_cover_url": album_images[0]["url"] if album_images else None,
                    "duration_ms": track.get("duration_ms"),
                    "explicit": track.get("explicit"),
                    "added_at": item.get("added_at"),
                })

            offset += 100
            if offset >= results.get("total", 0):
                break

    df = pd.DataFrame(tracks)
    if not df.empty and "added_at" in df.columns:
        df["added_at"] = pd.to_datetime(df["added_at"])
    logger.info("Fetched %d tracks from playlist %s", len(df), playlist_id)
    return df


# ---------------------------------------------------------------------------
# Top tracks
# ---------------------------------------------------------------------------


def fetch_top_tracks(
    sp: spotipy.Spotify,
    time_range: str = "medium_term",
    limit: int = 50,
) -> pd.DataFrame:
    """Fetch user's top tracks.

    Args:
        sp: Authenticated Spotify client.
        time_range: One of 'short_term', 'medium_term', 'long_term'.
        limit: Number of tracks (max 50).

    Returns:
        DataFrame with columns [track_id, track_name, artist, artist_id,
        album, album_cover_url, duration_ms, rank].
    """
    results = sp.current_user_top_tracks(limit=limit, time_range=time_range)
    tracks: list[dict] = []

    for i, item in enumerate(results.get("items", []), start=1):
        artists = item.get("artists", [])
        album = item.get("album", {})
        album_images = album.get("images", [])
        tracks.append({
            "track_id": item.get("id"),
            "track_name": item.get("name"),
            "artist": artists[0]["name"] if artists else "Unknown",
            "artist_id": artists[0]["id"] if artists else None,
            "album": album.get("name"),
            "album_cover_url": album_images[0]["url"] if album_images else None,
            "duration_ms": item.get("duration_ms"),
            "rank": i,
        })

    logger.info("Fetched %d top tracks (%s)", len(tracks), time_range)
    return pd.DataFrame(tracks)


# ---------------------------------------------------------------------------
# Player (Now Playing)
# ---------------------------------------------------------------------------


def fetch_currently_playing(sp: spotipy.Spotify) -> dict | None:
    """Fetch the currently playing track.

    Args:
        sp: Authenticated Spotify client.

    Returns:
        Dict with track info or None if nothing is playing.
    """
    try:
        result = sp.current_user_playing_track()
    except Exception as e:
        logger.warning("Failed to fetch currently playing: %s", e)
        return None

    if not result or not result.get("item"):
        return None

    item = result["item"]
    artists = item.get("artists", [])
    album = item.get("album", {})
    album_images = album.get("images", [])

    return {
        "track_id": item.get("id"),
        "track_name": item.get("name"),
        "artist": artists[0]["name"] if artists else "Unknown",
        "artist_id": artists[0]["id"] if artists else None,
        "album": album.get("name"),
        "album_cover_url": album_images[0]["url"] if album_images else None,
        "duration_ms": item.get("duration_ms"),
        "progress_ms": result.get("progress_ms", 0),
        "is_playing": result.get("is_playing", False),
        "uri": item.get("uri", ""),
    }


def fetch_recently_played(
    sp: spotipy.Spotify,
    limit: int = 50,
) -> pd.DataFrame:
    """Fetch recently played tracks.

    Args:
        sp: Authenticated Spotify client.
        limit: Number of tracks (max 50).

    Returns:
        DataFrame with columns [track_id, track_name, artist, artist_id,
        album, album_cover_url, played_at].
    """
    try:
        results = sp.current_user_recently_played(limit=limit)
    except Exception as e:
        logger.warning("Failed to fetch recently played: %s", e)
        return pd.DataFrame()

    tracks: list[dict] = []
    for item in results.get("items", []):
        track = item.get("track", {})
        artists = track.get("artists", [])
        album = track.get("album", {})
        album_images = album.get("images", [])
        tracks.append({
            "track_id": track.get("id"),
            "track_name": track.get("name"),
            "artist": artists[0]["name"] if artists else "Unknown",
            "artist_id": artists[0]["id"] if artists else None,
            "album": album.get("name"),
            "album_cover_url": album_images[0]["url"] if album_images else None,
            "played_at": item.get("played_at"),
        })

    df = pd.DataFrame(tracks)
    if not df.empty and "played_at" in df.columns:
        df["played_at"] = pd.to_datetime(df["played_at"])
    logger.info("Fetched %d recently played tracks", len(df))
    return df


def fetch_playback_state(sp: spotipy.Spotify) -> dict | None:
    """Fetch current playback state.

    Args:
        sp: Authenticated Spotify client.

    Returns:
        Dict with playback info or None.
    """
    try:
        return sp.current_playback()
    except Exception as e:
        logger.warning("Failed to fetch playback state: %s", e)
        return None


def fetch_queue(sp: spotipy.Spotify) -> list[dict]:
    """Fetch the current playback queue.

    Args:
        sp: Authenticated Spotify client.

    Returns:
        List of dicts with track info for queued tracks.
    """
    try:
        result = sp.queue()
    except Exception as e:
        logger.warning("Failed to fetch queue: %s", e)
        return []

    queued: list[dict] = []
    for item in result.get("queue", [])[:20]:
        artists = item.get("artists", [])
        album = item.get("album", {})
        album_images = album.get("images", [])
        queued.append({
            "track_id": item.get("id"),
            "track_name": item.get("name"),
            "artist": artists[0]["name"] if artists else "Unknown",
            "album": album.get("name"),
            "album_cover_url": album_images[0]["url"] if album_images else None,
            "uri": item.get("uri", ""),
        })
    return queued


def fetch_devices(sp: spotipy.Spotify) -> list[dict]:
    """Fetch available playback devices.

    Args:
        sp: Authenticated Spotify client.

    Returns:
        List of dicts with device info.
    """
    try:
        result = sp.devices()
    except Exception as e:
        logger.warning("Failed to fetch devices: %s", e)
        return []

    return [
        {
            "id": d.get("id"),
            "name": d.get("name"),
            "type": d.get("type"),
            "is_active": d.get("is_active", False),
        }
        for d in result.get("devices", [])
    ]


# ---------------------------------------------------------------------------
# Player controls
# ---------------------------------------------------------------------------


def player_play(
    sp: spotipy.Spotify,
    device_id: str | None = None,
    uris: list[str] | None = None,
) -> bool:
    """Start or resume playback.

    Args:
        sp: Authenticated Spotify client.
        device_id: Target device ID (optional).
        uris: List of Spotify URIs to play (optional).

    Returns:
        True if successful.
    """
    try:
        sp.start_playback(device_id=device_id, uris=uris)
        return True
    except Exception as e:
        logger.warning("Player play failed: %s", e)
        return False


def player_pause(sp: spotipy.Spotify, device_id: str | None = None) -> bool:
    """Pause playback.

    Args:
        sp: Authenticated Spotify client.
        device_id: Target device ID (optional).

    Returns:
        True if successful.
    """
    try:
        sp.pause_playback(device_id=device_id)
        return True
    except Exception as e:
        logger.warning("Player pause failed: %s", e)
        return False


def player_next(sp: spotipy.Spotify, device_id: str | None = None) -> bool:
    """Skip to next track.

    Args:
        sp: Authenticated Spotify client.
        device_id: Target device ID (optional).

    Returns:
        True if successful.
    """
    try:
        sp.next_track(device_id=device_id)
        return True
    except Exception as e:
        logger.warning("Player next failed: %s", e)
        return False


def player_previous(sp: spotipy.Spotify, device_id: str | None = None) -> bool:
    """Skip to previous track.

    Args:
        sp: Authenticated Spotify client.
        device_id: Target device ID (optional).

    Returns:
        True if successful.
    """
    try:
        sp.previous_track(device_id=device_id)
        return True
    except Exception as e:
        logger.warning("Player previous failed: %s", e)
        return False


def player_add_to_queue(sp: spotipy.Spotify, uri: str) -> bool:
    """Add a track to the playback queue.

    Args:
        sp: Authenticated Spotify client.
        uri: Spotify URI of the track to add.

    Returns:
        True if successful.
    """
    try:
        sp.add_to_queue(uri)
        return True
    except Exception as e:
        logger.warning("Add to queue failed: %s", e)
        return False
