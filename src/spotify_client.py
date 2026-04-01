"""Spotify Web API client: OAuth + data fetching for personal page."""

import logging
import os
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

SCOPES: str = "user-library-read user-top-read playlist-read-private"
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

                tracks.append({
                    "track_id": track.get("id"),
                    "track_name": track.get("name"),
                    "artist": artist_name,
                    "artist_id": artist_id,
                    "album": album.get("name"),
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
        artists.append({
            "artist_id": item.get("id"),
            "artist": item.get("name"),
            "genres": item.get("genres", []),
            "rank": i,
        })

    logger.info("Fetched %d top artists (%s)", len(artists), time_range)
    return pd.DataFrame(artists)


def fetch_artist_genres(
    sp: spotipy.Spotify,
    artist_ids: list[str],
) -> dict[str, list[str]]:
    """Fetch genres for a list of artist IDs in batches of 50.

    Args:
        sp: Authenticated Spotify client.
        artist_ids: List of artist IDs.

    Returns:
        Dict mapping artist_id → list of genres.
    """
    genres_map: dict[str, list[str]] = {}
    unique_ids = list(set(aid for aid in artist_ids if aid))

    with st.spinner(f"Obteniendo géneros de {len(unique_ids)} artistas…"):
        for i in range(0, len(unique_ids), 50):
            batch = unique_ids[i : i + 50]
            try:
                results = sp.artists(batch)
                for artist in results.get("artists", []):
                    if artist:
                        genres_map[artist["id"]] = artist.get("genres", [])
            except Exception as e:
                logger.warning("Failed to fetch artist batch %d: %s", i, e)
                for aid in batch:
                    genres_map.setdefault(aid, [])

    return genres_map


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
