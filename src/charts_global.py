"""Plotly chart functions for the Global page."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.theme import (
    SPOTIFY_GREEN,
    SPOTIFY_GREEN_LIGHT,
    SPOTIFY_BLUE,
    SPOTIFY_PURPLE,
    SPOTIFY_PINK,
    GRAY_MID,
    TEXT_PRIMARY,
    BG_TRANSPARENT,
    PLOTLY_PALETTE,
    COLORSCALE_TREEMAP,
    COLORSCALE_DIVERGING,
    base_layout,
    radar_trace_style,
    radar_layout,
)


# ---------------------------------------------------------------------------
# G1 — Top Genres Treemap
# ---------------------------------------------------------------------------


def chart_top_genres(df_genres: pd.DataFrame) -> go.Figure:
    """Treemap of top genres by track count.

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
        texttemplate="<b>%{label}</b><br>%{value:,} tracks<br>%{customdata[0]:.1f}%",
        hovertemplate="<b>%{label}</b><br>Tracks: %{value:,}<br>Porcentaje: %{customdata[0]:.1f}%<extra></extra>",
    )
    fig.update_layout(
        title="Top Géneros por Número de Tracks",
        coloraxis_showscale=False,
        **base_layout(),
    )
    return fig


# ---------------------------------------------------------------------------
# G2 — Genre DNA Radar
# ---------------------------------------------------------------------------


def chart_genre_dna(df_dna: pd.DataFrame, genre: str) -> go.Figure:
    """Radar chart of audio features for a genre.

    Args:
        df_dna: DataFrame with columns [feature, value].
        genre: Genre name for chart title.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=df_dna["value"].tolist() + [df_dna["value"].iloc[0]],
        theta=df_dna["feature"].tolist() + [df_dna["feature"].iloc[0]],
        **radar_trace_style(genre, SPOTIFY_GREEN),
    ))
    fig.update_layout(**radar_layout(f"ADN Musical — {genre}"))
    fig.update_layout(showlegend=False)
    return fig


# ---------------------------------------------------------------------------
# G3 — Popularity vs Features Heatmap
# ---------------------------------------------------------------------------


def chart_popularity_correlation(corr_df: pd.DataFrame) -> go.Figure:
    """Heatmap of correlation matrix.

    Args:
        corr_df: Correlation DataFrame.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure(go.Heatmap(
        z=corr_df.values,
        x=corr_df.columns.tolist(),
        y=corr_df.index.tolist(),
        colorscale=COLORSCALE_DIVERGING,
        zmid=0,
        text=corr_df.values.round(2),
        texttemplate="%{text}",
        textfont=dict(size=11),
        hovertemplate="%{x} vs %{y}: %{z:.3f}<extra></extra>",
    ))
    fig.update_layout(
        title="Correlación Popularidad vs Audio Features",
        xaxis=dict(tickangle=-45),
        yaxis=dict(autorange="reversed"),
        **base_layout(),
    )
    return fig


# ---------------------------------------------------------------------------
# G4a — Sentiment by Year/Decade (Line/Area)
# ---------------------------------------------------------------------------


def chart_sentiment_by_year(df_sentiment: pd.DataFrame) -> go.Figure:
    """Area chart of mean valence by decade.

    Args:
        df_sentiment: DataFrame with columns [decade, valence_mean, track_count].

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sentiment["decade"],
        y=df_sentiment["valence_mean"],
        mode="lines+markers",
        fill="tozeroy",
        fillcolor="rgba(29, 185, 84, 0.15)",
        line=dict(color=SPOTIFY_GREEN, width=2.5, shape="spline"),
        marker=dict(size=8, color=SPOTIFY_GREEN_LIGHT, line=dict(width=1, color=SPOTIFY_GREEN)),
        hovertemplate="Década: %{x}s<br>Valence media: %{y:.3f}<extra></extra>",
    ))
    fig.update_layout(
        title="Sentimiento Musical por Década (Valence)",
        xaxis_title="Década",
        yaxis_title="Valence media",
        yaxis=dict(range=[0, 1]),
        **base_layout(),
    )
    return fig


# ---------------------------------------------------------------------------
# G4b — Popularity Distribution (Fallback)
# ---------------------------------------------------------------------------


def chart_popularity_distribution(df_dist: pd.DataFrame) -> go.Figure:
    """Histogram/bar chart of popularity distribution.

    Args:
        df_dist: DataFrame with columns [range, count, pct].

    Returns:
        Plotly Figure.
    """
    fig = px.bar(
        df_dist,
        x="range",
        y="count",
        text="pct",
        color_discrete_sequence=[SPOTIFY_GREEN],
        custom_data=["pct"],
    )
    fig.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        hovertemplate="Rango: %{x}<br>Tracks: %{y:,}<br>Porcentaje: %{customdata[0]:.1f}%<extra></extra>",
        marker=dict(line=dict(width=0), cornerradius=6),
    )
    fig.update_layout(
        title="Distribución de Popularidad",
        xaxis_title="Rango de popularidad",
        yaxis_title="Número de tracks",
        **base_layout(),
    )
    return fig
