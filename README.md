# SpotifyAnalytics

Dashboard multipage en Streamlit para analizar datos musicales de Spotify. Combina datos globales (HuggingFace + Kaggle) con datos personales (Spotify Web API).

**Proyecto académico P05** — Digitalización aplicada a los sectores productivos (DAM 1º).

## Fuentes de datos

| Fuente | Método | Datos |
|--------|--------|-------|
| **HuggingFace** | Descarga automática (parquet HTTP) | 114k tracks con audio features y género |
| **Kaggle** | Descarga automática (kagglehub API) | 600k tracks con año de lanzamiento |
| **Spotify Web API** | OAuth con Spotipy | Liked songs, top artists, géneros de artista |

## Requisitos

- Python 3.12+
- Cuenta de Spotify con **Premium** (requerido para Development Mode desde Feb 2026)
- Credenciales de Spotify Developer Dashboard
- Credenciales de Kaggle API (opcional, para descarga automática)

## Instalación

```bash
# Clonar el repositorio
git clone <url-del-repo>
cd SpotifyAnalytics

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

1. Copia `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```

2. Rellena las credenciales en `.env`:
   - **Spotify**: Obtén `Client ID` y `Client Secret` en [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - **Kaggle** (opcional): Genera tu API key en [Kaggle Settings](https://www.kaggle.com/settings) → API → Create New Token

3. En el Spotify Developer Dashboard, añade `http://127.0.0.1:8501` como Redirect URI.

## Uso

```bash
streamlit run app.py
```

La app se abrirá en `http://localhost:8501`.

### Páginas

- **Home**: Resumen del dataset global con métricas clave.
- **Global**: 4 KPIs con gráficos interactivos Plotly y filtros (género, popularidad, año, explicit).
- **Mi Perfil**: Conecta tu cuenta de Spotify y visualiza tus estadísticas personales (4 KPIs).

## KPIs

### Globales
| KPI | Descripción | Gráfico |
|-----|-------------|---------|
| G1 | Top géneros por número de tracks | Treemap |
| G2 | ADN musical por género (audio features) | Radar |
| G3 | Correlación popularidad vs audio features | Heatmap |
| G4 | Sentimiento musical por década / Distribución de popularidad | Area / Bar |

### Personales
| KPI | Descripción | Gráfico |
|-----|-------------|---------|
| P1 | Mis géneros (de artistas guardados) | Treemap |
| P2 | Timeline de canciones guardadas | Area |
| P3 | Mi ADN musical / Distribución de géneros | Radar / Donut |
| P4 | Mis top artistas | Bar horizontal |

## Estructura del proyecto

```
SpotifyAnalytics/
├── app.py                    # Home
├── pages/
│   ├── 1_Global.py           # Página Global
│   └── 2_Mi_Perfil.py        # Página Personal
├── src/
│   ├── data_loader.py        # Pipeline de datos: HF + Kaggle
│   ├── spotify_client.py     # OAuth + fetch datos Spotify
│   ├── kpis_global.py        # Cálculos KPI globales
│   ├── kpis_personal.py      # Cálculos KPI personales
│   ├── charts_global.py      # Gráficos Plotly globales
│   └── charts_personal.py    # Gráficos Plotly personales
├── auth.py                   # Script backup OAuth
├── data/                     # Datasets locales (gitignored)
├── .streamlit/config.toml    # Tema Spotify
├── .env.example              # Template de credenciales
└── requirements.txt          # Dependencias
```

## Tecnologías

- **Streamlit** — Framework de dashboard
- **Pandas** — Manipulación de datos
- **Plotly** — Gráficos interactivos
- **Spotipy** — Spotify Web API
- **kagglehub** — Descarga automática de datasets Kaggle
- **PyArrow** — Lectura de archivos parquet
