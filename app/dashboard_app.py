"""Panel de escritorio (estilo Power BI) para el modelo de predicción de
desempleo regional en Colombia.

Es una app nativa (ventana real, no navegador) que lee
outputs/report_data.json — el mismo archivo que usa el dashboard web — y lo
muestra con:

  - un panel de filtros ("slicer") de regiones en la barra lateral, que
    cruza-filtra los gráficos de histórico, dispersión y proyección;
  - páginas por pestaña, como las páginas de un reporte de Power BI;
  - los 5 gráficos son totalmente interactivos: zoom con la rueda del mouse
    o con la barra de herramientas (rectángulo de zoom, pan, deshacer,
    restablecer), tooltip al pasar el mouse con el valor exacto, y clic
    sobre un dato para "seleccionarlo" — el tooltip se fija en pantalla
    aunque muevas el mouse o hagas zoom, hasta que lo vuelvas a clicar;
  - una pestaña "6. Datos" para ver, buscar/filtrar y ordenar el CSV que
    realmente alimenta los gráficos, y botones para abrirlo (o abrir los
    Excel/zip originales del DANE) con el programa predeterminado del PC;
  - tarjetas de KPI arriba;
  - exportar el gráfico activo como imagen;
  - tema claro/oscuro.

Ejecutar:
    pip install -r requirements.txt
    python dashboard_app.py
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QFrame, QCheckBox, QPushButton, QTabWidget, QFileDialog,
    QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy,
    QComboBox, QLineEdit,
)

import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT
from matplotlib.figure import Figure

# BASE_DIR es la carpeta de este script (app/); si se empaqueta con
# PyInstaller (build_exe.bat) habría que revisar --add-data para que
# conserve la misma estructura relativa (src/, data/, models/, reports/)
# junto al ejecutable.
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent / "src"))
from config import RAW_DIR, INTERMEDIATE_DIR, PRIMARY_DIR, MODEL_OUTPUT_DIR, REPORTS_DIR  # noqa: E402

DATA_PATH = MODEL_OUTPUT_DIR / "report_data.json"

MODEL_LABELS_ORDER = ["NaiveRandomWalk", "LinearRegression", "Ridge", "RandomForest", "GradientBoosting", "XGBoost"]

# Los CSV que realmente alimentan los gráficos (pestaña "6. Datos")
CSV_CATALOG = [
    ("Panel final (usado para graficar y entrenar)", PRIMARY_DIR / "panel_final.csv"),
    ("Predicciones en el set de prueba", MODEL_OUTPUT_DIR / "test_predictions.csv"),
    ("Proyección del próximo semestre", MODEL_OUTPUT_DIR / "forecast_next_period.csv"),
    ("Panel regional GEIH (fuente 1)", INTERMEDIATE_DIR / "geih_regional_panel.csv"),
    ("Informalidad laboral nacional (fuente 2)", INTERMEDIATE_DIR / "informalidad_laboral_nacional.csv"),
    ("Informalidad empresarial nacional (fuente 3)", INTERMEDIATE_DIR / "informalidad_empresarial_nacional.csv"),
    ("Informalidad micronegocios nacional (fuente 4)", INTERMEDIATE_DIR / "informalidad_micronegocios_nacional.csv"),
    ("Dispersión regional de TD (fuente 5)", INTERMEDIATE_DIR / "td_dispersion_regional.csv"),
    ("Informalidad laboral real por región (fuente 6)", INTERMEDIATE_DIR / "informalidad_laboral_regional.csv"),
]

# Los Excel/zip/CSV originales, tal como los entregó el DANE (algunos
# comprimidos con gzip para caber en el repo de GitHub, ver data/01_raw)
SOURCE_FILES = [
    ("GEIH Reportes Regionales Procesado.xlsx", RAW_DIR / "GEIH Reportes Regionales Procesado.xlsx"),
    ("GEIH-ANEXOS.zip", RAW_DIR / "GEIH-ANEXOS.zip"),
    ("IMIE2024_Procesado.xlsx", RAW_DIR / "IMIE2024_Procesado.xlsx"),
    ("EMICRON_2024_consolidado.csv.gz", RAW_DIR / "EMICRON_2024_consolidado.csv.gz"),
    ("Mercado laboral por departamentos.zip", RAW_DIR / "Mercado laboral por departamentos.zip"),
    ("GEIH_consolidado_2022_2026.csv.gz", RAW_DIR / "GEIH_consolidado_2022_2026.csv.gz"),
]


def open_with_default_app(path):
    """Abre un archivo o carpeta con el programa predeterminado del sistema
    (Excel para .xlsx, el explorador de archivos para carpetas, etc.)."""
    if sys.platform.startswith("win"):
        os.startfile(str(path))  # noqa: S606 — abrir con la app predeterminada es el propósito
    elif sys.platform == "darwin":
        subprocess.Popen(["open", str(path)])
    else:
        subprocess.Popen(["xdg-open", str(path)])

LIGHT = {
    "window": "#f9f9f7", "surface": "#fcfcfb", "sidebar": "#f2f2ef",
    "text": "#0b0b0b", "text2": "#52514e", "muted": "#898781",
    "grid": "#e1e0d9", "border": "#d9d8d0",
    "good": "#0ca30c", "series": ["#2a78d6", "#1baf7a", "#eda100", "#008300", "#4a3aa7"],
}
DARK = {
    "window": "#0d0d0d", "surface": "#1a1a19", "sidebar": "#161615",
    "text": "#ffffff", "text2": "#c3c2b7", "muted": "#898781",
    "grid": "#2c2c2a", "border": "#333331",
    "good": "#0ca30c", "series": ["#3987e5", "#199e70", "#c98500", "#008300", "#9085e9"],
}


def qss(t):
    return f"""
    QMainWindow, QWidget#central {{ background: {t['window']}; }}
    QWidget#sidebar {{ background: {t['sidebar']}; border-right: 1px solid {t['border']}; }}
    QLabel {{ color: {t['text']}; }}
    QLabel[role="title"] {{ font-size: 19px; font-weight: 700; }}
    QLabel[role="subtitle"] {{ color: {t['text2']}; font-size: 12px; }}
    QLabel[role="section"] {{ color: {t['muted']}; font-size: 11px; font-weight: 700; letter-spacing: 0.04em; text-transform: uppercase; }}
    QLabel[role="kpiLabel"] {{ color: {t['muted']}; font-size: 11px; }}
    QLabel[role="kpiValue"] {{ color: {t['text']}; font-size: 22px; font-weight: 700; }}
    QLabel[role="kpiValueGood"] {{ color: {t['good']}; font-size: 22px; font-weight: 700; }}
    QLabel[role="kpiSub"] {{ color: {t['text2']}; font-size: 11px; }}
    QFrame[class="kpiCard"] {{ background: {t['surface']}; border: 1px solid {t['border']}; border-radius: 10px; }}
    QTabWidget::pane {{ border: 1px solid {t['border']}; background: {t['surface']}; border-radius: 8px; }}
    QTabBar::tab {{ background: transparent; color: {t['text2']}; padding: 9px 16px; margin-right: 2px; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
    QTabBar::tab:selected {{ background: {t['surface']}; color: {t['text']}; font-weight: 600; border: 1px solid {t['border']}; border-bottom: none; }}
    QCheckBox {{ color: {t['text']}; font-size: 12.5px; padding: 3px 2px; }}
    QPushButton {{ background: {t['surface']}; color: {t['text']}; border: 1px solid {t['border']}; border-radius: 6px; padding: 5px 10px; font-size: 12px; }}
    QPushButton:hover {{ background: {t['grid']}; }}
    QTableWidget {{ background: {t['surface']}; color: {t['text']}; gridline-color: {t['grid']}; border: none; font-size: 12px; }}
    QHeaderView::section {{ background: {t['sidebar']}; color: {t['muted']}; border: none; padding: 5px; font-size: 10.5px; font-weight: 700; text-transform: uppercase; }}
    QStatusBar {{ background: {t['sidebar']}; color: {t['muted']}; font-size: 11px; border-top: 1px solid {t['border']}; }}
    """


def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró {DATA_PATH}.\n\n"
            "Corre primero el pipeline: python pipelines/pipeline_ml.py"
        )
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def style_axes(ax, t):
    ax.set_facecolor(t["surface"])
    for spine in ax.spines.values():
        spine.set_color(t["border"])
    ax.tick_params(colors=t["text2"], labelsize=8.5)
    ax.xaxis.label.set_color(t["text2"])
    ax.yaxis.label.set_color(t["text2"])
    ax.grid(True, color=t["grid"], linewidth=0.7, alpha=0.9)
    ax.set_axisbelow(True)


class Chart(QWidget):
    """Un lienzo matplotlib con barra de herramientas de zoom/pan, zoom con
    rueda del mouse, y botón de exportar — listo para meter en una pestaña."""

    def __init__(self, title):
        super().__init__()
        self.title = title
        self.fig = Figure(figsize=(7.5, 4.6), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar2QT(self.canvas, self)
        self.toolbar.setIconSize(self.toolbar.iconSize() * 0.72)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 10)
        lay.setSpacing(2)
        lay.addWidget(self.toolbar)
        lay.addWidget(self.canvas)
        self._scroll_cid = None

    def reset_view(self):
        self.toolbar.home()

    def connect_scroll_zoom(self, ax):
        """Zoom con la rueda del mouse, centrado en el cursor. Hay que
        reconectar en cada redraw porque fig.clear() invalida el 'ax'."""
        if self._scroll_cid is not None:
            self.canvas.mpl_disconnect(self._scroll_cid)

        def on_scroll(event):
            if event.inaxes != ax or event.xdata is None or event.ydata is None:
                return
            scale = 0.82 if event.button == "up" else 1.22
            xlim, ylim = ax.get_xlim(), ax.get_ylim()
            fx = (event.xdata - xlim[0]) / (xlim[1] - xlim[0]) if xlim[1] != xlim[0] else 0.5
            fy = (event.ydata - ylim[0]) / (ylim[1] - ylim[0]) if ylim[1] != ylim[0] else 0.5
            new_w = (xlim[1] - xlim[0]) * scale
            new_h = (ylim[1] - ylim[0]) * scale
            ax.set_xlim(event.xdata - new_w * fx, event.xdata + new_w * (1 - fx))
            ax.set_ylim(event.ydata - new_h * fy, event.ydata + new_h * (1 - fy))
            self.canvas.draw_idle()

        self._scroll_cid = self.canvas.mpl_connect("scroll_event", on_scroll)

    def export_png(self, parent):
        path, _ = QFileDialog.getSaveFileName(
            parent, f"Exportar '{self.title}' como imagen",
            str(BASE_DIR / f"{self.title}.png"), "Imagen PNG (*.png)"
        )
        if path:
            self.fig.savefig(path, dpi=200, facecolor=self.fig.get_facecolor())


class HoverTooltip:
    """Tooltip con hover + clic-para-fijar ('seleccionar un dato') para un
    gráfico matplotlib embebido.

    locate_fn(event) -> None, o (xy, texto, key) del dato más cercano al
    cursor. 'key' identifica el dato (para saber si el clic fue sobre el
    mismo dato ya fijado, y así soltarlo). Clic sobre un dato lo fija —
    sigue visible aunque el mouse se mueva o salga del gráfico, útil para
    hacer zoom mientras se lee la info. Clic de nuevo sobre el mismo dato
    (o en un área vacía) lo suelta.
    """

    def __init__(self, chart, ax, t, locate_fn, on_change=None):
        self.chart = chart
        self.ax = ax
        self.locate_fn = locate_fn
        self.on_change = on_change
        self.pinned = False
        self.pinned_key = None
        self.annot = ax.annotate(
            "", xy=(0, 0), xytext=(12, 12), textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.5", fc=t["surface"], ec=t["border"], alpha=0.97),
            fontsize=8.5, color=t["text"], visible=False, zorder=10,
        )
        self.cid_move = chart.canvas.mpl_connect("motion_notify_event", self._on_move)
        self.cid_click = chart.canvas.mpl_connect("button_press_event", self._on_click)

    def disconnect(self):
        self.chart.canvas.mpl_disconnect(self.cid_move)
        self.chart.canvas.mpl_disconnect(self.cid_click)

    def _hide(self):
        if self.annot.get_visible():
            self.annot.set_visible(False)
            if self.on_change:
                self.on_change(None)
            self.chart.canvas.draw_idle()

    def _show(self, xy, text, key):
        xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()
        fx = (xy[0] - xlim[0]) / (xlim[1] - xlim[0]) if xlim[1] != xlim[0] else 0
        fy = (xy[1] - ylim[0]) / (ylim[1] - ylim[0]) if ylim[1] != ylim[0] else 0
        flip_x, flip_y = fx > 0.7, fy > 0.78
        self.annot.xyann = (-12 if flip_x else 12, -18 if flip_y else 12)
        self.annot.set_ha("right" if flip_x else "left")
        self.annot.xy = xy
        self.annot.set_text(text)
        self.annot.set_visible(True)
        if self.on_change:
            self.on_change(key)
        self.chart.canvas.draw_idle()

    def _on_move(self, event):
        if self.pinned:
            return
        if event.inaxes != self.ax:
            self._hide()
            return
        result = self.locate_fn(event)
        if result is None:
            self._hide()
            return
        xy, text, key = result
        self._show(xy, text, key)

    def _on_click(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
        if getattr(self.chart.toolbar, "mode", ""):
            return  # el usuario está usando la herramienta de pan/zoom, no seleccionar
        result = self.locate_fn(event)
        if result is None:
            if self.pinned:
                self.pinned = False
                self.pinned_key = None
                self._hide()
            return
        xy, text, key = result
        if self.pinned and key == self.pinned_key:
            self.pinned = False
            self.pinned_key = None
            self._hide()
        else:
            self.pinned = True
            self.pinned_key = key
            self._show(xy, text, key)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data = load_data()
        self.theme_name = "light"
        self.selected_regions = set(self.data["regions"])
        self._hover = {}
        self._current_data_df = None

        self.setWindowTitle("Panel ML — Desempleo Regional Colombia")
        self.resize(1280, 820)

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 14, 16, 10)
        root.setSpacing(10)

        root.addLayout(self._build_header())
        root.addLayout(self._build_kpis())

        body = QHBoxLayout()
        body.setSpacing(12)
        body.addWidget(self._build_sidebar(), 0)

        self.tabs = QTabWidget()
        self.chart_historico = Chart("historico_td_por_region")
        self.chart_modelos = Chart("comparacion_modelos")
        self.table_modelos = QTableWidget()
        self.chart_scatter = Chart("real_vs_predicho")
        self.chart_importance = Chart("variables_influyentes")
        self.chart_forecast = Chart("proyeccion_siguiente_semestre")

        self.tabs.addTab(self._wrap(self.chart_historico), "1. Histórico")
        self.tabs.addTab(self._build_modelos_tab(), "2. Modelos")
        self.tabs.addTab(self._wrap(self.chart_scatter), "3. Real vs. predicho")
        self.tabs.addTab(self._wrap(self.chart_importance), "4. Variables")
        self.tabs.addTab(self._wrap(self.chart_forecast), "5. Proyección")
        self.tabs.addTab(self._build_datos_tab(), "6. Datos")
        body.addWidget(self.tabs, 1)

        root.addLayout(body, 1)

        self._build_menu()
        self.status = self.statusBar()
        meta = self.data.get("generated_at", "—")
        self.status.showMessage(
            f"Generado el {meta}  ·  Fuente: DANE (GEIH, GEIH-ANEXOS, IMIE)  ·  {DATA_PATH}"
        )

        self.apply_theme()
        self.redraw_all()
        self._load_data_table()

    # ---------- layout builders ----------
    def _wrap(self, chart):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(chart)
        return w

    def _build_header(self):
        row = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Predicción de la tasa de desempleo regional en Colombia")
        title.setProperty("role", "title")
        subtitle = QLabel("Random Forest sobre panel región × semestre — GEIH, GEIH-ANEXOS, IMIE (DANE)")
        subtitle.setProperty("role", "subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        row.addLayout(title_box, 1)

        self.theme_btn = QPushButton("Tema oscuro")
        self.theme_btn.clicked.connect(self.toggle_theme)
        row.addWidget(self.theme_btn, 0, Qt.AlignmentFlag.AlignTop)
        return row

    def _kpi_card(self, label, value, sub, good=False):
        frame = QFrame()
        frame.setProperty("class", "kpiCard")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 10, 14, 10)
        lbl = QLabel(label)
        lbl.setProperty("role", "kpiLabel")
        val = QLabel(value)
        val.setProperty("role", "kpiValueGood" if good else "kpiValue")
        subl = QLabel(sub)
        subl.setProperty("role", "kpiSub")
        subl.setWordWrap(True)
        lay.addWidget(lbl)
        lay.addWidget(val)
        lay.addWidget(subl)
        return frame

    def _build_kpis(self):
        row = QHBoxLayout()
        row.setSpacing(10)
        metrics = {m["model"]: m for m in self.data["metrics_table"]}
        best = metrics[self.data["best_model"]]
        naive = metrics.get("NaiveRandomWalk", {})

        cards = [
            ("Mejor modelo", self.data["best_model_label"], f"de {len(self.data['metrics_table'])} modelos evaluados", False),
            ("Error medio (MAE)", f"{best['test_mae']:.2f} pts", f"vs. {naive.get('test_mae', 0):.2f} pts del baseline ingenuo", True),
            ("R² en test", f"{best['test_r2']:.2f}", f"baseline ingenuo: {naive.get('test_r2', 0):.2f}", False),
            ("Datos usados", f"{self.data['n_train'] + self.data['n_test']}", f"{self.data['n_train']} entren. · {self.data['n_test']} prueba (≥ {self.data['test_cutoff_year']})", False),
        ]
        self.kpi_frames = []
        for label, value, sub, good in cards:
            f = self._kpi_card(label, value, sub, good)
            self.kpi_frames.append(f)
            row.addWidget(f)
        return row

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(12, 14, 12, 14)
        lay.setSpacing(6)

        section = QLabel("FILTRO · REGIÓN")
        section.setProperty("role", "section")
        lay.addWidget(section)

        btn_row = QHBoxLayout()
        all_btn = QPushButton("Todas")
        none_btn = QPushButton("Ninguna")
        all_btn.clicked.connect(lambda: self._set_all_regions(True))
        none_btn.clicked.connect(lambda: self._set_all_regions(False))
        btn_row.addWidget(all_btn)
        btn_row.addWidget(none_btn)
        lay.addLayout(btn_row)
        lay.addSpacing(4)

        self.region_checks = {}
        for i, reg in enumerate(self.data["regions"]):
            cb = QCheckBox(reg)
            cb.setToolTip(reg)
            cb.setChecked(True)
            cb.stateChanged.connect(self._on_region_toggled)
            self.region_checks[reg] = cb
            lay.addWidget(cb)

        lay.addStretch(1)
        note = QLabel("El filtro afecta las páginas 1, 3 y 5 (por región). Modelos, Variables y Datos son globales.")
        note.setWordWrap(True)
        note.setProperty("role", "kpiSub")
        lay.addWidget(note)
        return sidebar

    def _build_datos_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(8)

        section = QLabel("VER EL ARCHIVO QUE ALIMENTA LOS GRÁFICOS")
        section.setProperty("role", "section")
        lay.addWidget(section)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Archivo:"))
        self.data_file_combo = QComboBox()
        for label, path in CSV_CATALOG:
            self.data_file_combo.addItem(label, str(path))
        self.data_file_combo.currentIndexChanged.connect(self._load_data_table)
        row1.addWidget(self.data_file_combo, 1)

        open_btn = QPushButton("Abrir con Excel")
        open_btn.setToolTip("Abre el CSV con el programa predeterminado de tu sistema (normalmente Excel)")
        open_btn.clicked.connect(self._open_current_data_file)
        row1.addWidget(open_btn)

        folder_btn = QPushButton("Abrir carpeta")
        folder_btn.clicked.connect(self._open_current_data_folder)
        row1.addWidget(folder_btn)
        lay.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Buscar:"))
        self.data_search = QLineEdit()
        self.data_search.setPlaceholderText("Filtra filas por cualquier columna (región, año, valor...)")
        self.data_search.textChanged.connect(self._filter_data_table)
        row2.addWidget(self.data_search, 1)
        self.data_rowcount_label = QLabel("")
        self.data_rowcount_label.setProperty("role", "kpiSub")
        row2.addWidget(self.data_rowcount_label)
        lay.addLayout(row2)

        self.data_table = QTableWidget()
        self.data_table.setSortingEnabled(True)
        self.data_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.data_table.setAlternatingRowColors(True)
        lay.addWidget(self.data_table, 1)

        section2 = QLabel("ARCHIVOS FUENTE ORIGINALES (EXCEL / ZIP DEL DANE)")
        section2.setProperty("role", "section")
        lay.addWidget(section2)
        src_row = QHBoxLayout()
        for label, path in SOURCE_FILES:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked=False, p=path: self._open_path(p))
            src_row.addWidget(btn)
        src_row.addStretch(1)
        lay.addLayout(src_row)

        return w

    def _build_modelos_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addWidget(self.chart_modelos)
        self.table_modelos.setColumnCount(5)
        self.table_modelos.setHorizontalHeaderLabels(["Modelo", "MAE test", "RMSE test", "R² test", "MAE CV (temporal)"])
        self.table_modelos.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_modelos.verticalHeader().setVisible(False)
        self.table_modelos.setFixedHeight(190)
        self.table_modelos.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.table_modelos)
        return w

    def _build_menu(self):
        menu = self.menuBar()
        m_file = menu.addMenu("&Archivo")

        act_reload = QAction("Recargar datos", self)
        act_reload.setShortcut("Ctrl+R")
        act_reload.triggered.connect(self.reload_data)
        m_file.addAction(act_reload)

        act_export = QAction("Exportar gráfico activo como PNG...", self)
        act_export.setShortcut("Ctrl+E")
        act_export.triggered.connect(self.export_current_chart)
        m_file.addAction(act_export)

        m_file.addSeparator()
        act_quit = QAction("Salir", self)
        act_quit.setShortcut("Ctrl+Q")
        act_quit.triggered.connect(self.close)
        m_file.addAction(act_quit)

        m_view = menu.addMenu("&Ver")
        act_theme = QAction("Cambiar tema claro/oscuro", self)
        act_theme.setShortcut("Ctrl+T")
        act_theme.triggered.connect(self.toggle_theme)
        m_view.addAction(act_theme)

    # ---------- interactions ----------
    def _set_all_regions(self, checked):
        for cb in self.region_checks.values():
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)
        self._on_region_toggled()

    def _on_region_toggled(self):
        self.selected_regions = {r for r, cb in self.region_checks.items() if cb.isChecked()}
        self.draw_historico()
        self.draw_scatter()
        self.draw_forecast()

    def _load_data_table(self):
        path = Path(self.data_file_combo.currentData())
        if not path.exists():
            self._current_data_df = None
            self.data_table.setRowCount(0)
            self.data_table.setColumnCount(0)
            self.data_rowcount_label.setText("Archivo no encontrado — corre pipelines/pipeline_ml.py")
            return
        try:
            df = pd.read_csv(path)
        except Exception as exc:
            QMessageBox.warning(self, "No se pudo leer el archivo", f"{path}\n\n{exc}")
            return
        self._current_data_df = df
        self.data_search.blockSignals(True)
        self.data_search.clear()
        self.data_search.blockSignals(False)

        self.data_table.setSortingEnabled(False)
        self.data_table.setColumnCount(len(df.columns))
        self.data_table.setHorizontalHeaderLabels([str(c) for c in df.columns])
        self.data_table.setRowCount(len(df))
        for i in range(len(df)):
            for j, col in enumerate(df.columns):
                val = df.iat[i, j]
                text = "" if pd.isna(val) else str(val)
                item = QTableWidgetItem(text)
                if isinstance(val, (int, float)) and not pd.isna(val):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.data_table.setItem(i, j, item)
        self.data_table.setSortingEnabled(True)
        self.data_table.resizeColumnsToContents()
        self.data_rowcount_label.setText(f"{len(df)} filas · {len(df.columns)} columnas")

    def _filter_data_table(self, text):
        text = text.strip().lower()
        total = self.data_table.rowCount()
        visible = 0
        for i in range(total):
            match = not text
            if not match:
                for j in range(self.data_table.columnCount()):
                    item = self.data_table.item(i, j)
                    if item and text in item.text().lower():
                        match = True
                        break
            self.data_table.setRowHidden(i, not match)
            visible += int(match)
        suffix = f"{visible} de {total} filas" if text else f"{total} filas · {self.data_table.columnCount()} columnas"
        self.data_rowcount_label.setText(suffix)

    def _open_current_data_file(self):
        self._open_path(Path(self.data_file_combo.currentData()))

    def _open_current_data_folder(self):
        self._open_path(Path(self.data_file_combo.currentData()).parent)

    def _open_path(self, path):
        path = Path(path)
        if not path.exists():
            QMessageBox.warning(
                self, "No encontrado",
                f"No se encontró:\n{path}\n\n"
                "Si estás usando la app empaquetada (.exe), esta función funciona "
                "mejor corriendo 'python dashboard_app.py' desde la carpeta del proyecto."
            )
            return
        try:
            open_with_default_app(path)
        except Exception as exc:
            QMessageBox.warning(self, "No se pudo abrir", f"{path}\n\n{exc}")

    def reload_data(self):
        try:
            self.data = load_data()
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "No se encontraron datos", str(exc))
            return
        self.status.showMessage(
            f"Generado el {self.data.get('generated_at', '—')}  ·  Fuente: DANE (GEIH, GEIH-ANEXOS, IMIE)  ·  {DATA_PATH}"
        )
        self.redraw_all()
        self._load_data_table()
        QMessageBox.information(self, "Datos recargados", "El panel se actualizó con los datos más recientes.")

    def export_current_chart(self):
        idx = self.tabs.currentIndex()
        charts = [self.chart_historico, self.chart_modelos, self.chart_scatter,
                  self.chart_importance, self.chart_forecast]
        if idx >= len(charts):
            QMessageBox.information(
                self, "Nada que exportar",
                "La pestaña 'Datos' no tiene un gráfico — usa 'Abrir con Excel' para exportar/editar la tabla."
            )
            return
        charts[idx].export_png(self)

    def toggle_theme(self):
        self.theme_name = "dark" if self.theme_name == "light" else "light"
        self.theme_btn.setText("Tema oscuro" if self.theme_name == "light" else "Tema claro")
        self.apply_theme()
        self.redraw_all()

    def apply_theme(self):
        t = DARK if self.theme_name == "dark" else LIGHT
        self.setStyleSheet(qss(t))

    # ---------- chart drawing ----------
    def theme(self):
        return DARK if self.theme_name == "dark" else LIGHT

    def _attach_hover(self, chart, ax, t, locate_fn, on_change=None):
        """(Re)conecta un HoverTooltip para un gráfico, desconectando el
        anterior — hay que rehacerlo en cada redraw porque fig.clear()
        invalida los artistas (ax, anotación) que usaba el anterior."""
        old = self._hover.get(chart.title)
        if old is not None:
            old.disconnect()
        ht = HoverTooltip(chart, ax, t, locate_fn, on_change)
        self._hover[chart.title] = ht
        return ht

    def redraw_all(self):
        self.draw_historico()
        self.draw_modelos()
        self.draw_scatter()
        self.draw_importance()
        self.draw_forecast()

    def draw_historico(self):
        t = self.theme()
        fig = self.chart_historico.fig
        fig.clear()
        fig.patch.set_facecolor(t["surface"])
        ax = fig.add_subplot(111)
        for i, reg in enumerate(self.data["regions"]):
            if reg not in self.selected_regions:
                continue
            pts = self.data["historico"][reg]
            xs = [p["t"] for p in pts]
            ys = [p["td"] for p in pts]
            ax.plot(xs, ys, label=reg, color=t["series"][i % len(t["series"])], linewidth=2.1)
        ax.set_ylabel("TD (%)")
        ax.set_title("Tasa de desocupación por región (2010–2025)", color=t["text"], fontsize=11, loc="left", fontweight="bold")
        if self.selected_regions:
            ax.legend(loc="upper right", fontsize=8, frameon=False, labelcolor=t["text2"])
        else:
            ax.text(0.5, 0.5, "Ninguna región seleccionada", ha="center", va="center",
                    color=t["muted"], transform=ax.transAxes)

        all_ts = sorted({p["t"] for reg in self.selected_regions for p in self.data["historico"][reg]})
        # fija el rango del eje X a partir de los datos reales ANTES de agregar
        # la línea guía invisible de abajo — si no, una línea en x=0 (fuera del
        # rango 2010-2025) hace que autoscale estire el eje hasta 0 y comprima
        # todo el histórico en una franja angosta a la derecha.
        if all_ts:
            span = max(all_ts) - min(all_ts)
            pad = span * 0.02 if span > 0 else 0.5
            ax.set_xlim(min(all_ts) - pad, max(all_ts) + pad)
        style_axes(ax, t)

        vline = ax.axvline(
            x=all_ts[0] if all_ts else 0, color=t["muted"], linestyle="--", linewidth=1, visible=False
        )

        def locate(event):
            if event.xdata is None or not all_ts:
                return None
            nearest_t = min(all_ts, key=lambda tt: abs(tt - event.xdata))
            lines = []
            for reg in self.data["regions"]:
                if reg not in self.selected_regions:
                    continue
                p = next((pp for pp in self.data["historico"][reg] if pp["t"] == nearest_t), None)
                if p:
                    lines.append(f"{reg}: {p['td']:.1f}%")
            if not lines:
                return None
            anio = int(nearest_t)
            periodo = "I" if abs(nearest_t - anio) < 0.25 else "II"
            text = f"{anio} · Semestre {periodo}\n" + "\n".join(lines)
            y = event.ydata if event.ydata is not None else sum(ax.get_ylim()) / 2
            return (nearest_t, y), text, nearest_t

        def on_change(nearest_t):
            if nearest_t is None:
                vline.set_visible(False)
            else:
                vline.set_xdata([nearest_t, nearest_t])
                vline.set_visible(True)

        self._attach_hover(self.chart_historico, ax, t, locate, on_change)
        self.chart_historico.connect_scroll_zoom(ax)
        fig.tight_layout()
        self.chart_historico.canvas.draw()

    def draw_modelos(self):
        t = self.theme()
        fig = self.chart_modelos.fig
        fig.clear()
        fig.patch.set_facecolor(t["surface"])
        ax = fig.add_subplot(111)

        rows = sorted(self.data["metrics_table"], key=lambda r: r["test_mae"])
        labels = [r["label"] for r in rows]
        values = [r["test_mae"] for r in rows]
        colors = [
            t["good"] if r["model"] == self.data["best_model"]
            else (t["muted"] if r["model"] == "NaiveRandomWalk" else t["series"][0])
            for r in rows
        ]
        y_pos = range(len(rows))
        bars = ax.barh(list(y_pos), values, color=colors, height=0.55)
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels)
        ax.invert_yaxis()
        ax.set_xlabel("MAE en test (puntos porcentuales)")
        ax.set_title("Comparación de modelos", color=t["text"], fontsize=11, loc="left", fontweight="bold")
        for bar, v in zip(bars, values):
            ax.text(bar.get_width() + max(values) * 0.015, bar.get_y() + bar.get_height() / 2,
                    f"{v:.2f}", va="center", fontsize=8.5, color=t["text"])
        style_axes(ax, t)
        ax.grid(axis="y", visible=False)

        def locate(event):
            for bar, r in zip(bars, rows):
                contains, _ = bar.contains(event)
                if contains:
                    cv = f"{r['cv_mae_mean']:.2f} ± {r['cv_mae_std']:.2f}" if r.get("cv_mae_mean") is not None else "—"
                    text = (
                        f"{r['label']}\nMAE test: {r['test_mae']:.2f} pts\n"
                        f"RMSE test: {r['test_rmse']:.2f}\nR² test: {r['test_r2']:.2f}\n"
                        f"MAE CV (temporal): {cv}"
                    )
                    return (bar.get_width(), bar.get_y() + bar.get_height() / 2), text, r["model"]
            return None

        self._attach_hover(self.chart_modelos, ax, t, locate)
        self.chart_modelos.connect_scroll_zoom(ax)
        fig.tight_layout()
        self.chart_modelos.canvas.draw()

        self.table_modelos.setRowCount(len(rows))
        for i, r in enumerate(rows):
            cv = f"{r['cv_mae_mean']:.2f} ± {r['cv_mae_std']:.2f}" if r.get("cv_mae_mean") is not None else "—"
            values_row = [r["label"], f"{r['test_mae']:.2f}", f"{r['test_rmse']:.2f}", f"{r['test_r2']:.2f}", cv]
            for j, val in enumerate(values_row):
                item = QTableWidgetItem(val)
                if j > 0:
                    item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table_modelos.setItem(i, j, item)

    def draw_scatter(self):
        t = self.theme()
        fig = self.chart_scatter.fig
        fig.clear()
        fig.patch.set_facecolor(t["surface"])
        ax = fig.add_subplot(111)

        pts = [p for p in self.data["test_scatter"] if p["region"] in self.selected_regions]
        if pts:
            all_v = [p["y_true"] for p in pts] + [p["pred_best"] for p in pts]
            lo, hi = min(all_v) - 1, max(all_v) + 1
            ax.plot([lo, hi], [lo, hi], linestyle="--", color=t["muted"], linewidth=1)
            for i, reg in enumerate(self.data["regions"]):
                reg_pts = [p for p in pts if p["region"] == reg]
                if not reg_pts:
                    continue
                ax.scatter([p["y_true"] for p in reg_pts], [p["pred_best"] for p in reg_pts],
                           label=reg, color=t["series"][i % len(t["series"])], s=42, alpha=0.9,
                           edgecolors=t["surface"], linewidths=0.8)
            ax.legend(loc="upper left", fontsize=7.5, frameon=False, labelcolor=t["text2"])
        else:
            ax.text(0.5, 0.5, "Ninguna región seleccionada", ha="center", va="center",
                    color=t["muted"], transform=ax.transAxes)
        ax.set_xlabel("TD real (%)")
        ax.set_ylabel(f"TD predicho — {self.data['best_model_label']} (%)")
        ax.set_title("Real vs. predicho (set de prueba)", color=t["text"], fontsize=11, loc="left", fontweight="bold")
        style_axes(ax, t)

        def locate(event):
            if not pts:
                return None
            mx, my = event.x, event.y
            disp = ax.transData.transform([(p["y_true"], p["pred_best"]) for p in pts])
            dists = ((disp[:, 0] - mx) ** 2 + (disp[:, 1] - my) ** 2) ** 0.5
            idx = int(dists.argmin())
            if dists[idx] > 18:
                return None
            p = pts[idx]
            text = (
                f"{p['region']} · {p['anio']}-{p['periodo']}\n"
                f"Real: {p['y_true']:.2f}%\nPredicho: {p['pred_best']:.2f}%"
            )
            return (p["y_true"], p["pred_best"]), text, (p["region"], p["anio"], p["periodo"])

        self._attach_hover(self.chart_scatter, ax, t, locate)
        self.chart_scatter.connect_scroll_zoom(ax)
        fig.tight_layout()
        self.chart_scatter.canvas.draw()

    def draw_importance(self):
        t = self.theme()
        fig = self.chart_importance.fig
        fig.clear()
        fig.patch.set_facecolor(t["surface"])
        ax = fig.add_subplot(111)

        rows = list(reversed(self.data["importance"]))
        labels = [r["label"] for r in rows]
        values = [r["importance"] for r in rows]
        y_pos = range(len(rows))
        bars = ax.barh(list(y_pos), values, color=t["series"][0], height=0.6)
        ax.set_yticks(list(y_pos))
        ax.set_yticklabels(labels, fontsize=8)
        ax.set_xlabel("Importancia relativa")
        ax.set_title(f"Variables más influyentes — {self.data['best_model_label']}", color=t["text"], fontsize=11, loc="left", fontweight="bold")
        for i, v in enumerate(values):
            ax.text(v + max(values) * 0.015, i, f"{v * 100:.1f}%", va="center", fontsize=8, color=t["text"])
        style_axes(ax, t)
        ax.grid(axis="y", visible=False)

        def locate(event):
            for bar, r in zip(bars, rows):
                contains, _ = bar.contains(event)
                if contains:
                    text = f"{r['label']}\nImportancia: {r['importance'] * 100:.1f}%"
                    return (bar.get_width(), bar.get_y() + bar.get_height() / 2), text, r["label"]
            return None

        self._attach_hover(self.chart_importance, ax, t, locate)
        self.chart_importance.connect_scroll_zoom(ax)
        fig.tight_layout()
        self.chart_importance.canvas.draw()

    def draw_forecast(self):
        t = self.theme()
        fig = self.chart_forecast.fig
        fig.clear()
        fig.patch.set_facecolor(t["surface"])
        ax = fig.add_subplot(111)

        rows = [r for r in self.data["forecast"] if r["region"] in self.selected_regions]
        bars_base, bars_fc = [], []
        if rows:
            regions = [r["region"] for r in rows]
            base = [r["td_base"] for r in rows]
            fc = [r["td_forecast"] for r in rows]
            y = range(len(rows))
            h = 0.35
            bars_base = ax.barh([yy + h / 2 for yy in y], base, height=h, color=t["muted"], alpha=0.8, label="TD actual")
            bars_fc = ax.barh([yy - h / 2 for yy in y], fc, height=h, color=t["series"][0], label="TD proyectada")
            ax.set_yticks(list(y))
            ax.set_yticklabels(regions)
            ax.invert_yaxis()
            for yy, v in zip(y, base):
                ax.text(v + max(base + fc) * 0.01, yy + h / 2, f"{v:.1f}%", va="center", fontsize=8, color=t["text"])
            for yy, v in zip(y, fc):
                ax.text(v + max(base + fc) * 0.01, yy - h / 2, f"{v:.1f}%", va="center", fontsize=8, color=t["text"])
            ax.legend(loc="lower right", fontsize=8, frameon=False, labelcolor=t["text2"])
            r0 = rows[0]
            ax.set_title(
                f"Proyección {r0['periodo_base']} {r0['anio_base']} → {r0['periodo_forecast']} {r0['anio_forecast']}",
                color=t["text"], fontsize=11, loc="left", fontweight="bold")
        else:
            ax.text(0.5, 0.5, "Ninguna región seleccionada", ha="center", va="center",
                    color=t["muted"], transform=ax.transAxes)
        style_axes(ax, t)
        ax.grid(axis="y", visible=False)

        def locate(event):
            for bar, r in zip(bars_base, rows):
                contains, _ = bar.contains(event)
                if contains:
                    text = f"{r['region']}\nTD actual: {r['td_base']:.2f}%\n({r['periodo_base']} {r['anio_base']})"
                    return (bar.get_width(), bar.get_y() + bar.get_height() / 2), text, (r["region"], "base")
            for bar, r in zip(bars_fc, rows):
                contains, _ = bar.contains(event)
                if contains:
                    text = f"{r['region']}\nTD proyectada: {r['td_forecast']:.2f}%\n({r['periodo_forecast']} {r['anio_forecast']})"
                    return (bar.get_width(), bar.get_y() + bar.get_height() / 2), text, (r["region"], "fc")
            return None

        self._attach_hover(self.chart_forecast, ax, t, locate)
        self.chart_forecast.connect_scroll_zoom(ax)
        fig.tight_layout()
        self.chart_forecast.canvas.draw()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Panel ML — Desempleo Regional")
    try:
        win = MainWindow()
    except FileNotFoundError as exc:
        QMessageBox.critical(None, "Faltan datos", str(exc))
        sys.exit(1)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
