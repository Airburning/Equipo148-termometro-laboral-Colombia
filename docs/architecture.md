# Arquitectura e integración de fuentes

## Diagrama de flujo

```mermaid
flowchart LR
    subgraph raw["data/01_raw (6 fuentes DANE)"]
        R1["GEIH Reportes\nRegionales.xlsx"]
        R2["GEIH-ANEXOS.zip"]
        R3["IMIE2024.xlsx"]
        R4["EMICRON_2024.csv.gz"]
        R5["Mercado laboral por\ndepartamentos.zip"]
        R6["GEIH_consolidado\n2022_2026.csv.gz"]
    end

    subgraph extract["src/extract_*.py"]
        E1[extract_geih_regional]
        E2[extract_geih_anexos]
        E3[extract_imie]
        E4[extract_emicron]
        E5[extract_departamentos]
        E6[extract_geih_informalidad_regional]
    end

    subgraph inter["data/02_intermediate"]
        I1[geih_regional_panel.csv]
        I2[informalidad_laboral_nacional.csv]
        I3[informalidad_empresarial_nacional.csv]
        I4[informalidad_micronegocios_nacional.csv]
        I5[td_dispersion_regional.csv]
        I6[informalidad_laboral_regional.csv]
    end

    R1 --> E1 --> I1
    R2 --> E2 --> I2
    R3 --> E3 --> I3
    R4 --> E4 --> I4
    R5 --> E5 --> I5
    R6 --> E6 --> I6

    I1 & I2 & I3 & I4 & I5 & I6 --> BD["src/build_dataset.py\n(merge + fill + lags/roll)"]
    BD --> PF["data/03_primary/panel_final.csv"]
    PF --> TM["src/train_model.py\n(5 modelos + baseline)"]
    TM --> MO["models/*.joblib\ndata/04_model_output/metrics.json"]
    MO --> FN["src/forecast_next.py"]
    FN --> ERD["src/export_report_data.py"]
    ERD --> RD["data/04_model_output/report_data.json"]
    RD --> GF["src/generate_figures.py"] --> FIG["reports/figures/*.png"]
    RD --> BDash["app/build_dashboard.py"] --> HTML["reports/reporte_final.html"]
    RD --> App["app/dashboard_app.py\n(app de escritorio)"]
```

## Por qué esta estructura de `data/`

Sigue el patrón *raw → intermediate → primary → model output*, para que
cada capa tenga una responsabilidad clara y sea fácil saber qué se puede
borrar y regenerar (todo lo que no está en `01_raw/` se reconstruye
corriendo `pipelines/pipeline_ml.py`):

- **01_raw**: exactamente como llegó del DANE (comprimido donde hacía
  falta para caber en GitHub). Nunca se edita a mano.
- **02_intermediate**: una fuente ya limpia y homologada a semestre, pero
  todavía **sin combinar** con las demás.
- **03_primary**: el panel único, ya combinado, con todas las features de
  historia reciente. Es lo que entra a `train_model.py`.
- **04_model_output**: todo lo que sale de entrenar/evaluar/proyectar
  (menos el modelo serializado en sí, que vive en `models/` porque
  conceptualmente es un artefacto distinto a un dato tabular).

## Por qué `src/` tiene 6 extractores en vez de 1 solo

Cada fuente tiene un formato de origen distinto (Excel con hoja pivotante,
zip con Excel adentro, CSV plano, microdato de 3.7M filas) y una lógica de
limpieza propia y no trivial (ver docstring de cada script). Forzarlos a
un único `data_cleaning.py` habría escondido esa complejidad en vez de
hacerla explícita; se prefirió una función/script por fuente, todas
important­ables desde `pipelines/pipeline_ml.py`.

## Cómo se resuelven las rutas

`src/config.py` es la única fuente de verdad para las rutas del proyecto
(`RAW_DIR`, `INTERMEDIATE_DIR`, `PRIMARY_DIR`, `MODEL_OUTPUT_DIR`,
`MODELS_DIR`, `REPORTS_DIR`), calculadas desde la ubicación del propio
`config.py`. Todo lo demás (extractores, `build_dataset.py`,
`train_model.py`, la app de escritorio) importa de ahí — mover o renombrar
una carpeta de datos solo implica editar ese archivo.
