"""Genera las figuras estáticas de reports/figures/ a partir de los datos
y métricas reales del pipeline (no capturas del dashboard interactivo).
No hay matriz de confusión porque el problema es de regresión (TD futura),
no de clasificación; en su lugar se incluye real-vs-predicho.
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from config import PRIMARY_DIR, MODEL_OUTPUT_DIR, REPORTS_DIR

FIGURES_DIR = REPORTS_DIR / "figures"

FEATURE_COLS_FOR_CORR = [
    "td", "to", "tgp", "ts",
    "informalidad_laboral_nacional", "informalidad_empresarial_nacional",
    "informalidad_micronegocios_nacional", "informalidad_laboral_regional_real",
    "td_dispersion_regional",
]


def historico_td(panel):
    fig, ax = plt.subplots(figsize=(9, 5))
    panel = panel.copy()
    panel["t"] = panel["anio"] + panel["periodo"].map({"I": 0.0, "II": 0.5})
    for region, g in panel.groupby("region"):
        g = g.sort_values("t")
        ax.plot(g["t"], g["td"], marker="o", markersize=2, label=region)
    ax.set_title("Tasa de Desocupación (TD) por región, 2010-2025")
    ax.set_xlabel("Año")
    ax.set_ylabel("TD (%)")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "distribucion_td_regional.png", dpi=130)
    plt.close(fig)


def correlaciones(panel):
    corr = panel[FEATURE_COLS_FOR_CORR].corr()
    fig, ax = plt.subplots(figsize=(7.5, 6.5))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right", fontsize=8)
    ax.set_yticks(range(len(corr.columns)))
    ax.set_yticklabels(corr.columns, fontsize=8)
    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=6)
    ax.set_title("Correlación entre variables clave del panel")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "correlaciones.png", dpi=130)
    plt.close(fig)


def comparacion_modelos(metrics):
    results = metrics["results"]
    names = [n for n in results if n != "NaiveRandomWalk"]
    mae = [results[n]["test_mae"] for n in names]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(names, mae, color="#4C72B0")
    ax.axhline(results["NaiveRandomWalk"]["test_mae"], color="gray", linestyle="--",
               label=f"Baseline ingenuo (MAE={results['NaiveRandomWalk']['test_mae']:.2f})")
    ax.set_ylabel("MAE en test (puntos porcentuales de TD)")
    ax.set_title("Comparación de modelos (menor = mejor)")
    ax.legend(fontsize=8)
    for b, v in zip(bars, mae):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:.2f}", ha="center", va="bottom", fontsize=8)
    fig.autofmt_xdate(rotation=20)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "comparacion_modelos.png", dpi=130)
    plt.close(fig)


def real_vs_predicho(preds, best_model):
    fig, ax = plt.subplots(figsize=(6, 6))
    y_true = preds["y_true"]
    y_pred = preds[f"pred_{best_model}"]
    ax.scatter(y_true, y_pred, alpha=0.7)
    lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
    ax.plot(lims, lims, color="gray", linestyle="--", label="Predicción perfecta")
    ax.set_xlabel("TD real (%)")
    ax.set_ylabel(f"TD predicho — {best_model} (%)")
    ax.set_title("Real vs. predicho en el set de prueba (2023 en adelante)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "real_vs_predicho.png", dpi=130)
    plt.close(fig)


def importancia_variables(importance):
    top = importance.head(10).sort_values("importance")
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(top["feature"], top["importance"], color="#55A868")
    ax.set_xlabel("Importancia")
    ax.set_title("Variables más influyentes (mejor modelo)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "importancia_variables.png", dpi=130)
    plt.close(fig)


def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(PRIMARY_DIR / "panel_final.csv")
    metrics = json.load(open(MODEL_OUTPUT_DIR / "metrics.json"))
    preds = pd.read_csv(MODEL_OUTPUT_DIR / "test_predictions.csv")
    importance = pd.read_csv(MODEL_OUTPUT_DIR / f"feature_importance_{metrics['best_model']}.csv")

    historico_td(panel)
    correlaciones(panel)
    comparacion_modelos(metrics)
    real_vs_predicho(preds, metrics["best_model"])
    importancia_variables(importance)
    print(f"OK -> {FIGURES_DIR} (5 figuras)")


if __name__ == "__main__":
    main()
