import streamlit as st

from src.data_loader import get_global_dataframe
from src.personal_loader import has_personal_data
from src.theme import inject_premium_css
from src.sidebar import render_sidebar_player

st.set_page_config(
    page_title="SpotifyAnalytics",
    page_icon=":material/music_note:",
    layout="wide",
)
inject_premium_css()

# ---------------------------------------------------------------------------
# OAuth redirect handler
# ---------------------------------------------------------------------------

if "code" in st.query_params:
    from src.spotify_auth import _get_oauth_manager
    oauth = _get_oauth_manager()
    try:
        oauth.get_access_token(st.query_params["code"], as_dict=False)
    except Exception:
        pass
    st.query_params.clear()
    st.switch_page("pages/3_Mi_Perfil.py")

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

df, match_rate = get_global_dataframe()
has_year: bool = "year" in df.columns

# ---------------------------------------------------------------------------
# Auth check (non-blocking)
# ---------------------------------------------------------------------------

from src.spotify_auth import get_spotify_client_silent
from src.spotify_data import fetch_user_profile

sp = get_spotify_client_silent()
profile: dict | None = None

if sp is not None:
    try:
        profile = fetch_user_profile(sp)
    except Exception:
        profile = None

is_authenticated: bool = sp is not None and profile is not None
has_csv_personal: bool = has_personal_data()

# Sidebar mini-player (only if authenticated)
if is_authenticated:
    render_sidebar_player(sp)

# ---------------------------------------------------------------------------
# Header — personalised greeting or generic title
# ---------------------------------------------------------------------------

if is_authenticated:
    col_avatar, col_greeting = st.columns([1, 11])
    with col_avatar:
        if profile.get("image_url"):
            st.image(profile["image_url"], width=72)
        else:
            st.markdown("### :material/person:")
    with col_greeting:
        st.title(f"Hola, {profile['display_name']}")
        st.caption("Bienvenido a tu dashboard de análisis musical")
else:
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
        st.caption(f":material/check_circle: Merge HF + Kaggle exitoso — {pct:.1f}% de tracks con año.")
    else:
        st.caption(
            f":material/warning: Merge HF + Kaggle: solo {pct:.1f}% de coincidencia "
            "(< 10%) — columna año descartada."
        )
else:
    st.caption(":material/info: Dataset Kaggle no encontrado — funcionando solo con HuggingFace.")

# ---------------------------------------------------------------------------
# Navigation cards — two blocks: CSV (offline) vs Spotify API (OAuth)
# ---------------------------------------------------------------------------

st.space("medium")

# Block 1: CSV-based (always available)
st.subheader(":material/storage: Datos locales (CSV)")
st.caption("Disponibles sin conexión a Spotify.")

col_csv1, col_csv2 = st.columns(2)
with col_csv1:
    with st.container(border=True):
        st.markdown(":material/public: **Global**")
        st.caption("114k+ tracks: géneros, audio features, tendencias por década.")
        st.page_link("pages/1_Global.py", label="Explorar", icon=":material/arrow_forward:")
with col_csv2:
    with st.container(border=True):
        st.markdown(":material/person: **Demo Perfil Spotify**")
        if has_csv_personal:
            st.caption("Tu ADN musical, top artistas y canciones guardadas (snapshot).")
            st.page_link("pages/2_Demo_Perfil_Spotify.py", label="Ver perfil", icon=":material/arrow_forward:")
        else:
            st.caption(
                "Genera tus CSVs personales con "
                "`python scripts/export_personal_data.py`."
            )
            st.page_link("pages/2_Demo_Perfil_Spotify.py", label="Ver demo", icon=":material/arrow_forward:")

st.space("small")

# Block 2: Spotify API (requires OAuth)
st.subheader(":material/cloud: Spotify en vivo (OAuth)")

if is_authenticated:
    st.caption(f"Conectado como **{profile['display_name']}**.")
    col_api0, col_api1, col_api2 = st.columns(3)
    with col_api0:
        with st.container(border=True):
            st.markdown(":material/person: **Mi Perfil**")
            st.caption("Tu ADN musical, top artistas y tracks en tiempo real.")
            st.page_link("pages/3_Mi_Perfil.py", label="Ver perfil", icon=":material/arrow_forward:")
    with col_api1:
        with st.container(border=True):
            st.markdown(":material/queue_music: **Mis Playlists**")
            st.caption("Analiza y compara tus playlists en tiempo real.")
            st.page_link("pages/4_Mis_Playlists.py", label="Analizar", icon=":material/arrow_forward:")
    with col_api2:
        with st.container(border=True):
            st.markdown(":material/headphones: **Now Playing**")
            st.caption("Reproductor, cola y análisis de escuchas recientes.")
            st.page_link("pages/5_Now_Playing.py", label="Reproducir", icon=":material/arrow_forward:")
else:
    st.caption(
        ":material/lock: Conecta tu cuenta de Spotify para acceder a "
        "Mi Perfil, Mis Playlists y Now Playing."
    )
    col_api0, col_api1, col_api2 = st.columns(3)
    with col_api0:
        with st.container(border=True):
            st.markdown(":material/person: **Mi Perfil**")
            st.caption("Requiere conectar tu cuenta de Spotify.")
            st.page_link("pages/3_Mi_Perfil.py", label="Conectar", icon=":material/link:")
    with col_api1:
        with st.container(border=True):
            st.markdown(":material/queue_music: **Mis Playlists**")
            st.caption("Requiere conectar tu cuenta de Spotify.")
            st.page_link("pages/4_Mis_Playlists.py", label="Conectar", icon=":material/link:")
    with col_api2:
        with st.container(border=True):
            st.markdown(":material/headphones: **Now Playing**")
            st.caption("Requiere conectar tu cuenta de Spotify.")
            st.page_link("pages/5_Now_Playing.py", label="Conectar", icon=":material/link:")
