"""Calcula la informalidad laboral REAL por región-semestre desde el
microdato GEIH persona-mes (GEIH_consolidado_2022_2026.csv.gz, ~3.7M filas).

A diferencia de 'informalidad_laboral_nacional' (GEIH-ANEXOS, un solo
valor nacional repetido para las 5 regiones), esta fuente sí varía por
región porque el microdato trae el departamento de cada persona. Se
procesa en chunks (el archivo pesa ~430MB sin comprimir) y se pondera por
FACTOR_EXPANSION. Solo cubre 2022 en adelante (antes de eso no hay
microdato disponible), así que en build_dataset.py se completa hacia
atrás igual que las demás series nacionales.

Nota: el nivel resultante (~70-88%) es mucho más alto que
'informalidad_laboral_nacional' (~55%, de GEIH-ANEXOS) porque esa serie
de DANE solo cubre las 13-23 áreas metropolitanas principales, mientras
que este cálculo usa TODOS los departamentos (incluida el área rural,
donde la informalidad es estructuralmente mucho más alta). No es un
error: son dos definiciones de cobertura distintas y complementarias.
"""
import pandas as pd

from config import RAW_DIR, INTERMEDIATE_DIR

SRC = RAW_DIR / "GEIH_consolidado_2022_2026.csv.gz"
OUT = INTERMEDIATE_DIR / "informalidad_laboral_regional.csv"
CHUNKSIZE = 500_000

DPTO_A_REGION = {
    8: "Caribe", 13: "Caribe", 20: "Caribe", 23: "Caribe", 44: "Caribe",
    47: "Caribe", 70: "Caribe", 88: "Caribe",
    11: "Oriental", 15: "Oriental", 25: "Oriental", 50: "Oriental",
    54: "Oriental", 68: "Oriental",
    5: "Central", 17: "Central", 18: "Central", 41: "Central",
    63: "Central", 66: "Central", 73: "Central",
    19: "Pacífica", 27: "Pacífica", 52: "Pacífica", 76: "Pacífica",
    81: "Orinoquía/Amazonía/Insular", 85: "Orinoquía/Amazonía/Insular",
    86: "Orinoquía/Amazonía/Insular", 91: "Orinoquía/Amazonía/Insular",
    94: "Orinoquía/Amazonía/Insular", 95: "Orinoquía/Amazonía/Insular",
    97: "Orinoquía/Amazonía/Insular", 99: "Orinoquía/Amazonía/Insular",
}


def main():
    informal_w = {}
    total_w = {}

    reader = pd.read_csv(
        SRC,
        usecols=["ANIO", "MES", "DPTO", "FACTOR_EXPANSION", "INFORMALIDAD_DANE"],
        chunksize=CHUNKSIZE,
    )
    for chunk in reader:
        chunk = chunk[chunk["INFORMALIDAD_DANE"].isin(["Formal", "Informal"])].copy()
        unmapped = set(chunk["DPTO"].unique()) - set(DPTO_A_REGION)
        if unmapped:
            raise RuntimeError(f"Códigos DPTO sin mapeo a región: {sorted(unmapped)}")
        chunk["region"] = chunk["DPTO"].map(DPTO_A_REGION)
        chunk["periodo"] = chunk["MES"].apply(lambda m: "I" if m <= 6 else "II")
        chunk["is_informal_w"] = chunk["FACTOR_EXPANSION"].where(chunk["INFORMALIDAD_DANE"] == "Informal", 0.0)

        g_total = chunk.groupby(["region", "ANIO", "periodo"])["FACTOR_EXPANSION"].sum()
        g_informal = chunk.groupby(["region", "ANIO", "periodo"])["is_informal_w"].sum()
        for key, val in g_total.items():
            total_w[key] = total_w.get(key, 0.0) + val
        for key, val in g_informal.items():
            informal_w[key] = informal_w.get(key, 0.0) + val

    rows = []
    for key, tot in total_w.items():
        region, anio, periodo = key
        rows.append((region, anio, periodo, 100 * informal_w.get(key, 0.0) / tot))

    out = pd.DataFrame(rows, columns=["region", "anio", "periodo", "informalidad_laboral_regional_real"])
    out = out.sort_values(["region", "anio", "periodo"]).reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"OK -> {OUT}  filas={len(out)}")
    print(out.tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
