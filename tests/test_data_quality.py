"""Validaciones básicas de calidad sobre el panel final generado por
src/build_dataset.py. Requiere haber corrido pipelines/pipeline_ml.py al
menos una vez (o los pasos 1-7) para que data/03_primary/panel_final.csv
exista.
"""
import pandas as pd
import pytest

from config import PRIMARY_DIR

EXPECTED_REGIONS = {"Caribe", "Central", "Oriental", "Orinoquía/Amazonía/Insular", "Pacífica"}
RATE_COLUMNS = [
    "td", "to", "tgp", "ts",
    "informalidad_laboral_nacional", "informalidad_empresarial_nacional",
    "informalidad_micronegocios_nacional", "informalidad_laboral_regional_real",
]
OBS_FLAG_COLUMNS = [
    "informalidad_empresarial_nacional_obs", "informalidad_laboral_nacional_obs",
    "informalidad_micronegocios_nacional_obs", "informalidad_laboral_regional_real_obs",
    "td_dispersion_regional_obs",
]


@pytest.fixture(scope="module")
def panel():
    path = PRIMARY_DIR / "panel_final.csv"
    if not path.exists():
        pytest.skip(f"{path} no existe todavía — corre pipelines/pipeline_ml.py primero")
    return pd.read_csv(path)


def test_panel_has_rows(panel):
    assert len(panel) > 0


def test_expected_regions_only(panel):
    assert set(panel["region"].unique()) == EXPECTED_REGIONS


def test_no_duplicate_region_periods(panel):
    dupes = panel.duplicated(subset=["region", "anio", "periodo"]).sum()
    assert dupes == 0


def test_rate_columns_in_plausible_range(panel):
    for col in RATE_COLUMNS:
        assert col in panel.columns, f"falta la columna {col}"
        valid = panel[col].dropna()
        assert (valid >= 0).all(), f"{col} tiene valores negativos"
        assert (valid <= 100).all(), f"{col} tiene valores por encima de 100%"


def test_obs_flags_are_binary(panel):
    for col in OBS_FLAG_COLUMNS:
        assert col in panel.columns, f"falta la columna {col}"
        assert set(panel[col].dropna().unique()) <= {0, 1}


def test_region_dummies_sum_to_one(panel):
    # build_dataset.py genera una dummy por región (las 5); train_model.py
    # es quien omite region_Caribe como categoría base al armar FEATURES,
    # así que a nivel de panel las 5 columnas deben existir y ser un
    # one-hot válido (exactamente un 1 por fila).
    dummy_cols = [c for c in panel.columns if c.startswith("region_")]
    assert len(dummy_cols) == 5
    assert (panel[dummy_cols].sum(axis=1) == 1).all()
