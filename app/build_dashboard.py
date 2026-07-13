"""Combina dashboard_template.html + report_data.json en un único archivo
HTML autocontenido (reports/reporte_final.html) que se puede abrir en
cualquier PC con un navegador, sin instalar nada y sin conexión a internet.
"""
from pathlib import Path

from config import MODEL_OUTPUT_DIR, REPORTS_DIR

APP_DIR = Path(__file__).resolve().parent
TEMPLATE = APP_DIR / "dashboard_template.html"
DATA_JSON = MODEL_OUTPUT_DIR / "report_data.json"
OUT_HTML = REPORTS_DIR / "reporte_final.html"


def main():
    template = TEMPLATE.read_text(encoding="utf-8")
    data = DATA_JSON.read_text(encoding="utf-8")
    if "__REPORT_DATA_JSON__" not in template:
        raise RuntimeError("La plantilla no tiene el marcador __REPORT_DATA_JSON__")
    html = template.replace("__REPORT_DATA_JSON__", data)
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"OK -> {OUT_HTML}  ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
