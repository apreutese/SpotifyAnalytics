"""Backup OAuth script — run from terminal if Streamlit OAuth fails.

Usage:
    python auth.py

This will open a browser for Spotify login and cache the token
in .spotify_cache for the Streamlit app to reuse.
"""

import os

from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

SCOPES: str = (
    "user-library-read user-top-read playlist-read-private "
    "user-read-playback-state user-modify-playback-state "
    "user-read-currently-playing user-read-recently-played "
    "user-read-private"
)


def main() -> None:
    """Run OAuth flow in browser and cache the token."""
    client_id = os.getenv("SPOTIFY_CLIENT_ID", "")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8501")

    if not client_id or not client_secret:
        print("ERROR: Configura SPOTIFY_CLIENT_ID y SPOTIFY_CLIENT_SECRET en .env")
        return

    oauth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPES,
        cache_path=".spotify_cache",
        show_dialog=True,
    )

    token_info = oauth.get_cached_token()
    if token_info:
        print("Token cacheado encontrado. Ya estás autenticado.")
        return

    auth_url = oauth.get_authorize_url()
    print(f"\nAbre esta URL en tu navegador:\n{auth_url}\n")

    response_url = input("Pega la URL de redirección aquí: ").strip()
    code = oauth.parse_response_code(response_url)

    if code:
        oauth.get_access_token(code)
        print("Autenticación exitosa. Token guardado en .spotify_cache")
    else:
        print("ERROR: No se pudo extraer el código de autorización.")


if __name__ == "__main__":
    main()
