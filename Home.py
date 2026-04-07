import streamlit as st

from src.data_loader import get_global_dataframe
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
    from src.spotify_client import _get_oauth_manager
    oauth = _get_oauth_manager()
    try:
        oauth.get_access_token(st.query_params["code"], as_dict=False)
    except Exception:
        pass
    st.query_params.clear()
    st.switch_page("pages/2_Mi_Perfil.py")

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

df, match_rate = get_global_dataframe()
has_year: bool = "year" in df.columns

# ---------------------------------------------------------------------------
# Auth check (non-blocking)
# ---------------------------------------------------------------------------

from src.spotify_client import get_spotify_client_silent, fetch_user_profile, fetch_currently_playing

sp = get_spotify_client_silent()
profile: dict | None = None
currently_playing: dict | None = None

if sp is not None:
    try:
        profile = fetch_user_profile(sp)
    except Exception:
        profile = None
    try:
        currently_playing = fetch_currently_playing(sp)
    except Exception:
        currently_playing = None

is_authenticated: bool = sp is not None and profile is not None

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
# Currently Playing embed (authenticated only)
# ---------------------------------------------------------------------------

if is_authenticated and currently_playing:
    with st.container(border=True):
        cp_col_info, cp_col_embed = st.columns([1, 2])
        with cp_col_info:
            st.caption(":material/play_circle: ESCUCHANDO AHORA")
            st.markdown(f"### {currently_playing['track_name']}")
            st.caption(f"{currently_playing['artist']} — {currently_playing['album']}")
        with cp_col_embed:
            track_id = currently_playing.get("track_id", "")
            if track_id:
                embed_html = (
                    f'<iframe src="https://open.spotify.com/embed/track/{track_id}'
                    f'?theme=0" width="100%" height="152" frameBorder="0" '
                    f'allow="autoplay; clipboard-write; encrypted-media; '
                    f'fullscreen; picture-in-picture" loading="lazy" '
                    f'style="border-radius:12px"></iframe>'
                )
                st.html(embed_html)
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
# Navigation cards
# ---------------------------------------------------------------------------

st.space("medium")

if is_authenticated:
    # 4 cards: Global, Mi Perfil, Mis Playlists, Now Playing
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        with st.container(border=True):
            st.markdown(":material/public: **Global**")
            st.caption("114k+ tracks: géneros, audio features, tendencias por década.")
            st.page_link("pages/1_Global.py", label="Explorar", icon=":material/arrow_forward:")
    with col2:
        with st.container(border=True):
            st.markdown(":material/person: **Mi Perfil**")
            st.caption("Tu ADN musical, top artistas y canciones guardadas.")
            st.page_link("pages/2_Mi_Perfil.py", label="Ver perfil", icon=":material/arrow_forward:")
    with col3:
        with st.container(border=True):
            st.markdown(":material/queue_music: **Mis Playlists**")
            st.caption("Analiza y compara tus playlists propias.")
            st.page_link("pages/3_Mis_Playlists.py", label="Analizar", icon=":material/arrow_forward:")
    with col4:
        with st.container(border=True):
            st.markdown(":material/headphones: **Now Playing**")
            st.caption("Reproductor, cola y análisis de escuchas recientes.")
            st.page_link("pages/4_Now_Playing.py", label="Reproducir", icon=":material/arrow_forward:")
else:
    # 2 cards: Global (active) + personal (locked)
    col_g, col_p = st.columns(2)
    with col_g:
        with st.container(border=True):
            st.markdown(":material/public: **Global**")
            st.caption("Explora 114k+ tracks: géneros, audio features, tendencias por década.")
            st.page_link("pages/1_Global.py", label="Ir a Global", icon=":material/arrow_forward:")
    with col_p:
        with st.container(border=True):
            st.markdown(":material/lock: **Funciones personales**")
            st.caption(
                "Conecta tu cuenta de Spotify para desbloquear "
                "Mi Perfil, Playlists y Now Playing."
            )
            st.page_link("pages/2_Mi_Perfil.py", label="Conectar Spotify", icon=":material/link:")
