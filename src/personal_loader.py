"""Local CSV loader for personal Spotify data (no API, no OAuth).

Reads pre-exported CSVs from data/. Run scripts/export_personal_data.py
to generate them from your Spotify account.
"""

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"


# ---------------------------------------------------------------------------
# Liked songs
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner="Cargando canciones guardadas…")
def load_my_liked_songs(enriched: bool = True) -> pd.DataFrame | None:
    """Load liked songs from local CSV.

    Args:
        enriched: If True, try the enriched version (with audio features)
            first. Falls back to the base CSV.

    Returns:
        DataFrame or None if no CSV found.
    """
    if enriched:
        path = DATA_DIR / "my_liked_songs_enriched.csv"
        if path.exists():
            df = pd.read_csv(path)
            if "added_at" in df.columns:
                df["added_at"] = pd.to_datetime(df["added_at"])
            logger.info("Loaded %d enriched liked songs from %s", len(df), path)
            return df

    path = DATA_DIR / "my_liked_songs.csv"
    if not path.exists():
        logger.warning("Liked songs CSV not found at %s", path)
        return None

    df = pd.read_csv(path)
    if "added_at" in df.columns:
        df["added_at"] = pd.to_datetime(df["added_at"])
    logger.info("Loaded %d liked songs from %s", len(df), path)
    return df


# ---------------------------------------------------------------------------
# Top tracks
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner="Cargando top tracks…")
def load_my_top_tracks(time_range: str = "medium_term") -> pd.DataFrame | None:
    """Load top tracks from local CSV.

    Args:
        time_range: One of 'short_term', 'medium_term', 'long_term'.

    Returns:
        DataFrame or None if no CSV found.
    """
    path = DATA_DIR / f"my_top_tracks_{time_range}.csv"
    if not path.exists():
        logger.warning("Top tracks CSV not found at %s", path)
        return None

    df = pd.read_csv(path)
    logger.info("Loaded %d top tracks (%s) from %s", len(df), time_range, path)
    return df


# ---------------------------------------------------------------------------
# Top artists
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner="Cargando top artistas…")
def load_my_top_artists(time_range: str = "medium_term") -> pd.DataFrame | None:
    """Load top artists from local CSV.

    Args:
        time_range: One of 'short_term', 'medium_term', 'long_term'.

    Returns:
        DataFrame or None if no CSV found.
    """
    path = DATA_DIR / f"my_top_artists_{time_range}.csv"
    if not path.exists():
        logger.warning("Top artists CSV not found at %s", path)
        return None

    df = pd.read_csv(path)
    # Reconstruct genres list from string representation
    if "genres" in df.columns:
        import ast
        df["genres"] = df["genres"].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else []
        )
    logger.info("Loaded %d top artists (%s) from %s", len(df), time_range, path)
    return df


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------


def has_personal_data() -> bool:
    """Check if at least the liked songs CSV exists.

    Returns:
        True if personal CSVs are available.
    """
    return (DATA_DIR / "my_liked_songs.csv").exists() or (
        DATA_DIR / "my_liked_songs_enriched.csv"
    ).exists()
