"""Pruebas de consistencia sobre el modelo entrenado: que cargue, que las
features coincidan con el panel, y que produzca predicciones en un rango
razonable de TD (no valores absurdos como negativos o >100%).

Requiere haber corrido pipelines/pipeline_ml.py al menos una vez para que
models/best_model_*.joblib y data/04_model_output/metrics.json existan.
"""
import glob
import json

import joblib
import pandas as pd
import pytest

from config import PRIMARY_DIR, MODEL_OUTPUT_DIR, MODELS_DIR


@pytest.fixture(scope="module")
def bundle():
    metrics_path = MODEL_OUTPUT_DIR / "metrics.json"
    if not metrics_path.exists():
        pytest.skip(f"{metrics_path} no existe todavía — corre pipelines/pipeline_ml.py primero")
    metrics = json.load(open(metrics_path))
    matches = glob.glob(str(MODELS_DIR / f"best_model_{metrics['best_model']}.joblib"))
    assert matches, f"no se encontró el .joblib del mejor modelo ({metrics['best_model']})"
    return joblib.load(matches[0])


@pytest.fixture(scope="module")
def panel():
    path = PRIMARY_DIR / "panel_final.csv"
    if not path.exists():
        pytest.skip(f"{path} no existe todavía — corre pipelines/pipeline_ml.py primero")
    return pd.read_csv(path)


def test_bundle_has_model_and_features(bundle):
    assert "model" in bundle and "features" in bundle
    assert len(bundle["features"]) > 0


def test_features_exist_in_panel(bundle, panel):
    missing = set(bundle["features"]) - set(panel.columns)
    assert not missing, f"features del modelo ausentes en el panel: {missing}"


def test_prediction_on_latest_row_is_plausible(bundle, panel):
    model, features = bundle["model"], bundle["features"]
    latest_idx = panel.groupby("region")["sidx"].idxmax()
    latest = panel.loc[latest_idx].dropna(subset=features)
    assert len(latest) > 0, "ninguna región tiene features completos en el semestre más reciente"

    pred_delta = model.predict(latest[features])
    pred_level = latest["td"].values + pred_delta

    # un cambio semestral de TD de más de 15 puntos porcentuales no es
    # realista en un semestre (la mayor caída histórica observada en el
    # panel es de un solo dígito), y el nivel de TD no puede ser negativo
    assert (abs(pred_delta) < 15).all()
    assert (pred_level > 0).all()
