"""KPI functions for the Playlists page."""

import pandas as pd

from src.data_loader import AUDIO_FEATURES


def kpi_playlist_genres(
    tracks_df: pd.DataFrame,
    top_n: int = 15,
) -> pd.DataFrame:
    """Genre breakdown for a playlist (from HF enrichment).

    Args:
        tracks_df: Enriched playlist tracks DataFrame (must have 'genre').
        top_n: Number of top genres to return.

    Returns:
        DataFrame with columns [genre, count, pct].
    """
    if "genre" not in tracks_df.columns or tracks_df["genre"].dropna().empty:
        return pd.DataFrame(columns=["genre", "count", "pct"])

    genre_counts = (
        tracks_df["genre"]
        .dropna()
        .value_counts()
        .head(top_n)
        .reset_index()
    )
    genre_counts.columns = ["genre", "count"]
    total = genre_counts["count"].sum()
    genre_counts["pct"] = (genre_counts["count"] / total * 100) if total > 0 else 0
    return genre_counts


def kpi_playlist_audio_dna(
    tracks_df: pd.DataFrame,
) -> pd.DataFrame:
    """Average audio features for a playlist (radar chart data).

    Args:
        tracks_df: Enriched playlist tracks DataFrame.

    Returns:
        DataFrame with columns [feature, value].
    """
    available = [f for f in AUDIO_FEATURES if f in tracks_df.columns]
    if not available:
        return pd.DataFrame(columns=["feature", "value"])

    valid = tracks_df.dropna(subset=available)
    if valid.empty:
        return pd.DataFrame(columns=["feature", "value"])

    means = valid[available].mean()
    return pd.DataFrame({"feature": means.index, "value": means.values})


def kpi_playlist_timeline(
    tracks_df: pd.DataFrame,
) -> pd.DataFrame:
    """Timeline of when tracks were added to the playlist.

    Args:
        tracks_df: Playlist tracks DataFrame (must have 'added_at').

    Returns:
        DataFrame with columns [month, count].
    """
    if "added_at" not in tracks_df.columns or tracks_df["added_at"].dropna().empty:
        return pd.DataFrame(columns=["month", "count"])

    df = tracks_df.dropna(subset=["added_at"]).copy()
    df["month"] = df["added_at"].dt.to_period("M").astype(str)
    timeline = df.groupby("month").size().reset_index(name="count")
    return timeline


def kpi_playlist_summary(tracks_df: pd.DataFrame) -> dict:
    """Summary metrics for a playlist.

    Args:
        tracks_df: Playlist tracks DataFrame.

    Returns:
        Dict with total_tracks, total_duration_min, unique_artists,
        unique_genres.
    """
    total_tracks = len(tracks_df)
    total_duration_min = 0
    if "duration_ms" in tracks_df.columns:
        total_duration_min = round(
            tracks_df["duration_ms"].dropna().sum() / 60_000, 1
        )
    unique_artists = tracks_df["artist"].nunique() if "artist" in tracks_df.columns else 0
    unique_genres = 0
    if "genre" in tracks_df.columns:
        unique_genres = tracks_df["genre"].dropna().nunique()

    return {
        "total_tracks": total_tracks,
        "total_duration_min": total_duration_min,
        "unique_artists": unique_artists,
        "unique_genres": unique_genres,
    }
