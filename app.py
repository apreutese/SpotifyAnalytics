import streamlit as st

from src.data_loader import get_global_dataframe

st.set_page_config(
    page_title="SpotifyAnalytics",
    page_icon="🎵",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

df, match_rate = get_global_dataframe()
has_year: bool = "year" in df.columns

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🎵 SpotifyAnalytics")
st.markdown(
    "Dashboard de análisis de datos musicales de Spotify. "
    "Combina datos globales (HuggingFace + Kaggle) con datos personales "
    "de tu cuenta de Spotify."
)

st.divider()

# ---------------------------------------------------------------------------
# Dataset metrics
# ---------------------------------------------------------------------------

st.subheader("📊 Resumen del dataset")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Tracks", f"{len(df):,}")
col2.metric("Artistas", f"{df['artist'].nunique():,}")
col3.metric("Géneros", f"{df['genre'].nunique():,}")

if has_year:
    year_min = int(df["year"].dropna().min())
    year_max = int(df["year"].dropna().max())
    col4.metric("Rango temporal", f"{year_min} – {year_max}")
else:
    col4.metric("Rango temporal", "No disponible")

# ---------------------------------------------------------------------------
# Merge info
# ---------------------------------------------------------------------------

if match_rate is not None:
    pct = match_rate * 100
    if has_year:
        st.caption(f"✅ Merge HF + Kaggle exitoso — {pct:.1f}% de tracks con año.")
    else:
        st.caption(
            f"⚠️ Merge HF + Kaggle: solo {pct:.1f}% de coincidencia "
            "(< 10%) — columna año descartada."
        )
else:
    st.caption("ℹ️ Dataset Kaggle no encontrado — funcionando solo con HuggingFace.")

# ---------------------------------------------------------------------------
# Navigation hint
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    "👈 Usa el **menú lateral** para navegar a las páginas "
    "**Global** o **Mi Perfil**."
)
