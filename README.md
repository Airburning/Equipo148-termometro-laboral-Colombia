# Termómetro laboral regional de Colombia

Modelo de machine learning que proyecta la **Tasa de Desocupación (TD)**
del siguiente semestre, por región, combinando **6 fuentes oficiales del
DANE**. Incluye una app de escritorio estilo Power BI y un dashboard web
autocontenido, ambos alimentados por el mismo pipeline reproducible.

## Ficha técnica

| | |
|---|---|
| **Problema** | Forecasting a un paso de la TD por región (Caribe, Central, Oriental, Orinoquía/Amazonía/Insular, Pacífica) |
| **Unidad de análisis** | Región × semestre (2010-2025), 160 filas |
| **Fuentes** | 6 fuentes DANE — ver `docs/fuentes_datos.md` |
| **Features** | 28 variables: rezagos, promedios móviles, estacionalidad, tendencia, informalidad (laboral/empresarial/micronegocios), dispersión regional — ver `docs/data_dictionary.md` |
| **Modelos comparados** | Regresión lineal, Ridge, Random Forest, Gradient Boosting, XGBoost, vs. baseline ingenuo (random walk) |
| **Mejor modelo** | XGBoost — MAE 0.82 p.p. de TD, R² 0.74 en test (2023 en adelante) — ver `docs/conclusiones.md` |
| **Validación** | Split temporal (train < 2023, test ≥ 2023) + `TimeSeriesSplit` en CV, para evitar fuga de información hacia el pasado |
| **Licencia del código** | MIT (`LICENSE`) |
| **Licencia de los datos** | Públicos, DANE / datos.gov.co — ver `docs/fuentes_datos.md` |

## Inicio rápido

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Regenera todo desde las 6 fuentes crudas (data/01_raw/):
python pipelines/pipeline_ml.py
```

Esto deja:
- `reports/reporte_final.html` — dashboard web, ábrelo con doble clic.
- `reports/figures/*.png` — gráficos estáticos del análisis.
- `data/04_model_output/metrics.json` — métricas de los 5 modelos.
- `models/best_model_*.joblib` — el modelo ganador, serializado.

### En Windows, sin usar la terminal

Doble clic en orden: `1_Instalar.bat` (una vez) → `3_Actualizar_Datos.bat`
→ `2_Abrir_App.bat` (la app de escritorio). Los 3 se autolocalizan: no
importa a qué PC, usuario o carpeta muevas el repositorio completo.

## Estructura del repositorio

```
.
├── RECURSOS/                 # Material visual (presentación, portada)
├── docs/                     # Documentación técnica (ver índice abajo)
├── data/
│   ├── 01_raw/               # Las 6 fuentes DANE tal como se descargaron
│   │                         # (2 comprimidas con gzip para caber en GitHub)
│   ├── 02_intermediate/      # Una fuente ya limpia, sin combinar (src/extract_*.py)
│   ├── 03_primary/           # panel_final.csv — el panel único integrado
│   └── 04_model_output/      # Métricas, predicciones, proyección, report_data.json
├── notebooks/                # Exploración, limpieza, análisis, modelo, reportes
├── src/                      # Pipeline modular (config, extractores, modelo)
├── models/                   # Modelo entrenado serializado (.joblib)
├── reports/                  # reporte_final.html + figures/*.png
├── tests/                    # pytest: calidad de datos + inferencia del modelo
├── pipelines/                # pipeline_ml.py — corre todo de punta a punta
├── app/                      # App de escritorio (PyQt6) + plantilla del dashboard web
└── .github/workflows/        # CI: corre pytest en cada push/PR
```

Ver `docs/architecture.md` para el diagrama de flujo completo (qué script
lee qué archivo y escribe qué otro).

## Documentación

| Documento | Contenido |
|---|---|
| `docs/planteamiento_problema.md` | Qué problema resuelve, para quién, y qué no hace |
| `docs/marco_metodologico.md` | CRISP-ML aplicado a este proyecto, paso a paso |
| `docs/fuentes_datos.md` | Las 6 fuentes, su cobertura real y sus advertencias |
| `docs/architecture.md` | Diagrama de flujo e integración de fuentes |
| `docs/data_dictionary.md` | Todas las columnas de `panel_final.csv` explicadas |
| `docs/conclusiones.md` | Resultados, qué variables importan, limitaciones |
| `docs/validacion_guide.md` | Guía para que un par reproduzca y valide todo en ~15 min |

## Correr las pruebas

```bash
python -m pytest tests/ -v
```

## Notas sobre los datos crudos

`GEIH_consolidado_2022_2026.csv` (~430MB) y
`EMICRON_2024_consolidado.csv` (~42MB) se subieron comprimidos con
`gzip -9` (`.csv.gz`, ~44MB y ~7MB) para no superar el límite de 100MB
por archivo de GitHub, sin necesidad de Git LFS. `pandas.read_csv` los
lee de forma transparente por la extensión `.gz` — ningún script tiene
que descomprimirlos manualmente.

## Autoría

Proyecto de **Equipo148**. Contribuciones y correcciones son bienvenidas
vía pull request.
