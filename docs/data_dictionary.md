# Diccionario de datos — `data/03_primary/panel_final.csv`

Una fila = una región en un semestre determinado. 160 filas (5 regiones ×
32 semestres, 2010-2025).

## Identificadores

| Columna | Tipo | Descripción |
|---|---|---|
| `region` | texto | Una de las 5 grandes regiones DANE: Caribe, Central, Oriental, Orinoquía/Amazonía/Insular, Pacífica |
| `anio` | entero | Año calendario |
| `periodo` | texto | `I` (enero-junio) o `II` (julio-diciembre) |
| `sidx` | entero | Índice semestral continuo (`anio*2 + periodo`), usado para ordenar y calcular rezagos |

## Variables base (fuente 1: GEIH Reportes Regionales)

| Columna | Descripción |
|---|---|
| `td` | Tasa de Desocupación (%) — variable objetivo del semestre actual |
| `to` | Tasa de Ocupación (%) |
| `tgp` | Tasa Global de Participación (%) |
| `ts` | Tasa de Subocupación (%) |
| `pct_poblacion_edad_trabajar`, `poblacion_desocupada`, `poblacion_edad_trabajar`, `poblacion_fuera_fuerza_trabajo`, `poblacion_ocupada`, `poblacion_subocupada`, `poblacion_total`, `fuerza_trabajo`, `fuerza_trabajo_potencial` | Conteos poblacionales que acompañan a las tasas (no se usan como feature del modelo, pero quedan disponibles para análisis descriptivo) |

## Variables macro nacionales (fuentes 2, 3, 4)

| Columna | Descripción |
|---|---|
| `informalidad_laboral_nacional` | % informalidad laboral, nacional (13-23 áreas metropolitanas), GEIH-ANEXOS |
| `informalidad_laboral_nacional_obs` | 1 si el dato de esa fila es real, 0 si fue rellenado (forward/backward fill) |
| `informalidad_empresarial_nacional` | % informalidad empresarial multidimensional, nacional, IMIE |
| `informalidad_empresarial_nacional_obs` | 1 = real, 0 = rellenado |
| `informalidad_micronegocios_nacional` | % micronegocios sin registro en Cámara de Comercio, nacional, EMICRON 2024 |
| `informalidad_micronegocios_nacional_obs` | 1 = real (solo 2024), 0 = rellenado |

## Variables regionales/departamentales (fuentes 5, 6)

| Columna | Descripción |
|---|---|
| `informalidad_laboral_regional_real` | % informalidad laboral calculado del microdato GEIH, sí varía por región (cobertura total, incluye zona rural — no comparable en nivel con `informalidad_laboral_nacional`, ver `docs/fuentes_datos.md`) |
| `informalidad_laboral_regional_real_obs` | 1 = real (2022 en adelante), 0 = rellenado |
| `td_dispersion_regional` | Desviación estándar de TD entre los departamentos de esa región ese año — mide qué tan pareja o desigual es la región internamente |
| `td_dispersion_regional_obs` | 1 = calculado con datos reales de departamentos, 0 = rellenado con el promedio de las otras regiones ese año (aplica sobre todo a Orinoquía/Amazonía/Insular, sin departamentos con muestra directa) |

## Features de historia reciente (construidas en `build_dataset.py`)

| Patrón | Descripción |
|---|---|
| `{td,to,tgp,ts}_lag1` | Valor del semestre anterior, misma región |
| `{td,to,tgp,ts}_lag2` | Valor de hace 2 semestres, misma región |
| `{td,to,tgp,ts}_roll4` | Promedio móvil de los últimos 4 semestres (excluyendo el actual) |
| `informalidad_laboral_lag1`, `informalidad_empresarial_lag1`, `informalidad_micronegocios_lag1`, `informalidad_laboral_regional_real_lag1`, `td_dispersion_regional_lag1` | Rezago de 1 periodo (semestre o año, según la fuente) de cada variable macro/regional |
| `periodo_II` | 1 si el semestre es "II", captura estacionalidad |
| `year_trend` | Años transcurridos desde 2010, captura la tendencia estructural de largo plazo |
| `region_Central`, `region_Oriental`, `region_Orinoquía/Amazonía/Insular`, `region_Pacífica`, `region_Caribe` | Dummies one-hot de región (las 5 existen en el panel; `train_model.py` omite `region_Caribe` como categoría base al construir `FEATURES`, para evitar colinealidad perfecta) |

## Variable objetivo

| Columna | Descripción |
|---|---|
| `td_target` | TD del **siguiente** semestre, misma región (`NaN` en el último semestre disponible de cada región, porque todavía no existe) |

`train_model.py` no entrena directamente sobre `td_target` sino sobre
`td_target - td` (el cambio semestral) — ver
`docs/marco_metodologico.md`, sección "el truco: predecir el cambio, no
el nivel".

## Las 28 variables que sí ve el modelo (`FEATURES` en `src/train_model.py`)

```
td_lag1, td_lag2, td_roll4, to_lag1, to_lag2, to_roll4,
tgp_lag1, tgp_lag2, tgp_roll4, ts_lag1, ts_lag2, ts_roll4,
informalidad_laboral_nacional, informalidad_laboral_lag1,
informalidad_empresarial_nacional, informalidad_empresarial_lag1,
informalidad_micronegocios_nacional, informalidad_micronegocios_lag1,
informalidad_laboral_regional_real, informalidad_laboral_regional_real_lag1,
td_dispersion_regional, td_dispersion_regional_lag1,
periodo_II, year_trend,
region_Central, region_Oriental, region_Orinoquía/Amazonía/Insular, region_Pacífica
```

Nótese que **no** se le da al modelo el nivel de TD "sin más contexto" —
todo lo que ve son rezagos, promedios y tendencias, que es lo que en la
práctica se puede usar para predecir hacia adelante sin hacer trampa
(*data leakage*).
