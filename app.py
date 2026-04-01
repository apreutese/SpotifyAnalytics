import streamlit as st

from src.data_loader import get_global_dataframe

st.set_page_config(
    page_title="SpotifyAnalytics",
    page_icon=":material/music_note:",
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

st.title(":material/music_note: SpotifyAnalytics")
st.caption(
    "Dashboard de análisis de datos musicales de Spotify. "
    "Combina datos globales (HuggingFace + Kaggle) con datos personales "
    "de tu cuenta de Spotify."
)

st.space("small")

# ---------------------------------------------------------------------------
# Dataset metrics
# ---------------------------------------------------------------------------

st.subheader(":material/analytics: Resumen del dataset")

with st.container(horizontal=True):
    st.metric("Tracks", f"{len(df):,}", border=True)
    st.metric("Artistas", f"{df['artist'].nunique():,}", border=True)
    st.metric("Géneros", f"{df['genre'].nunique():,}", border=True)
    if has_year:
        year_min = int(df["year"].dropna().min())
        year_max = int(df["year"].dropna().max())
        st.metric("Rango temporal", f"{year_min} – {year_max}", border=True)
    else:
        st.metric("Rango temporal", "No disponible", border=True)

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

st.space("medium")

col_g, col_p = st.columns(2)
with col_g:
    with st.container(border=True):
        st.subheader(":material/public: Global")
        st.caption("Explora 114k+ tracks: géneros, audio features, tendencias por década.")
        st.page_link("pages/1_Global.py", label="Ir a Global", icon=":material/arrow_forward:")
with col_p:
    with st.container(border=True):
        st.subheader(":material/person: Mi Perfil")
        st.caption("Conecta tu cuenta de Spotify y descubre tu ADN musical.")
        st.page_link("pages/2_Mi_Perfil.py", label="Ir a Mi Perfil", icon=":material/arrow_forward:")
