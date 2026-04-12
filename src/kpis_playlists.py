"""KPI functions for the Playlists page.

Playlist-specific KPIs use only basic track metadata.
For shared KPIs (decades, explicit, albums) use kpis_personal directly.
"""

import pandas as pd


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
        unique_albums.
    """
    total_tracks = len(tracks_df)
    total_duration_min = 0
    if "duration_ms" in tracks_df.columns:
        total_duration_min = round(
            tracks_df["duration_ms"].dropna().sum() / 60_000, 1
        )
    unique_artists = tracks_df["artist"].nunique() if "artist" in tracks_df.columns else 0
    unique_albums = tracks_df["album"].nunique() if "album" in tracks_df.columns else 0

    return {
        "total_tracks": total_tracks,
        "total_duration_min": total_duration_min,
        "unique_artists": unique_artists,
        "unique_albums": unique_albums,
    }
