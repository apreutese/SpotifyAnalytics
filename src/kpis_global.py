"""KPI calculation functions for the Global page."""

import pandas as pd

from src.data_loader import AUDIO_FEATURES

# 6 features used for radar charts (exclude loudness, liveness, speechiness)
RADAR_FEATURES: list[str] = [
    "danceability",
    "energy",
    "valence",
    "acousticness",
    "instrumentalness",
    "tempo",
]


def kpi_top_genres(df: pd.DataFrame, top_n: int = 20) -> pd.DataFrame:
    """Count tracks per genre and return top N.

    Args:
        df: Global DataFrame with 'genre' column.
        top_n: Number of top genres to return.

    Returns:
        DataFrame with columns [genre, count, pct].
    """
    counts = (
        df["genre"]
        .value_counts()
        .head(top_n)
        .reset_index()
    )
    counts.columns = ["genre", "count"]
    counts["pct"] = (counts["count"] / counts["count"].sum() * 100).round(1)
    return counts


def kpi_genre_dna(df: pd.DataFrame, genre: str) -> pd.DataFrame:
    """Compute mean audio features for a given genre.

    Args:
        df: Global DataFrame.
        genre: Genre name to filter.

    Returns:
        DataFrame with columns [feature, value] (6 radar features).
    """
    subset = df[df["genre"] == genre]
    if subset.empty:
        return pd.DataFrame(columns=["feature", "value"])

    means = subset[RADAR_FEATURES].mean()
    # Normalize tempo to 0-1 scale (divide by 250 as reasonable max)
    if "tempo" in means.index:
        means["tempo"] = means["tempo"] / 250.0

    result = means.reset_index()
    result.columns = ["feature", "value"]
    result["value"] = result["value"].round(3)
    return result


def kpi_popularity_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """Pearson correlation between popularity and audio features.

    Args:
        df: Global DataFrame with 'popularity' and audio feature columns.

    Returns:
        DataFrame correlation matrix (features × features+popularity).
    """
    cols = ["popularity"] + [f for f in AUDIO_FEATURES if f in df.columns]
    corr = df[cols].corr().round(3)
    return corr


def kpi_sentiment_by_year(df: pd.DataFrame) -> pd.DataFrame | None:
    """Mean valence grouped by decade.

    Args:
        df: Global DataFrame. Must contain 'year' column.

    Returns:
        DataFrame with columns [decade, valence_mean, track_count]
        or None if 'year' column is missing.
    """
    if "year" not in df.columns:
        return None

    temp = df.dropna(subset=["year"]).copy()
    temp["decade"] = (temp["year"] // 10 * 10).astype(int)

    result = (
        temp.groupby("decade")
        .agg(valence_mean=("valence", "mean"), track_count=("track_id", "count"))
        .reset_index()
    )
    result["valence_mean"] = result["valence_mean"].round(3)
    return result


def kpi_popularity_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Popularity distribution in ranges (fallback for G4).

    Args:
        df: Global DataFrame with 'popularity' column.

    Returns:
        DataFrame with columns [range, count, pct].
    """
    bins = [0, 20, 40, 60, 80, 100]
    labels = ["0-19", "20-39", "40-59", "60-79", "80-100"]
    temp = df.copy()
    temp["range"] = pd.cut(temp["popularity"], bins=bins, labels=labels, right=False)
    counts = temp["range"].value_counts().sort_index().reset_index()
    counts.columns = ["range", "count"]
    counts["pct"] = (counts["count"] / counts["count"].sum() * 100).round(1)
    return counts
