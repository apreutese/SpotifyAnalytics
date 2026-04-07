"""Plotly chart functions for the Personal page."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.theme import (
    SPOTIFY_GREEN,
    SPOTIFY_GREEN_LIGHT,
    SPOTIFY_BLUE,
    SPOTIFY_PURPLE,
    BG_TRANSPARENT,
    COLORSCALE_TREEMAP,
    PLOTLY_PALETTE,
    base_layout,
    radar_trace_style,
    radar_layout,
)


# ---------------------------------------------------------------------------
# P1 — My Genres Treemap
# ---------------------------------------------------------------------------


def chart_my_genres(df_genres: pd.DataFrame) -> go.Figure:
    """Treemap of user's genres.

    Args:
        df_genres: DataFrame with columns [genre, count, pct].

    Returns:
        Plotly Figure.
    """
    fig = px.treemap(
        df_genres,
        path=["genre"],
        values="count",
        color="count",
        color_continuous_scale=COLORSCALE_TREEMAP,
        custom_data=["pct"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{value} tracks<br>%{customdata[0]:.1f}%",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{customdata[0]:.1f}%<extra></extra>",
    )
    fig.update_layout(
        title="Mis Géneros",
        coloraxis_showscale=False,
        **base_layout(),
    )
    return fig


# ---------------------------------------------------------------------------
# P2 — Saved Timeline (Area chart)
# ---------------------------------------------------------------------------


def chart_saved_timeline(df_timeline: pd.DataFrame) -> go.Figure:
    """Area chart of liked songs over time.

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
        hovertemplate="Mes: %{x}<br>Tracks guardados: %{y}<extra></extra>",
    ))
    fig.update_layout(
        title="Timeline de Canciones Guardadas",
        xaxis_title="Mes",
        yaxis_title="Tracks guardados",
        **base_layout(),
    )
    return fig


# ---------------------------------------------------------------------------
# P3a — My Audio DNA (Radar)
# ---------------------------------------------------------------------------


def chart_my_audio_dna(df_dna: pd.DataFrame) -> go.Figure:
    """Radar chart of user's audio features.

    Args:
        df_dna: DataFrame with columns [feature, value].

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=df_dna["value"].tolist() + [df_dna["value"].iloc[0]],
        theta=df_dna["feature"].tolist() + [df_dna["feature"].iloc[0]],
        **radar_trace_style("Mi ADN", SPOTIFY_GREEN),
    ))
    fig.update_layout(**radar_layout("Mi ADN Musical"))
    fig.update_layout(showlegend=False)
    return fig


# ---------------------------------------------------------------------------
# P3b — Genre Distribution Donut (Fallback)
# ---------------------------------------------------------------------------


def chart_genre_distribution(df_genres: pd.DataFrame) -> go.Figure:
    """Donut chart of full genre distribution.

    Args:
        df_genres: DataFrame with columns [genre, count, pct].

    Returns:
        Plotly Figure.
    """
    n = max(len(df_genres), 1)
    colors = [
        PLOTLY_PALETTE[i % len(PLOTLY_PALETTE)] for i in range(n)
    ]
    fig = go.Figure(go.Pie(
        labels=df_genres["genre"],
        values=df_genres["count"],
        hole=0.5,
        marker=dict(colors=colors),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        title="Distribución de Géneros",
        showlegend=False,
        **base_layout(),
    )
    return fig


# ---------------------------------------------------------------------------
# P4 — Top Artists (Horizontal bar)
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
