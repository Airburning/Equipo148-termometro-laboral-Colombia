# Fuentes de datos

Las 6 fuentes son públicas, publicadas por el **DANE** (Departamento
Administrativo Nacional de Estadística de Colombia). Los archivos
originales viven comprimidos en `data/01_raw/` (ver nota de compresión al
final); cada uno tiene un extractor dedicado en `src/`.

| # | Archivo en `data/01_raw/` | Extractor | Qué aporta | Cobertura |
|---|---|---|---|---|
| 1 | `GEIH Reportes Regionales Procesado.xlsx` | `extract_geih_regional.py` | TD, TO, TGP, TS por región (la columna base del panel) | Semestral, 2010-2025 |
| 2 | `GEIH-ANEXOS.zip` | `extract_geih_anexos.py` | Informalidad laboral, nacional (13-23 áreas metropolitanas) | Trimestres móviles desde 2021 |
| 3 | `IMIE2024_Procesado.xlsx` | `extract_imie.py` | Informalidad empresarial multidimensional, nacional | Anual, 2019-2024 |
| 4 | `EMICRON_2024_consolidado.csv.gz` | `extract_emicron.py` | Informalidad de micronegocios (% sin registro en Cámara de Comercio), nacional | Un solo año, 2024 |
| 5 | `Mercado laboral por departamentos.zip` | `extract_departamentos.py` | Dispersión de TD entre departamentos de una misma región | Anual, 2007-2025, 23 de 33 departamentos |
| 6 | `GEIH_consolidado_2022_2026.csv.gz` | `extract_geih_informalidad_regional.py` | Informalidad laboral real **por región** (microdato persona-mes) | Mensual desde 2022 |

## Dónde conseguirlas

Todas provienen del portal de DANE (microdatos y anexos de la GEIH,
IMIE y EMICRON) y/o de datos.gov.co. Si necesitas la versión original sin
comprimir, los nombres de archivo/hoja/entrada de zip que espera cada
extractor están documentados en el docstring de cada script de `src/`.

## Por qué 3 de las 6 son "nacionales" y no regionales

`GEIH-ANEXOS.zip` (informalidad laboral) e `IMIE2024_Procesado.xlsx`
(informalidad empresarial) solo reportan un valor para todo el país, no
por región — capturan el ciclo económico general, no diferencias
regionales de informalidad. `EMICRON` es también nacional y de un solo
año. Por eso el panel las repite igual para las 5 regiones (con
forward/backward-fill donde falta el año), y por eso se agregaron las
fuentes 5 y 6 — para que el modelo también tenga variables que sí varíen
por región.

## Dos definiciones de informalidad que no son comparables entre sí

`informalidad_laboral_nacional` (fuente 2, ~55%) e
`informalidad_laboral_regional_real` (fuente 6, ~70-88%) miden cosas
relacionadas pero no idénticas: la primera cubre solo las 13-23 áreas
metropolitanas principales de DANE; la segunda usa **todos** los
departamentos del microdato, incluyendo zona rural, donde la informalidad
es estructuralmente mucho más alta. No es un error de cálculo — son dos
definiciones de cobertura distintas, y el modelo se beneficia de ver
ambas (ver importancia de variables en `docs/conclusiones.md`).

## Compresión de los archivos crudos

Dos de las fuentes pesan varios cientos de MB sin comprimir
(`GEIH_consolidado_2022_2026.csv`: ~430MB; `EMICRON_2024_consolidado.csv`:
~42MB), por encima o cerca del límite de 100MB por archivo de GitHub. Se
subieron comprimidos con `gzip -9` (`.csv.gz`, ~44MB y ~7MB
respectivamente) — pandas los lee de forma transparente
(`pd.read_csv(...)` detecta `.gz` solo por la extensión, sin cambios de
código más allá del nombre del archivo).
