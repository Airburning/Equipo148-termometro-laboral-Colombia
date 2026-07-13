"""Combina las 6 fuentes en un panel único (región x semestre) y construye
las features para el modelo. Target: tasa de desocupación (TD) del
siguiente semestre, por región (forecasting a un paso).
"""
import pandas as pd

from config import INTERMEDIATE_DIR, PRIMARY_DIR

OUT = PRIMARY_DIR / "panel_final.csv"

PERIODO_ORDER = {"I": 0, "II": 1}


def semestre_index(anio, periodo):
    return anio * 2 + periodo.map(PERIODO_ORDER)


def main():
    geih = pd.read_csv(INTERMEDIATE_DIR / "geih_regional_panel.csv")
    informal_lab = pd.read_csv(INTERMEDIATE_DIR / "informalidad_laboral_nacional.csv")
    informal_emp = pd.read_csv(INTERMEDIATE_DIR / "informalidad_empresarial_nacional.csv")
    informal_micro = pd.read_csv(INTERMEDIATE_DIR / "informalidad_micronegocios_nacional.csv")
    td_dispersion = pd.read_csv(INTERMEDIATE_DIR / "td_dispersion_regional.csv")
    informal_lab_regional = pd.read_csv(INTERMEDIATE_DIR / "informalidad_laboral_regional.csv")

    geih["sidx"] = semestre_index(geih["anio"], geih["periodo"])
    informal_lab["sidx"] = semestre_index(informal_lab["anio"], informal_lab["periodo"])
    informal_lab_regional["sidx"] = semestre_index(informal_lab_regional["anio"], informal_lab_regional["periodo"])

    df = geih.merge(
        informal_lab[["sidx", "informalidad_laboral_nacional"]], on="sidx", how="left"
    )
    df = df.merge(informal_emp, on="anio", how="left")
    df = df.merge(informal_micro, on="anio", how="left")
    df = df.merge(td_dispersion, on=["region", "anio"], how="left")
    df = df.merge(
        informal_lab_regional[["region", "sidx", "informalidad_laboral_regional_real"]],
        on=["region", "sidx"], how="left",
    )

    # la informalidad empresarial es anual (2019-2024): rellenar hacia
    # adelante/atrás para cubrir años fuera de ese rango, marcando el origen
    df["informalidad_empresarial_nacional_obs"] = df["informalidad_empresarial_nacional"].notna().astype(int)
    df = df.sort_values(["anio", "periodo"])
    df["informalidad_empresarial_nacional"] = (
        df.groupby("region")["informalidad_empresarial_nacional"]
        .transform(lambda s: s.ffill().bfill())
    )
    # igual para informalidad laboral (solo disponible 2021 en adelante)
    df["informalidad_laboral_nacional_obs"] = df["informalidad_laboral_nacional"].notna().astype(int)
    df["informalidad_laboral_nacional"] = (
        df.groupby("region")["informalidad_laboral_nacional"]
        .transform(lambda s: s.ffill().bfill())
    )
    # informalidad de micronegocios (EMICRON): un solo año (2024), nacional
    df["informalidad_micronegocios_nacional_obs"] = df["informalidad_micronegocios_nacional"].notna().astype(int)
    df["informalidad_micronegocios_nacional"] = (
        df.groupby("region")["informalidad_micronegocios_nacional"]
        .transform(lambda s: s.ffill().bfill())
    )
    # informalidad laboral real por región (microdato GEIH): solo 2022 en adelante
    df["informalidad_laboral_regional_real_obs"] = df["informalidad_laboral_regional_real"].notna().astype(int)
    df["informalidad_laboral_regional_real"] = (
        df.groupby("region")["informalidad_laboral_regional_real"]
        .transform(lambda s: s.ffill().bfill())
    )
    # dispersión regional de TD (Mercado laboral por departamentos): 2007 en
    # adelante y ya viene sin NaN (extract_departamentos.py rellena
    # Orinoquía/Amazonía/Insular con el promedio de las otras regiones)
    df["td_dispersion_regional"] = (
        df.groupby("region")["td_dispersion_regional"]
        .transform(lambda s: s.ffill().bfill())
    )
    df["td_dispersion_regional_obs"] = (
        df.groupby("region")["td_dispersion_regional_obs"]
        .transform(lambda s: s.ffill().bfill())
    )

    df = df.sort_values(["region", "sidx"]).reset_index(drop=True)

    lag_cols = ["td", "to", "tgp", "ts"]
    g = df.groupby("region")
    for col in lag_cols:
        df[f"{col}_lag1"] = g[col].shift(1)
        df[f"{col}_lag2"] = g[col].shift(2)
        df[f"{col}_roll4"] = g[col].transform(lambda s: s.shift(1).rolling(4, min_periods=2).mean())

    df["informalidad_laboral_lag1"] = g["informalidad_laboral_nacional"].shift(1)
    df["informalidad_empresarial_lag1"] = g["informalidad_empresarial_nacional"].shift(1)
    df["informalidad_micronegocios_lag1"] = g["informalidad_micronegocios_nacional"].shift(1)
    df["informalidad_laboral_regional_real_lag1"] = g["informalidad_laboral_regional_real"].shift(1)
    df["td_dispersion_regional_lag1"] = g["td_dispersion_regional"].shift(1)

    # target: TD del siguiente semestre, misma región
    df["td_target"] = g["td"].shift(-1)

    df["periodo_II"] = (df["periodo"] == "II").astype(int)
    df["year_trend"] = df["anio"] - df["anio"].min()

    region_dummies = pd.get_dummies(df["region"], prefix="region", dtype=int)
    df = pd.concat([df, region_dummies], axis=1)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    n_total = len(df)
    n_usable = df["td_target"].notna().sum()
    n_full_features = df.dropna(subset=[c for c in df.columns if c.endswith("_lag2")] + ["td_target"]).shape[0]
    print(f"OK -> {OUT}")
    print(f"filas totales={n_total}  con target={n_usable}  con lags completos+target={n_full_features}")
    print(df[["region", "anio", "periodo", "td", "td_target", "informalidad_laboral_nacional",
              "informalidad_empresarial_nacional", "informalidad_micronegocios_nacional",
              "informalidad_laboral_regional_real", "td_dispersion_regional"]].tail(12).to_string())


if __name__ == "__main__":
    main()
