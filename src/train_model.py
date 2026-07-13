"""Entrena y compara varios modelos de ML para predecir la Tasa de
Desocupación (TD) del siguiente semestre por región, combinando el panel
laboral regional (GEIH) con las variables macro nacionales de informalidad
laboral (GEIH-ANEXOS), informalidad empresarial (IMIE), informalidad de
micronegocios (EMICRON), informalidad laboral real por región (microdato
GEIH) y dispersión regional de TD (Mercado laboral por departamentos).

TD tiene una tendencia estructural fuerte y no estacionaria (cayó de ~20%
en 2010 a ~8% en 2025), lo que hace que los modelos de árboles no puedan
extrapolar bien en nivel (no generalizan fuera del rango visto en train).
Por eso el target real de entrenamiento es el CAMBIO semestral
(td_target - td_actual), que es mucho más estacionario; el nivel se
reconstruye sumando ese cambio al valor actual.

Split temporal (no aleatorio): train = semestres antes de 2023,
test = 2023 en adelante. Así se evita fuga de información hacia el pasado.
Se compara contra un baseline ingenuo (random walk: TD no cambia).
"""
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit
from xgboost import XGBRegressor

from config import PRIMARY_DIR, MODEL_OUTPUT_DIR, MODELS_DIR

FEATURES = [
    "td_lag1", "td_lag2", "td_roll4",
    "to_lag1", "to_lag2", "to_roll4",
    "tgp_lag1", "tgp_lag2", "tgp_roll4",
    "ts_lag1", "ts_lag2", "ts_roll4",
    "informalidad_laboral_nacional", "informalidad_laboral_lag1",
    "informalidad_empresarial_nacional", "informalidad_empresarial_lag1",
    "informalidad_micronegocios_nacional", "informalidad_micronegocios_lag1",
    "informalidad_laboral_regional_real", "informalidad_laboral_regional_real_lag1",
    "td_dispersion_regional", "td_dispersion_regional_lag1",
    "periodo_II", "year_trend",
    # region_Caribe se omite como categoría base (evita colinealidad perfecta)
    "region_Central", "region_Oriental",
    "region_Orinoquía/Amazonía/Insular", "region_Pacífica",
]
TARGET_LEVEL = "td_target"
TEST_CUTOFF_YEAR = 2023


def main():
    df = pd.read_csv(PRIMARY_DIR / "panel_final.csv")
    modelable = df.dropna(subset=FEATURES + [TARGET_LEVEL, "td"]).copy()
    modelable["td_delta"] = modelable[TARGET_LEVEL] - modelable["td"]

    train = modelable[modelable["anio"] < TEST_CUTOFF_YEAR]
    test = modelable[modelable["anio"] >= TEST_CUTOFF_YEAR]

    X_train, y_train = train[FEATURES], train["td_delta"]
    X_test, y_test_level = test[FEATURES], test[TARGET_LEVEL]
    test_td_now = test["td"].values

    naive_pred_level = test_td_now  # random walk: TD del próximo semestre = TD actual
    naive_mae = mean_absolute_error(y_test_level, naive_pred_level)
    naive_rmse = np.sqrt(mean_squared_error(y_test_level, naive_pred_level))
    naive_r2 = r2_score(y_test_level, naive_pred_level)

    models = {
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(alpha=1.0),
        "RandomForest": RandomForestRegressor(
            n_estimators=400, max_depth=4, min_samples_leaf=4, random_state=42
        ),
        "GradientBoosting": GradientBoostingRegressor(
            n_estimators=200, max_depth=2, learning_rate=0.03, random_state=42
        ),
        "XGBoost": XGBRegressor(
            n_estimators=200, max_depth=2, learning_rate=0.03,
            subsample=0.8, colsample_bytree=0.8, random_state=42,
        ),
    }

    tscv = TimeSeriesSplit(n_splits=5)
    results = {"NaiveRandomWalk": {
        "cv_mae_mean": None, "cv_mae_std": None,
        "test_mae": float(naive_mae), "test_rmse": float(naive_rmse), "test_r2": float(naive_r2),
    }}
    predictions = {"region": test["region"].values, "anio": test["anio"].values,
                    "periodo": test["periodo"].values, "y_true": y_test_level.values,
                    "pred_NaiveRandomWalk": naive_pred_level}

    for name, model in models.items():
        cv_mae = []
        for tr_idx, va_idx in tscv.split(X_train):
            model.fit(X_train.iloc[tr_idx], y_train.iloc[tr_idx])
            pred_va_delta = model.predict(X_train.iloc[va_idx])
            pred_va_level = train["td"].iloc[va_idx].values + pred_va_delta
            true_va_level = train[TARGET_LEVEL].iloc[va_idx].values
            cv_mae.append(mean_absolute_error(true_va_level, pred_va_level))

        model.fit(X_train, y_train)
        pred_test_delta = model.predict(X_test)
        pred_test_level = test_td_now + pred_test_delta
        predictions[f"pred_{name}"] = pred_test_level

        results[name] = {
            "cv_mae_mean": float(np.mean(cv_mae)),
            "cv_mae_std": float(np.std(cv_mae)),
            "test_mae": float(mean_absolute_error(y_test_level, pred_test_level)),
            "test_rmse": float(np.sqrt(mean_squared_error(y_test_level, pred_test_level))),
            "test_r2": float(r2_score(y_test_level, pred_test_level)),
        }

    ml_only = {k: v for k, v in results.items() if k != "NaiveRandomWalk"}
    best_name = min(ml_only, key=lambda k: ml_only[k]["test_mae"])
    best_model = models[best_name]

    if hasattr(best_model, "feature_importances_"):
        importances = pd.DataFrame({
            "feature": FEATURES, "importance": best_model.feature_importances_,
        }).sort_values("importance", ascending=False)
    elif hasattr(best_model, "coef_"):
        importances = pd.DataFrame({
            "feature": FEATURES, "importance": np.abs(best_model.coef_),
        }).sort_values("importance", ascending=False)
    else:
        importances = pd.DataFrame({"feature": FEATURES, "importance": np.nan})

    pd.DataFrame(predictions).to_csv(MODEL_OUTPUT_DIR / "test_predictions.csv", index=False)
    importances.to_csv(MODEL_OUTPUT_DIR / f"feature_importance_{best_name}.csv", index=False)
    with open(MODEL_OUTPUT_DIR / "metrics.json", "w") as f:
        json.dump({"results": results, "best_model": best_name,
                    "n_train": len(train), "n_test": len(test),
                    "test_cutoff_year": TEST_CUTOFF_YEAR,
                    "target": "cambio semestral de TD (reconstruido a nivel)"},
                   f, indent=2, ensure_ascii=False)
    joblib.dump({"model": best_model, "features": FEATURES, "predicts": "delta_td"},
                MODELS_DIR / f"best_model_{best_name}.joblib")

    print(f"n_train={len(train)}  n_test={len(test)}")
    print(pd.DataFrame(results).T.to_string())
    print(f"\nMejor modelo ML: {best_name} (baseline ingenuo: NaiveRandomWalk)")
    print("\nTop features:")
    print(importances.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
