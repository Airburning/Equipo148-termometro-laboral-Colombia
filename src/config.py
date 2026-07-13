"""Rutas centrales del proyecto. Todos los scripts de src/ importan de aquí
en vez de calcular sus propias rutas, para que mover o renombrar carpetas
solo implique editar este archivo.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = REPO_ROOT / "data" / "01_raw"
INTERMEDIATE_DIR = REPO_ROOT / "data" / "02_intermediate"
PRIMARY_DIR = REPO_ROOT / "data" / "03_primary"
MODEL_OUTPUT_DIR = REPO_ROOT / "data" / "04_model_output"
MODELS_DIR = REPO_ROOT / "models"
REPORTS_DIR = REPO_ROOT / "reports"

for _dir in (INTERMEDIATE_DIR, PRIMARY_DIR, MODEL_OUTPUT_DIR, MODELS_DIR, REPORTS_DIR / "figures"):
    _dir.mkdir(parents=True, exist_ok=True)
