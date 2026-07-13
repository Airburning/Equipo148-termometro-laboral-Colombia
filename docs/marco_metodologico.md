# Marco metodológico (CRISP-ML)

El proyecto sigue las fases de **CRISP-ML(Q)** (la extensión de CRISP-DM
para machine learning). Cada fase se mapea a artefactos concretos del
repo, no es solo teoría:

## 1. Entendimiento del negocio y los datos

- Objetivo y alcance: `docs/planteamiento_problema.md`.
- Fuentes disponibles y su cobertura real (qué tan confiables/completas
  son): `docs/fuentes_datos.md`.
- Exploración inicial: `notebooks/01_EDA_exploracion_datos.ipynb` y
  `notebooks/02_limpieza_transformacion.ipynb`.

## 2. Preparación de datos

Seis fuentes oficiales del DANE, cada una con su propio extractor en
`src/` (`extract_geih_regional.py`, `extract_geih_anexos.py`,
`extract_imie.py`, `extract_emicron.py`, `extract_departamentos.py`,
`extract_geih_informalidad_regional.py`), que dejan un CSV limpio por
fuente en `data/02_intermediate/`.

`src/build_dataset.py` las combina en un panel único
**región × semestre** (`data/03_primary/panel_final.csv`):

- Homologa granularidades: hay fuentes semestrales, trimestrales,
  anuales y mensuales — todas se llevan a semestre.
- Rellena (forward/backward fill) las fuentes que no cubren todo el rango
  2010-2025, y marca con una columna `_obs` si el dato de cada fila es
  real o rellenado (transparencia sobre qué tan "real" es cada número).
- Construye las features de historia reciente: rezagos (`_lag1`,
  `_lag2`), promedios móviles (`_roll4`), estacionalidad (`periodo_II`),
  tendencia (`year_trend`) y dummies de región.

Ver el detalle completo en `docs/data_dictionary.md`.

## 3. Modelado

`src/train_model.py` entrena y compara 5 algoritmos (regresión lineal,
Ridge, Random Forest, Gradient Boosting, XGBoost) contra un baseline
ingenuo (*random walk*: "la TD del próximo semestre es igual a la
actual").

### El truco: predecir el cambio, no el nivel

La TD tiene una tendencia estructural fuerte (cayó de ~20% en 2010 a ~8%
en 2025). Los modelos de árboles **no extrapolan bien fuera del rango que
vieron en entrenamiento**: si entrenaron con TD entre 8% y 20% y el futuro
real cae a 6%, un árbol no sabe predecir por debajo de lo que ya vio.

La solución: el target de entrenamiento no es el nivel de TD del
siguiente semestre, sino el **cambio** (`td_siguiente − td_actual`), que
es mucho más estacionario. El nivel se reconstruye sumando el cambio
predicho al valor actual.

### Validación temporal, no aleatoria

- **Split**: entrenamiento = semestres antes de 2023; prueba = 2023 en
  adelante. Nunca se mezclan al azar, para no filtrar información del
  futuro hacia el pasado.
- **Validación cruzada**: `TimeSeriesSplit` (5 folds), que respeta el
  orden temporal dentro del set de entrenamiento.

## 4. Evaluación

Métricas: MAE, RMSE y R² sobre el nivel de TD reconstruido (no sobre el
cambio), comparadas siempre contra el baseline ingenuo — un modelo que
"gana" pero pierde contra el random walk no aporta nada. Resultados
completos y su interpretación en `docs/conclusiones.md` y
`data/04_model_output/metrics.json`.

## 5. Despliegue

Dos formas de consumir el resultado, generadas por el mismo pipeline:

- **App de escritorio** (`app/dashboard_app.py`): ventana nativa estilo
  Power BI, con filtros por región y 6 páginas (histórico, modelos, real
  vs. predicho, variables, proyección, datos crudos).
- **Dashboard web autocontenido** (`reports/reporte_final.html`): mismo
  contenido, sin necesidad de instalar Python, abrible en cualquier
  navegador.

`pipelines/pipeline_ml.py` corre las 12 etapas de punta a punta con un
solo comando (ver `README.md`).

## 6. Monitoreo (calidad continua)

- `tests/test_data_quality.py`: rangos plausibles, sin duplicados,
  regiones esperadas, flags `_obs` binarios.
- `tests/test_model_inference.py`: el modelo carga, sus features existen
  en el panel, y sus predicciones caen en un rango realista.
- `.github/workflows/ci.yml`: corre `pytest` automáticamente en cada
  push/PR.

Ver `docs/validacion_guide.md` para la guía paso a paso pensada para
que un par (no el autor original) reproduzca y valide los resultados.
