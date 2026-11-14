#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lógica del Sistema de Alerta Temprana (independiente de la GUI).

Coordina:
  - Transiciones de estado discreto por vértice.
  - Validación por umbral de consenso booleano C(R, k).
  - Propagación topológica aguas abajo mediante BFS (instantánea o por capas animadas).
  - Simulación formal de palabras w ∈ Σ* sobre un nodo.
  - Generación de informe técnico-matemático completo (Unidades 3 y 4 + Prof. Yesneri Zuleta).
"""

from __future__ import annotations

from datetime import datetime
from typing import Callable, Iterable, List, Optional, Tuple

from modelo_discreto import (
    CuencaDAG,
    DESCRIPCION,
    Estado,
    Nodo,
    Simbolo,
    ValidadorConsenso,
)

LogFn = Callable[[str, str], None]  # (mensaje, etiqueta)


class SistemaAlerta:
    """Coordina transición de estados + consenso booleano + propagación BFS sobre el DAG."""

    def __init__(self, cuenca: CuencaDAG, k: int, log: LogFn) -> None:
        self.cuenca = cuenca
        self.k = k
        self.log = log
        self._contador_ciudadanos = 0
        self.bitacora_eventos: List[Tuple[str, str, str]] = []

    def _emitir(self, mensaje: str, etiqueta: str = "info") -> None:
        hora = datetime.now().strftime("%H:%M:%S")
        self.bitacora_eventos.append((hora, etiqueta, mensaje))
        self.log(mensaje, etiqueta)

    def _transicion(self, nodo: Nodo, simbolo: Simbolo) -> bool:
        antes, despues = nodo.control_estado.procesar(simbolo)
        cambio = antes is not despues
        marca = "→" if cambio else "(sin cambio)"
        self._emitir(
            f"[ESTADO] {nodo.id}: δ({antes.value}, {simbolo.value}) = {despues.value} {marca}",
            "estado",
        )
        return cambio

    def tiene_ancestro_critico(self, id_nodo: str) -> bool:
        return any(
            self.cuenca.nodos[u].estado is Estado.ROJO
            for u in self.cuenca.ancestros(id_nodo)
        )

    def enviar_reporte(
        self,
        id_nodo: str,
        propagar_inmediato: bool = True,
    ) -> Optional[List[Tuple[int, List[str]]]]:
        nodo = self.cuenca.nodos[id_nodo]
        self._contador_ciudadanos += 1
        ciudadano = f"C-{self._contador_ciudadanos:03d}"
        nodo.reportantes.add(ciudadano)
        n = len(nodo.reportantes)
        self._emitir(f"Reporte ciudadano {ciudadano} en {nodo.id} ({nodo.corto}).", "info")

        validado = ValidadorConsenso.consenso(nodo.reportantes, self.k)
        self._emitir(
            f"[LÓGICA] C(R,k) = (|R| ≥ k) = ({n} ≥ {self.k}) = {'V' if validado else 'F'}",
            "logica",
        )

        if nodo.estado is Estado.ROJO:
            self._emitir(
                f"{nodo.id} ya está en ROJO; reporte adicional registrado en R_{nodo.id}.",
                "info",
            )
            return None

        if validado:
            self._emitir(
                f"Emergencia VALIDADA en {nodo.id}: umbral de consenso alcanzado.",
                "critico",
            )
            self._transicion(nodo, Simbolo.CONSENSO)
            if propagar_inmediato:
                self._propagar(nodo)
                return None
            return self.preparar_propagacion_bfs(nodo.id)
        else:
            self._emitir(
                f"Faltan {self.k - n} reporte(s) independiente(s) para validar.",
                "info",
            )
            self._transicion(nodo, Simbolo.REPORTE)
            return None

    def procesar_palabra_en_nodo(
        self,
        id_nodo: str,
        simbolos: Iterable[Simbolo],
        propagar_si_rojo: bool = True,
    ) -> None:
        lista_simbolos = list(simbolos)
        if not lista_simbolos:
            return
        nodo = self.cuenca.nodos[id_nodo]
        q_inicial = nodo.estado
        cad = " · ".join(s.value for s in lista_simbolos)
        self._emitir(
            f"[EVENTOS] Evaluando secuencia w = ({cad}) en {nodo.id} desde q = {q_inicial.value}",
            "estado",
        )
        for s in lista_simbolos:
            if s is Simbolo.REINICIO:
                nodo.reportantes.clear()
            self._transicion(nodo, s)
            if s is Simbolo.CONSENSO and propagar_si_rojo:
                self._propagar(nodo)

    def simular_crecida(self) -> None:
        self._emitir("=== SIMULACIÓN: crecida en las cabeceras de la cuenca ===", "critico")
        for id_ in self.cuenca.cabeceras():
            nodo = self.cuenca.nodos[id_]
            if nodo.estado is Estado.ROJO:
                continue
            self._emitir(f"Crecida forzada en cabecera {nodo.id} ({nodo.corto}).", "alerta")
            self._transicion(nodo, Simbolo.CONSENSO)
            self._propagar(nodo)

    def preparar_propagacion_bfs(self, id_origen: str) -> List[Tuple[int, List[str]]]:
        capas = self.cuenca.capas_bfs(id_origen)
        total = sum(len(ns) for _, ns in capas)
        if not capas:
            self._emitir(f"[BFS] {id_origen} no tiene descendientes aguas abajo.", "alerta")
        else:
            self._emitir(
                f"[BFS] Propagando desde {id_origen}: {total} nodo(s) aguas abajo en {len(capas)} capa(s).",
                "alerta",
            )
        return capas

    def aplicar_capa_bfs(self, dist: int, ids_nodos: List[str]) -> None:
        for id_ in ids_nodos:
            nodo = self.cuenca.nodos[id_]
            self._emitir(
                f"   ↳ nivel +{dist}: alerta preventiva a {nodo.id} ({nodo.corto})",
                "alerta",
            )
            self._transicion(nodo, Simbolo.ALERTA)

    def _propagar(self, origen: Nodo) -> None:
        capas = self.preparar_propagacion_bfs(origen.id)
        for dist, ids_nodos in capas:
            self.aplicar_capa_bfs(dist, ids_nodos)

    def reiniciar(self) -> None:
        for nodo in self.cuenca.nodos.values():
            nodo.reiniciar()
        self._contador_ciudadanos = 0
        self._emitir(
            "Red reiniciada: todos los vértices en q0 = VERDE, conjuntos R_v = ∅.",
            "sistema",
        )

    def generar_informe_texto(self) -> str:
        """Genera un informe completo con todos los análisis de las Unidades 3 y 4."""
        g = self.cuenca
        lineas: List[str] = []
        lineas.append("=" * 80)
        lineas.append("INFORME TÉCNICO Y MATEMÁTICO – SISTEMA DE ALERTA TEMPRANA DE ARROYOS")
        lineas.append("Zona Universidad del Norte – Cuenca Occidental (Arroyo León / Mallorquín)")
        lineas.append(f"Fecha y hora de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lineas.append("=" * 80)
        lineas.append("")

        # 1. Modelación y propiedades del grafo (Unidades 3 y 4)
        s_in, s_out, num_e, cumple_lema = g.verificar_lema_apreton_manos()
        ext = g.extremos_grados()
        bip = g.analisis_bipartito()
        ehp = g.analisis_euler_hamilton_plano()
        cent = g.analisis_centralidades_unidad4()
        mst = g.mst_kruskal_prim()

        lineas.append("1. MODELACIÓN Y PROPIEDADES ESTRUCTURALES (UNIDADES 3 Y 4)")
        lineas.append("-" * 80)
        lineas.append(f"  • Orden y tamaño: n = |V| = {len(g.nodos)}, m = |E| = {num_e}")
        lineas.append(
            f"  • Extremos de grado (no dirigido): δ(G)={ext['delta_min']}, Δ(G)={ext['delta_max']} "
            f"| ∑grad(v) = {ext['suma_grados_no_dirigido']} = 2m"
        )
        lineas.append(
            f"  • Extremos de grado (digrafo): δ⁻={ext['delta_in_min']}, Δ⁻={ext['delta_in_max']}, "
            f"δ⁺={ext['delta_out_min']}, Δ⁺={ext['delta_out_max']} | ∑grad⁻=∑grad⁺={num_e}"
        )
        lineas.append(
            f"  • Bipartito: {bip['es_bipartito']} (V1={bip['V1']}, V2={bip['V2']})"
        )
        lineas.append(
            f"  • Planaridad (Fórmula de Euler V-E+F=2): {ehp['n']} - {ehp['m']} + {ehp['caras_F']} = 2 "
            f"| Cota E ≤ 2V-4: {ehp['m']} ≤ {ehp['cota_plana_bipartita']}"
        )
        lineas.append(
            f"  • Árbol de Expansión Mínimo (MST Kruskal/Prim): {mst['num_aristas_mst']} aristas, "
            f"costo total = {mst['costo_total']} m"
        )
        lineas.append("")

        # 2. Centralidades (Unidad 4)
        lineas.append("2. ANÁLISIS DE REDES: CENTRALIDAD DE GRADO, CERCANÍA E INTERMEDIACIÓN (UNIDAD 4)")
        lineas.append("-" * 80)
        lineas.append(
            f"  {'Nodo':<5} {'deg(v)':>6} {'C_D(v)':>8} {'C_D⁻':>7} {'C_D⁺':>7} "
            f"{'∑d(v,u)':>8} {'C_C(v)':>8} {'H_dir(v)':>9} {'C_B(v)':>8} {'C_B norm':>9}"
        )
        for f in cent["tabla"]:  # type: ignore[union-attr]
            lineas.append(
                f"  {str(f['id']):<5} {int(f['deg']):>6} {float(f['cd']):>8.3f} "
                f"{float(f['cd_in']):>7.3f} {float(f['cd_out']):>7.3f} "
                f"{int(f['suma_dist']):>8} {float(f['cc']):>8.3f} {float(f['h_dir']):>9.3f} "
                f"{float(f['cb']):>8.2f} {float(f['cb_norm']):>9.3f}"
            )
        lineas.append(
            f"  ⇒ Más central por Grado: {cent['lider_grado']} | "
            f"Por Cercanía: {cent['lider_cercania']} | "
            f"Por Intermediación (Puente/Cuello de botella): {cent['lider_intermediacion']}"
        )
        lineas.append("")

        # 3. Estado de los vértices
        lineas.append(f"3. ESTADO ACTUAL DE LOS VÉRTICES (Umbral k = {self.k})")
        lineas.append("-" * 80)
        for fila in g.tabla_grados():
            vid = str(fila["id"])
            n = g.nodos[vid]
            ev = ValidadorConsenso.evaluacion_formal(
                n.reportantes,
                self.k,
                self.tiene_ancestro_critico(vid),
            )
            w_str = "ε" if not n.control_estado.palabra else " · ".join(s.value for s in n.control_estado.palabra)
            lineas.append(
                f"  [{vid}] {n.nombre}\n"
                f"       Estado     : {n.estado.value} ({DESCRIPCION[n.estado]})\n"
                f"       Vecindades : N⁻={fila['vecindad_in']}, N⁺={fila['vecindad_out']}, N(v)={fila['vecindad_abierta']}\n"
                f"       Consenso   : {ev['formula_consenso']} con R_{vid} = {ev['conjunto_R']}\n"
                f"       Traza w∈Σ* : {w_str}"
            )
        lineas.append("")

        # 4. Bitácora
        lineas.append("4. BITÁCORA CRONOLÓGICA DE EVENTOS")
        lineas.append("-" * 80)
        for hora, etq, msg in self.bitacora_eventos:
            lineas.append(f"  [{hora}] ({etq.upper():7s}) {msg}")
        lineas.append("")
        return "\n".join(lineas)
