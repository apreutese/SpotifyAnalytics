"""Spotify OAuth: authentication flow, token management."""

import logging
import os
from pathlib import Path

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
    "user-read-private streaming"
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


def get_access_token() -> str | None:
    """Return the current Spotify access token or None.

    Useful for passing to the Web Playback SDK.
    """
    if not CLIENT_ID or not CLIENT_SECRET:
        return None
    oauth = _get_oauth_manager()
    token_info = oauth.get_cached_token()
    if token_info:
        return token_info["access_token"]
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
