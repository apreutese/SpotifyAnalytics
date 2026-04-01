"""Plotly chart functions for the Personal page."""

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

# ---------------------------------------------------------------------------
# Spotify palette
# ---------------------------------------------------------------------------

SPOTIFY_GREEN: str = "#1DB954"
SPOTIFY_GREEN_LIGHT: str = "#1ED760"
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
        color_continuous_scale=["#181818", SPOTIFY_GREEN, SPOTIFY_GREEN_LIGHT],
        custom_data=["pct"],
    )
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{value} tracks<br>%{customdata[0]:.1f}%",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{customdata[0]:.1f}%<extra></extra>",
    )
    fig.update_layout(
        title="Mis Géneros",
        coloraxis_showscale=False,
        **_base_layout(),
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
        fillcolor="rgba(29, 185, 84, 0.2)",
        line=dict(color=SPOTIFY_GREEN, width=2),
        marker=dict(size=6, color=SPOTIFY_GREEN_LIGHT),
        hovertemplate="Mes: %{x}<br>Tracks guardados: %{y}<extra></extra>",
    ))
    fig.update_layout(
        title="Timeline de Canciones Guardadas",
        xaxis_title="Mes",
        yaxis_title="Tracks guardados",
        **_base_layout(),
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
        fill="toself",
        fillcolor="rgba(29, 185, 84, 0.25)",
        line=dict(color=SPOTIFY_GREEN, width=2),
        name="Mi ADN",
    ))
    fig.update_layout(
        title="Mi ADN Musical",
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
# P3b — Genre Distribution Donut (Fallback)
# ---------------------------------------------------------------------------


def chart_genre_distribution(df_genres: pd.DataFrame) -> go.Figure:
    """Donut chart of full genre distribution.

    Args:
        df_genres: DataFrame with columns [genre, count, pct].

    Returns:
        Plotly Figure.
    """
    fig = go.Figure(go.Pie(
        labels=df_genres["genre"],
        values=df_genres["count"],
        hole=0.5,
        marker=dict(
            colors=px.colors.sample_colorscale(
                "Greens", [i / max(len(df_genres), 1) for i in range(len(df_genres))]
            )
        ),
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(
        title="Distribución de Géneros",
        showlegend=False,
        **_base_layout(),
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
        marker=dict(color=SPOTIFY_GREEN),
        hovertemplate="<b>%{y}</b><br>Canciones guardadas: %{x}<extra></extra>",
    ))
    fig.update_layout(
        title="Mis Top Artistas (por canciones guardadas)",
        xaxis_title="Canciones guardadas",
        yaxis_title="",
        **_base_layout(),
    )
    return fig
