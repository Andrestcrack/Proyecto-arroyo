#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Monitoreo Colaborativo y Alerta Temprana de Arroyos
Zona Universidad del Norte – cuenca occidental (Arroyo León / Ciénaga de Mallorquín)
===================================================================================
Aplicación de escritorio (tkinter) que modela la escorrentía de la zona de Uninorte
con estructuras de Matemáticas Discretas:

  * Grafo dirigido acíclico  G = (V, E)           -> clase CuencaDAG (modelo_discreto.py)
  * Autómata finito determinista M = (Q,Σ,δ,q0,F) -> clase AFD (modelo_discreto.py)
  * Lógica booleana / umbral de consenso           -> clase ValidadorConsenso (modelo_discreto.py)
  * Recorrido BFS sobre el DAG (propagación)       -> CuencaDAG.descendientes_bfs / capas_bfs
  * Matrices discretas y relaciones (Adyacencia, Incidencia, Warshall, Poset, Camino Crítico)

Arquitectura modular:
  - modelo_discreto.py : Estructuras formales (AFD, ValidadorConsenso, Nodo, CuencaDAG)
  - sistema_alerta.py  : Coordinación de eventos, propagación BFS y generación de informes
  - interfaz_app.py    : Interfaz gráfica interactiva (Mapa, Diagrama AFD en vivo, Análisis Discreto)
  - recursos_mapa.py   : Mapa base en formato PNG (Base64)
  - test_arroyos.py    : Suite de pruebas unitarias automatizadas

Ejecutar aplicación:  python arroyos_uninorte.py
Ejecutar pruebas:     python -m unittest test_arroyos.py -v
"""

from __future__ import annotations

from interfaz_app import App
from modelo_discreto import (
    AFD,
    COLORES,
    CuencaDAG,
    DESCRIPCION,
    Estado,
    FUENTE_AUTOR,
    FUENTE_OFICIAL,
    FUENTE_TERRENO,
    Nodo,
    Simbolo,
    ValidadorConsenso,
    crear_cuenca_uninorte,
)
from recursos_mapa import MAPA_PANORAMICO_B64, MAPA_PNG_B64
from sistema_alerta import LogFn, SistemaAlerta

__all__ = [
    "AFD",
    "App",
    "COLORES",
    "CuencaDAG",
    "DESCRIPCION",
    "Estado",
    "FUENTE_AUTOR",
    "FUENTE_OFICIAL",
    "FUENTE_TERRENO",
    "LogFn",
    "MAPA_PANORAMICO_B64",
    "MAPA_PNG_B64",
    "Nodo",
    "Simbolo",
    "SistemaAlerta",
    "ValidadorConsenso",
    "crear_cuenca_uninorte",
]


if __name__ == "__main__":
    App().mainloop()
