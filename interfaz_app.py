#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interfaz Gráfica Interactiva (tkinter / ttk) para el Sistema de Monitoreo Colaborativo
y Alerta Temprana de Arroyos – Zona Universidad del Norte.

Integra:
  - Nuevo mapa panorámico de gran perspectiva (con la Ciénaga de Mallorquín integrada)
    y opción de conmutar al mapa detallado del campus.
  - Unidad 3 (MSc Iván Gómez & Prof. Yesneri Zuleta): Vecindades abiertas/cerradas/dirigidas,
    extremos δ(G) y Δ(G), Lema del Apretón de Manos y Corolario, Bipartición V1∪V2,
    Subgrafo inducido G - v, Euler/Hamilton (Dirac/Ore), Planaridad (V-E+F=2),
    Trazas BFS vs. DFS paso a paso, Árboles con raíz, Dijkstra, Kruskal y Prim (MST).
  - Unidad 4 (MSc Iván Gómez): Receta del proyecto final, 4 preguntas de modelación,
    Distancias geodésicas BFS y diámetro, Centralidad de Grado C_D(v), Cercanía C_C(v)
    (y variante armónica H(v)), Intermediación C_B(v) y Red Bipartita Ciudadanos–Nodos.
  - Función discreta de transición de estados de alerta y Consenso Booleano C(R, k).
"""

from __future__ import annotations

import math
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Set, Tuple

from modelo_discreto import (
    COLORES,
    ControlEstados,
    CuencaDAG,
    DESCRIPCION,
    Estado,
    Simbolo,
    ValidadorConsenso,
    crear_cuenca_uninorte,
)
from recursos_mapa import (
    MAPA_BARRANQUILLA_GOOGLE_B64,
    MAPA_PANORAMICO_B64,
    MAPA_PNG_B64,
)
from sistema_alerta import SistemaAlerta


class App(tk.Tk):
    RADIO = 15

    # Dimensiones del lienzo del mapa (Cercanías Uninorte: 920 x 474)
    CANVAS_W, CANVAS_H = 920, 474

    # Coordenadas georreferenciadas sobre el MAPA DE CERCANÍAS UNINORTE (920 x 474)
    # Cubre el corredor Uninorte / Villa Julia / Cra 53 / Villa Campestre / Eduardo Santos / Arroyo León / Mallorquín
    POS_GOOGLE: Dict[str, Tuple[int, int]] = {
        "N1": (555, 445),  # Entrada Circunvalar / Cra 51B (Villa Julia)
        "N2": (745, 405),  # Rotonda Makro / Cra 53 (PriceSmart)
        "N3": (645, 340),  # Depresión Portoazul / Corredor Universitario
        "N4": (495, 400),  # Frente Uninorte / Cra 51B (Puerta 1)
        "N5": (545, 360),  # Drenaje interno campus Uninorte
        "N6": (405, 330),  # Box-culvert Villa Campestre / Cra 51B
        "N7": (345, 255),  # Confluencia canal colector perimetral (Eduardo Santos)
        "N8": (425, 215),  # Arroyo León (Troncal / Vía La Playa)
        "N9": (495, 95),   # Ciénaga de Mallorquín
    }
    ETIQUETA_ARRIBA_GOOGLE = {"N1", "N3", "N5", "N7", "N8", "N9"}

    # Geometría vial calle por calle sobre el lienzo (920 x 474) para que las rutas sigan las avenidas reales
    TRAZADO_CALLES_GOOGLE: Dict[Tuple[str, str], List[Tuple[int, int]]] = {
        ("N1", "N4"): [(555, 445), (515, 428), (495, 400)],
        ("N1", "N2"): [(555, 445), (595, 455), (645, 463), (698, 462), (722, 435), (745, 405)],
        ("N2", "N3"): [(745, 405), (752, 382), (730, 375), (695, 360), (645, 340)],
        ("N3", "N5"): [(645, 340), (625, 355), (590, 358), (545, 360)],
        ("N4", "N5"): [(495, 400), (520, 382), (545, 360)],
        ("N4", "N6"): [(495, 400), (455, 392), (432, 365), (405, 330)],
        ("N6", "N7"): [(405, 330), (390, 315), (390, 280), (365, 272), (345, 255)],
        ("N5", "N7"): [(545, 360), (510, 342), (485, 322), (450, 300), (415, 282), (388, 274), (345, 255)],
        ("N3", "N7"): [(645, 340), (625, 315), (550, 295), (485, 280), (425, 232), (402, 268), (368, 268), (345, 255)],
        ("N7", "N8"): [(345, 255), (368, 268), (402, 268), (418, 242), (425, 215)],
        ("N8", "N9"): [(425, 215), (445, 175), (470, 135), (495, 95)],
    }

    # Coordenadas sobre el NUEVO MAPA PANORÁMICO (800×540)
    POS_PANORAMICO: Dict[str, Tuple[int, int]] = {
        "N1": (522, 452),
        "N2": (560, 405),
        "N3": (502, 362),
        "N4": (425, 442),
        "N5": (398, 392),
        "N6": (308, 430),
        "N7": (242, 355),
        "N8": (192, 265),
        "N9": (335, 165),
    }
    ETIQUETA_ARRIBA_PANORAMICO = {"N2", "N3", "N5", "N8", "N9"}

    # Coordenadas sobre el mapa original cercano al campus (con franja izquierda)
    MARGEN_CAMPUS = 130
    POS_CAMPUS: Dict[str, Tuple[int, int]] = {
        "N1": (503, 228),
        "N2": (563, 205),
        "N3": (466, 154),
        "N4": (318, 224),
        "N5": (369, 183),
        "N6": (216, 228),
        "N7": (164, 174),
        "N8": (65, 215),
        "N9": (65, 110),
    }
    ETIQUETA_ARRIBA_CAMPUS = {"N3", "N5", "N9"}

    def __init__(self) -> None:
        super().__init__()
        self.title(
            "Alerta Temprana de Arroyos – Uninorte (Matemáticas Discretas: Grafos, Árboles y Redes)"
        )
        self.geometry("1440x810")
        self.minsize(1300, 720)
        self.configure(bg="#f1f5f9")

        self._configurar_estilos()

        self.cuenca: CuencaDAG = crear_cuenca_uninorte()
        self.sistema: SistemaAlerta = SistemaAlerta(self.cuenca, k=3, log=self._log)
        self.seleccion: str = "N4"

        # Opciones visuales del mapa
        self.modo_mapa_var = tk.StringVar(value="google")  # "google", "panoramico" o "campus"
        self.animar_bfs_var = tk.BooleanVar(value=True)
        self.mostrar_pesos_var = tk.BooleanVar(value=True)
        self.capa_resaltado_var = tk.StringVar(value="ruta")  # por defecto en modo Ruta Segura

        # Opciones de Navegación / Ruta Segura ("Google Maps de Arroyos")
        self.origen_ruta_id: str = "N1"
        self.destino_ruta_id: str = "N6"
        self.evitar_preventivos_var = tk.BooleanVar(value=False)
        self.hora_pico_var = tk.BooleanVar(value=False)
        self.resumen_ruta_var = tk.StringVar(
            value="Selecciona Origen y Destino para trazar la ruta óptima libre de arroyos."
        )

        self._after_id_bfs: Optional[str] = None
        self._nodos_onda_actual: Set[str] = set()
        self._distancias_onda: Dict[str, int] = {}

        # Carga de imágenes de mapa en memoria
        self.mapa_google: Optional[tk.PhotoImage] = None
        self.mapa_panoramico: Optional[tk.PhotoImage] = None
        self.mapa_campus: Optional[tk.PhotoImage] = None
        try:
            self.mapa_google = tk.PhotoImage(data="".join(MAPA_BARRANQUILLA_GOOGLE_B64.split()))
        except tk.TclError:
            self.mapa_google = None
        try:
            self.mapa_panoramico = tk.PhotoImage(data="".join(MAPA_PANORAMICO_B64.split()))
        except tk.TclError:
            self.mapa_panoramico = None
        try:
            self.mapa_campus = tk.PhotoImage(data="".join(MAPA_PNG_B64.split()))
        except tk.TclError:
            self.mapa_campus = None

        self.mapa_combo: Dict[str, str] = {
            f"{n.id} · {n.nombre}": n.id for n in self.cuenca.nodos.values()
        }

        self._construir_ui()
        self._mensajes_iniciales()
        self._dibujar()

    @property
    def pos_actual(self) -> Dict[str, Tuple[int, int]]:
        if self.modo_mapa_var.get() == "google":
            return self.POS_GOOGLE
        elif self.modo_mapa_var.get() == "panoramico":
            return self.POS_PANORAMICO
        return self.POS_CAMPUS

    @property
    def etiquetas_arriba_actual(self) -> Set[str]:
        if self.modo_mapa_var.get() == "google":
            return self.ETIQUETA_ARRIBA_GOOGLE
        elif self.modo_mapa_var.get() == "panoramico":
            return self.ETIQUETA_ARRIBA_PANORAMICO
        return self.ETIQUETA_ARRIBA_CAMPUS

    # -- estilos visuales ttk -------------------------------------------------
    def _configurar_estilos(self) -> None:
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure(".", font=("Segoe UI", 9), background="#f1f5f9")
        style.configure("TFrame", background="#f1f5f9")
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure(
            "TLabelframe",
            background="#ffffff",
            bordercolor="#cbd5e1",
            relief="solid",
        )
        style.configure(
            "TLabelframe.Label",
            background="#ffffff",
            foreground="#0f172a",
            font=("Segoe UI", 9, "bold"),
        )
        style.configure("TLabel", background="#ffffff", foreground="#1e293b")
        style.configure("Bg.TLabel", background="#f1f5f9", foreground="#1e293b")
        style.configure("TCheckbutton", background="#ffffff", foreground="#1e293b")
        style.configure("TRadiobutton", background="#ffffff", foreground="#1e293b")
        style.configure(
            "Primary.TButton",
            font=("Segoe UI", 9, "bold"),
            background="#1d4ed8",
            foreground="#ffffff",
            padding=(8, 5),
        )
        style.map(
            "Primary.TButton",
            background=[("active", "#1e40af"), ("pressed", "#1e3a8a")],
        )
        style.configure(
            "Danger.TButton",
            font=("Segoe UI", 9, "bold"),
            background="#b91c1c",
            foreground="#ffffff",
            padding=(8, 5),
        )
        style.map(
            "Danger.TButton",
            background=[("active", "#991b1b"), ("pressed", "#7f1d1d")],
        )
        style.configure(
            "Action.TButton",
            font=("Segoe UI", 9),
            background="#e2e8f0",
            foreground="#0f172a",
            padding=(6, 4),
        )
        style.map("Action.TButton", background=[("active", "#cbd5e1")])
        style.configure("TNotebook", background="#f1f5f9", tabmargins=[2, 4, 2, 0])
        style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 9, "bold"),
            padding=[9, 5],
            background="#e2e8f0",
            foreground="#334155",
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#ffffff")],
            foreground=[("selected", "#1d4ed8")],
        )
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 8, "bold"),
            background="#e2e8f0",
            foreground="#0f172a",
        )
        style.configure("Treeview", font=("Consolas", 8), rowheight=21)

    # -- construcción de widgets ----------------------------------------------
    def _construir_ui(self) -> None:
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # =====================================================================
        # COLUMNA IZQUIERDA: Barra superior + Mapa Panorámico + Capas + Leyenda
        # =====================================================================
        col_izq = ttk.Frame(self)
        col_izq.grid(row=0, column=0, sticky="nsew", padx=(10, 6), pady=8)

        # 1. Barra superior de métricas y selector de mapa
        barra_sup = ttk.Frame(col_izq, style="Card.TFrame")
        barra_sup.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        barra_sup.columnconfigure(0, weight=1)

        self.metricas_var = tk.StringVar()
        ttk.Label(
            barra_sup,
            textvariable=self.metricas_var,
            font=("Segoe UI", 9, "bold"),
            foreground="#0f172a",
        ).grid(row=0, column=0, sticky="w", padx=10, pady=5)

        marco_vista = ttk.Frame(barra_sup, style="Card.TFrame")
        marco_vista.grid(row=0, column=1, sticky="e", padx=8, pady=4)
        ttk.Label(
            marco_vista,
            text="📍 Mapa: Cercanías Uninorte",
            font=("Segoe UI", 9, "bold"),
            foreground="#1e40af",
        ).pack(side="left", padx=(0, 10))

        ttk.Button(
            marco_vista,
            text="🌐 Abrir Google Maps con Zoom & Movimiento",
            style="Primary.TButton",
            command=self._abrir_mapa_web_interactivo,
        ).pack(side="left")

        # 2. Barra de capas matemáticas superpuestas sobre el mapa
        barra_capas = ttk.Frame(col_izq, style="Card.TFrame")
        barra_capas.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        ttk.Label(
            barra_capas,
            text="Superponer en mapa:",
            font=("Segoe UI", 8, "bold"),
        ).pack(side="left", padx=(10, 6), pady=4)

        for texto_c, val_c in [
            ("Normal", "ninguna"),
            ("🧭 Ruta Segura", "ruta"),
            ("Subgrafo BFS", "bfs"),
            ("MST (Kruskal/Prim)", "mst"),
            ("Camino Crítico", "critico"),
            ("Bipartición (V₁/V₂)", "bipartito"),
        ]:
            ttk.Radiobutton(
                barra_capas,
                text=texto_c,
                value=val_c,
                variable=self.capa_resaltado_var,
                command=self._dibujar,
            ).pack(side="left", padx=4)

        ttk.Checkbutton(
            barra_capas,
            text="Pesos w(u,v)",
            variable=self.mostrar_pesos_var,
            command=self._dibujar,
        ).pack(side="right", padx=10)

        # 3. Lienzo del mapa (800 x 540)
        self.canvas = tk.Canvas(
            col_izq,
            width=self.CANVAS_W,
            height=self.CANVAS_H,
            bg="#dbeafe",
            highlightthickness=1,
            highlightbackground="#94a3b8",
        )
        self.canvas.grid(row=2, column=0, sticky="nw")

        # 4. Barra de estado bajo el mapa
        self.estado_mapa_var = tk.StringVar(
            value="Clic en un vértice para inspeccionarlo · Doble clic para enviar un reporte ciudadano."
        )
        ttk.Label(
            col_izq,
            textvariable=self.estado_mapa_var,
            style="Bg.TLabel",
            font=("Segoe UI", 8, "italic"),
        ).grid(row=3, column=0, sticky="ew", pady=(3, 3))

        # 5. Leyenda de niveles de alerta en los vértices
        leyenda = ttk.LabelFrame(col_izq, text="Niveles Discretos de Alerta en los Vértices (Q)")
        leyenda.grid(row=4, column=0, sticky="ew")
        for i, est in enumerate(Estado):
            marco = ttk.Frame(leyenda, style="Card.TFrame")
            marco.grid(row=0, column=i, padx=10, pady=4, sticky="w")
            c = tk.Canvas(marco, width=16, height=16, bg="#ffffff", highlightthickness=0)
            c.create_oval(2, 2, 14, 14, fill=COLORES[est], outline="#222222", width=1.4)
            c.pack(side="left")
            etq_q = " (Crítico)" if est in ControlEstados.F else (" (Inicial)" if est is ControlEstados.Q0 else "")
            ttk.Label(
                marco,
                text=f"{est.value}{etq_q} – {DESCRIPCION[est]}",
                font=("Segoe UI", 8, "bold" if est is Estado.ROJO else "normal"),
            ).pack(side="left", padx=4)

        # =====================================================================
        # COLUMNA DERECHA: Control, Navegación y Monitoreo de Arroyos
        # =====================================================================
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=1, sticky="nsew", padx=(4, 10), pady=8)

        self.tab_control = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_control, text=" 🧭 Navegación y Monitoreo de Arroyos ")

        self._construir_tab_control()

    # -- Pestaña 1: Control y Bitácora ----------------------------------------
    def _construir_tab_control(self) -> None:
        tab = self.tab_control
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(3, weight=1)

        ctrl = ttk.LabelFrame(tab, text="Panel de Control y Simulación Hidrológica")
        ctrl.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 3))
        ctrl.columnconfigure(0, weight=1)
        ctrl.columnconfigure(1, weight=1)

        ttk.Label(ctrl, text="Vértice / Punto de monitoreo (v ∈ V):").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 0)
        )
        self.combo = ttk.Combobox(ctrl, state="readonly", values=list(self.mapa_combo))
        self.combo.set(f"{self.seleccion} · {self.cuenca.nodos[self.seleccion].nombre}")
        self.combo.grid(row=1, column=0, columnspan=2, sticky="ew", padx=8, pady=3)
        self.combo.bind("<<ComboboxSelected>>", self._on_combo)

        fila_param = ttk.Frame(ctrl, style="Card.TFrame")
        fila_param.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=2)
        ttk.Label(fila_param, text="Umbral de consenso k:").pack(side="left")
        self.k_var = tk.IntVar(value=self.sistema.k)
        ttk.Spinbox(
            fila_param,
            from_=1,
            to=10,
            width=4,
            textvariable=self.k_var,
            command=self._on_k,
        ).pack(side="left", padx=(6, 14))
        self.k_var.trace_add("write", lambda *_: self._on_k())

        ttk.Checkbutton(
            fila_param,
            text="Animar propagación BFS por capas",
            variable=self.animar_bfs_var,
        ).pack(side="left")

        ttk.Button(
            ctrl,
            text="📢 Enviar Reporte Ciudadano (+1 a R_v)",
            style="Primary.TButton",
            command=self._on_reporte,
        ).grid(row=3, column=0, columnspan=2, sticky="ew", padx=8, pady=(4, 2))

        ttk.Button(
            ctrl,
            text="🌊 Simular Crecida en Cabecera (N1, N2)",
            style="Danger.TButton",
            command=self._on_crecida,
        ).grid(row=4, column=0, columnspan=2, sticky="ew", padx=8, pady=2)

        ttk.Button(
            ctrl,
            text="🔄 Reiniciar Red",
            style="Action.TButton",
            command=self._on_reiniciar,
        ).grid(row=5, column=0, sticky="ew", padx=(8, 4), pady=(2, 6))

        ttk.Button(
            ctrl,
            text="💾 Exportar Informe (.txt)",
            style="Action.TButton",
            command=self._on_exportar,
        ).grid(row=5, column=1, sticky="ew", padx=(4, 8), pady=(2, 6))

        # ---------------------------------------------------------------------
        # Navegador Ciudadano ("Google Maps de Arroyos") con Dijkstra + Subgrafo Seguro
        # ---------------------------------------------------------------------
        nav = ttk.LabelFrame(
            tab,
            text="🧭 Navegador de Ruta Segura (Tipo Google Maps sin Arroyos — Dijkstra en G - V_bloq)",
        )
        nav.grid(row=1, column=0, sticky="ew", padx=6, pady=3)
        nav.columnconfigure(1, weight=1)
        nav.columnconfigure(3, weight=1)

        ttk.Label(nav, text="Origen (s):").grid(row=0, column=0, sticky="w", padx=(8, 2), pady=3)
        self.combo_origen_ruta = ttk.Combobox(
            nav, state="readonly", values=list(self.mapa_combo), width=22
        )
        self.combo_origen_ruta.set(
            f"{self.origen_ruta_id} · {self.cuenca.nodos[self.origen_ruta_id].nombre}"
        )
        self.combo_origen_ruta.grid(row=0, column=1, sticky="ew", padx=(2, 6), pady=3)
        self.combo_origen_ruta.bind("<<ComboboxSelected>>", self._on_cambio_param_ruta)

        ttk.Label(nav, text="Destino (t):").grid(row=0, column=2, sticky="w", padx=(4, 2), pady=3)
        self.combo_destino_ruta = ttk.Combobox(
            nav, state="readonly", values=list(self.mapa_combo), width=22
        )
        self.combo_destino_ruta.set(
            f"{self.destino_ruta_id} · {self.cuenca.nodos[self.destino_ruta_id].nombre}"
        )
        self.combo_destino_ruta.grid(row=0, column=3, sticky="ew", padx=(2, 8), pady=3)
        self.combo_destino_ruta.bind("<<ComboboxSelected>>", self._on_cambio_param_ruta)

        fila_opts_nav = ttk.Frame(nav, style="Card.TFrame")
        fila_opts_nav.grid(row=1, column=0, columnspan=4, sticky="ew", padx=8, pady=1)
        ttk.Checkbutton(
            fila_opts_nav,
            text="Evitar también alertas preventivas (🟡/🟠)",
            variable=self.evitar_preventivos_var,
            command=self._on_cambio_param_ruta,
        ).pack(side="left", padx=(0, 10))
        ttk.Checkbutton(
            fila_opts_nav,
            text="Tráfico en hora pico",
            variable=self.hora_pico_var,
            command=self._on_cambio_param_ruta,
        ).pack(side="left")
        ttk.Button(
            fila_opts_nav,
            text="🧭 Trazar Ruta Segura",
            style="Primary.TButton",
            command=self._on_calcular_ruta_segura,
        ).pack(side="right")

        self.lbl_resumen_ruta = ttk.Label(
            nav,
            textvariable=self.resumen_ruta_var,
            wraplength=460,
            justify="left",
            font=("Consolas", 8, "bold"),
            foreground="#065f46",
        )
        self.lbl_resumen_ruta.grid(
            row=2, column=0, columnspan=4, sticky="ew", padx=8, pady=(2, 5)
        )

        # Inspector formal del vértice seleccionado
        ficha = ttk.LabelFrame(
            tab,
            text="Inspector Formal del Vértice (Vecindades N_G, Grados, Alerta y Consenso)",
        )
        ficha.grid(row=2, column=0, sticky="ew", padx=6, pady=3)
        ficha.columnconfigure(0, weight=1)
        self.info_var = tk.StringVar()
        ttk.Label(
            ficha,
            textvariable=self.info_var,
            wraplength=460,
            justify="left",
            font=("Consolas", 8),
        ).grid(row=0, column=0, sticky="ew", padx=8, pady=4)

        # Consola de eventos
        cons = ttk.LabelFrame(tab, text="Consola de Eventos (Bitácora Formal)")
        cons.grid(row=3, column=0, sticky="nsew", padx=6, pady=(3, 6))
        cons.rowconfigure(0, weight=1)
        cons.columnconfigure(0, weight=1)
        self.consola = tk.Text(
            cons,
            width=50,
            height=9,
            wrap="word",
            state="disabled",
            font=("Consolas", 9),
            bg="#fcfcfd",
            relief="flat",
        )
        scroll = ttk.Scrollbar(cons, command=self.consola.yview)
        self.consola.configure(yscrollcommand=scroll.set)
        self.consola.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        scroll.grid(row=0, column=1, sticky="ns", pady=4)
        for etiqueta, color, negrita in [
            ("info", "#1e293b", False),
            ("estado", "#1d4ed8", False),
            ("logica", "#7e22ce", False),
            ("alerta", "#c2570c", False),
            ("critico", "#b91c1c", True),
            ("sistema", "#475569", False),
        ]:
            fuente = ("Consolas", 9, "bold") if negrita else ("Consolas", 9)
            self.consola.tag_configure(etiqueta, foreground=color, font=fuente)

    # -- Pestaña 2: Unidad 4 - Centralidades y Análisis de Redes --------------
    def _construir_tab_redes(self) -> None:
        tab = self.tab_redes
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(2, weight=1)

        # Tabla comparativa lado a lado de las 3 medidas de centralidad
        marco_t = ttk.LabelFrame(
            tab,
            text="Unidad 4: Centralidad de Grado (C_D), Cercanía (C_C / H) e Intermediación (C_B)",
        )
        marco_t.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 4))
        marco_t.columnconfigure(0, weight=1)

        cols = ("id", "deg", "cd", "cd_in", "cd_out", "sum_d", "cc", "h_dir", "cb", "cb_norm")
        self.tree_cent = ttk.Treeview(marco_t, columns=cols, show="headings", height=9)
        encabezados = [
            ("id", "Nodo", 42),
            ("deg", "deg(v)", 46),
            ("cd", "C_D(v)", 54),
            ("cd_in", "C_D⁻", 48),
            ("cd_out", "C_D⁺", 48),
            ("sum_d", "∑d(v,u)", 54),
            ("cc", "C_C(v)", 54),
            ("h_dir", "H_dir(v)", 58),
            ("cb", "C_B(v)", 52),
            ("cb_norm", "C_B norm", 62),
        ]
        for col, texto, ancho in encabezados:
            self.tree_cent.heading(col, text=texto)
            self.tree_cent.column(col, width=ancho, anchor="center")

        self.tree_cent.tag_configure("lider", background="#fef08a", font=("Consolas", 8, "bold"))
        self.tree_cent.tag_configure("seleccion", background="#dbeafe", font=("Consolas", 8, "bold"))
        self.tree_cent.tag_configure("normal", background="#ffffff")
        self.tree_cent.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        self.tree_cent.bind("<<TreeviewSelect>>", self._on_select_tree_cent)

        # Selector de sección detallada de la Unidad 4
        marco_sel = ttk.LabelFrame(tab, text="Receta para Analizar una Red Real (Unidad 4 - MSc Iván Gómez)")
        marco_sel.grid(row=1, column=0, sticky="ew", padx=6, pady=2)
        marco_sel.columnconfigure(0, weight=1)

        self.vistas_u4 = [
            "1. Las 4 Preguntas de Modelación e Interpretación de Centralidades (Receta Proyecto Final)",
            "2. Matriz de Distancias Geodésicas d(u, v) con BFS y Diámetro de la Red",
            "3. Cálculo Paso a Paso de Intermediación C_B(v): Fracciones σ_st(v) / σ_st",
            "4. Red Bipartita Ciudadanos–Nodos y su Proyección sobre los Ciudadanos",
        ]
        self.combo_u4 = ttk.Combobox(marco_sel, state="readonly", values=self.vistas_u4)
        self.combo_u4.current(0)
        self.combo_u4.grid(row=0, column=0, sticky="ew", padx=8, pady=5)
        self.combo_u4.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_tab_redes())

        # Visor de texto de la Unidad 4
        marco_txt = ttk.LabelFrame(tab, text="Desarrollo y Justificación Matemática (Unidad 4)")
        marco_txt.grid(row=2, column=0, sticky="nsew", padx=6, pady=(4, 6))
        marco_txt.columnconfigure(0, weight=1)
        marco_txt.rowconfigure(0, weight=1)

        self.txt_redes = tk.Text(
            marco_txt,
            wrap="word",
            font=("Consolas", 8),
            bg="#fcfcfd",
            fg="#0f172a",
            relief="flat",
            state="disabled",
        )
        sc_r = ttk.Scrollbar(marco_txt, orient="vertical", command=self.txt_redes.yview)
        self.txt_redes.configure(yscrollcommand=sc_r.set)
        self.txt_redes.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=6)
        sc_r.grid(row=0, column=1, sticky="ns", pady=6)

    def _on_select_tree_cent(self, _e: object = None) -> None:
        sel = self.tree_cent.selection()
        if not sel:
            return
        valores = self.tree_cent.item(sel[0], "values")
        if valores and valores[0] in self.cuenca.nodos and valores[0] != self.seleccion:
            self._seleccionar(str(valores[0]))

    # -- Pestaña 3: Unidad 3 - Teoría de Grafos y Árboles ---------------------
    def _construir_tab_grafo(self) -> None:
        tab = self.tab_grafo
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(1, weight=1)

        selector_frame = ttk.LabelFrame(
            tab,
            text="Temas de Unidad 3 (MSc Iván Gómez & Prof. Yesneri Zuleta Saldarriaga)",
        )
        selector_frame.grid(row=0, column=0, sticky="ew", padx=6, pady=(6, 4))
        selector_frame.columnconfigure(0, weight=1)

        self.vistas_grafo = [
            "1. Vecindades (N_G, N_G[v], N⁻, N⁺), Valencia (δ, Δ, δ±, Δ±), TAM y Corolario (Prof. Zuleta)",
            "2. Clasificación (Simple, Digrafo, Ponderado, Bipartito) y Subgrafo Inducido G - v",
            "3. Representaciones: Lista de Adyacencia, Matriz de Adyacencia y Matriz de Incidencia",
            "4. Conectividad (Fuerte vs. Débil), Clausura de Warshall y Orden Parcial (Poset)",
            "5. Teorema de Euler (1736), Hamiltoniano (Dirac y Ore) y Grafos Planos (V - E + F = 2)",
            "6. Trazas Paso a Paso de BFS (Cola) vs. DFS (Llamado desde) y Árboles con Raíz",
            "7. Árbol de Expansión Mínimo (MST: Kruskal y Prim), Dijkstra e Inducción Matemática",
        ]
        self.combo_vista_grafo = ttk.Combobox(
            selector_frame,
            state="readonly",
            values=self.vistas_grafo,
        )
        self.combo_vista_grafo.current(0)
        self.combo_vista_grafo.grid(row=0, column=0, sticky="ew", padx=8, pady=6)
        self.combo_vista_grafo.bind("<<ComboboxSelected>>", lambda _e: self._actualizar_tab_grafo())

        visor_frame = ttk.LabelFrame(tab, text="Desarrollo Formal y Resultados sobre la Cuenca de Uninorte")
        visor_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(4, 6))
        visor_frame.columnconfigure(0, weight=1)
        visor_frame.rowconfigure(0, weight=1)

        self.txt_grafo = tk.Text(
            visor_frame,
            wrap="none",
            font=("Consolas", 8),
            bg="#fcfcfd",
            fg="#0f172a",
            relief="flat",
            state="disabled",
        )
        scroll_y = ttk.Scrollbar(visor_frame, orient="vertical", command=self.txt_grafo.yview)
        scroll_x = ttk.Scrollbar(visor_frame, orient="horizontal", command=self.txt_grafo.xview)
        self.txt_grafo.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        self.txt_grafo.grid(row=0, column=0, sticky="nsew", padx=(6, 0), pady=(6, 0))
        scroll_y.grid(row=0, column=1, sticky="ns", pady=(6, 0))
        scroll_x.grid(row=1, column=0, sticky="ew", padx=(6, 0))

    # -- mensajes iniciales de arranque ---------------------------------------
    def _mensajes_iniciales(self) -> None:
        g = self.cuenca
        s_in, s_out, num_e, _ = g.verificar_lema_apreton_manos()
        cent = g.analisis_centralidades_unidad4()
        mst = g.mst_kruskal_prim()
        self.sistema._emitir(
            f"Sistema iniciado. Grafo G=(V,E): |V|={len(g.nodos)}, |E|={num_e} "
            f"(∑grad⁻={s_in}, ∑grad⁺={s_out}, ∑grad=2m={2*num_e}).",
            "sistema",
        )
        self.sistema._emitir(
            "Orden topológico (Kahn): " + " → ".join(g.orden_topologico()),
            "sistema",
        )
        self.sistema._emitir(
            f"Centralidades (U4) → Grado: {cent['lider_grado']} | "
            f"Cercanía: {cent['lider_cercania']} | "
            f"Intermediación (Puente): {cent['lider_intermediacion']}.",
            "sistema",
        )
        self.sistema._emitir(
            f"MST (Kruskal/Prim): {mst['num_aristas_mst']} aristas, costo mínimo = {mst['costo_total']} m.",
            "sistema",
        )

    # -- callbacks y acciones -------------------------------------------------
    def _abrir_mapa_web_interactivo(self) -> None:
        """Lanza el servidor web local con Google Maps interactivo (pan & zoom) en el navegador."""
        import threading
        import webbrowser
        try:
            from servidor_web_arroyos import iniciar_servidor_web
            t = threading.Thread(
                target=lambda: iniciar_servidor_web(
                    puerto=8080,
                    abrir_navegador=True,
                    cuenca=self.cuenca,
                    sistema=self.sistema,
                ),
                daemon=True,
            )
            t.start()
            self.sistema._emitir(
                "🌐 Google Maps Interactivo iniciado en el navegador (Pan, Zoom y Rutas Viales en tiempo real).",
                "sistema",
            )
        except Exception as exc:
            webbrowser.open("http://localhost:8080")
            self.sistema._emitir(f"Abriendo mapa interactivo: {exc}", "sistema")

    def _on_combo(self, _e: object = None) -> None:
        self.seleccion = self.mapa_combo[self.combo.get()]
        self._dibujar()

    def _on_cambio_param_ruta(self, _e: object = None) -> None:
        if hasattr(self, "combo_origen_ruta") and self.combo_origen_ruta.get() in self.mapa_combo:
            self.origen_ruta_id = self.mapa_combo[self.combo_origen_ruta.get()]
        if hasattr(self, "combo_destino_ruta") and self.combo_destino_ruta.get() in self.mapa_combo:
            self.destino_ruta_id = self.mapa_combo[self.combo_destino_ruta.get()]
        self._dibujar()

    def _on_calcular_ruta_segura(self) -> None:
        if hasattr(self, "combo_origen_ruta") and self.combo_origen_ruta.get() in self.mapa_combo:
            self.origen_ruta_id = self.mapa_combo[self.combo_origen_ruta.get()]
        if hasattr(self, "combo_destino_ruta") and self.combo_destino_ruta.get() in self.mapa_combo:
            self.destino_ruta_id = self.mapa_combo[self.combo_destino_ruta.get()]
        self.capa_resaltado_var.set("ruta")
        info = self.cuenca.calcular_ruta_segura(
            self.origen_ruta_id,
            self.destino_ruta_id,
            evitar_preventivos=bool(self.evitar_preventivos_var.get()),
            hora_pico=bool(self.hora_pico_var.get()),
        )
        if info["hay_ruta_segura"]:
            rs = info["ruta_segura"]
            cam_txt = " → ".join(rs["camino"])  # type: ignore[index]
            if info["cambio_ruta"]:
                rh = info["ruta_habitual"]
                evitados = ", ".join(info["peligros_en_habitual"])  # type: ignore[arg-type]
                self.sistema._emitir(
                    f"[RUTA SEGURA] Desvío automático por arroyo en {{{evitados}}}: "
                    f"Ruta habitual ({' → '.join(rh['camino'])}) reemplazada por "  # type: ignore[index]
                    f"({cam_txt}) en G - V_bloq ({rs['distancia_m']} m, ~{rs['tiempo_min']} min).",  # type: ignore[index]
                    "logica",
                )
            else:
                self.sistema._emitir(
                    f"[RUTA SEGURA] Ruta óptima libre de arroyos: {cam_txt} "
                    f"({rs['distancia_m']} m, ~{rs['tiempo_min']} min).",  # type: ignore[index]
                    "info",
                )
        else:
            self.sistema._emitir(
                f"[RUTA BLOQUEADA] {info['motivo_sin_ruta']}",
                "critico",
            )
        self._dibujar()

    def _on_k(self) -> None:
        try:
            k = int(self.k_var.get())
        except (tk.TclError, ValueError):
            return
        if k >= 1:
            self.sistema.k = k
            self._dibujar()

    def _cancelar_animacion_bfs(self) -> None:
        if self._after_id_bfs is not None:
            try:
                self.after_cancel(self._after_id_bfs)
            except tk.TclError:
                pass
            self._after_id_bfs = None
        self._nodos_onda_actual.clear()
        self._distancias_onda.clear()

    def _on_reporte(self) -> None:
        self._reportar_en(self.seleccion)

    def _on_crecida(self) -> None:
        self._cancelar_animacion_bfs()
        self.sistema.simular_crecida()
        self._dibujar()

    def _on_reiniciar(self) -> None:
        self._cancelar_animacion_bfs()
        self.sistema.reiniciar()
        self.estado_mapa_var.set("Red reiniciada: todos los vértices regresaron al estado inicial q₀ = VERDE.")
        self._dibujar()

    def _on_exportar(self) -> None:
        ruta = filedialog.asksaveasfilename(
            parent=self,
            title="Exportar Informe Técnico y Bitácora",
            defaultextension=".txt",
            initialfile=f"informe_arroyos_uninorte_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            filetypes=[("Archivo de texto", "*.txt"), ("Todos los archivos", "*.*")],
        )
        if not ruta:
            return
        contenido = self.sistema.generar_informe_texto()
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            self.sistema._emitir(f"Informe exportado exitosamente en: {ruta}", "sistema")
            messagebox.showinfo(
                "Informe Exportado",
                f"El informe matemático y la bitácora se guardaron en:\n{ruta}",
                parent=self,
            )
        except OSError as exc:
            messagebox.showerror("Error al guardar", str(exc), parent=self)

    def _seleccionar(self, id_: str) -> None:
        self.seleccion = id_
        self.combo.set(f"{id_} · {self.cuenca.nodos[id_].nombre}")
        n = self.cuenca.nodos[id_]
        self.estado_mapa_var.set(
            f"Seleccionado {id_} ({n.nombre}) — Estado: {n.estado.value} | "
            f"grad⁻={self.cuenca.grado_entrada(id_)}, grad⁺={self.cuenca.grado_salida(id_)}, "
            f"grad={self.cuenca.grado_no_dirigido(id_)}"
        )
        self._dibujar()

    def _reportar_en(self, id_: str) -> None:
        self._cancelar_animacion_bfs()
        self.seleccion = id_
        self.combo.set(f"{id_} · {self.cuenca.nodos[id_].nombre}")
        animar = bool(self.animar_bfs_var.get())
        capas = self.sistema.enviar_reporte(id_, propagar_inmediato=not animar)
        self._dibujar()
        if animar and capas:
            self._iniciar_animacion_capas_bfs(id_, capas, indice=0)

    def _iniciar_animacion_capas_bfs(
        self,
        id_origen: str,
        capas: List[Tuple[int, List[str]]],
        indice: int,
    ) -> None:
        if indice >= len(capas):
            self._nodos_onda_actual.clear()
            self._after_id_bfs = None
            self.estado_mapa_var.set(
                f"Propagación BFS desde {id_origen} completada ({len(capas)} capas alcanzadas)."
            )
            self._dibujar()
            return

        dist, ids_nodos = capas[indice]
        self.sistema.aplicar_capa_bfs(dist, ids_nodos)
        self._nodos_onda_actual = set(ids_nodos)
        for v in ids_nodos:
            self._distancias_onda[v] = dist
        self.estado_mapa_var.set(
            f"🌊 Onda BFS desde {id_origen} → Capa d = +{dist}: {', '.join(ids_nodos)}"
        )
        self._dibujar()
        self._after_id_bfs = self.after(
            520,
            lambda: self._iniciar_animacion_capas_bfs(id_origen, capas, indice + 1),
        )

    # -- bitácora -------------------------------------------------------------
    def _log(self, mensaje: str, etiqueta: str = "info") -> None:
        if not hasattr(self, "consola"):
            return
        hora = datetime.now().strftime("%H:%M:%S")
        self.consola.configure(state="normal")
        self.consola.insert("end", f"[{hora}] {mensaje}\n", etiqueta)
        self.consola.see("end")
        self.consola.configure(state="disabled")

    # -- renderizado del mapa (Google Maps, Panorámico o Detalle Campus) ------
    def _dibujar_fondo(self) -> None:
        c = self.canvas
        modo = self.modo_mapa_var.get()
        if modo == "google":
            if self.mapa_google is not None:
                c.create_image(0, 0, image=self.mapa_google, anchor="nw")
            else:
                c.create_rectangle(0, 0, self.CANVAS_W, self.CANVAS_H, fill="#e0f2fe", outline="")
            c.create_rectangle(6, 6, 420, 28, fill="#ffffff", outline="#cbd5e1")
            c.create_text(
                12,
                17,
                anchor="w",
                fill="#0f172a",
                font=("Segoe UI", 8, "bold"),
                text="Mapa: Cercanías Uninorte – Red de Arroyos y Ruteo Seguro",
            )
        elif modo == "panoramico":
            if self.mapa_panoramico is not None:
                c.create_image(0, 0, image=self.mapa_panoramico, anchor="nw")
            else:
                c.create_rectangle(0, 0, self.CANVAS_W, self.CANVAS_H, fill="#e0f2fe", outline="")
            c.create_rectangle(6, 6, 465, 28, fill="#ffffff", outline="#cbd5e1")
            c.create_text(
                12,
                17,
                anchor="w",
                fill="#0f172a",
                font=("Segoe UI", 8, "bold"),
                text="Vista Panorámica: Cuenca Uninorte → Arroyo León → Ciénaga de Mallorquín",
            )
        else:
            # Vista original cercana al campus (760x460 centrada verticalmente con franja izquierda)
            offset_y = 40
            c.create_rectangle(0, 0, self.CANVAS_W, self.CANVAS_H, fill="#e2e8f0", outline="")
            c.create_rectangle(
                0, offset_y, self.MARGEN_CAMPUS, offset_y + 460, fill="#dbeafe", outline=""
            )
            c.create_text(
                self.MARGEN_CAMPUS // 2,
                offset_y + 390,
                width=114,
                justify="center",
                fill="#1e3a8a",
                font=("Segoe UI", 8, "italic"),
                text="Tramo fuera del mapa: hacia el occidente, Arroyo León y Ciénaga de Mallorquín",
            )
            if self.mapa_campus is not None:
                c.create_image(self.MARGEN_CAMPUS, offset_y, image=self.mapa_campus, anchor="nw")

        c.create_text(
            self.CANVAS_W - 6,
            self.CANVAS_H - 4,
            anchor="se",
            fill="#334155",
            font=("Segoe UI", 7),
            text="Mapa base: © Google / © TomTom / © OpenStreetMap",
        )

    def _dibujar(self) -> None:
        c = self.canvas
        c.delete("all")
        self._dibujar_fondo()
        r = self.RADIO
        pos = self.pos_actual
        etq_arriba = self.etiquetas_arriba_actual
        capa = self.capa_resaltado_var.get()

        # Precalcular subconjuntos para las capas de resaltado
        alcanzables_sel: Dict[str, int] = dict(self.cuenca.descendientes_bfs(self.seleccion))
        _, cam_critico = self.cuenca.camino_critico()
        aristas_criticas_dag: Set[Tuple[str, str]] = {
            (cam_critico[i], cam_critico[i + 1]) for i in range(len(cam_critico) - 1)
        }
        mst_info = self.cuenca.mst_kruskal_prim()
        aristas_mst: Set[Tuple[str, str]] = {
            (u, v) for u, v, _ in mst_info["mst_kruskal"]  # type: ignore[union-attr]
        }
        bip_info = self.cuenca.analisis_bipartito()
        v1_set: Set[str] = set(bip_info["V1"])  # type: ignore[arg-type]

        ruta_info = self.cuenca.calcular_ruta_segura(
            self.origen_ruta_id,
            self.destino_ruta_id,
            evitar_preventivos=bool(self.evitar_preventivos_var.get()),
            hora_pico=bool(self.hora_pico_var.get()),
        )
        aristas_ruta_segura: List[Tuple[str, str]] = (
            list(ruta_info["ruta_segura"]["aristas"])  # type: ignore[index]
            if ruta_info["hay_ruta_segura"]
            else []
        )
        pares_ruta_segura: Set[Tuple[str, str]] = set()
        for ua, va in aristas_ruta_segura:
            pares_ruta_segura.add((ua, va))
            pares_ruta_segura.add((va, ua))

        # Helper para obtener la polilínea vial siguiendo las calles del mapa
        def _coords_calle(u_id: str, v_id: str, trim_ini: float = 0.0, trim_fin: float = 0.0) -> List[float]:
            if self.modo_mapa_var.get() == "google":
                if (u_id, v_id) in self.TRAZADO_CALLES_GOOGLE:
                    pts = [ (float(px), float(py)) for px, py in self.TRAZADO_CALLES_GOOGLE[(u_id, v_id)] ]
                elif (v_id, u_id) in self.TRAZADO_CALLES_GOOGLE:
                    pts = [ (float(px), float(py)) for px, py in reversed(self.TRAZADO_CALLES_GOOGLE[(v_id, u_id)]) ]
                else:
                    pts = [ (float(pos[u_id][0]), float(pos[u_id][1])), (float(pos[v_id][0]), float(pos[v_id][1])) ]
            else:
                pts = [ (float(pos[u_id][0]), float(pos[u_id][1])), (float(pos[v_id][0]), float(pos[v_id][1])) ]

            if len(pts) >= 2 and trim_ini > 0:
                dx0, dy0 = pts[1][0] - pts[0][0], pts[1][1] - pts[0][1]
                d0 = math.hypot(dx0, dy0) or 1.0
                pts[0] = (pts[0][0] + (dx0 / d0) * trim_ini, pts[0][1] + (dy0 / d0) * trim_ini)
            if len(pts) >= 2 and trim_fin > 0:
                dx1, dy1 = pts[-1][0] - pts[-2][0], pts[-1][1] - pts[-2][1]
                d1 = math.hypot(dx1, dy1) or 1.0
                pts[-1] = (pts[-1][0] - (dx1 / d1) * trim_fin, pts[-1][1] - (dy1 / d1) * trim_fin)

            flat: List[float] = []
            for px, py in pts:
                flat.extend([px, py])
            return flat

        # 0. Si la capa es "ruta", dibujar primero los corredores viales urbanos extra (cota alta)
        if capa == "ruta":
            for ux_id, vx_id, wx_m, _desc in self.cuenca.corredores_viales_extra():
                coords_extra = _coords_calle(ux_id, vx_id, r, r)
                c.create_line(
                    *coords_extra,
                    fill="#475569",
                    width=3,
                    dash=(5, 3),
                    capstyle=tk.ROUND,
                    joinstyle=tk.ROUND,
                )
                if self.mostrar_pesos_var.get():
                    mid_idx = (len(coords_extra) // 2) & ~1
                    mx, my = coords_extra[mid_idx], coords_extra[mid_idx + 1]
                    tw = c.create_text(
                        mx,
                        my,
                        text=f"Vía {wx_m}m",
                        font=("Segoe UI", 7, "bold"),
                        fill="#0f172a",
                    )
                    bx0, by0, bx1, by1 = c.bbox(tw)
                    fw = c.create_rectangle(
                        bx0 - 2,
                        by0 - 1,
                        bx1 + 2,
                        by1 + 1,
                        fill="#e0f2fe",
                        outline="#38bdf8",
                    )
                    c.tag_lower(fw, tw)

        # 1. Aristas dirigidas
        for u, v in self.cuenca.aristas:
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            d = math.hypot(x2 - x1, y2 - y1) or 1.0
            ux, uy = (x2 - x1) / d, (y2 - y1) / d
            ix1, iy1 = x1 + ux * r, y1 + uy * r
            ix2, iy2 = x2 - ux * (r + 3), y2 - uy * (r + 3)

            # Resaltado según la capa activa
            if capa == "critico" and (u, v) in aristas_criticas_dag:
                c.create_line(ix1, iy1, ix2, iy2, fill="#f59e0b", width=9, capstyle=tk.ROUND)
            elif capa == "bfs" and (u == self.seleccion or u in alcanzables_sel) and (v in alcanzables_sel):
                c.create_line(ix1, iy1, ix2, iy2, fill="#38bdf8", width=8, capstyle=tk.ROUND)
            elif capa == "mst":
                if (u, v) in aristas_mst:
                    c.create_line(ix1, iy1, ix2, iy2, fill="#10b981", width=9, capstyle=tk.ROUND)
                else:
                    # Arista descartada por Kruskal/Prim
                    c.create_line(
                        ix1, iy1, ix2, iy2, fill="#94a3b8", width=2, dash=(4, 4)
                    )
                    continue

            critica = self.cuenca.nodos[u].estado is Estado.ROJO
            c.create_line(
                ix1,
                iy1,
                ix2,
                iy2,
                arrow=tk.LAST,
                arrowshape=(10, 12, 5),
                fill="#d62828" if critica else "#1e3a8a",
                width=4 if critica else 3,
            )

            # Etiqueta de peso w(u, v) en metros
            if self.mostrar_pesos_var.get():
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
                w_uv = self.cuenca.peso(u, v)
                tw = c.create_text(
                    mx,
                    my,
                    text=f"{w_uv}m",
                    font=("Segoe UI", 7, "bold"),
                    fill="#0f172a",
                )
                bx0, by0, bx1, by1 = c.bbox(tw)
                fw = c.create_rectangle(
                    bx0 - 2,
                    by0 - 1,
                    bx1 + 2,
                    by1 + 1,
                    fill="#f8fafc",
                    outline="#cbd5e1",
                )
                c.tag_lower(fw, tw)

        # 1.b Si la capa activa es "ruta", trazar el camino seguro siguiendo las calles con flechas de navegación
        if capa == "ruta":
            if ruta_info["cambio_ruta"]:
                aristas_hab: List[Tuple[str, str]] = list(
                    ruta_info["ruta_habitual"]["aristas"]  # type: ignore[index]
                )
                for uh, vh in aristas_hab:
                    if (uh, vh) not in pares_ruta_segura:
                        coords_hab = _coords_calle(uh, vh, r, r)
                        c.create_line(
                            *coords_hab,
                            fill="#ef4444",
                            width=4,
                            dash=(6, 4),
                            capstyle=tk.ROUND,
                            joinstyle=tk.ROUND,
                        )

            for us, vs_next in aristas_ruta_segura:
                coords_seg = _coords_calle(us, vs_next, r, r + 3)
                c.create_line(
                    *coords_seg,
                    fill="#34d399",
                    width=11,
                    capstyle=tk.ROUND,
                    joinstyle=tk.ROUND,
                )
                c.create_line(
                    *coords_seg,
                    arrow=tk.LAST,
                    arrowshape=(11, 13, 5),
                    fill="#047857",
                    width=5,
                    capstyle=tk.ROUND,
                    joinstyle=tk.ROUND,
                )

        # 2. Etiquetas de nombre corto
        for id_, nodo in self.cuenca.nodos.items():
            x, y = pos[id_]
            arriba = id_ in etq_arriba
            ty = y - r - 5 if arriba else y + r + 5
            t = c.create_text(
                x,
                ty,
                text=nodo.corto,
                width=112,
                justify="center",
                anchor="s" if arriba else "n",
                font=("Segoe UI", 8, "bold" if id_ == self.seleccion else "normal"),
                fill="#0f172a",
                tags=(f"nodo_{id_}",),
            )
            x0, y0, x1, y1 = c.bbox(t)
            fondo = c.create_rectangle(
                x0 - 3,
                y0 - 1,
                x1 + 3,
                y1 + 1,
                fill="#ffffff",
                outline="#2563eb" if id_ == self.seleccion else "#94a3b8",
                tags=(f"nodo_{id_}",),
            )
            c.tag_lower(fondo, t)

        # 3. Vértices coloreados
        for id_, nodo in self.cuenca.nodos.items():
            x, y = pos[id_]
            est = nodo.estado
            sel = id_ == self.seleccion
            en_onda = id_ in self._nodos_onda_actual
            tag = f"nodo_{id_}"

            # Halo de bipartición V1 vs V2 si esa capa está activa
            if capa == "bipartito":
                col_bip = "#8b5cf6" if id_ in v1_set else "#06b6d4"
                c.create_oval(
                    x - r - 6,
                    y - r - 6,
                    x + r + 6,
                    y + r + 6,
                    outline=col_bip,
                    width=3,
                )

            if en_onda:
                c.create_oval(
                    x - r - 8,
                    y - r - 8,
                    x + r + 8,
                    y + r + 8,
                    outline="#f59e0b",
                    width=3,
                    dash=(3, 2),
                )
            elif sel:
                c.create_oval(
                    x - r - 4,
                    y - r - 4,
                    x + r + 4,
                    y + r + 4,
                    outline="#2563eb",
                    width=2.5,
                )

            c.create_oval(
                x - r,
                y - r,
                x + r,
                y + r,
                fill=COLORES[est],
                outline="#0b3d91" if sel else "#1f2937",
                width=3 if sel else 2,
                tags=(tag,),
            )
            if est in ControlEstados.F:
                c.create_oval(
                    x - r + 3,
                    y - r + 3,
                    x + r - 3,
                    y + r - 3,
                    outline="#ffffff",
                    width=1.2,
                    tags=(tag,),
                )

            c.create_text(
                x,
                y,
                text=id_,
                fill="#111827" if est is Estado.AMARILLO else "#ffffff",
                font=("Segoe UI", 9, "bold"),
                tags=(tag,),
            )

            # Insignia de reportes R: n/k
            n = len(nodo.reportantes)
            if n:
                bx, by = x + r + 4, y - r + 2
                txt_r = c.create_text(
                    bx,
                    by,
                    anchor="w",
                    text=f"R:{n}/{self.sistema.k}",
                    font=("Segoe UI", 8, "bold"),
                    fill="#ffffff",
                )
                rx0, ry0, rx1, ry1 = c.bbox(txt_r)
                rect_r = c.create_rectangle(
                    rx0 - 3,
                    ry0 - 1,
                    rx1 + 3,
                    ry1 + 1,
                    fill="#7e22ce",
                    outline="#ffffff",
                )
                c.tag_lower(rect_r, txt_r)

            # Insignia de distancia BFS o conjunto bipartito
            dist_mostrar: Optional[int] = None
            if id_ in self._distancias_onda:
                dist_mostrar = self._distancias_onda[id_]
            elif capa == "bfs" and id_ in alcanzables_sel:
                dist_mostrar = alcanzables_sel[id_]

            if dist_mostrar is not None:
                dx, dy = x - r - 4, y - r + 2
                txt_d = c.create_text(
                    dx,
                    dy,
                    anchor="e",
                    text=f"d=+{dist_mostrar}",
                    font=("Segoe UI", 7, "bold"),
                    fill="#0f172a",
                )
                dx0, dy0, dx1, dy1 = c.bbox(txt_d)
                rect_d = c.create_rectangle(
                    dx0 - 2,
                    dy0 - 1,
                    dx1 + 2,
                    dy1 + 1,
                    fill="#fef08a",
                    outline="#ca8a04",
                )
                c.tag_lower(rect_d, txt_d)
            elif capa == "bipartito":
                dx, dy = x - r - 4, y - r + 2
                etq_b = "V₁" if id_ in v1_set else "V₂"
                col_b = "#8b5cf6" if id_ in v1_set else "#0891b2"
                txt_b = c.create_text(
                    dx,
                    dy,
                    anchor="e",
                    text=etq_b,
                    font=("Segoe UI", 7, "bold"),
                    fill="#ffffff",
                )
                bx0, by0, bx1, by1 = c.bbox(txt_b)
                rect_b = c.create_rectangle(
                    bx0 - 2,
                    by0 - 1,
                    bx1 + 2,
                    by1 + 1,
                    fill=col_b,
                    outline="#ffffff",
                )
                c.tag_lower(rect_b, txt_b)
            elif capa == "ruta":
                etq_r: Optional[str] = None
                col_r = "#059669"
                if id_ == self.origen_ruta_id and id_ == self.destino_ruta_id:
                    etq_r = "ORIGEN=DESTINO"
                elif id_ == self.origen_ruta_id:
                    etq_r = "🚩 ORIGEN"
                    col_r = "#0284c7"
                elif id_ == self.destino_ruta_id:
                    etq_r = "🏁 DESTINO"
                    col_r = "#059669"
                elif id_ in ruta_info["nodos_bloqueados"]:  # type: ignore[operator]
                    etq_r = "⛔ ARROYO"
                    col_r = "#b91c1c"
                if etq_r is not None:
                    dx, dy = x - r - 4, y - r + 2
                    txt_rt = c.create_text(
                        dx,
                        dy,
                        anchor="e",
                        text=etq_r,
                        font=("Segoe UI", 7, "bold"),
                        fill="#ffffff",
                    )
                    bx0, by0, bx1, by1 = c.bbox(txt_rt)
                    rect_rt = c.create_rectangle(
                        bx0 - 3,
                        by0 - 1,
                        bx1 + 3,
                        by1 + 1,
                        fill=col_r,
                        outline="#ffffff",
                    )
                    c.tag_lower(rect_rt, txt_rt)

        # Banner de navegación en el mapa si la capa "ruta" está activa
        if capa == "ruta":
            if ruta_info["hay_ruta_segura"]:
                rs = ruta_info["ruta_segura"]
                cam_str = " → ".join(rs["camino"])  # type: ignore[index]
                desvio_str = (
                    f" (Desvío: evita arroyo en {', '.join(ruta_info['peligros_en_habitual'])})"  # type: ignore[arg-type]
                    if ruta_info["cambio_ruta"]
                    else " (Vía habitual despejada)"
                )
                texto_banner = (
                    f"🧭 RUTA SEGURA: {cam_str}  |  {rs['distancia_m']} m (~{rs['tiempo_min']} min){desvio_str}"  # type: ignore[index]
                )
                col_banner_bg = "#ecfdf5"
                col_banner_bd = "#059669"
                col_banner_fg = "#065f46"
            else:
                texto_banner = f"⛔ RUTA CORTADA POR ARROYO: {ruta_info['motivo_sin_ruta']}"
                col_banner_bg = "#fef2f2"
                col_banner_bd = "#dc2626"
                col_banner_fg = "#991b1b"

            c.create_rectangle(
                8,
                self.CANVAS_H - 36,
                self.CANVAS_W - 8,
                self.CANVAS_H - 14,
                fill=col_banner_bg,
                outline=col_banner_bd,
                width=1.5,
            )
            c.create_text(
                14,
                self.CANVAS_H - 25,
                anchor="w",
                fill=col_banner_fg,
                font=("Segoe UI", 8, "bold"),
                text=texto_banner,
            )

        for id_ in self.cuenca.nodos:
            tag = f"nodo_{id_}"
            c.tag_bind(tag, "<Button-1>", lambda _e, i=id_: self._seleccionar(i))
            c.tag_bind(tag, "<Double-Button-1>", lambda _e, i=id_: self._reportar_en(i))
            c.tag_bind(tag, "<Enter>", lambda _e: self.canvas.configure(cursor="hand2"))
            c.tag_bind(tag, "<Leave>", lambda _e: self.canvas.configure(cursor=""))

        self._actualizar_resumen_ruta(ruta_info)
        self._actualizar_metricas_superiores()
        self._actualizar_ficha()
        self._actualizar_tab_redes()
        self._actualizar_tab_grafo()

    def _actualizar_resumen_ruta(self, ruta_info: Dict[str, object]) -> None:
        if not hasattr(self, "resumen_ruta_var"):
            return
        if ruta_info["hay_ruta_segura"]:
            rs = ruta_info["ruta_segura"]
            rh = ruta_info["ruta_habitual"]
            cam_seg = " → ".join(rs["camino"])  # type: ignore[index]
            if ruta_info["cambio_ruta"]:
                evitados = ", ".join(ruta_info["peligros_en_habitual"])  # type: ignore[arg-type]
                cam_hab = " → ".join(rh["camino"])  # type: ignore[index]
                self.resumen_ruta_var.set(
                    f"✅ RUTA SEGURA (desvío activo): {cam_seg} ({rs['distancia_m']} m, ~{rs['tiempo_min']} min)\n"  # type: ignore[index]
                    f"⚠️ Evita arroyo en {{{evitados}}} de la ruta habitual ({cam_hab}, {rh['distancia_m']} m)."  # type: ignore[index]
                )
                if hasattr(self, "lbl_resumen_ruta"):
                    self.lbl_resumen_ruta.configure(foreground="#047857")
            else:
                self.resumen_ruta_var.set(
                    f"✅ RUTA ÓPTIMA DESPEJADA: {cam_seg}  ·  Distancia: {rs['distancia_m']} m  ·  "  # type: ignore[index]
                    f"Tiempo est.: ~{rs['tiempo_min']} min (sin arroyos en el trayecto)."  # type: ignore[index]
                )
                if hasattr(self, "lbl_resumen_ruta"):
                    self.lbl_resumen_ruta.configure(foreground="#065f46")
        else:
            self.resumen_ruta_var.set(f"⛔ SIN PASO SEGURO: {ruta_info['motivo_sin_ruta']}")
            if hasattr(self, "lbl_resumen_ruta"):
                self.lbl_resumen_ruta.configure(foreground="#b91c1c")

    # -- actualización de paneles ---------------------------------------------
    def _actualizar_metricas_superiores(self) -> None:
        conteo = {e: 0 for e in Estado}
        for n in self.cuenca.nodos.values():
            conteo[n.estado] += 1
        total_rep = sum(len(n.reportantes) for n in self.cuenca.nodos.values())
        self.metricas_var.set(
            f"G=(V,E): |V|={len(self.cuenca.nodos)}, |E|={len(self.cuenca.aristas)}  ·  "
            f"🟢 {conteo[Estado.VERDE]}  🟡 {conteo[Estado.AMARILLO]}  "
            f"🟠 {conteo[Estado.NARANJA]}  🔴 {conteo[Estado.ROJO]}  ·  "
            f"∑|R_v|={total_rep}"
        )

    def _actualizar_ficha(self) -> None:
        n = self.cuenca.nodos[self.seleccion]
        g = self.cuenca
        alerta_arriba = self.sistema.tiene_ancestro_critico(n.id)
        ev = ValidadorConsenso.evaluacion_formal(n.reportantes, self.sistema.k, alerta_arriba)
        niveles = g.niveles_topologicos()

        n_in = "{" + ", ".join(g.vecindad_entrada(n.id)) + "}" if g.vecindad_entrada(n.id) else "∅"
        n_out = "{" + ", ".join(g.vecindad_salida(n.id)) + "}" if g.vecindad_salida(n.id) else "∅"
        n_ab = "{" + ", ".join(g.vecindad_abierta(n.id)) + "}"
        n_ce = "{" + ", ".join(g.vecindad_cerrada(n.id)) + "}"
        critico = "Crítico (Desbordado)" if n.control_estado.es_critico() else "Operativo"

        self.info_var.set(
            f"Vértice    : {n.id} · {n.nombre}\n"
            f"Vecindades : N⁻({n.id})={n_in} | N⁺({n.id})={n_out}\n"
            f"No dirigido: N_G({n.id})={n_ab} | N_G[{n.id}]={n_ce}\n"
            f"Valencia   : grad⁻={g.grado_entrada(n.id)}, grad⁺={g.grado_salida(n.id)}, "
            f"grad({n.id})={g.grado_no_dirigido(n.id)} | Nivel L={niveles[n.id]} ({g.clasificar_nodo(n.id)})\n"
            f"Estado     : {n.estado.value} ({DESCRIPCION[n.estado]}) — {critico}\n"
            f"Consenso   : R_{n.id} = {ev['conjunto_R']}  ⇒  {ev['formula_consenso']}"
        )

    # -- Pestaña 2: Unidad 4 (Centralidades y Redes) --------------------------
    def _actualizar_tab_redes(self) -> None:
        if not hasattr(self, "tree_cent"):
            return
        g = self.cuenca
        cent = g.analisis_centralidades_unidad4()

        for item in self.tree_cent.get_children():
            self.tree_cent.delete(item)

        for f in cent["tabla"]:  # type: ignore[union-attr]
            vid = str(f["id"])
            es_lider = vid in {
                cent["lider_grado"],
                cent["lider_cercania"],
                cent["lider_intermediacion"],
            }
            tag = "seleccion" if vid == self.seleccion else ("lider" if es_lider else "normal")
            self.tree_cent.insert(
                "",
                "end",
                values=(
                    vid,
                    f["deg"],
                    f"{float(f['cd']):.3f}",
                    f"{float(f['cd_in']):.3f}",
                    f"{float(f['cd_out']):.3f}",
                    f["suma_dist"],
                    f"{float(f['cc']):.3f}",
                    f"{float(f['h_dir']):.3f}",
                    f"{float(f['cb']):.2f}",
                    f"{float(f['cb_norm']):.3f}",
                ),
                tags=(tag,),
            )

        idx = self.combo_u4.current()
        lineas: List[str] = []

        if idx == 0:
            lineas.append("═" * 74)
            lineas.append("RECETA PARA ANALIZAR UNA RED REAL (UNIDAD 4 – MSc IVÁN GÓMEZ)")
            lineas.append("═" * 74)
            lineas.append("1. MODELAR (Las cuatro preguntas de modelación - Sección 4.1):")
            lineas.append("   • Nodos (V): 9 puntos críticos de control hidrológico (intersecciones")
            lineas.append("     viales, obras de drenaje, Arroyo León y Ciénaga de Mallorquín).")
            lineas.append("   • Aristas (E): Tramos de escorrentía superficial directa entre puntos.")
            lineas.append("   • Dirección: Digrafo (u, v) ∈ E donde el agua fluye por gravedad de u a v.")
            lineas.append("   • Peso w(u,v): Distancia aproximada en metros (y w=1 paso para BFS).")
            lineas.append("")
            lineas.append("2. COMPARACIÓN DE LAS TRES MEDIDAS DE CENTRALIDAD (Sección 4.3):")
            lineas.append(
                f"   • Más central por GRADO C_D(v) = deg(v)/(n-1) → {cent['lider_grado']} (C_D = 4/8 = 0.500)"
            )
            lineas.append(
                "     Responde: ¿Quién tiene más contactos directos? N7 recibe 3 caudales"
            )
            lineas.append(
                "     (N3, N5, N6) y descarga hacia N8 (mayor grado entrante Δ⁻(G) = 3)."
            )
            lineas.append(
                f"   • Más central por CERCANÍA C_C(v) = (n-1)/∑d(v,u) → {cent['lider_cercania']} (C_C = 8/14 = 0.571)"
            )
            lineas.append(
                "     Responde: ¿Quién está mejor ubicado en promedio respecto a toda la red?"
            )
            lineas.append(
                "     En el digrafo (no fuertemente conexo), usamos la VARIANTE ARMÓNICA (diap. 14):"
            )
            lineas.append(
                "     H(v) = (1/(n-1)) ∑ (1/d_dir(v,u)) con 1/∞ = 0, donde destacan N1 y N4"
            )
            lineas.append(
                "     por su capacidad de difundir alertas tempranas hacia aguas abajo."
            )
            lineas.append(
                f"   • Más central por INTERMEDIACIÓN C_B(v) = ∑(σ_st(v)/σ_st) → {cent['lider_intermediacion']} (C_B = 15.0, norm = 0.536)"
            )
            lineas.append(
                "     Responde: ¿Quién es el PUENTE o CUELLO DE BOTELLA?"
            )
            lineas.append(
                "     ¡N7 (Canal colector perimetral) es el puente crítico! Todos los caminos"
            )
            lineas.append(
                "     desde la zona alta (N1..N6) hacia el Arroyo León (N8) y la Ciénaga (N9)"
            )
            lineas.append(
                "     pasan por N7. Decisión de ingeniería: priorizar sensores y limpieza en N7 y N4."
            )

        elif idx == 1:
            orden = g.ids_ordenados
            d_nodir = cent["distancias_no_dirigidas"]  # type: ignore[assignment]
            d_dir = cent["distancias_dirigidas"]  # type: ignore[assignment]
            lineas.append("═" * 74)
            lineas.append("MATRIZ DE DISTANCIAS GEODÉSICAS d(u, v) CON BFS Y DIÁMETRO (SECCIÓN 4.3)")
            lineas.append("═" * 74)
            lineas.append(
                f"• Grafo subyacente (conexo): Diámetro = {cent['diametro_no_dirigido']} aristas "
                "(mayor distancia geodésica entre dos vértices, ej. d(N1, N9) = 5 y d(N1, N2) = 5)."
            )
            lineas.append("  " + " ".join(f"{v:>3}" for v in orden) + " │ ∑d(v,u)")
            lineas.append("  " + "────" * len(orden) + "─┼────────")
            for u in orden:
                fila = " ".join(f"{d_nodir[(u, v)]:>3}" for v in orden)  # type: ignore[index]
                suma_u = sum(d_nodir[(u, v)] for v in orden if v != u)  # type: ignore[index, misc]
                lineas.append(f"{u:>2} {fila} │ {suma_u:>5}")
            lineas.append("")
            lineas.append(
                f"• Digrafo aguas abajo (d(u,v) = ∞ si no hay camino dirigido): Diámetro finito = {cent['diametro_dirigido']}"
            )
            lineas.append("  " + " ".join(f"{v:>3}" for v in orden))
            for u in orden:
                fila_d = " ".join(
                    f"{(str(d_dir[(u, v)]) if d_dir[(u, v)] is not None else '∞'):>3}"  # type: ignore[index]
                    for v in orden
                )
                lineas.append(f"{u:>2} {fila_d}")

        elif idx == 2:
            lineas.append("═" * 74)
            lineas.append("CÁLCULO PASO A PASO DE INTERMEDIACIÓN C_B(v) (SECCIÓN 4.3, DIAP. 16-18)")
            lineas.append("═" * 74)
            lineas.append("Fórmula: C_B(v) = ∑_{s<t, s,t≠v} (σ_st(v) / σ_st)")
            lineas.append("Regla clave (diap. 17): Si hay 2 o más caminos geodésicos (σ_st ≥ 2),")
            lineas.append("se suma la FRACCIÓN σ_st(v)/σ_st de ellos que pasan por v.")
            lineas.append("")
            lineas.append("Pares con múltiples caminos más cortos (σ_st = 2) en nuestra cuenca:")
            for s, t in [("N1", "N7"), ("N4", "N7"), ("N4", "N8"), ("N4", "N9"), ("N5", "N6")]:
                cams = g.caminos_mas_cortos_entre(s, t, dirigido=False)
                cams_str = "  y  ".join("→".join(c) for c in cams)
                lineas.append(f"  • Par {{{s}, {t}}}: σ_{{{s},{t}}} = {len(cams)} caminos geodésicos:")
                lineas.append(f"      {cams_str}")
                lineas.append(
                    f"      ⇒ N5 y N6 reciben cada uno σ({s},{t}|v)/σ({s},{t}) = 1/2 = 0.50 en este par."
                )
            lineas.append("")
            lineas.append(f"Desglose para el nodo seleccionado ({self.seleccion}):")
            vs = g.ids_ordenados
            total_v = 0.0
            for i in range(len(vs)):
                for j in range(i + 1, len(vs)):
                    s, t = vs[i], vs[j]
                    if s == self.seleccion or t == self.seleccion:
                        continue
                    cams = g.caminos_mas_cortos_entre(s, t, dirigido=False)
                    pasan = [c for c in cams if self.seleccion in c[1:-1]]
                    if pasan:
                        frac = len(pasan) / len(cams)
                        total_v += frac
                        lineas.append(
                            f"  • Par {{{s},{t}}}: pasan {len(pasan)}/{len(cams)} = {frac:.2f} "
                            f"({' | '.join('~'.join(c) for c in pasan)})"
                        )
            if total_v == 0:
                lineas.append(f"  Ningún camino más corto entre otros pares pasa por {self.seleccion} (C_B = 0).")
            else:
                lineas.append(f"  ⇒ Total C_B({self.seleccion}) = {total_v:.2f} (Normalizada = {total_v/28:.3f})")

        else:
            lineas.append("═" * 74)
            lineas.append("RED BIPARTITA CIUDADANOS–NODOS Y SU PROYECCIÓN (SECCIÓN 4.2, DIAP. 5-6)")
            lineas.append("═" * 74)
            lineas.append("Definición: Sea una red bipartita con clases U (Ciudadanos reportantes)")
            lineas.append("y W = V (Nodos de la cuenca), donde (c, v) indica que el ciudadano c")
            lineas.append("reportó en el nodo v. En la proyección sobre U, dos ciudadanos c1, c2")
            lineas.append("son adyacentes si reportaron en el mismo nodo v ∈ V (forman un clique por nodo).")
            lineas.append("")
            total_c = sum(len(n.reportantes) for n in g.nodos.values())
            if total_c == 0:
                lineas.append("Actualmente no hay reportes activos (U = ∅).")
                lineas.append("Envía reportes ciudadanos en uno o varios nodos para ver la red bipartita")
                lineas.append("U × V y cuántas aristas genera su proyección sobre los ciudadanos.")
            else:
                aristas_proy = 0
                for v, n in g.nodos.items():
                    if n.reportantes:
                        reps = sorted(n.reportantes)
                        k_r = len(reps)
                        aristas_clique = k_r * (k_r - 1) // 2
                        aristas_proy += aristas_clique
                        lineas.append(
                            f"  • Nodo {v} ({n.corto}): vecinos en U = {{{', '.join(reps)}}} "
                            f"→ genera K_{k_r} con {aristas_clique} arista(s) en la proyección."
                        )
                lineas.append("")
                lineas.append(
                    f"Total de ciudadanos |U| = {total_c} | Total de aristas en la proyección sobre U = {aristas_proy}."
                )

        self.txt_redes.configure(state="normal")
        self.txt_redes.delete("1.0", "end")
        self.txt_redes.insert("1.0", "\n".join(lineas))
        self.txt_redes.configure(state="disabled")

    # -- Pestaña 3: Unidad 3 (Teoría de Grafos y Árboles) ---------------------
    def _actualizar_tab_grafo(self) -> None:
        if not hasattr(self, "txt_grafo"):
            return
        idx = self.combo_vista_grafo.current()
        g = self.cuenca
        lineas: List[str] = []

        if idx == 0:
            ext = g.extremos_grados()
            s_in, s_out, num_e, _ = g.verificar_lema_apreton_manos()
            lineas.append("═" * 76)
            lineas.append("1. VECINDADES, VALENCIA (δ, Δ, δ±, Δ±), TAM Y COROLARIO (PROF. YESNERI ZULETA)")
            lineas.append("═" * 76)
            lineas.append(
                f" ID   {'grad⁻':>5} {'grad⁺':>5} {'grad':>5}  {'N_G⁻(v)':<14} {'N_G⁺(v)':<12} {'N_G(v) (Abierta)':<20} {'N_G[v] (Cerrada)'}"
            )
            lineas.append("─" * 76)
            for f in g.tabla_grados():
                marca = "►" if f["id"] == self.seleccion else " "
                ni = "{" + ",".join(f["vecindad_in"]) + "}"  # type: ignore[arg-type]
                no = "{" + ",".join(f["vecindad_out"]) + "}"  # type: ignore[arg-type]
                na = "{" + ",".join(f["vecindad_abierta"]) + "}"  # type: ignore[arg-type]
                nc = "{" + ",".join(f["vecindad_cerrada"]) + "}"  # type: ignore[arg-type]
                lineas.append(
                    f"{marca}{f['id']:<4} {int(f['deg_in']):>5} {int(f['deg_out']):>5} "
                    f"{int(f['deg_total']):>5}  {ni:<14} {no:<12} {na:<20} {nc}"
                )
            lineas.append("─" * 76)
            lineas.append("• Extremos en Grafo Subyacente No Dirigido (Prof. Zuleta, diap. 8):")
            lineas.append(
                f"    Grado mínimo δ(G) = {ext['delta_min']}  |  Grado máximo Δ(G) = {ext['delta_max']}  |  "
                f"Lema 0 ≤ grad(v) ≤ n-1: {'CUMPLE ✓' if ext['cumple_cota_grado'] else 'NO'}"
            )
            lineas.append(
                f"    ¿Vértices aislados (grad=0)? {ext['vertices_aislados'] or 'Ninguno (∅)'}  |  "
                f"¿Es r-regular? {'SÍ' if ext['es_regular'] else 'NO (δ(G) ≠ Δ(G))'}"
            )
            lineas.append("• Extremos en el Digrafo (Prof. Zuleta, diap. 9):")
            lineas.append(
                f"    Δ⁺(G) = {ext['delta_out_max']} (en N4), δ⁺(G) = {ext['delta_out_min']} (en N9)  |  "
                f"Δ⁻(G) = {ext['delta_in_max']} (en N7), δ⁻(G) = {ext['delta_in_min']} (en N1, N2)"
            )
            lineas.append("• Teorema del Apretón de Manos (TAM) y Corolario (Prof. Zuleta, diap. 3, 7, 9):")
            lineas.append(
                f"    No dirigido: ∑ grad(v) = 2m ⇒ {ext['suma_grados_no_dirigido']} = 2({num_e}) = {ext['dos_m']} (par ✓)"
            )
            lineas.append(
                f"    Corolario: Vértices con grado impar = {ext['vertices_impares']} "
                f"(total = {len(ext['vertices_impares'])}, que es un NÚMERO PAR ✓)"
            )
            lineas.append(
                f"    Dirigido: ∑ grad⁻(v) = ∑ grad⁺(v) = m ⇒ {s_in} = {s_out} = {num_e} ✓"
            )

        elif idx == 1:
            bip = g.analisis_bipartito()
            sub = g.subgrafo_inducido_sin_vertice(self.seleccion)
            lineas.append("═" * 76)
            lineas.append("2. CLASIFICACIÓN EN LAS 4 CATEGORÍAS (3.2) Y SUBGRAFO INDUCIDO G - v")
            lineas.append("═" * 76)
            lineas.append("A) Clasificación de la red de la cuenca (Ejercicio tipo Diap. 12 - Unidad 3):")
            lineas.append("  1. ¿Simple o multigrafo? : SIMPLE (sin lazos u=v ni aristas múltiples; es 1-grafo).")
            lineas.append("  2. ¿Dirigido o no?       : DIRIGIDO (los arcos siguen la pendiente hacia la ciénaga).")
            lineas.append("  3. ¿Ponderado?           : SÍ, cada arco tiene peso w(u,v) = distancia en metros.")
            lineas.append(
                f"  4. ¿Bipartito?           : {'SÍ ✓' if bip['es_bipartito'] else 'NO'} — {bip['justificacion']}"
            )
            lineas.append(f"     • Clase V₁ = {bip['V1']}")
            lineas.append(f"     • Clase V₂ = {bip['V2']}  (V₁ ∩ V₂ = ∅ y toda arista une V₁ con V₂)")
            lineas.append("")
            lineas.append(
                f"B) Subgrafo Inducido G - {self.seleccion} por V - {{{self.seleccion}}} (Prof. Zuleta, diap. 4):"
            )
            lineas.append(
                f"  • Vértices V' = V - {{{self.seleccion}}} (|V'| = {len(sub['vertices_restantes'])}) | "
                f"Aristas restantes |A'| = {sub['num_aristas_restantes']}"
            )
            lineas.append(
                f"  • Número de componentes conexas c(G - {self.seleccion}) = {sub['num_componentes']} "
                f"⇒ ¿Es punto de articulación? {'SÍ (Cuello de botella)' if sub['es_punto_articulacion'] else 'NO'}"
            )
            for idx_c, comp in enumerate(sub["componentes"], 1):  # type: ignore[arg-type]
                lineas.append(f"      Componente {idx_c}: {comp}")
            lineas.append(
                f"  • Nodos que pierden drenaje hacia el sumidero N9 si colapsa {self.seleccion}: "
                f"{sub['desconectados_del_sumidero'] or 'Ninguno'}"
            )

        elif idx == 2:
            orden, mat_a = g.matriz_adyacencia(dirigido=True)
            _, aristas, mat_m_nodir = g.matriz_incidencia(dirigido=False)
            _, _, mat_b_dir = g.matriz_incidencia(dirigido=True)
            etq_e = [f"e{j+1}" for j in range(len(aristas))]
            lineas.append("═" * 76)
            lineas.append("3. REPRESENTACIONES: LISTA DE ADYACENCIA, MATRIZ DE ADYACENCIA E INCIDENCIA (3.3)")
            lineas.append("═" * 76)
            lineas.append("A) Lista de Adyacencia Dirigida y No Dirigida — Espacio O(|V| + |E|) = O(18):")
            for v in orden:
                lineas.append(
                    f"   {v} : N⁺={g.vecindad_salida(v)}  |  N(v) no dirigido={g.vecindad_abierta(v)}"
                )
            lineas.append("")
            lineas.append("B) Matriz de Adyacencia Dirigida A (|V|×|V|) — Espacio O(|V|²):")
            lineas.append("      " + " ".join(f"{v:>3}" for v in orden) + " │ grad⁺")
            for i, u in enumerate(orden):
                f_str = " ".join(f"{mat_a[i][j]:>3}" for j in range(len(orden)))
                lineas.append(f" {u:>2} │ {f_str} │ {sum(mat_a[i]):>3}")
            lineas.append("")
            lineas.append(
                "C) Matriz de Incidencia No Dirigida M_ie ∈ {0,1} (Unidad 3.3, diap. 15: cada columna suma 2):"
            )
            lineas.append("   Aristas: " + ", ".join(f"e{j+1}={u}{v}" for j, (u, v) in enumerate(aristas)))
            lineas.append("      " + " ".join(f"{e:>3}" for e in etq_e) + " │ suma=deg(v)")
            for i, v in enumerate(orden):
                f_str = " ".join(f"{mat_m_nodir[i][j]:>3}" for j in range(len(aristas)))
                lineas.append(f" {v:>2} │ {f_str} │ {sum(mat_m_nodir[i]):>3}")
            lineas.append("")
            lineas.append("D) Matriz de Incidencia Dirigida B_ie ∈ {-1, 0, +1} (cada columna suma 0):")
            for i, v in enumerate(orden):
                f_str = " ".join(f"{mat_b_dir[i][j]:>3}" for j in range(len(aristas)))
                lineas.append(f" {v:>2} │ {f_str}")

        elif idx == 3:
            con = g.analisis_conectividad()
            orden, w = g.clausura_transitiva_warshall()
            props = g.propiedades_relacion_alcanzabilidad()
            lineas.append("═" * 76)
            lineas.append("4. CONECTIVIDAD EN DIGRAFOS (3.4), CLAUSURA DE WARSHALL Y ORDEN PARCIAL")
            lineas.append("═" * 76)
            lineas.append("• Conectividad del Digrafo (Unidad 3.4, diap. 21):")
            lineas.append(
                f"    ¿Fuertemente conexo? : {'SÍ' if con['fuertemente_conexo'] else 'NO (no hay ciclos dirigidos; el agua no sube por gravedad)'}"
            )
            lineas.append(
                f"    ¿Débilmente conexo?  : {'SÍ ✓' if con['debilmente_conexo'] else 'NO'} "
                f"(al ignorar direcciones es conexo con c(G) = {con['num_componentes']} componente)."
            )
            lineas.append("")
            lineas.append("• Matriz de Alcanzabilidad / Clausura Transitiva de Warshall W = A⁺:")
            lineas.append("      " + " ".join(f"{v:>3}" for v in orden) + " │ Alcanza")
            for i, u in enumerate(orden):
                f_str = " ".join(f"{('1' if val else '·'):>3}" for val in w[i])
                lineas.append(f" {u:>2} │ {f_str} │ {sum(w[i]):>3}")
            lineas.append("")
            lineas.append(
                f"• Relación de alcanzabilidad R⁺: Irreflexiva={props['irreflexiva']}, "
                f"Asimétrica={props['asimetrica']}, Transitiva={props['transitiva']} "
                f"⇒ Orden Parcial Estricto = {props['es_orden_parcial_estricto']} ({props['num_pares_alcanzables']} pares)."
            )

        elif idx == 4:
            ehp = g.analisis_euler_hamilton_plano()
            lineas.append("═" * 76)
            lineas.append("5. TEOREMA DE EULER (3.5), HAMILTONIANO (DIRAC/ORE) Y GRAFOS PLANOS (3.6)")
            lineas.append("═" * 76)
            lineas.append("A) Camino y Circuito Euleriano (Teorema de Euler, 1736 - Diap. 24-26):")
            lineas.append(
                f"   • Vértices de grado impar en el grafo subyacente: {ehp['impares']} (total = {ehp['num_impares']})"
            )
            lineas.append("   • Regla práctica (Diap. 25): 0 impares ⇒ circuito; 2 impares ⇒ camino; >2 ⇒ ninguno.")
            lineas.append(
                "   ⇒ Conclusión: Como hay 4 vértices de grado impar (> 2), la cuenca NO tiene"
            )
            lineas.append("     ni camino ni circuito Euleriano.")
            lineas.append("")
            lineas.append("B) Camino y Circuito Hamiltoniano (Teoremas de Dirac 1952 y Ore 1960 - Diap. 28-30):")
            lineas.append(
                f"   • Teorema de Dirac: ¿deg(v) ≥ n/2 = {ehp['umbral_dirac']} para todo v? "
                f"{'SÍ' if ehp['cumple_dirac'] else 'NO (δ(G) = 1 < 4.5)'}."
            )
            min_ore_val = ehp["min_suma_ore"]
            lineas.append(
                f"   • Teorema de Ore: ¿deg(u)+deg(v) ≥ n = {ehp['n']} para todo par no adyacente? "
                f"{'SÍ' if ehp['cumple_ore'] else f'NO (mínimo = {min_ore_val} < 9)'}."
            )
            lineas.append(
                "   • Verificación estructural: como N1, N2 y N9 tienen grado 1 (hojas colgantes),"
            )
            lineas.append("     ningún ciclo o camino simple puede visitar los 9 vértices sin repetir.")
            lineas.append("")
            lineas.append("C) Grafos Planos y Fórmula de Euler (Sección 3.6 - Diap. 32-35):")
            lineas.append(
                f"   • Cota general (E ≤ 3V - 6)   : {ehp['m']} ≤ 3({ehp['n']}) - 6 = {ehp['cota_plana_general']}  [NO SE VIOLA ✓]"
            )
            lineas.append(
                f"   • Cota bipartita (E ≤ 2V - 4) : {ehp['m']} ≤ 2({ehp['n']}) - 4 = {ehp['cota_plana_bipartita']}  [NO SE VIOLA ✓]"
            )
            lineas.append(
                f"   • Fórmula de Euler (V - E + F = 2): {ehp['n']} - {ehp['m']} + {ehp['caras_F']} = 2 ✓"
            )
            lineas.append(
                "     Las F = 2 caras del embebido plano son: f₁ (región cerrada N4-N5-N7-N6)"
            )
            lineas.append("     y f₂ (cara exterior infinita). El grafo es PLANO (sin K₅ ni K₃,₃).")

        elif idx == 5:
            t_bfs = g.traza_bfs_detallada(self.seleccion, dirigido=True)
            t_dfs = g.traza_dfs_detallada(self.seleccion, dirigido=True)
            t_bfs_sub = g.traza_bfs_detallada(self.seleccion, dirigido=False)
            t_dfs_sub = g.traza_dfs_detallada(self.seleccion, dirigido=False)
            lineas.append("═" * 76)
            lineas.append(f"6. TRAZAS PASO A PASO DE BFS Y DFS DESDE {self.seleccion} (SECCIÓN 3.8, DIAP. 46-50)")
            lineas.append("═" * 76)
            lineas.append(f"A) Recorrido Dirigido Aguas Abajo desde {self.seleccion}:")
            lineas.append("   Traza de BFS (Cola FIFO)                     │ Traza de DFS (Recursión / Pila)")
            lineas.append("   Paso  Llama  Se entera nuevo  Cola           │ Paso  Visita  Llamado desde")
            lineas.append("   ─────────────────────────────────────────────┼────────────────────────────")
            pasos_b = t_bfs["pasos"]  # type: ignore[assignment]
            pasos_d = t_dfs["pasos"]  # type: ignore[assignment]
            max_p = max(len(pasos_b), len(pasos_d))
            for i in range(max_p):
                izq = (
                    f"   {pasos_b[i]['paso']:>4}  {pasos_b[i]['quien_llama']:<5}  "
                    f"{pasos_b[i]['se_entera_nuevo']:<15}  {pasos_b[i]['cola']:<14}"
                    if i < len(pasos_b)
                    else " " * 47
                )
                der = (
                    f" {pasos_d[i]['paso']:>4}  {pasos_d[i]['visita']:<6}  {pasos_d[i]['llamado_desde']}"
                    if i < len(pasos_d)
                    else ""
                )
                lineas.append(f"{izq} │{der}")
            lineas.append("")
            lineas.append(
                f"   • Orden de visita BFS dirigido: {', '.join(t_bfs['orden_visita'])}"  # type: ignore[arg-type]
            )
            lineas.append(
                f"   • Orden de visita DFS dirigido: {', '.join(t_dfs['orden_visita'])}"  # type: ignore[arg-type]
            )
            lineas.append(
                f"   • Vocabulario de Árbol con Raíz {self.seleccion} (3.7, diap. 39): "
                f"Altura = {t_bfs['altura']}, Hojas = {t_bfs['hojas']}"
            )
            lineas.append("")
            lineas.append(
                f"B) Comparación Árbol de Expansión BFS vs. Árbol DFS en Grafo Completo Conexo (Diap. 49):"
            )
            lineas.append(
                f"   Ambos generan un árbol de expansión con n - 1 = 8 aristas (de las 9 totales):"
            )
            lineas.append(f"   • Orden BFS (no dirigido): {', '.join(t_bfs_sub['orden_visita'])}")  # type: ignore[arg-type]
            lineas.append(f"   • Orden DFS (no dirigido): {', '.join(t_dfs_sub['orden_visita'])}")  # type: ignore[arg-type]

        else:
            mst = g.mst_kruskal_prim()
            dijk = g.dijkstra(self.seleccion, dirigido=True)
            lineas.append("═" * 76)
            lineas.append("7. ÁRBOL DE EXPANSIÓN MÍNIMO (MST: KRUSKAL Y PRIM), DIJKSTRA E INDUCCIÓN")
            lineas.append("═" * 76)
            lineas.append("A) Árbol de Expansión Mínimo (MST - Sección 3.8, diap. 44):")
            lineas.append(
                f"   El grafo subyacente conexo tiene |V|=9 vértices y |E|=9 aristas (1 ciclo de 4 aristas)."
            )
            lineas.append(
                f"   Todo árbol de expansión usa exactamente n - 1 = 8 aristas (descarta 1 arista del ciclo)."
            )
            lineas.append("   • Aristas seleccionadas por Kruskal / Prim (ordenadas):")
            for u, v, w in mst["mst_kruskal"]:  # type: ignore[union-attr]
                lineas.append(f"       ({u}, {v}) con peso w = {w} m")
            for u, v, w in mst["descartadas_kruskal"]:  # type: ignore[union-attr]
                lineas.append(
                    f"   • Arista descartada para evitar ciclo: ({u}, {v}) de peso {w} m (la más costosa del ciclo N4-N5-N7-N6)."
                )
            lineas.append(f"   ⇒ Costo total del MST = {mst['costo_total']} m (actívalo en el mapa con 'MST').")
            lineas.append("")
            lineas.append(f"B) Caminos Más Cortos Ponderados desde {self.seleccion} (Algoritmo de Dijkstra):")
            dist_d = dijk["distancias"]  # type: ignore[assignment]
            cams_d = dijk["caminos"]  # type: ignore[assignment]
            for dest in g.ids_ordenados:
                if dist_d[dest] < float("inf"):
                    lineas.append(
                        f"   • Hacia {dest}: costo mínimo = {int(dist_d[dest]):>4} m  |  Ruta: {' → '.join(cams_d[dest])}"
                    )
            lineas.append("")
            lineas.append("C) Principio de Inducción Matemática (Prof. Yesneri Zuleta, diap. 4-5):")
            lineas.append("   Proposición P(n): 'Todo árbol T con n ≥ 1 vértices tiene exactamente n - 1 aristas'.")
            lineas.append("   (i) Paso base P(1): Para n = 1 vértice sin ciclos, hay 0 = 1 - 1 aristas. Cumple.")
            lineas.append("   (ii) Paso inductivo P(k) ⇒ P(k+1): Sea T un árbol con k+1 vértices. Al tener al menos")
            lineas.append("        una hoja v de grado 1, T - v es un árbol de k vértices (por H.I. tiene k - 1 aristas).")
            lineas.append("        Al reincorporar v y su única arista incidente, T tiene (k - 1) + 1 = k aristas. Q.E.D.")

        self.txt_grafo.configure(state="normal")
        self.txt_grafo.delete("1.0", "end")
        self.txt_grafo.insert("1.0", "\n".join(lineas))
        self.txt_grafo.configure(state="disabled")
