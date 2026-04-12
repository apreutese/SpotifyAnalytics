"""KPI calculation functions for the Personal / Playlist pages.

All KPIs here use only basic track metadata (no audio features, no genres).
"""

import pandas as pd


# ---------------------------------------------------------------------------
# P1 — Saved Timeline
# ---------------------------------------------------------------------------


def kpi_saved_timeline(df: pd.DataFrame) -> pd.DataFrame:
    """Group tracks by month of added_at.

    Args:
        df: DataFrame with 'added_at' datetime column.

    Returns:
        DataFrame with columns [month, count].
    """
    if df.empty or "added_at" not in df.columns:
        return pd.DataFrame(columns=["month", "count"])

    temp = df.copy()
    if temp["added_at"].dt.tz is not None:
        temp["added_at"] = temp["added_at"].dt.tz_localize(None)
    temp["month"] = temp["added_at"].dt.to_period("M").astype(str)
    result = (
        temp.groupby("month")
        .size()
        .reset_index(name="count")
        .sort_values("month")
    )
    return result


# ---------------------------------------------------------------------------
# P2 — Release Decades
# ---------------------------------------------------------------------------


def kpi_release_decades(df: pd.DataFrame) -> pd.DataFrame:
    """Distribution of tracks by release decade.

    Args:
        df: DataFrame with 'album_release_date' column (str, e.g. '2002-07-09').

    Returns:
        DataFrame with columns [decade, count, pct] sorted by decade.
    """
    if df.empty or "album_release_date" not in df.columns:
        return pd.DataFrame(columns=["decade", "count", "pct"])

    temp = df.dropna(subset=["album_release_date"]).copy()
    temp["year"] = pd.to_numeric(
        temp["album_release_date"].astype(str).str[:4], errors="coerce"
    )
    temp = temp.dropna(subset=["year"])
    temp["decade"] = (temp["year"] // 10 * 10).astype(int).astype(str) + "s"

    counts = (
        temp.groupby("decade")
        .size()
        .reset_index(name="count")
        .sort_values("decade")
    )
    total = counts["count"].sum()
    counts["pct"] = (counts["count"] / total * 100).round(1) if total else 0
    return counts


# ---------------------------------------------------------------------------
# P3 — Explicit vs Clean
# ---------------------------------------------------------------------------


def kpi_explicit_ratio(df: pd.DataFrame) -> pd.DataFrame:
    """Proportion of explicit vs clean tracks.

    Args:
        df: DataFrame with 'explicit' column (bool or str).

    Returns:
        DataFrame with columns [label, count, pct].
    """
    if df.empty or "explicit" not in df.columns:
        return pd.DataFrame(columns=["label", "count", "pct"])

    temp = df.copy()
    temp["is_explicit"] = temp["explicit"].astype(str).str.lower().isin(["true", "1"])
    n_explicit = temp["is_explicit"].sum()
    n_clean = len(temp) - n_explicit
    total = len(temp)

    rows = [
        {"label": "Explicit", "count": int(n_explicit), "pct": round(n_explicit / total * 100, 1) if total else 0},
        {"label": "Clean", "count": int(n_clean), "pct": round(n_clean / total * 100, 1) if total else 0},
    ]
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# P4 — Top Albums
# ---------------------------------------------------------------------------


def kpi_top_albums(df: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    """Albums with most saved/playlist tracks.

    Args:
        df: DataFrame with 'album' and optionally 'album_cover_url' columns.
        top_n: Number of top albums to return.

    Returns:
        DataFrame with columns [album, count] (+ album_cover_url if available).
    """
    if df.empty or "album" not in df.columns:
        return pd.DataFrame(columns=["album", "count"])

    counts = (
        df.groupby("album")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(top_n)
    )

    if "album_cover_url" in df.columns:
        first_cover = (
            df.dropna(subset=["album_cover_url"])
            .drop_duplicates(subset=["album"])
            [["album", "album_cover_url"]]
        )
        counts = counts.merge(first_cover, on="album", how="left")

    return counts.reset_index(drop=True)


# ---------------------------------------------------------------------------
# P5 — Top Artists (by saved count + ranking)
# ---------------------------------------------------------------------------


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
        merge_cols = ["artist", "rank"]
        if "artist_image_url" in top_artists_df.columns:
            merge_cols.append("artist_image_url")
        merged = liked_counts.merge(
            top_artists_df[merge_cols].rename(columns={"rank": "top_rank"}),
            on="artist",
            how="left",
        )
    else:
        merged = liked_counts.copy()
        merged["top_rank"] = None

    return merged.sort_values("liked_count", ascending=False).reset_index(drop=True)
