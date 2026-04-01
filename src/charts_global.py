"""Plotly chart functions for the Global page."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ---------------------------------------------------------------------------
# Spotify palette
# ---------------------------------------------------------------------------

SPOTIFY_GREEN: str = "#1DB954"
SPOTIFY_GREEN_LIGHT: str = "#1ED760"
SPOTIFY_PALETTE: list[str] = [
    "#1DB954", "#1ED760", "#535353", "#B3B3B3", "#509BF5", "#AF2896",
]
BG_COLOR: str = "rgba(0,0,0,0)"
TEXT_COLOR: str = "#FFFFFF"


def _base_layout() -> dict:
    """Shared Plotly layout settings for Spotify theme."""
    return dict(
        paper_bgcolor=BG_COLOR,
        plot_bgcolor=BG_COLOR,
        font=dict(color=TEXT_COLOR, family="Inter, sans-serif"),
        margin=dict(l=40, r=40, t=50, b=40),
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
        color_continuous_scale=["#181818", SPOTIFY_GREEN, SPOTIFY_GREEN_LIGHT],
        custom_data=["pct"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{value:,} tracks<br>%{customdata[0]:.1f}%",
        hovertemplate="<b>%{label}</b><br>Tracks: %{value:,}<br>Porcentaje: %{customdata[0]:.1f}%<extra></extra>",
    )
    fig.update_layout(
        title="Top Géneros por Número de Tracks",
        coloraxis_showscale=False,
        **_base_layout(),
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
        fill="toself",
        fillcolor=f"rgba(29, 185, 84, 0.25)",
        line=dict(color=SPOTIFY_GREEN, width=2),
        name=genre,
    ))
    fig.update_layout(
        title=f"ADN Musical — {genre}",
        polar=dict(
            bgcolor=BG_COLOR,
            radialaxis=dict(visible=True, range=[0, 1], color="#535353"),
            angularaxis=dict(color=TEXT_COLOR),
        ),
        showlegend=False,
        **_base_layout(),
    )
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
        colorscale=[[0, "#AF2896"], [0.5, "#181818"], [1, SPOTIFY_GREEN]],
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
        **_base_layout(),
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
        fillcolor="rgba(29, 185, 84, 0.2)",
        line=dict(color=SPOTIFY_GREEN, width=2),
        marker=dict(size=8, color=SPOTIFY_GREEN_LIGHT),
        hovertemplate="Década: %{x}s<br>Valence media: %{y:.3f}<extra></extra>",
    ))
    fig.update_layout(
        title="Sentimiento Musical por Década (Valence)",
        xaxis_title="Década",
        yaxis_title="Valence media",
        yaxis=dict(range=[0, 1]),
        **_base_layout(),
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
    )
    fig.update_layout(
        title="Distribución de Popularidad",
        xaxis_title="Rango de popularidad",
        yaxis_title="Número de tracks",
        **_base_layout(),
    )
    return fig
