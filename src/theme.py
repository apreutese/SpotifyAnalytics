"""Shared theme constants for Plotly charts and UI components."""

# ---------------------------------------------------------------------------
# Brand colors
# ---------------------------------------------------------------------------

SPOTIFY_GREEN: str = "#1DB954"
SPOTIFY_GREEN_LIGHT: str = "#1ED760"
SPOTIFY_BLUE: str = "#509BF5"
SPOTIFY_PURPLE: str = "#AF2896"
SPOTIFY_PINK: str = "#E8115B"
SPOTIFY_ORANGE: str = "#F59B23"
GRAY_LIGHT: str = "#B3B3B3"
GRAY_MID: str = "#535353"
GRAY_DARK: str = "#252525"
BG_APP: str = "#0A0A0A"
BG_CARD: str = "#141414"
BG_SIDEBAR: str = "#0F0F0F"
BG_TRANSPARENT: str = "rgba(0,0,0,0)"
TEXT_PRIMARY: str = "#EAEAEA"
TEXT_SECONDARY: str = "#B3B3B3"

# ---------------------------------------------------------------------------
# Plotly categorical palette (purple → green → blue cycle)
# ---------------------------------------------------------------------------

PLOTLY_PALETTE: list[str] = [
    SPOTIFY_GREEN,
    SPOTIFY_BLUE,
    SPOTIFY_PURPLE,
    SPOTIFY_GREEN_LIGHT,
    SPOTIFY_PINK,
    SPOTIFY_ORANGE,
    GRAY_LIGHT,
    GRAY_MID,
]

# Continuous color scales
COLORSCALE_GREEN: list[list] = [
    [0, "#0A0A0A"],
    [0.5, SPOTIFY_GREEN],
    [1, SPOTIFY_GREEN_LIGHT],
]

COLORSCALE_DIVERGING: list[list] = [
    [0, SPOTIFY_PURPLE],
    [0.25, SPOTIFY_PINK],
    [0.5, "#1a1a1a"],
    [0.75, SPOTIFY_GREEN],
    [1, SPOTIFY_GREEN_LIGHT],
]

COLORSCALE_TREEMAP: list[list] = [
    [0, "#141414"],
    [0.4, SPOTIFY_PURPLE],
    [0.7, SPOTIFY_GREEN],
    [1, SPOTIFY_GREEN_LIGHT],
]

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

FONT_FAMILY: str = "Space Grotesk, sans-serif"
CODE_FONT_FAMILY: str = "JetBrains Mono, monospace"

# ---------------------------------------------------------------------------
# Plotly base layout
# ---------------------------------------------------------------------------


def base_layout(**overrides: object) -> dict:
    """Return shared Plotly layout settings for the Premium theme.

    Args:
        **overrides: Additional layout keys to merge/override.

    Returns:
        Dict ready to be unpacked into ``fig.update_layout()``.
    """
    layout = dict(
        paper_bgcolor=BG_TRANSPARENT,
        plot_bgcolor=BG_TRANSPARENT,
        font=dict(color=TEXT_PRIMARY, family=FONT_FAMILY, size=13),
        margin=dict(l=40, r=40, t=50, b=40),
        hoverlabel=dict(
            bgcolor=BG_CARD,
            bordercolor=GRAY_DARK,
            font=dict(color=TEXT_PRIMARY, family=FONT_FAMILY, size=12),
        ),
    )
    layout.update(overrides)
    return layout


# ---------------------------------------------------------------------------
# Radar chart helpers
# ---------------------------------------------------------------------------


def radar_trace_style(
    name: str,
    color: str = SPOTIFY_GREEN,
    opacity: float = 0.25,
) -> dict:
    """Return common style kwargs for a Scatterpolar trace.

    Args:
        name: Trace legend name.
        color: Line and fill base color.
        opacity: Fill opacity.

    Returns:
        Dict of kwargs for ``go.Scatterpolar()``.
    """
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    return dict(
        fill="toself",
        fillcolor=f"rgba({r}, {g}, {b}, {opacity})",
        line=dict(color=color, width=2),
        name=name,
    )


def radar_layout(title: str = "") -> dict:
    """Return Plotly layout for a radar/polar chart.

    Args:
        title: Chart title.

    Returns:
        Dict ready to be unpacked into ``fig.update_layout()``.
    """
    return base_layout(
        title=title,
        polar=dict(
            bgcolor=BG_TRANSPARENT,
            radialaxis=dict(visible=True, range=[0, 1], color=GRAY_MID),
            angularaxis=dict(color=TEXT_PRIMARY),
        ),
        showlegend=True,
    )


# ---------------------------------------------------------------------------
# CSS injection for Premium styling
# ---------------------------------------------------------------------------

PREMIUM_CSS: str = """
<style>
    /* Subtle gradient on main header area */
    [data-testid="stAppViewContainer"] > .main {
        background: linear-gradient(180deg, #0F1A12 0%, #0A0A0A 300px);
    }

    /* Glassmorphism for bordered containers */
    [data-testid="stVerticalBlock"] [data-testid="stContainer"][data-border="true"] {
        background: rgba(20, 20, 20, 0.6) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
    }

    /* Subtle glow on primary buttons */
    [data-testid="stBaseButton-primary"] {
        box-shadow: 0 0 20px rgba(29, 185, 84, 0.25);
        transition: box-shadow 0.3s ease;
    }
    [data-testid="stBaseButton-primary"]:hover {
        box-shadow: 0 0 30px rgba(29, 185, 84, 0.4);
    }

    /* Metric cards: subtle left accent */
    [data-testid="stMetric"] {
        border-left: 3px solid rgba(29, 185, 84, 0.3) !important;
        padding-left: 12px !important;
    }

    /* Smoother sidebar transition */
    [data-testid="stSidebar"] {
        border-right: 1px solid rgba(255, 255, 255, 0.04);
    }

    /* Plotly charts: remove extra padding */
    .stPlotlyChart {
        border-radius: 0.75rem;
    }
</style>
"""


def inject_premium_css() -> None:
    """Inject the Premium CSS into the current Streamlit page.

    Call once at the top of each page, after ``st.set_page_config()``.
    """
    import streamlit as st
    st.html(PREMIUM_CSS)
