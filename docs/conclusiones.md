# Conclusiones, limitaciones y próximos pasos

## Resultados (semestres de prueba: 2023 en adelante)

| Modelo | MAE (test) | RMSE (test) | R² (test) |
|---|---|---|---|
| Ingenuo (random walk) | 1.75 | 1.99 | 0.20 |
| Regresión lineal | 11.32 | 11.91 | -27.58 |
| Ridge | 5.60 | 5.83 | -5.84 |
| Random Forest | 0.86 | 1.09 | 0.76 |
| Gradient Boosting | 0.86 | 1.21 | 0.71 |
| **XGBoost (mejor)** | **0.82** | **1.13** | **0.74** |

Todos los modelos de árboles superan claramente al baseline ingenuo
(MAE ~0.82-0.86 puntos porcentuales de TD, frente a 1.75 del random walk).
La regresión lineal y Ridge rinden mal por la alta colinealidad entre
rezagos y promedios móviles — es un patrón esperado, no un error del
pipeline (ver `docs/marco_metodologico.md`).

## Qué variables importan más

Según la importancia de features del mejor modelo (XGBoost):

1. `periodo_II` (estacionalidad)
2. `informalidad_empresarial_nacional`
3. `tgp_roll4`
4. `td_lag1`
5. `to_lag1`
6. `informalidad_laboral_regional_real_lag1` ← una de las 3 fuentes nuevas
7. `td_dispersion_regional` ← una de las 3 fuentes nuevas

Dos de las tres fuentes agregadas en esta iteración del proyecto
(informalidad laboral real por región y dispersión regional de TD)
quedaron entre las 10 variables más importantes — es evidencia de que
aportan señal real, no solo ruido, incluso con un panel pequeño.

## El costo de agregar más fuentes/features en un panel pequeño

Antes de incorporar las fuentes 4, 5 y 6, el mejor modelo era Random
Forest (MAE 0.837, R² 0.780). Después de agregarlas (22 → 28 features),
el mejor modelo pasó a ser XGBoost (MAE 0.818, R² 0.743): el MAE mejora
levemente, pero el R² del mejor modelo baja. Con solo 160 filas de panel
(117 para entrenar), meter más variables siempre trae ese riesgo de
sobreajuste — por eso se limitaron las adiciones a 6 features (no 12: se
descartó agregar dispersión de TO/TGP/TS, solo se dejó la de TD) y se
prefirió no pasar a granularidad de departamento (33 categorías en vez de
5), que hubiera aumentado el tamaño del panel pero también su ruido.

## Limitaciones conocidas

- **Panel pequeño**: 160 filas totales, 117 para entrenar. Limita cuántos
  hiperparámetros/variables se pueden ajustar sin sobreajustar.
- **Dos definiciones de informalidad laboral no son comparables en nivel**
  (~55% nacional-metropolitana vs. ~70-88% regional-total): ver
  `docs/fuentes_datos.md`. El modelo las usa como señales complementarias,
  no intercambiables.
- **Dispersión regional de TD (fuente 5) solo cubre 23 de 33
  departamentos**: la región Orinoquía/Amazonía/Insular no tiene
  departamentos con muestra GEIH directa, así que su dispersión se rellena
  con el promedio de las otras regiones (columna `td_dispersion_regional_obs`
  marca esto explícitamente).
- **No es un modelo causal**: no explica por qué sube o baja la TD, solo
  la proyecta estadísticamente a partir del patrón histórico. No captura
  choques no observados en el historial (una crisis nueva, un cambio de
  política abrupto).
- **El mapeo departamento → región** (usado en las fuentes 5 y 6) se
  tomó de la clasificación estándar del DANE, no de una tabla oficial
  incluida en los archivos fuente — ver nota en `docs/fuentes_datos.md`.

## Próximos pasos posibles

- Si se consigue una tabla oficial departamento→región del DANE,
  validar/corregir el mapeo usado en `extract_departamentos.py` y
  `extract_geih_informalidad_regional.py`.
- Explorar un modelo por región en vez de uno solo con dummies de región,
  ahora que hay más features regionales (fuentes 5 y 6) que podrían
  interactuar distinto por región.
- Cuando la fuente 6 (microdato GEIH) acumule más años, reevaluar si
  puede reemplazar en lugar de complementar a la fuente 2 (informalidad
  laboral nacional), o si conviene calcular también informalidad
  empresarial y de micronegocios a nivel regional con el mismo enfoque.
- Agregar un intervalo de confianza/predicción a la proyección de
  `forecast_next.py` (hoy es una sola estimación puntual).
