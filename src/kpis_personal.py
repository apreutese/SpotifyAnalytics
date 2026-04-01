"""KPI calculation functions for the Personal page."""

import pandas as pd

from src.data_loader import AUDIO_FEATURES

RADAR_FEATURES: list[str] = [
    "danceability",
    "energy",
    "valence",
    "acousticness",
    "instrumentalness",
    "tempo",
]

MIN_HF_MATCHES: int = 20


def kpi_my_genres(
    liked_df: pd.DataFrame,
    artist_genres: dict[str, list[str]],
) -> pd.DataFrame:
    """Count genres from liked songs' artists.

    Args:
        liked_df: Liked songs DataFrame with 'artist_id'.
        artist_genres: Dict mapping artist_id → list of genres.

    Returns:
        DataFrame with columns [genre, count, pct].
    """
    all_genres: list[str] = []
    for aid in liked_df["artist_id"].dropna().unique():
        all_genres.extend(artist_genres.get(aid, []))

    if not all_genres:
        return pd.DataFrame(columns=["genre", "count", "pct"])

    counts = (
        pd.Series(all_genres)
        .value_counts()
        .head(20)
        .reset_index()
    )
    counts.columns = ["genre", "count"]
    counts["pct"] = (counts["count"] / counts["count"].sum() * 100).round(1)
    return counts


def kpi_saved_timeline(liked_df: pd.DataFrame) -> pd.DataFrame:
    """Group liked songs by month of added_at.

    Args:
        liked_df: Liked songs DataFrame with 'added_at' datetime column.

    Returns:
        DataFrame with columns [month, count].
    """
    if liked_df.empty or "added_at" not in liked_df.columns:
        return pd.DataFrame(columns=["month", "count"])

    temp = liked_df.copy()
    temp["month"] = temp["added_at"].dt.to_period("M").astype(str)
    result = (
        temp.groupby("month")
        .size()
        .reset_index(name="count")
        .sort_values("month")
    )
    return result


def kpi_my_audio_dna(liked_df: pd.DataFrame) -> pd.DataFrame | None:
    """Mean audio features from liked songs matched with HF dataset.

    Args:
        liked_df: Enriched liked songs DataFrame (with audio feature columns).

    Returns:
        DataFrame with columns [feature, value] or None if < MIN_HF_MATCHES.
    """
    matched = liked_df.dropna(subset=[RADAR_FEATURES[0]])
    if len(matched) < MIN_HF_MATCHES:
        return None

    means = matched[RADAR_FEATURES].mean()
    if "tempo" in means.index:
        means["tempo"] = means["tempo"] / 250.0

    result = means.reset_index()
    result.columns = ["feature", "value"]
    result["value"] = result["value"].round(3)
    return result


def kpi_genre_distribution(
    artist_genres: dict[str, list[str]],
) -> pd.DataFrame:
    """Full genre distribution (fallback for P3).

    Args:
        artist_genres: Dict mapping artist_id → list of genres.

    Returns:
        DataFrame with columns [genre, count, pct].
    """
    all_genres: list[str] = []
    for genres in artist_genres.values():
        all_genres.extend(genres)

    if not all_genres:
        return pd.DataFrame(columns=["genre", "count", "pct"])

    counts = pd.Series(all_genres).value_counts().reset_index()
    counts.columns = ["genre", "count"]
    counts["pct"] = (counts["count"] / counts["count"].sum() * 100).round(1)
    return counts


def kpi_top_artists(
    liked_df: pd.DataFrame,
    top_artists_df: pd.DataFrame,
) -> pd.DataFrame:
    """Combine liked song artist counts with top artists ranking.

    Args:
        liked_df: Liked songs DataFrame.
        top_artists_df: Top artists DataFrame with 'rank' column.

    Returns:
        DataFrame with columns [artist, liked_count, top_rank].
    """
    liked_counts = (
        liked_df.groupby("artist")
        .size()
        .reset_index(name="liked_count")
        .sort_values("liked_count", ascending=False)
        .head(20)
    )

    if not top_artists_df.empty:
        merged = liked_counts.merge(
            top_artists_df[["artist", "rank"]].rename(columns={"rank": "top_rank"}),
            on="artist",
            how="left",
        )
    else:
        merged = liked_counts.copy()
        merged["top_rank"] = None

    return merged.sort_values("liked_count", ascending=False).reset_index(drop=True)
