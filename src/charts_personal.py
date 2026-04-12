"""Plotly chart functions for the Personal / Playlist pages.

All charts use only basic track metadata (no audio features, no genres).
"""

import plotly.graph_objects as go
import pandas as pd

from src.theme import (
    SPOTIFY_GREEN,
    SPOTIFY_GREEN_LIGHT,
    SPOTIFY_PURPLE,
    PLOTLY_PALETTE,
    base_layout,
)


# ---------------------------------------------------------------------------
# P1 — Saved Timeline (Area chart)
# ---------------------------------------------------------------------------


def chart_saved_timeline(df_timeline: pd.DataFrame) -> go.Figure:
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
        hovertemplate="Mes: %{x}<br>Tracks: %{y}<extra></extra>",
    ))
    fig.update_layout(
        title="Timeline de Canciones",
        xaxis_title="Mes",
        yaxis_title="Tracks",
        **base_layout(),
    )
    return fig


# ---------------------------------------------------------------------------
# P2 — Release Decades (Bar chart)
# ---------------------------------------------------------------------------


def chart_release_decades(df_decades: pd.DataFrame) -> go.Figure:
    """Bar chart of tracks by release decade.

    Args:
        df_decades: DataFrame with columns [decade, count, pct].

    Returns:
        Plotly Figure.
    """
    fig = go.Figure(go.Bar(
        x=df_decades["decade"],
        y=df_decades["count"],
        marker=dict(color=SPOTIFY_GREEN, cornerradius=4),
        text=df_decades["pct"].apply(lambda v: f"{v:.0f}%"),
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y} tracks<br>%{text}<extra></extra>",
    ))
    fig.update_layout(
        title="Décadas de Lanzamiento",
        xaxis_title="Década",
        yaxis_title="Tracks",
        **base_layout(),
    )
    return fig


# ---------------------------------------------------------------------------
# P3 — Explicit vs Clean (Donut)
# ---------------------------------------------------------------------------


def chart_explicit_ratio(df_explicit: pd.DataFrame) -> go.Figure:
    """Donut chart of explicit vs clean proportion.

    Args:
        df_explicit: DataFrame with columns [label, count, pct].

    Returns:
        Plotly Figure.
    """
    colors = [SPOTIFY_PURPLE, SPOTIFY_GREEN]
    fig = go.Figure(go.Pie(
        labels=df_explicit["label"],
        values=df_explicit["count"],
        hole=0.55,
        marker=dict(colors=colors),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value} tracks<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        title="Explicit vs Clean",
        showlegend=False,
        **base_layout(),
    )
    return fig


# ---------------------------------------------------------------------------
# P4 — Top Albums (Horizontal bar)
# ---------------------------------------------------------------------------


def chart_top_albums(df_albums: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of top albums by track count.

    Args:
        df_albums: DataFrame with columns [album, count].

    Returns:
        Plotly Figure.
    """
    df_sorted = df_albums.sort_values("count", ascending=True)

    fig = go.Figure(go.Bar(
        x=df_sorted["count"],
        y=df_sorted["album"],
        orientation="h",
        marker=dict(color=SPOTIFY_GREEN, line=dict(width=0), cornerradius=4),
        hovertemplate="<b>%{y}</b><br>%{x} tracks<extra></extra>",
    ))
    fig.update_layout(
        title="Álbumes Más Repetidos",
        xaxis_title="Tracks",
        yaxis_title="",
        **base_layout(),
    )
    return fig


# ---------------------------------------------------------------------------
# P5 — Top Artists (Horizontal bar)
# ---------------------------------------------------------------------------


def chart_top_artists(df_artists: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of top artists by liked song count.

    Args:
        df_artists: DataFrame with columns [artist, liked_count, top_rank].

    Returns:
        Plotly Figure.
    """
    df_sorted = df_artists.sort_values("liked_count", ascending=True)

    fig = go.Figure(go.Bar(
        x=df_sorted["liked_count"],
        y=df_sorted["artist"],
        orientation="h",
        marker=dict(color=SPOTIFY_GREEN, line=dict(width=0), cornerradius=4),
        hovertemplate="<b>%{y}</b><br>Canciones guardadas: %{x}<extra></extra>",
    ))
    fig.update_layout(
        title="Mis Top Artistas (por canciones guardadas)",
        xaxis_title="Canciones guardadas",
        yaxis_title="",
        **base_layout(),
    )
    return fig
