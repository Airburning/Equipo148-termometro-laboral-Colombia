"""Extrae un indicador nacional de informalidad de micronegocios desde
EMICRON_2024_consolidado.csv.gz (Encuesta de Micronegocios, DANE).

Usa P3000 (¿el negocio está registrado en Cámara de Comercio / tiene
registro mercantil?, 1=Sí, 2=No) como proxy de informalidad, ponderado por
el factor de expansión nacional (F_EXP). Es un solo año (2024), a
diferencia de IMIE (informalidad empresarial "multidimensional"), por lo
que se trata como una fuente aparte y no como sustituto de esa serie.
Como referencia, el resultado (~88%) es consistente con el nivel de IMIE
2024 (~87%), lo que confirma que P3000 mide el mismo fenómeno.
"""
import pandas as pd

from config import RAW_DIR, INTERMEDIATE_DIR

SRC = RAW_DIR / "EMICRON_2024_consolidado.csv.gz"
OUT = INTERMEDIATE_DIR / "informalidad_micronegocios_nacional.csv"
ANIO = 2024


def main():
    df = pd.read_csv(SRC, usecols=["P3000", "F_EXP"])
    df = df[df["P3000"].isin([1, 2])]

    informal_w = df.loc[df["P3000"] == 2, "F_EXP"].sum()
    total_w = df["F_EXP"].sum()
    pct_informal = 100 * informal_w / total_w

    out = pd.DataFrame({
        "anio": [ANIO],
        "informalidad_micronegocios_nacional": [pct_informal],
    })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"OK -> {OUT}")
    print(out.to_string(index=False))


if __name__ == "__main__":
    main()
