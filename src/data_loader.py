"""Data loading pipeline: local HF CSV + Kaggle CSVs merge.

Reads pre-downloaded files from data/. Run scripts/download_datasets.py
to fetch the datasets before first use.
"""

import logging
from pathlib import Path

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATA_DIR: Path = Path(__file__).resolve().parent.parent / "data"

HF_LOCAL_CSV: Path = DATA_DIR / "hf_tracks.csv"
HF_PARQUET_URL: str = (
    "https://huggingface.co/datasets/maharshipandya/"
    "spotify-tracks-dataset/resolve/refs%2Fconvert%2Fparquet/"
    "default/train/0000.parquet"
)

KAGGLE_LOCAL_CSV: Path = DATA_DIR / "kaggle_tracks.csv"
KAGGLE_ARTISTS_CSV: Path = DATA_DIR / "kaggle_artists.csv"

AUDIO_FEATURES: list[str] = [
    "danceability",
    "energy",
    "valence",
    "tempo",
    "acousticness",
    "speechiness",
    "instrumentalness",
    "liveness",
    "loudness",
]

MIN_MERGE_MATCH_RATE: float = 0.10

# ---------------------------------------------------------------------------
# HuggingFace loader
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner="Cargando dataset HuggingFace…")
def load_hf_dataset() -> pd.DataFrame:
    """Load and clean the HuggingFace Spotify tracks CSV.

    Reads from the local file first (data/hf_tracks.csv). Falls back
    to remote parquet URL if the local file doesn't exist yet.

    Returns:
        Cleaned DataFrame with standardised column names.
    """
    if HF_LOCAL_CSV.exists():
        df = pd.read_csv(HF_LOCAL_CSV)
        logger.info("HF loaded from local CSV: %d rows", len(df))
    else:
        logger.info("Local HF CSV not found — downloading parquet from URL…")
        df = pd.read_parquet(HF_PARQUET_URL)
        logger.info("HF downloaded: %d rows", len(df))

    # Drop useless index column
    df = df.drop(columns=["Unnamed: 0"], errors="ignore")

    # Rename for consistency
    df = df.rename(columns={
        "artists": "artist",
        "album_name": "album",
        "track_genre": "genre",
    })

    # Drop rows with null essentials
    df = df.dropna(subset=["track_id", "track_name", "artist", "album"])

    # Deduplicate by track_id (keep first)
    df = df.drop_duplicates(subset="track_id", keep="first")

    # Take first artist when multi-artist (separated by ';')
    df["artist"] = df["artist"].str.split(";").str[0].str.strip()

    logger.info("HF cleaned rows: %d", len(df))
    return df


# ---------------------------------------------------------------------------
# Kaggle loader
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner="Cargando dataset Kaggle…")
def load_kaggle_year() -> pd.DataFrame | None:
    """Load only track_id and year from the local Kaggle CSV.

    Returns:
        DataFrame with columns [track_id, year] or None if unavailable.
    """
    if not KAGGLE_LOCAL_CSV.exists():
        logger.warning("Kaggle CSV not found at %s — skipping.", KAGGLE_LOCAL_CSV)
        return None

    logger.info("Loading Kaggle CSV from %s", KAGGLE_LOCAL_CSV)
    df = pd.read_csv(
        KAGGLE_LOCAL_CSV,
        usecols=["id", "release_date"],
        dtype={"id": str, "release_date": str},
    )
    df = df.rename(columns={"id": "track_id"})
    # Extract year from release_date (formats: 'YYYY', 'YYYY-MM', 'YYYY-MM-DD')
    df["year"] = pd.to_numeric(
        df["release_date"].str[:4], errors="coerce",
    ).astype("Int64")
    df = df.drop(columns=["release_date"])
    df = df.dropna(subset=["year"])
    df = df.drop_duplicates(subset="track_id", keep="first")
    logger.info("Kaggle year rows: %d", len(df))
    return df


@st.cache_data(show_spinner="Cargando artistas Kaggle…")
def load_kaggle_artists() -> pd.DataFrame | None:
    """Load artist info from the local Kaggle artists CSV.

    Returns:
        DataFrame with columns [artist_id, artist_name, genres,
        popularity, followers] or None if unavailable.
    """
    if not KAGGLE_ARTISTS_CSV.exists():
        logger.warning("Kaggle artists CSV not found at %s — skipping.", KAGGLE_ARTISTS_CSV)
        return None

    logger.info("Loading Kaggle artists from %s", KAGGLE_ARTISTS_CSV)
    df = pd.read_csv(KAGGLE_ARTISTS_CSV)

    # Rename id → artist_id, name → artist_name for consistency
    rename_map = {}
    if "id" in df.columns:
        rename_map["id"] = "artist_id"
    if "name" in df.columns:
        rename_map["name"] = "artist_name"
    if rename_map:
        df = df.rename(columns=rename_map)

    df = df.drop_duplicates(subset="artist_id", keep="first")
    logger.info("Kaggle artists: %d rows", len(df))
    return df


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner="Combinando datasets…")
def merge_datasets(
    _hf_df: pd.DataFrame,
    _kaggle_year: pd.DataFrame | None,
) -> tuple[pd.DataFrame, float | None]:
    """Merge HF dataset with Kaggle year column.

    Args:
        _hf_df: Cleaned HuggingFace DataFrame.
        _kaggle_year: Kaggle DataFrame with [track_id, year] or None.

    Returns:
        Tuple of (merged DataFrame, match_rate or None if no Kaggle data).
    """
    if _kaggle_year is None:
        logger.warning("No Kaggle data — skipping merge.")
        return _hf_df, None

    merged = _hf_df.merge(
        _kaggle_year[["track_id", "year"]],
        on="track_id",
        how="left",
    )
    match_rate: float = merged["year"].notna().mean()
    logger.info("Merge match rate: %.2f%%", match_rate * 100)

    if match_rate < MIN_MERGE_MATCH_RATE:
        logger.warning(
            "Match rate %.2f%% < threshold %.0f%% — discarding year column.",
            match_rate * 100,
            MIN_MERGE_MATCH_RATE * 100,
        )
        merged = merged.drop(columns=["year"])

    return merged, match_rate


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner="Preparando datos globales…")
def get_global_dataframe() -> tuple[pd.DataFrame, float | None]:
    """Load, clean, and merge global datasets.

    Returns:
        Tuple of (final DataFrame, merge match_rate or None).
    """
    hf_df = load_hf_dataset()
    kaggle_year = load_kaggle_year()
    df, match_rate = merge_datasets(hf_df, kaggle_year)
    logger.info("Global dataset ready — %d rows, %d columns", len(df), len(df.columns))
    return df, match_rate
