"""Plotly chart functions for the Playlists page."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.theme import (
    SPOTIFY_GREEN,
    SPOTIFY_GREEN_LIGHT,
    SPOTIFY_BLUE,
    SPOTIFY_PURPLE,
    COLORSCALE_TREEMAP,
    PLOTLY_PALETTE,
    base_layout,
    radar_trace_style,
    radar_layout,
)


# ---------------------------------------------------------------------------
# PL1 — Playlist Genres Treemap
# ---------------------------------------------------------------------------


def chart_playlist_genres(df_genres: pd.DataFrame) -> go.Figure:
    """Treemap of playlist genres.

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
        title="Géneros de la Playlist",
        coloraxis_showscale=False,
        **base_layout(),
    )
    return fig


# ---------------------------------------------------------------------------
# PL2 — Playlist Audio DNA Radar
# ---------------------------------------------------------------------------


def chart_playlist_audio_dna(
    df_dna: pd.DataFrame,
    name: str = "Playlist",
) -> go.Figure:
    """Radar chart of playlist audio features.

    Args:
        df_dna: DataFrame with columns [feature, value].
        name: Playlist name for legend.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=df_dna["value"].tolist() + [df_dna["value"].iloc[0]],
        theta=df_dna["feature"].tolist() + [df_dna["feature"].iloc[0]],
        **radar_trace_style(name, SPOTIFY_GREEN),
    ))
    fig.update_layout(**radar_layout(f"Audio DNA — {name}"))
    fig.update_layout(showlegend=False)
    return fig


# ---------------------------------------------------------------------------
# PL2b — Comparator: two playlists on the same radar
# ---------------------------------------------------------------------------


def chart_compare_playlists(
    df_dna_a: pd.DataFrame,
    df_dna_b: pd.DataFrame,
    name_a: str = "Playlist A",
    name_b: str = "Playlist B",
) -> go.Figure:
    """Overlaid radar chart comparing two playlists.

    Args:
        df_dna_a: Audio DNA DataFrame for playlist A.
        df_dna_b: Audio DNA DataFrame for playlist B.
        name_a: Name of playlist A.
        name_b: Name of playlist B.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=df_dna_a["value"].tolist() + [df_dna_a["value"].iloc[0]],
        theta=df_dna_a["feature"].tolist() + [df_dna_a["feature"].iloc[0]],
        **radar_trace_style(name_a, SPOTIFY_GREEN),
    ))
    fig.add_trace(go.Scatterpolar(
        r=df_dna_b["value"].tolist() + [df_dna_b["value"].iloc[0]],
        theta=df_dna_b["feature"].tolist() + [df_dna_b["feature"].iloc[0]],
        **radar_trace_style(name_b, SPOTIFY_PURPLE, opacity=0.2),
    ))

    fig.update_layout(**radar_layout(f"{name_a} vs {name_b}"))
    return fig


# ---------------------------------------------------------------------------
# PL3 — Playlist Timeline
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
