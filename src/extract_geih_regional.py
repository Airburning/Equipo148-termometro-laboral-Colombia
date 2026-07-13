"""Extrae el panel semestral de indicadores laborales por región desde
'GEIH Reportes Regionales Procesado.xlsx' (hoja Mod_TNAL_Regiones) y lo
convierte a formato ancho: una fila por (region, anio, periodo).
"""
import openpyxl
import pandas as pd

from config import RAW_DIR, INTERMEDIATE_DIR

SRC = RAW_DIR / "GEIH Reportes Regionales Procesado.xlsx"
OUT = INTERMEDIATE_DIR / "geih_regional_panel.csv"

CONCEPTO_A_COL = {
    "% población en edad de trabajar ": "pct_poblacion_edad_trabajar",
    "Fuerza de trabajo": "fuerza_trabajo",
    "Fuerza de trabajo potencial": "fuerza_trabajo_potencial",
    "Población desocupada": "poblacion_desocupada",
    "Población en edad de trabajar": "poblacion_edad_trabajar",
    "Población fuera de la fuerza de trabajo": "poblacion_fuera_fuerza_trabajo",
    "Población ocupada": "poblacion_ocupada",
    "Población subocupada": "poblacion_subocupada",
    "Población total": "poblacion_total",
    "Tasa Global de Participación (TGP)": "tgp",
    "Tasa de Desocupación (TD)": "td",
    "Tasa de Ocupación (TO)": "to",
    "Tasa de Subocupación (TS)": "ts",
}


def main():
    wb = openpyxl.load_workbook(SRC, read_only=True, data_only=True)
    ws = wb["Mod_TNAL_Regiones"]
    rows = []
    for r in ws.iter_rows(min_row=2, values_only=True):
        concepto, region, anio, periodo, valor = r[:5]
        if concepto is None or region is None:
            continue
        rows.append((CONCEPTO_A_COL.get(concepto, concepto), region, int(anio), periodo, valor))
    wb.close()

    df = pd.DataFrame(rows, columns=["concepto", "region", "anio", "periodo", "valor"])
    wide = df.pivot_table(index=["region", "anio", "periodo"], columns="concepto", values="valor", aggfunc="first").reset_index()
    wide = wide.sort_values(["region", "anio", "periodo"]).reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    wide.to_csv(OUT, index=False)
    print(f"OK -> {OUT}  filas={len(wide)}  columnas={list(wide.columns)}")


if __name__ == "__main__":
    main()
