"""Usa el mejor modelo entrenado para proyectar la Tasa de Desocupación (TD)
del siguiente semestre por región, a partir del último dato disponible.
"""
import glob
import json

import joblib
import pandas as pd

from config import PRIMARY_DIR, MODEL_OUTPUT_DIR, MODELS_DIR


def next_period_label(anio, periodo):
    return (anio + 1, "I") if periodo == "II" else (anio, "II")


def main():
    with open(MODEL_OUTPUT_DIR / "metrics.json") as f:
        metrics = json.load(f)
    best_name = metrics["best_model"]
    bundle = joblib.load(glob.glob(str(MODELS_DIR / f"best_model_{best_name}.joblib"))[0])
    model, features = bundle["model"], bundle["features"]

    df = pd.read_csv(PRIMARY_DIR / "panel_final.csv")
    latest_idx = df.groupby("region")["sidx"].idxmax()
    latest = df.loc[latest_idx].copy()

    missing = latest[features].isna().any(axis=1)
    if missing.any():
        print("Aviso: regiones sin features completos para forecast:", latest.loc[missing, "region"].tolist())
    latest = latest.dropna(subset=features)

    pred_delta = model.predict(latest[features])
    latest["td_forecast"] = latest["td"].values + pred_delta
    next_labels = latest.apply(lambda r: next_period_label(int(r["anio"]), r["periodo"]), axis=1)
    latest["anio_forecast"] = [l[0] for l in next_labels]
    latest["periodo_forecast"] = [l[1] for l in next_labels]

    result = latest[["region", "anio", "periodo", "td", "anio_forecast", "periodo_forecast", "td_forecast"]]
    result = result.rename(columns={"anio": "anio_base", "periodo": "periodo_base", "td": "td_base"})
    result.to_csv(MODEL_OUTPUT_DIR / "forecast_next_period.csv", index=False)
    print(f"Modelo usado: {best_name}")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
