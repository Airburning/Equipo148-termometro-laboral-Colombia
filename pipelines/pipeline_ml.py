"""Reconstruye todo el pipeline en orden, de punta a punta:

   1. extract_geih_regional.py              -> data/02_intermediate/geih_regional_panel.csv
   2. extract_geih_anexos.py                 -> data/02_intermediate/informalidad_laboral_nacional.csv
   3. extract_imie.py                        -> data/02_intermediate/informalidad_empresarial_nacional.csv
   4. extract_emicron.py                     -> data/02_intermediate/informalidad_micronegocios_nacional.csv
   5. extract_departamentos.py               -> data/02_intermediate/td_dispersion_regional.csv
   6. extract_geih_informalidad_regional.py  -> data/02_intermediate/informalidad_laboral_regional.csv
   7. build_dataset.py                       -> data/03_primary/panel_final.csv
   8. train_model.py                         -> models/*.joblib, data/04_model_output/metrics.json, etc.
   9. forecast_next.py                       -> data/04_model_output/forecast_next_period.csv
  10. export_report_data.py                  -> data/04_model_output/report_data.json
  11. generate_figures.py                    -> reports/figures/*.png
  12. build_dashboard.py (en app/)           -> reports/reporte_final.html

Uso:
    python pipelines/pipeline_ml.py

Requiere las 6 fuentes originales en data/01_raw/ (ver docs/fuentes_datos.md
y README.md). Todas las rutas se resuelven desde src/config.py, así que el
repo completo se puede clonar/copiar a cualquier PC y correr igual.
El paso 6 procesa un CSV de ~430MB (comprimido a ~44MB en el repo) en
chunks, así que puede tardar más que el resto.
"""
import importlib
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
APP_DIR = REPO_ROOT / "app"
sys.path.insert(0, str(SRC_DIR))
sys.path.insert(0, str(APP_DIR))

STEPS = [
    "extract_geih_regional",
    "extract_geih_anexos",
    "extract_imie",
    "extract_emicron",
    "extract_departamentos",
    "extract_geih_informalidad_regional",
    "build_dataset",
    "train_model",
    "forecast_next",
    "export_report_data",
    "generate_figures",
    "build_dashboard",
]


def main():
    for i, mod_name in enumerate(STEPS, 1):
        print(f"\n[{i}/{len(STEPS)}] {mod_name}.py")
        print("-" * 60)
        t0 = time.time()
        try:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "main"):
                mod.main()
        except Exception as exc:
            print(f"\nFALLÓ en el paso {i} ({mod_name}.py): {exc}")
            sys.exit(1)
        print(f"({time.time() - t0:.1f}s)")

    print("\nListo. Abre reports/reporte_final.html en cualquier navegador.")


if __name__ == "__main__":
    main()
