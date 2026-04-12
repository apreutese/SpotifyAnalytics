"""Plotly chart functions for the Playlists page.

Playlist-specific charts. Shared charts (decades, explicit, albums)
are in charts_personal and can be reused directly.
"""

import plotly.graph_objects as go
import pandas as pd

from src.theme import (
    SPOTIFY_GREEN,
    SPOTIFY_GREEN_LIGHT,
    base_layout,
)


# ---------------------------------------------------------------------------
# PL1 — Playlist Timeline
# ---------------------------------------------------------------------------


def chart_playlist_timeline(df_timeline: pd.DataFrame) -> go.Figure:
    """Area chart of tracks added over time.

    Args:
        df_timeline: DataFrame with columns [month, count].

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_timeline["month"],
        y=df_timeline["count"],
        mode="lines+markers",
        fill="tozeroy",
        fillcolor="rgba(29, 185, 84, 0.15)",
        line=dict(color=SPOTIFY_GREEN, width=2.5, shape="spline"),
        marker=dict(size=6, color=SPOTIFY_GREEN_LIGHT, line=dict(width=1, color=SPOTIFY_GREEN)),
        hovertemplate="Mes: %{x}<br>Tracks añadidos: %{y}<extra></extra>",
    ))
    fig.update_layout(
        title="Timeline de Tracks Añadidos",
        xaxis_title="Mes",
        yaxis_title="Tracks añadidos",
        **base_layout(),
    )
    return fig
