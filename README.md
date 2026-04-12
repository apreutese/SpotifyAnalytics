# SpotifyAnalytics

Dashboard interactivo con gráficas y métricas sobre datos musicales de Spotify. Trabaja con dos datasets públicos combinados (+114 000 canciones), un perfil de demostración exportado en CSV y la opción de conectar tu propia cuenta de Spotify para analizar tus datos reales.

**Proyecto académico P05** — Digitalización aplicada a los sectores productivos (1º DAM).

## Qué hace

La app tiene 5 páginas principales:

| Página | Descripción |
|--------|-------------|
| **Global** | Análisis del dataset global: géneros, popularidad, audio features y distribución por décadas. Incluye filtros y un reproductor con las 100 canciones más populares. |
| **Demo Perfil** | Versión de demostración del perfil personal. Usa datos precargados (CSV) para mostrar los KPIs sin necesidad de iniciar sesión. |
| **Mi Perfil** | Tu perfil real de Spotify. Muestra tus canciones guardadas, top artistas, décadas favoritas, ratio explicit/clean y álbumes más repetidos. Requiere iniciar sesión con OAuth. |
| **Mis Playlists** | Análisis individual de tus playlists (décadas, explicit, álbumes, timeline) y un comparador entre dos playlists con artistas en común. |
| **Now Playing** | Reproductor en tiempo real con el Spotify Web Playback SDK. Muestra la canción actual, historial reciente y cola de reproducción. |

## Requisitos

- Python 3.12+

Las páginas **Global** y **Demo Perfil** funcionan sin cuenta de Spotify.
Para usar **Mi Perfil**, **Mis Playlists** y **Now Playing** necesitas:

- Una cuenta de Spotify (Premium recomendado para el reproductor)
- Credenciales de [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)

## Instalación

```bash
git clone https://github.com/apreutese/SpotifyAnalytics.git
cd SpotifyAnalytics

python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

## Configuración (opcional)

> Solo necesario si quieres conectar tu cuenta de Spotify. Sin esto, las páginas Global y Demo Perfil funcionan igualmente.

1. Copia `.env.example` a `.env` y rellena tus credenciales:

   ```
   SPOTIFY_CLIENT_ID=tu_client_id
   SPOTIFY_CLIENT_SECRET=tu_client_secret
   SPOTIFY_REDIRECT_URI=http://127.0.0.1:8501
   ```

2. En el [Spotify Developer Dashboard](https://developer.spotify.com/dashboard), añade `http://127.0.0.1:8501` como **Redirect URI** en tu app.

## Cómo ejecutar

```bash
streamlit run Home.py
```

Se abre en `http://localhost:8501`. Si has configurado las credenciales, pulsa "Conectar con Spotify" en las páginas que lo requieran.

## Estructura

```
SpotifyAnalytics/
├── Home.py                          # Página de inicio
├── auth.py                          # Login por terminal (backup)
├── pages/
│   ├── 1_Global.py
│   ├── 2_Demo_Perfil_Spotify.py
│   ├── 3_Mi_Perfil.py
│   ├── 4_Mis_Playlists.py
│   └── 5_Now_Playing.py
├── src/
│   ├── data_loader.py               # Carga de datasets (HF + Kaggle)
│   ├── spotify_auth.py              # OAuth y gestión de tokens
│   ├── spotify_data.py              # Llamadas a la API de Spotify
│   ├── kpis_global.py               # KPIs globales
│   ├── kpis_personal.py             # KPIs personales
│   ├── kpis_playlists.py            # KPIs de playlists
│   ├── charts_global.py             # Gráficos globales
│   ├── charts_personal.py           # Gráficos personales
│   ├── charts_playlists.py          # Gráficos de playlists
│   ├── personal_loader.py           # Carga de CSVs personales
│   ├── sidebar.py                   # Sidebar con reproductor
│   ├── spotify_player.py            # Reproductor SDK
│   ├── theme.py                     # Estilos y colores
│   └── components/
│       └── playlist_player.py       # Componente de lista de reproducción
├── data/                            # Datasets locales (CSV)
├── .streamlit/config.toml           # Tema visual (colores Spotify)
├── .env.example                     # Plantilla de credenciales
└── requirements.txt
```

## Tecnologías

- **Streamlit** — Interfaz web
- **Pandas** — Manejo de datos
- **Plotly** — Gráficos interactivos
- **Spotipy** — Conexión con Spotify
- **python-dotenv** — Variables de entorno
