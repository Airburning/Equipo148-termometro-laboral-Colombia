# Changelog

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/).

## [1.1.0] - 2026-07-13

### Added
- Reestructuración completa del repositorio al layout estándar
  (`data/01_raw..04_model_output`, `src/`, `pipelines/`, `app/`,
  `models/`, `reports/`, `notebooks/`, `tests/`, `docs/`, `RECURSOS/`,
  `.github/workflows/`), preparado para publicarse en GitHub.
- `src/config.py` centraliza todas las rutas del proyecto.
- `src/generate_figures.py`: genera `reports/figures/*.png` (histórico
  de TD, correlaciones, comparación de modelos, real vs. predicho,
  importancia de variables) a partir de los datos reales.
- `notebooks/01..05`: exploración, limpieza, análisis descriptivo,
  modelado y reportes, ejecutables de punta a punta.
- `tests/test_data_quality.py` y `tests/test_model_inference.py` (9
  pruebas) + `.github/workflows/ci.yml` corriéndolas en cada push/PR.
- `docs/`: planteamiento del problema, marco metodológico (CRISP-ML),
  fuentes de datos, arquitectura, diccionario de datos, conclusiones y
  guía de validación para pares.
- 3 fuentes de datos nuevas integradas al modelo (antes el pipeline solo
  usaba 3 de las 6 disponibles):
  - EMICRON (informalidad de micronegocios, nacional, 2024).
  - Dispersión regional de TD entre departamentos (`Mercado laboral por
    departamentos.zip`, 2007-2025).
  - Informalidad laboral real por región, calculada del microdato GEIH
    persona-mes (antes solo existía un proxy nacional).
- Archivos crudos pesados comprimidos con gzip para caber en GitHub sin
  Git LFS (`GEIH_consolidado_2022_2026.csv`: 409MB → 44MB;
  `EMICRON_2024_consolidado.csv`: 42MB → 7MB).

### Changed
- `FEATURES` en el modelo pasó de 22 a 28 variables. El mejor modelo pasó
  de Random Forest (MAE 0.837, R² 0.780) a XGBoost (MAE 0.818, R² 0.743)
  — ver `docs/conclusiones.md` para el análisis honesto de este
  trade-off (mejora leve de MAE, con un costo de R² en un panel pequeño).
- `run_all.py` se convirtió en `pipelines/pipeline_ml.py` (11 pasos en
  vez de 8), con imports actualizados a la nueva ubicación de los
  scripts en `src/`.
- La app de escritorio y el dashboard web (antes en la raíz del
  proyecto) se movieron a `app/`; el HTML generado pasó de `reporte.html`
  a `reports/reporte_final.html`.
- `requirements.txt`: se agregó `xlrd` (necesario para leer los `.xls`
  de la fuente de dispersión regional, faltaba y hubiera fallado en un
  PC nuevo) y, como dependencias de desarrollo, `jupyter` y `pytest`.

## [1.0.0] - 2026-07-10

### Added
- Primera versión funcional del pipeline: 3 fuentes DANE (GEIH Reportes
  Regionales, GEIH-ANEXOS, IMIE) combinadas en un panel región-semestre,
  5 modelos comparados contra un baseline ingenuo, app de escritorio
  (`dashboard_app.py`) y dashboard web (`reporte.html`) generados por el
  mismo pipeline (`run_all.py`).
