"""One-shot script: export personal Spotify data to local CSVs.

Requires a valid .spotify_cache token. Run `python auth.py` first if needed.

Usage:
    python scripts/export_personal_data.py
"""

import sys
from pathlib import Path

import pandas as pd

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"

# Minimal Streamlit mock so spinner/session_state don't crash outside app
import streamlit as st  # noqa: E402 — needed for spinner in fetch functions


def _get_client():
    """Get authenticated Spotify client from cached token."""
    from src.spotify_auth import get_spotify_client_silent
    sp = get_spotify_client_silent()
    if sp is None:
        print("ERROR: No se encontró token cacheado. Ejecuta `python auth.py` primero.")
        sys.exit(1)
    return sp


def export_liked_songs(sp) -> None:
    """Export liked songs to CSV."""
    from src.spotify_data import fetch_liked_songs
    path = DATA_DIR / "my_liked_songs.csv"
    print("[Liked] Obteniendo canciones guardadas…")
    df = fetch_liked_songs(sp)
    if df.empty:
        print("[Liked] No se encontraron canciones.")
        return
    df.to_csv(path, index=False)
    print(f"[Liked] {len(df):,} canciones → {path}")


def export_top_tracks(sp) -> None:
    """Export top tracks for all time ranges."""
    from src.spotify_data import fetch_top_tracks
    for time_range in ("short_term", "medium_term", "long_term"):
        path = DATA_DIR / f"my_top_tracks_{time_range}.csv"
        print(f"[Top Tracks] Obteniendo {time_range}…")
        df = fetch_top_tracks(sp, time_range=time_range)
        if not df.empty:
            df.to_csv(path, index=False)
            print(f"[Top Tracks] {len(df)} tracks → {path}")
        else:
            print(f"[Top Tracks] Sin datos para {time_range}.")


def export_top_artists(sp) -> None:
    """Export top artists for all time ranges."""
    from src.spotify_data import fetch_top_artists
    for time_range in ("short_term", "medium_term", "long_term"):
        path = DATA_DIR / f"my_top_artists_{time_range}.csv"
        print(f"[Top Artists] Obteniendo {time_range}…")
        df = fetch_top_artists(sp, time_range=time_range)
        if not df.empty:
            df.to_csv(path, index=False)
            print(f"[Top Artists] {len(df)} artistas → {path}")
        else:
            print(f"[Top Artists] Sin datos para {time_range}.")


def enrich_liked_with_audio_features(sp) -> None:
    """Enrich liked songs CSV with Spotify audio features API."""
    liked_path = DATA_DIR / "my_liked_songs.csv"
    enriched_path = DATA_DIR / "my_liked_songs_enriched.csv"

    # Delete old enriched CSV first
    if enriched_path.exists():
        enriched_path.unlink()
        print("[Enrich] Borrado my_liked_songs_enriched.csv anterior.")

    if not liked_path.exists():
        print("[Enrich] No se encontró my_liked_songs.csv — saltando.")
        return

    liked_df = pd.read_csv(liked_path)
    track_ids = liked_df["track_id"].dropna().tolist()

    if not track_ids:
        print("[Enrich] Sin track_ids — saltando.")
        return

    print(f"[Enrich] Obteniendo audio features para {len(track_ids)} tracks…")
    from src.spotify_data import fetch_audio_features_safe
    features_df = fetch_audio_features_safe(sp, track_ids, max_calls=8)

    if features_df is not None and not features_df.empty:
        enriched = liked_df.merge(features_df, on="track_id", how="left")
        matched = enriched["danceability"].notna().sum()
        enriched.to_csv(enriched_path, index=False)
        print(f"[Enrich] {matched}/{len(enriched)} tracks con audio features → {enriched_path}")
    else:
        print("[Enrich] audio_features no disponible (403 o error). Guardando sin audio features.")
        liked_df.to_csv(enriched_path, index=False)
        print(f"[Enrich] {len(liked_df)} tracks (sin audio features) → {enriched_path}")


def main() -> None:
    """Export all personal data."""
    DATA_DIR.mkdir(exist_ok=True)
    sp = _get_client()

    export_liked_songs(sp)
    export_top_tracks(sp)
    export_top_artists(sp)
    enrich_liked_with_audio_features(sp)

    print("\n✓ Exportación completa.")


if __name__ == "__main__":
    main()
