"""Spotify data fetching: liked songs, top artists/tracks, playlists, profile."""

import logging
import time

import pandas as pd
import spotipy
import streamlit as st

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Liked songs
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


# ---------------------------------------------------------------------------
# Top artists
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Artist genres (batch + fallback)
# ---------------------------------------------------------------------------


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
            try:
                results = sp.playlist_items(
                    playlist_id, limit=100, offset=offset,
                )
            except Exception as e:
                logger.error("playlist_items failed for %s: %s", playlist_id, e)
                break

            items = results.get("items", [])
            if not items:
                break

            for item in items:
                # Feb 2026 API returns "item" instead of "track"
                track = item.get("track") or item.get("item")
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
            total = results.get("total", 0)
            if total and offset >= total:
                break
            if not results.get("next"):
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
