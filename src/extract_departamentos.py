"""Extrae la dispersión regional de la Tasa de Desocupación (TD) desde
'Mercado laboral por departamentos.zip' (anexos GEIH por departamento,
DANE). Cada archivo del zip es una vintage acumulada (ej. la de 2025 trae
la serie completa 2007-2025), así que solo se usa la más reciente.

La hoja 'Departamentos anual' viene en bloques repetidos por
departamento (nombre, fila 'Concepto', fila de años, y 5 filas de
indicador: %PET, TGP, TO, TD, TS). El parser localiza cada bloque de forma
dinámica porque el formato cambia levemente entre vintages (la fila de
años a veces está pegada a 'Concepto' y a veces una fila más abajo).

Esta fuente solo cubre 23 de los 33 departamentos (los que tienen muestra
GEIH suficiente para una estimación directa; no incluye Bogotá,
San Andrés ni los departamentos de la Orinoquía/Amazonía), y todos caen
sin ambigüedad dentro de 4 de las 5 grandes regiones del panel -> la
región Orinoquía/Amazonía/Insular queda sin dato directo de dispersión y
se rellena con el promedio de las otras regiones ese año (ver
'td_dispersion_regional_obs' en el resultado).
"""
import re
import zipfile
import io

import pandas as pd

from config import RAW_DIR, INTERMEDIATE_DIR

ZIP_PATH = RAW_DIR / "Mercado laboral por departamentos.zip"
OUT = INTERMEDIATE_DIR / "td_dispersion_regional.csv"

DEPTO_A_REGION = {
    "Atlántico": "Caribe", "Bolívar": "Caribe", "Cesar": "Caribe",
    "Córdoba": "Caribe", "La Guajira": "Caribe", "Magdalena": "Caribe",
    "Sucre": "Caribe",
    "Boyacá": "Oriental", "Cundinamarca": "Oriental", "Meta": "Oriental",
    "Norte de Santander": "Oriental", "Santander": "Oriental",
    "Antioquia": "Central", "Caldas": "Central", "Caquetá": "Central",
    "Huila": "Central", "Quindío": "Central", "Risaralda": "Central",
    "Tolima": "Central",
    "Cauca": "Pacífica", "Chocó": "Pacífica", "Nariño": "Pacífica",
    "Valle del Cauca": "Pacífica",
}
ALL_REGIONS = ["Caribe", "Central", "Oriental", "Orinoquía/Amazonía/Insular", "Pacífica"]


def find_latest_file():
    z = zipfile.ZipFile(ZIP_PATH)
    candidates = []
    for name in z.namelist():
        m = re.search(r"anex-GEIHDepartamentos-(\d{4})\.xls$", name)
        if m:
            candidates.append((int(m.group(1)), name))
    if not candidates:
        raise RuntimeError("No se encontró ningún 'anex-GEIHDepartamentos-YYYY.xls' en el zip")
    candidates.sort()
    return z, candidates[-1][1]


def parse_departamentos_anual(df):
    col0 = df[0]
    td_rows = df.index[col0 == "Tasa de Desocupación (TD)"].tolist()
    records = []
    for r in td_rows:
        pet_row, tgp_row, to_row, ts_row = r - 3, r - 2, r - 1, r + 1

        year_row = None
        for cand in range(pet_row - 1, max(pet_row - 5, -1), -1):
            numeric = pd.to_numeric(df.iloc[cand, 1:], errors="coerce").dropna()
            if len(numeric) >= 5 and numeric.between(1990, 2100).all():
                year_row = cand
                break
        if year_row is None:
            continue

        dept = None
        for cand in range(year_row - 1, max(year_row - 6, -1), -1):
            val = df.iloc[cand, 0]
            if pd.notna(val) and val != "Concepto" and val != "Departamentos" and "Serie anual" not in str(val):
                dept = val
                break
        if dept is None:
            continue

        years = pd.to_numeric(df.iloc[year_row, 1:], errors="coerce")
        for concept_row, colname in [(pet_row, "pct_pet"), (tgp_row, "tgp"), (to_row, "to"), (r, "td"), (ts_row, "ts")]:
            vals = pd.to_numeric(df.iloc[concept_row, 1:], errors="coerce")
            for col_idx, yr in years.items():
                if pd.isna(yr):
                    continue
                v = vals.get(col_idx)
                if pd.isna(v):
                    continue
                records.append((dept, int(yr), colname, float(v)))

    long_df = pd.DataFrame(records, columns=["departamento", "anio", "concepto", "valor"])
    return long_df.pivot_table(index=["departamento", "anio"], columns="concepto", values="valor", aggfunc="first").reset_index()


def main():
    z, entry = find_latest_file()
    data = z.read(entry)
    raw = pd.read_excel(io.BytesIO(data), sheet_name="Departamentos anual", header=None)
    dept_year = parse_departamentos_anual(raw)

    unmapped = sorted(set(dept_year["departamento"]) - set(DEPTO_A_REGION))
    if unmapped:
        raise RuntimeError(f"Departamentos sin mapeo a región: {unmapped}")
    dept_year["region"] = dept_year["departamento"].map(DEPTO_A_REGION)

    dispersion = (
        dept_year.groupby(["region", "anio"])["td"]
        .std()
        .reset_index()
        .rename(columns={"td": "td_dispersion_regional"})
    )

    years = sorted(dept_year["anio"].unique())
    full_grid = pd.MultiIndex.from_product([ALL_REGIONS, years], names=["region", "anio"]).to_frame(index=False)
    dispersion = full_grid.merge(dispersion, on=["region", "anio"], how="left")
    dispersion["td_dispersion_regional_obs"] = dispersion["td_dispersion_regional"].notna().astype(int)

    year_mean = dispersion.groupby("anio")["td_dispersion_regional"].transform("mean")
    dispersion["td_dispersion_regional"] = dispersion["td_dispersion_regional"].fillna(year_mean)
    global_mean = dispersion["td_dispersion_regional"].mean()
    dispersion["td_dispersion_regional"] = dispersion["td_dispersion_regional"].fillna(global_mean)

    dispersion = dispersion.sort_values(["region", "anio"]).reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    dispersion.to_csv(OUT, index=False)
    print(f"OK -> {OUT}  (fuente: {entry})  filas={len(dispersion)}  departamentos={dept_year['departamento'].nunique()}")
    print(dispersion.tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
