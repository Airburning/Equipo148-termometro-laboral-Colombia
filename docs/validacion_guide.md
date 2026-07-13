# Guía de validación para pares

Pensada para que alguien que **no** trabajó en el proyecto pueda
reproducir y verificar los resultados en menos de 15 minutos, sin tener
que leer todo el código primero.

## 1. Instalar y correr el pipeline completo

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python pipelines/pipeline_ml.py
```

Debe terminar imprimiendo `Listo. Abre reports/reporte_final.html en
cualquier navegador.` sin ningún `FALLÓ en el paso...`. Si el paso 6
(`extract_geih_informalidad_regional`) tarda, es normal — procesa ~3.7M
filas de microdato en chunks.

## 2. Correr las pruebas automáticas

```bash
pip install pytest
python -m pytest tests/ -v
```

Deben pasar 9 pruebas: rangos plausibles de las tasas, sin filas
duplicadas por región-semestre, regiones esperadas, flags `_obs`
binarios, dummies de región consistentes, y que el modelo cargue y
prediga en un rango realista (`tests/test_data_quality.py`,
`tests/test_model_inference.py`).

## 3. Verificar los números clave contra `docs/conclusiones.md`

```bash
python -c "import json; print(json.load(open('data/04_model_output/metrics.json'))['best_model'])"
cat data/04_model_output/metrics.json
```

El `best_model` y sus métricas (`test_mae`, `test_rmse`, `test_r2`) deben
coincidir con la tabla de `docs/conclusiones.md` (pequeñas diferencias de
milésimas son normales por no-determinismo de punto flotante entre
versiones de librerías; diferencias grandes sí ameritan investigar).

## 4. Revisar que el panel tiene sentido

Abre `notebooks/01_EDA_exploracion_datos.ipynb` y
`notebooks/03_analisis_descriptivo.ipynb` — deberías ver:

- TD cayendo de forma sostenida entre 2010 y 2025 en las 5 regiones.
- TD del semestre II sistemáticamente distinta a la del semestre I
  (estacionalidad).
- La matriz de correlación sin valores fuera de `[-1, 1]` ni columnas
  completamente vacías.

## 5. Revisar la trazabilidad fuente → feature

Para cualquier columna de `data/03_primary/panel_final.csv` que te
parezca sospechosa: busca su nombre en `docs/data_dictionary.md` para
saber de qué fuente viene, y en el `src/extract_*.py` correspondiente
para ver exactamente cómo se calculó (todos tienen docstring explicando
el porqué de las decisiones no obvias, no solo el qué).

## 6. Cosas específicas que vale la pena cuestionar

Estos son los puntos donde un par debería mirar con más cuidado, porque
son juicios de diseño, no hechos verificables automáticamente:

- El mapeo departamento→región usado en `extract_departamentos.py` y
  `extract_geih_informalidad_regional.py` (`DEPTO_A_REGION`): ¿coincide
  con la clasificación oficial que use tu fuente de referencia?
- La decisión de **no** pasar a granularidad de departamento (se quedó en
  región) — ver la justificación en `docs/planteamiento_problema.md` y
  `docs/conclusiones.md`.
- Que las columnas `_obs` realmente reflejen qué está relleno y qué no
  (ábrelas y compara con los años/semestres esperados de cada fuente en
  `docs/fuentes_datos.md`).
