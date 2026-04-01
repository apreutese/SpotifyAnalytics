"""Data loading pipeline: HuggingFace parquet + Kaggle CSV merge."""

import logging
from pathlib import Path

import kagglehub
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

HF_PARQUET_URL: str = (
    "https://huggingface.co/datasets/maharshipandya/"
    "spotify-tracks-dataset/resolve/refs%2Fconvert%2Fparquet/"
    "default/train/0000.parquet"
)

KAGGLE_LOCAL_CSV: Path = Path(__file__).resolve().parent.parent / "data" / "kaggle_tracks.csv"
KAGGLE_DATASET: str = "yamaerenay/spotify-dataset-19212020-600k-tracks"

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


@st.cache_data(show_spinner="Descargando dataset de HuggingFace…")
def load_hf_dataset() -> pd.DataFrame:
    """Download and clean the HuggingFace Spotify tracks parquet.

    Returns:
        Cleaned DataFrame with standardised column names.
    """
    df = pd.read_parquet(HF_PARQUET_URL)
    logger.info("HF raw rows: %d", len(df))

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


def _resolve_kaggle_csv() -> Path | None:
    """Find the Kaggle tracks CSV: local fallback or kagglehub download.

    Returns:
        Path to tracks.csv or None if unavailable.
    """
    # 1. Local fallback
    if KAGGLE_LOCAL_CSV.exists():
        logger.info("Using local Kaggle CSV at %s", KAGGLE_LOCAL_CSV)
        return KAGGLE_LOCAL_CSV

    # 2. Auto-download via kagglehub
    try:
        dataset_dir = kagglehub.dataset_download(KAGGLE_DATASET)
        csv_path = Path(dataset_dir) / "tracks.csv"
        if csv_path.exists():
            logger.info("Downloaded Kaggle dataset via kagglehub: %s", csv_path)
            return csv_path
        logger.warning("kagglehub downloaded but tracks.csv not found in %s", dataset_dir)
    except Exception as e:
        logger.warning("kagglehub download failed: %s", e)

    return None


@st.cache_data(show_spinner="Cargando dataset Kaggle…")
def load_kaggle_year() -> pd.DataFrame | None:
    """Load only track_id and year from the Kaggle CSV.

    Tries kagglehub auto-download first, falls back to local CSV.

    Returns:
        DataFrame with columns [track_id, year] or None if unavailable.
    """
    csv_path = _resolve_kaggle_csv()
    if csv_path is None:
        logger.warning("Kaggle dataset not available — skipping.")
        return None

    df = pd.read_csv(
        csv_path,
        usecols=["id", "year"],
        dtype={"id": str, "year": "Int64"},
    )
    df = df.rename(columns={"id": "track_id"})
    df = df.drop_duplicates(subset="track_id", keep="first")
    logger.info("Kaggle year rows: %d", len(df))
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
