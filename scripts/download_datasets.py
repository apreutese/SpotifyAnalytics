"""One-shot script: download HF parquet + Kaggle CSV to data/.

Usage:
    python scripts/download_datasets.py
"""

import sys
from pathlib import Path

import pandas as pd

# Ensure project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"

HF_PARQUET_URL: str = (
    "https://huggingface.co/datasets/maharshipandya/"
    "spotify-tracks-dataset/resolve/refs%2Fconvert%2Fparquet/"
    "default/train/0000.parquet"
)
HF_LOCAL_PATH: Path = DATA_DIR / "hf_tracks.csv"


def download_hf() -> None:
    """Download HuggingFace Spotify tracks as CSV to data/."""
    if HF_LOCAL_PATH.exists():
        print(f"[HF] Ya existe: {HF_LOCAL_PATH} ({HF_LOCAL_PATH.stat().st_size:,} bytes)")
        resp = input("¿Reemplazar? (s/N): ").strip().lower()
        if resp != "s":
            print("[HF] Saltando descarga.")
            return

    print(f"[HF] Descargando desde {HF_PARQUET_URL} y convirtiendo a CSV…")
    df = pd.read_parquet(HF_PARQUET_URL)
    df.to_csv(HF_LOCAL_PATH, index=False)
    print(f"[HF] Guardado en {HF_LOCAL_PATH} — {len(df):,} filas, {HF_LOCAL_PATH.stat().st_size:,} bytes")


def main() -> None:
    """Download all datasets."""
    DATA_DIR.mkdir(exist_ok=True)

    download_hf()

    kaggle_tracks = DATA_DIR / "kaggle_tracks.csv"
    kaggle_artists = DATA_DIR / "kaggle_artists.csv"

    print("\n[Kaggle] Descarga manual desde:")
    print("  https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks")
    print("Copia los archivos así:")
    print(f"  tracks.csv  → {kaggle_tracks}")
    print(f"  artists.csv → {kaggle_artists}")
    print(f"  (dict_artists.json no es necesario)")

    if kaggle_tracks.exists():
        print(f"  ✓ kaggle_tracks.csv ya existe")
    else:
        print(f"  ✗ kaggle_tracks.csv no encontrado")

    if kaggle_artists.exists():
        print(f"  ✓ kaggle_artists.csv ya existe")
    else:
        print(f"  ✗ kaggle_artists.csv no encontrado")

    print("\n✓ Descarga completa.")


if __name__ == "__main__":
    main()
