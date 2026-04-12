"""Spotify playback: current track, queue, devices, player controls."""

import logging

import pandas as pd
import spotipy
import streamlit as st

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Current playback state
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
