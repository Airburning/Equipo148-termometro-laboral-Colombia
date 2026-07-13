"""Exporta panel, métricas, predicciones y proyección a un único JSON
(report_data.json) que consumen tanto la app de escritorio (app/) como el
dashboard web (reports/reporte_final.html).
"""
import json
from datetime import datetime

import pandas as pd

from config import PRIMARY_DIR, MODEL_OUTPUT_DIR

MESES_ES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

FEATURE_LABELS = {
    "td_lag1": "TD semestre anterior", "td_lag2": "TD hace 2 semestres",
    "td_roll4": "TD promedio móvil (4 sem.)",
    "to_lag1": "Tasa ocupación anterior", "to_lag2": "Tasa ocupación hace 2 sem.",
    "to_roll4": "Tasa ocupación prom. móvil",
    "tgp_lag1": "Participación laboral anterior", "tgp_lag2": "Participación hace 2 sem.",
    "tgp_roll4": "Participación prom. móvil",
    "ts_lag1": "Subocupación anterior", "ts_lag2": "Subocupación hace 2 sem.",
    "ts_roll4": "Subocupación prom. móvil",
    "informalidad_laboral_nacional": "Informalidad laboral (nacional)",
    "informalidad_laboral_lag1": "Informalidad laboral (sem. anterior)",
    "informalidad_empresarial_nacional": "Informalidad empresarial (nacional)",
    "informalidad_empresarial_lag1": "Informalidad empresarial (año anterior)",
    "informalidad_micronegocios_nacional": "Informalidad micronegocios (nacional)",
    "informalidad_micronegocios_lag1": "Informalidad micronegocios (año anterior)",
    "informalidad_laboral_regional_real": "Informalidad laboral real (región)",
    "informalidad_laboral_regional_real_lag1": "Informalidad laboral real región (sem. anterior)",
    "td_dispersion_regional": "Dispersión de TD entre departamentos (región)",
    "td_dispersion_regional_lag1": "Dispersión de TD región (año anterior)",
    "periodo_II": "Semestre = II (estacionalidad)",
    "year_trend": "Tendencia (año)",
    "region_Central": "Región = Central", "region_Oriental": "Región = Oriental",
    "region_Orinoquía/Amazonía/Insular": "Región = Orinoquía/Amazonía/Insular",
    "region_Pacífica": "Región = Pacífica",
}

MODEL_ORDER = ["NaiveRandomWalk", "LinearRegression", "Ridge", "RandomForest", "GradientBoosting", "XGBoost"]
MODEL_LABELS = {
    "NaiveRandomWalk": "Ingenuo (sin cambio)", "LinearRegression": "Regresión lineal",
    "Ridge": "Ridge", "RandomForest": "Random Forest",
    "GradientBoosting": "Gradient Boosting", "XGBoost": "XGBoost",
}


def fecha_es(dt):
    return f"{dt.day} de {MESES_ES[dt.month - 1]} de {dt.year}"


def main():
    panel = pd.read_csv(PRIMARY_DIR / "panel_final.csv")
    metrics = json.load(open(MODEL_OUTPUT_DIR / "metrics.json"))
    importance = pd.read_csv(MODEL_OUTPUT_DIR / f"feature_importance_{metrics['best_model']}.csv")
    preds = pd.read_csv(MODEL_OUTPUT_DIR / "test_predictions.csv")
    forecast = pd.read_csv(MODEL_OUTPUT_DIR / "forecast_next_period.csv")

    # histórico TD por región
    panel["periodo_num"] = panel["periodo"].map({"I": 0, "II": 1})
    panel["t"] = panel["anio"] + panel["periodo_num"] * 0.5
    hist = panel[["region", "anio", "periodo", "t", "td"]].dropna(subset=["td"])
    regions = sorted(hist["region"].unique())
    historico = {
        reg: hist[hist["region"] == reg][["t", "anio", "periodo", "td"]].to_dict("records")
        for reg in regions
    }

    # métricas de modelos
    metrics_table = [
        {"model": m, "label": MODEL_LABELS[m], **metrics["results"][m]}
        for m in MODEL_ORDER if m in metrics["results"]
    ]

    # actual vs predicho (mejor modelo) en test
    best = metrics["best_model"]
    preds["t"] = preds["anio"] + preds["periodo"].map({"I": 0, "II": 1}) * 0.5
    test_scatter = preds[["region", "anio", "periodo", "t", "y_true", f"pred_{best}", "pred_NaiveRandomWalk"]].rename(
        columns={f"pred_{best}": "pred_best"}
    ).to_dict("records")

    # feature importance
    importance_top = importance.head(10).copy()
    importance_top["label"] = importance_top["feature"].map(lambda f: FEATURE_LABELS.get(f, f))
    importance_top = importance_top[["label", "importance"]].to_dict("records")

    # forecast
    forecast_records = forecast.to_dict("records")

    payload = {
        "regions": regions,
        "historico": historico,
        "metrics_table": metrics_table,
        "best_model": best,
        "best_model_label": MODEL_LABELS[best],
        "test_scatter": test_scatter,
        "importance": importance_top,
        "forecast": forecast_records,
        "n_train": metrics["n_train"],
        "n_test": metrics["n_test"],
        "test_cutoff_year": metrics["test_cutoff_year"],
        "generated_at": fecha_es(datetime.now()),
    }

    MODEL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODEL_OUTPUT_DIR / "report_data.json", "w") as f:
        json.dump(payload, f, ensure_ascii=False)
    print("OK -> report_data.json")
    print(json.dumps({k: (len(v) if isinstance(v, (list, dict)) else v) for k, v in payload.items()}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
