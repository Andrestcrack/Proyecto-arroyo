#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de Estructuras de Matemáticas Discretas para el Sistema de Monitoreo de Arroyos.
Alineado con el programa de Matemáticas Discretas de la Universidad del Norte
(Prof. Yesneri Zuleta Saldarriaga y MSc Iván Gómez):

  1. Fundamentos y Grados (Prof. Yesneri Zuleta & Unidad 3.1-3.2):
     - Clasificación formal (Simple, Multigrafo, Pseudografo, Digrafo, Ponderado, Bipartito).
     - Vecindad abierta N_G(v), vecindad cerrada N_G[v], vecindades dirigidas N_G⁻(v) y N_G⁺(v).
     - Valencia / Grados: grad(v), δ(G), Δ(G), grad⁻(v), grad⁺(v), δ⁻(G), Δ⁻(G), δ⁺(G), Δ⁺(G).
     - Teorema del Apretón de Manos (TAM: ∑grad(v) = 2m y ∑grad⁻ = ∑grad⁺ = m) y Corolario
       (número par de vértices de grado impar), regularidad (r-regular) e Inducción Matemática.
     - Subgrafos, subgrafo generador y subgrafo inducido G - v (vulnerabilidad por obstrucción).

  2. Representaciones, Conectividad, Euler/Hamilton, Planaridad y Árboles (Unidad 3.3-3.8):
     - Lista de adyacencia O(|V|+|E|), Matriz de adyacencia O(|V|²) y Matriz de incidencia O(|V|×|E|)
       (tanto no dirigida M_ie ∈ {0,1} como dirigida B_ie ∈ {-1,0,+1}).
     - Conectividad fuerte vs. débil y componentes conexas c(G).
     - Camino/circuito Euleriano (Teorema de Euler, 1736) y Hamiltoniano (Teoremas de Dirac y Ore).
     - Grafos planos: Fórmula de Euler (V - E + F = 2) y cotas de aristas (E ≤ 3V - 6 y E ≤ 2V - 4).
     - Árboles con raíz (raíz, padres, hijos, hojas, niveles, altura), trazas paso a paso de
       BFS (cola) y DFS (recursión / llamado desde), Árbol BFS vs. Árbol DFS, Dijkstra, Kruskal y Prim (MST).

  3. Análisis de Redes y Centralidad (Unidad 4.1-4.3):
     - Las 4 preguntas de modelación y Red Bipartita Ciudadanos–Nodos con su proyección.
     - Distancias geodésicas d(u, v) con BFS y diámetro del grafo.
     - Centralidad de grado C_D(v), cercanía C_C(v) (y variante armónica H(v)) e intermediación C_B(v).

  4. Función de Transición de Estados f: Q × Σ → Q y Consenso Booleano C(R, k).
"""

from __future__ import annotations

import heapq
from collections import defaultdict, deque
from enum import Enum
from typing import Dict, Iterable, Iterator, List, Optional, Set, Tuple


# ============================================================================
# 1. FUNCIÓN DISCRETA DE TRANSICIÓN DE ESTADOS DE ALERTA
# ============================================================================
class Estado(Enum):
    """Conjunto finito de estados Q de alerta hidráulica."""
    VERDE = "VERDE"        # Normal
    AMARILLO = "AMARILLO"  # Preventivo aguas abajo
    NARANJA = "NARANJA"    # Reporte único (sin consenso)
    ROJO = "ROJO"          # Crítico / desbordamiento


class Simbolo(Enum):
    """Conjunto finito de eventos de entrada Σ."""
    REPORTE = "REPORTE"       # llega un reporte ciudadano (sin consenso aún)
    CONSENSO = "CONSENSO"     # se alcanzó el umbral k (o crecida forzada)
    ALERTA = "ALERTA_ARRIBA"  # un nodo aguas arriba está en ROJO
    REINICIO = "REINICIO"     # vuelta a la normalidad


COLORES: Dict[Estado, str] = {
    Estado.VERDE: "#2e9e4f",
    Estado.AMARILLO: "#f1c40f",
    Estado.NARANJA: "#f28c28",
    Estado.ROJO: "#d62828",
}

DESCRIPCION: Dict[Estado, str] = {
    Estado.VERDE: "Normal",
    Estado.AMARILLO: "Preventivo aguas abajo",
    Estado.NARANJA: "Reporte único",
    Estado.ROJO: "Crítico / Desbordamiento",
}


class ControlEstados:
    """
    Función discreta de transición de estados de alerta f: Q × Σ → Q
    y su evaluación secuencial sobre secuencias de eventos w ∈ Σ*.
    """

    Q = frozenset(Estado)
    SIGMA = frozenset(Simbolo)
    Q0 = Estado.VERDE
    F = frozenset({Estado.ROJO})

    ORDEN_ESTADOS: Tuple[Estado, ...] = (
        Estado.VERDE,
        Estado.AMARILLO,
        Estado.NARANJA,
        Estado.ROJO,
    )
    ORDEN_SIMBOLOS: Tuple[Simbolo, ...] = (
        Simbolo.REPORTE,
        Simbolo.ALERTA,
        Simbolo.CONSENSO,
        Simbolo.REINICIO,
    )

    @staticmethod
    def _construir_delta() -> Dict[Tuple[Estado, Simbolo], Estado]:
        delta: Dict[Tuple[Estado, Simbolo], Estado] = {}
        for q in Estado:
            delta[(q, Simbolo.CONSENSO)] = Estado.ROJO
            delta[(q, Simbolo.REINICIO)] = Estado.VERDE
            delta[(q, Simbolo.REPORTE)] = Estado.ROJO if q is Estado.ROJO else Estado.NARANJA
            delta[(q, Simbolo.ALERTA)] = Estado.AMARILLO if q is Estado.VERDE else q
        assert len(delta) == len(ControlEstados.Q) * len(ControlEstados.SIGMA)
        return delta

    DELTA: Dict[Tuple[Estado, Simbolo], Estado] = {}

    def __init__(self) -> None:
        if not ControlEstados.DELTA:
            ControlEstados.DELTA = ControlEstados._construir_delta()
        self.estado: Estado = ControlEstados.Q0
        self.palabra: List[Simbolo] = []
        self.historial: List[Tuple[Estado, Simbolo, Estado]] = []

    @property
    def ultima_transicion(self) -> Optional[Tuple[Estado, Simbolo, Estado]]:
        return self.historial[-1] if self.historial else None

    def es_critico(self, estado: Optional[Estado] = None) -> bool:
        q = self.estado if estado is None else estado
        return q in ControlEstados.F

    def procesar(self, simbolo: Simbolo) -> Tuple[Estado, Estado]:
        anterior = self.estado
        nuevo = ControlEstados.DELTA[(anterior, simbolo)]
        self.estado = nuevo
        self.palabra.append(simbolo)
        self.historial.append((anterior, simbolo, nuevo))
        return anterior, nuevo

    def procesar_palabra(self, palabra: Iterable[Simbolo]) -> List[Tuple[Estado, Simbolo, Estado]]:
        pasos: List[Tuple[Estado, Simbolo, Estado]] = []
        for s in palabra:
            ant, nue = self.procesar(s)
            pasos.append((ant, s, nue))
        return pasos

    def reiniciar(self) -> None:
        self.estado = ControlEstados.Q0
        self.palabra.clear()
        self.historial.clear()

    @classmethod
    def tabla_transicion_formal(
        cls,
    ) -> Tuple[List[Estado], List[Simbolo], Dict[Tuple[Estado, Simbolo], Estado]]:
        if not cls.DELTA:
            cls.DELTA = cls._construir_delta()
        return list(cls.ORDEN_ESTADOS), list(cls.ORDEN_SIMBOLOS), dict(cls.DELTA)


# ============================================================================
# 2. LÓGICA BOOLEANA: UMBRAL DE CONSENSO
# ============================================================================
class ValidadorConsenso:
    """Predicado booleano C(R, k) = (|R| ≥ k) sobre el conjunto R de reportantes."""

    @staticmethod
    def consenso(reportantes: Set[str], k: int) -> bool:
        return len(reportantes) >= k

    @staticmethod
    def evaluacion_formal(
        reportantes: Set[str],
        k: int,
        alerta_aguas_arriba: bool = False,
    ) -> Dict[str, object]:
        n = len(reportantes)
        p = n >= 1
        q = n >= k
        r = bool(alerta_aguas_arriba)
        conjunto_str = "∅" if n == 0 else "{" + ", ".join(sorted(reportantes)) + "}"
        return {
            "cardinalidad": n,
            "umbral_k": k,
            "conjunto_R": conjunto_str,
            "p_hay_reporte": p,
            "q_consenso": q,
            "r_alerta_arriba": r,
            "emergencia_critica": q,
            "alerta_naranja": p and not q,
            "alerta_preventiva": (not p) and r,
            "formula_consenso": f"C(R, {k}) ≡ (|R| ≥ {k}) ≡ ({n} ≥ {k}) ≡ {'V' if q else 'F'}",
        }


# ============================================================================
# 3. GRAFO DE LA CUENCA: TEORÍA DE GRAFOS, ÁRBOLES Y ANÁLISIS DE REDES
# ============================================================================
class Nodo:
    """Vértice v ∈ V con su control discreto de estados y su conjunto de reportantes R_v."""

    def __init__(self, id_: str, nombre: str, corto: str, fuente: str) -> None:
        self.id = id_
        self.nombre = nombre
        self.corto = corto
        self.fuente = fuente
        self.control_estado = ControlEstados()
        self.reportantes: Set[str] = set()

    @property
    def estado(self) -> Estado:
        return self.control_estado.estado

    def reiniciar(self) -> None:
        self.control_estado.reiniciar()
        self.reportantes.clear()


class CuencaDAG:
    """
    G = (V, E) dirigido, acíclico y ponderado.
    Permite analizar tanto el digrafo dirigido como su grafo subyacente no dirigido,
    cubriendo todas las unidades del curso de Matemáticas Discretas.
    """

    def __init__(self) -> None:
        self.nodos: Dict[str, Nodo] = {}
        self.sucesores: Dict[str, List[str]] = defaultdict(list)
        self.predecesores: Dict[str, List[str]] = defaultdict(list)
        # Pesos w(u, v) = distancia aproximada de escorrentía en metros
        self.pesos: Dict[Tuple[str, str], int] = {}

    def agregar_nodo(self, id_: str, nombre: str, corto: str, fuente: str) -> None:
        self.nodos[id_] = Nodo(id_, nombre, corto, fuente)

    def agregar_arista(self, u: str, v: str, peso: int = 1) -> None:
        if u not in self.nodos or v not in self.nodos:
            raise KeyError(f"Arista ({u}, {v}) referencia un nodo inexistente.")
        if v not in self.sucesores[u]:
            self.sucesores[u].append(v)
            self.predecesores[v].append(u)
        self.pesos[(u, v)] = peso

    @property
    def ids_ordenados(self) -> List[str]:
        return list(self.nodos.keys())

    @property
    def aristas(self) -> List[Tuple[str, str]]:
        return [(u, v) for u in self.nodos for v in self.sucesores[u]]

    def peso(self, u: str, v: str) -> int:
        if (u, v) in self.pesos:
            return self.pesos[(u, v)]
        if (v, u) in self.pesos:
            return self.pesos[(v, u)]
        return 1

    # ------------------------------------------------------------------------
    # 3.1 y Presentaciones Prof. Yesneri Zuleta: Vecindades y Grados (Valencia)
    # ------------------------------------------------------------------------
    def vecindad_entrada(self, v: str) -> List[str]:
        """N_G⁻(v) = {u ∈ V | (u, v) ∈ E}."""
        return list(self.predecesores[v])

    def vecindad_salida(self, v: str) -> List[str]:
        """N_G⁺(v) = {u ∈ V | (v, u) ∈ E}."""
        return list(self.sucesores[v])

    def vecindad_abierta(self, v: str) -> List[str]:
        """N_G(v) = {u ∈ V | {u, v} ∈ E_sub} en el grafo no dirigido subyacente."""
        vecinos = set(self.predecesores[v]) | set(self.sucesores[v])
        return [u for u in self.ids_ordenados if u in vecinos]

    def vecindad_cerrada(self, v: str) -> List[str]:
        """N_G[v] = N_G(v) ∪ {v}."""
        vecinos = set(self.vecindad_abierta(v)) | {v}
        return [u for u in self.ids_ordenados if u in vecinos]

    def grado_entrada(self, v: str) -> int:
        """grad⁻(v) = |N_G⁻(v)|."""
        return len(self.predecesores[v])

    def grado_salida(self, v: str) -> int:
        """grad⁺(v) = |N_G⁺(v)|."""
        return len(self.sucesores[v])

    def grado_no_dirigido(self, v: str) -> int:
        """grad(v) = |N_G(v)| en el grafo simple subyacente."""
        return len(self.vecindad_abierta(v))

    def extremos_grados(self) -> Dict[str, object]:
        """
        Calcula los invariantes de grado de las diapositivas de la Prof. Yesneri Zuleta:
          - No dirigido: δ(G), Δ(G), vértices aislados, vértices de grado impar, ¿es r-regular?
          - Digrafo: δ⁻(G), Δ⁻(G), δ⁺(G), Δ⁺(G).
        """
        vs = self.ids_ordenados
        grados = {v: self.grado_no_dirigido(v) for v in vs}
        g_in = {v: self.grado_entrada(v) for v in vs}
        g_out = {v: self.grado_salida(v) for v in vs}

        delta_min = min(grados.values()) if vs else 0
        delta_max = max(grados.values()) if vs else 0
        impares = [v for v in vs if grados[v] % 2 == 1]
        pares = [v for v in vs if grados[v] % 2 == 0]
        aislados = [v for v in vs if grados[v] == 0]

        return {
            "delta_min": delta_min,
            "delta_max": delta_max,
            "delta_in_min": min(g_in.values()) if vs else 0,
            "delta_in_max": max(g_in.values()) if vs else 0,
            "delta_out_min": min(g_out.values()) if vs else 0,
            "delta_out_max": max(g_out.values()) if vs else 0,
            "vertices_impares": impares,
            "vertices_pares": pares,
            "vertices_aislados": aislados,
            "es_regular": delta_min == delta_max,
            "cumple_cota_grado": all(0 <= grados[v] <= len(vs) - 1 for v in vs),
            "suma_grados_no_dirigido": sum(grados.values()),
            "dos_m": 2 * len(self.aristas),
        }

    def cabeceras(self) -> List[str]:
        return [v for v in self.nodos if not self.predecesores[v]]

    def sumideros(self) -> List[str]:
        return [v for v in self.nodos if not self.sucesores[v]]

    def confluencias(self) -> List[str]:
        return [v for v in self.nodos if len(self.predecesores[v]) >= 2]

    def bifurcaciones(self) -> List[str]:
        return [v for v in self.nodos if len(self.sucesores[v]) >= 2]

    def clasificar_nodo(self, v: str) -> str:
        ge = self.grado_entrada(v)
        gs = self.grado_salida(v)
        roles: List[str] = []
        if ge == 0:
            roles.append("Cabecera (fuente)")
        if gs == 0:
            roles.append("Sumidero")
        if ge >= 2:
            roles.append("Confluencia")
        if gs >= 2:
            roles.append("Bifurcación")
        if not roles:
            roles.append("Tramo intermedio")
        return " / ".join(roles)

    def tabla_grados(self) -> List[Dict[str, object]]:
        niveles = self.niveles_topologicos()
        filas: List[Dict[str, object]] = []
        for v, nodo in self.nodos.items():
            ge = self.grado_entrada(v)
            gs = self.grado_salida(v)
            g_sub = self.grado_no_dirigido(v)
            filas.append({
                "id": v,
                "corto": nodo.corto,
                "deg_in": ge,
                "deg_out": gs,
                "deg_total": g_sub,
                "vecindad_in": self.vecindad_entrada(v),
                "vecindad_out": self.vecindad_salida(v),
                "vecindad_abierta": self.vecindad_abierta(v),
                "vecindad_cerrada": self.vecindad_cerrada(v),
                "nivel": niveles.get(v, 0),
                "rol": self.clasificar_nodo(v),
            })
        return filas

    def verificar_lema_apreton_manos(self) -> Tuple[int, int, int, bool]:
        suma_in = sum(self.grado_entrada(v) for v in self.nodos)
        suma_out = sum(self.grado_salida(v) for v in self.nodos)
        num_e = len(self.aristas)
        return suma_in, suma_out, num_e, (suma_in == suma_out == num_e)

    # ------------------------------------------------------------------------
    # 3.2 Bipartición y Subgrafo Inducido G - v
    # ------------------------------------------------------------------------
    def analisis_bipartito(self) -> Dict[str, object]:
        """
        Determina mediante 2-coloración (BFS) si el grafo subyacente es bipartito:
        V = V1 ∪ V2 con V1 ∩ V2 = ∅. Un grafo es bipartito ⇔ no tiene ciclos de longitud impar.
        """
        color: Dict[str, int] = {}
        es_bip = True
        for inicio in self.ids_ordenados:
            if inicio in color:
                continue
            color[inicio] = 0
            cola: deque[str] = deque([inicio])
            while cola:
                u = cola.popleft()
                for w in self.vecindad_abierta(u):
                    if w not in color:
                        color[w] = 1 - color[u]
                        cola.append(w)
                    elif color[w] == color[u]:
                        es_bip = False
        v1 = [v for v in self.ids_ordenados if color.get(v) == 0]
        v2 = [v for v in self.ids_ordenados if color.get(v) == 1]
        return {
            "es_bipartito": es_bip,
            "V1": v1,
            "V2": v2,
            "justificacion": (
                "No contiene ciclos de longitud impar (el único ciclo subyacente "
                "N4-N5-N7-N6-N4 tiene longitud 4, que es par)."
                if es_bip
                else "Contiene al menos un ciclo de longitud impar."
            ),
        }

    def subgrafo_inducido_sin_vertice(self, v_excluir: str) -> Dict[str, object]:
        """
        Analiza el subgrafo G - v inducido por V - {v} (Prof. Yesneri Zuleta, diap. 4).
        Calcula las componentes conexas de G - v y qué nodos pierden ruta hacia el sumidero.
        """
        restantes = [v for v in self.ids_ordenados if v != v_excluir]
        aristas_rest = [
            (u, w) for u, w in self.aristas if u != v_excluir and w != v_excluir
        ]
        # Componentes conexas en el grafo subyacente de G - v
        visitados: Set[str] = set()
        componentes: List[List[str]] = []
        adj: Dict[str, List[str]] = {u: [] for u in restantes}
        for u, w in aristas_rest:
            adj[u].append(w)
            adj[w].append(u)

        for u in restantes:
            if u not in visitados:
                comp: List[str] = []
                cola: deque[str] = deque([u])
                visitados.add(u)
                while cola:
                    act = cola.popleft()
                    comp.append(act)
                    for vec in adj[act]:
                        if vec not in visitados:
                            visitados.add(vec)
                            cola.append(vec)
                componentes.append(comp)

        # Nodos que aún pueden llegar al sumidero N9 en el digrafo G - v
        sumidero = self.sumideros()[0] if self.sumideros() else "N9"
        llegan_a_sumidero: Set[str] = set()
        if sumidero in restantes:
            llegan_a_sumidero.add(sumidero)
            inv_adj: Dict[str, List[str]] = {u: [] for u in restantes}
            for u, w in aristas_rest:
                inv_adj[w].append(u)
            cola_s: deque[str] = deque([sumidero])
            while cola_s:
                act = cola_s.popleft()
                for pred in inv_adj[act]:
                    if pred not in llegan_a_sumidero:
                        llegan_a_sumidero.add(pred)
                        cola_s.append(pred)

        aislados_sumidero = [u for u in restantes if u not in llegan_a_sumidero]
        return {
            "vertice_removido": v_excluir,
            "vertices_restantes": restantes,
            "num_aristas_restantes": len(aristas_rest),
            "aristas_restantes": aristas_rest,
            "num_componentes": len(componentes),
            "componentes": componentes,
            "es_punto_articulacion": len(componentes) > 1,
            "desconectados_del_sumidero": aislados_sumidero,
        }

    # ------------------------------------------------------------------------
    # 3.4, 3.5 y 3.6: Conectividad, Euler, Hamilton y Grafos Planos
    # ------------------------------------------------------------------------
    def analisis_conectividad(self) -> Dict[str, object]:
        """
        Analiza conectividad débil y fuerte del digrafo (Unidad 3.4, diap. 20-21).
        """
        vs = self.ids_ordenados
        _, w = self.clausura_transitiva_warshall()
        n = len(vs)
        fuertemente_conexo = all(
            (i == j or w[i][j] == 1) for i in range(n) for j in range(n)
        )
        # Componentes conexas ignorando dirección
        visitados: Set[str] = set()
        componentes: List[List[str]] = []
        for u in vs:
            if u not in visitados:
                comp: List[str] = []
                cola: deque[str] = deque([u])
                visitados.add(u)
                while cola:
                    act = cola.popleft()
                    comp.append(act)
                    for vec in self.vecindad_abierta(act):
                        if vec not in visitados:
                            visitados.add(vec)
                            cola.append(vec)
                componentes.append(comp)
        return {
            "fuertemente_conexo": fuertemente_conexo,
            "debilmente_conexo": len(componentes) == 1,
            "num_componentes": len(componentes),
            "componentes": componentes,
        }

    def analisis_euler_hamilton_plano(self) -> Dict[str, object]:
        """
        Evalúa las propiedades de las secciones 3.5 (Euleriano, Hamiltoniano con
        Teoremas de Dirac y Ore) y 3.6 (Grafos Planos, Fórmula de Euler V-E+F=2 y cotas).
        """
        vs = self.ids_ordenados
        n = len(vs)
        m = len(self.aristas)
        ext = self.extremos_grados()
        impares = list(ext["vertices_impares"])  # type: ignore[arg-type]
        num_impares = len(impares)

        # Teorema de Euler (1736) sobre el grafo subyacente conexo
        tiene_circuito_euler = num_impares == 0
        tiene_camino_euler = num_impares == 2

        # Condiciones suficientes de Hamilton (Dirac 1952 y Ore 1960)
        grados = {v: self.grado_no_dirigido(v) for v in vs}
        umbral_dirac = n / 2.0
        cumple_dirac = n >= 3 and all(grados[v] >= umbral_dirac for v in vs)

        pares_no_ady: List[Tuple[str, str, int]] = []
        for i in range(n):
            for j in range(i + 1, n):
                u, v = vs[i], vs[j]
                if v not in self.vecindad_abierta(u):
                    pares_no_ady.append((u, v, grados[u] + grados[v]))
        cumple_ore = n >= 3 and all(suma >= n for _, _, suma in pares_no_ady)
        min_ore = min((s for _, _, s in pares_no_ady), default=0)

        # Grafos planos (Sección 3.6)
        bip = self.analisis_bipartito()
        es_bip = bool(bip["es_bipartito"])
        cota_general = 3 * n - 6
        cota_bipartita = 2 * n - 4
        # Por Fórmula de Euler en grafo plano conexo: V - E + F = 2 => F = 2 - V + E
        caras_euler = 2 - n + m

        return {
            "n": n,
            "m": m,
            "impares": impares,
            "num_impares": num_impares,
            "tiene_circuito_euler": tiene_circuito_euler,
            "tiene_camino_euler": tiene_camino_euler,
            "umbral_dirac": umbral_dirac,
            "cumple_dirac": cumple_dirac,
            "cumple_ore": cumple_ore,
            "min_suma_ore": min_ore,
            "cota_plana_general": cota_general,
            "cota_plana_bipartita": cota_bipartita,
            "cumple_cota_general": m <= cota_general,
            "cumple_cota_bipartita": m <= cota_bipartita if es_bip else True,
            "caras_F": caras_euler,
            "verifica_euler_plano": (n - m + caras_euler == 2),
        }

    # ------------------------------------------------------------------------
    # 3.7 y 3.8: Orden Topológico, Trazas BFS y DFS, Árboles de Expansión y MST
    # ------------------------------------------------------------------------
    def orden_topologico(self) -> List[str]:
        grado = {v: len(self.predecesores[v]) for v in self.nodos}
        cola = deque(v for v, g in grado.items() if g == 0)
        orden: List[str] = []
        while cola:
            u = cola.popleft()
            orden.append(u)
            for w in self.sucesores[u]:
                grado[w] -= 1
                if grado[w] == 0:
                    cola.append(w)
        if len(orden) != len(self.nodos):
            raise ValueError("El grafo contiene un ciclo: no es un DAG.")
        return orden

    def niveles_topologicos(self) -> Dict[str, int]:
        niveles: Dict[str, int] = {v: 0 for v in self.nodos}
        for u in self.orden_topologico():
            for w in self.sucesores[u]:
                if niveles[u] + 1 > niveles[w]:
                    niveles[w] = niveles[u] + 1
        return niveles

    def descendientes_bfs(self, origen: str) -> Iterator[Tuple[str, int]]:
        visitados: Set[str] = {origen}
        cola: deque[Tuple[str, int]] = deque([(origen, 0)])
        while cola:
            u, d = cola.popleft()
            for w in self.sucesores[u]:
                if w not in visitados:
                    visitados.add(w)
                    cola.append((w, d + 1))
                    yield w, d + 1

    def capas_bfs(self, origen: str) -> List[Tuple[int, List[str]]]:
        por_distancia: Dict[int, List[str]] = defaultdict(list)
        for v, dist in self.descendientes_bfs(origen):
            por_distancia[dist].append(v)
        return [(d, por_distancia[d]) for d in sorted(por_distancia)]

    def traza_bfs_detallada(
        self,
        origen: str,
        dirigido: bool = True,
    ) -> Dict[str, object]:
        """
        Genera la tabla paso a paso de BFS exacta a la diapositiva 47 de la Unidad 3:
          Columnas: (Paso, Quién llama, Se entera nuevo, Cola)
        Además devuelve el Árbol BFS (aristas usadas) y las aristas descartadas.
        """
        visitados: Set[str] = {origen}
        cola: deque[str] = deque([origen])
        pasos: List[Dict[str, object]] = []
        orden_visita: List[str] = [origen]
        aristas_arbol: List[Tuple[str, str]] = []
        nivel: Dict[str, int] = {origen: 0}
        padres: Dict[str, Optional[str]] = {origen: None}
        paso_num = 0

        while cola:
            paso_num += 1
            actual = cola.popleft()
            vecinos = (
                sorted(self.sucesores[actual])
                if dirigido
                else sorted(self.vecindad_abierta(actual))
            )
            nuevos: List[str] = []
            for w in vecinos:
                if w not in visitados:
                    visitados.add(w)
                    cola.append(w)
                    nuevos.append(w)
                    orden_visita.append(w)
                    aristas_arbol.append((actual, w))
                    nivel[w] = nivel[actual] + 1
                    padres[w] = actual
            pasos.append({
                "paso": paso_num,
                "quien_llama": actual,
                "se_entera_nuevo": ", ".join(nuevos) if nuevos else "—",
                "cola": "[" + ", ".join(cola) + "]",
            })

        hojas = [
            v for v in orden_visita
            if not any(p == v for p in padres.values())
        ]
        altura = max(nivel.values()) if nivel else 0
        return {
            "origen": origen,
            "pasos": pasos,
            "orden_visita": orden_visita,
            "aristas_arbol": aristas_arbol,
            "niveles": nivel,
            "padres": padres,
            "hojas": hojas,
            "altura": altura,
        }

    def traza_dfs_detallada(
        self,
        origen: str,
        dirigido: bool = True,
    ) -> Dict[str, object]:
        """
        Genera la tabla paso a paso de DFS exacta a la diapositiva 48 de la Unidad 3:
          Columnas: (Paso, Visita, Llamado desde)
        Además devuelve el Árbol DFS (aristas usadas) para compararlo con el Árbol BFS.
        """
        visitados: Set[str] = set()
        pasos: List[Dict[str, object]] = []
        orden_visita: List[str] = []
        aristas_arbol: List[Tuple[str, str]] = []

        def _dfs(u: str, desde: str) -> None:
            visitados.add(u)
            orden_visita.append(u)
            pasos.append({
                "paso": len(pasos) + 1,
                "visita": u,
                "llamado_desde": desde,
            })
            vecinos = (
                sorted(self.sucesores[u])
                if dirigido
                else sorted(self.vecindad_abierta(u))
            )
            for w in vecinos:
                if w not in visitados:
                    aristas_arbol.append((u, w))
                    _dfs(w, u)

        _dfs(origen, "(inicio)")
        return {
            "origen": origen,
            "pasos": pasos,
            "orden_visita": orden_visita,
            "aristas_arbol": aristas_arbol,
        }

    def dijkstra(self, origen: str, dirigido: bool = True) -> Dict[str, object]:
        """
        Algoritmo de Dijkstra para caminos más cortos en el grafo ponderado (w(u,v) en metros).
        """
        vs = self.ids_ordenados
        dist: Dict[str, float] = {v: float("inf") for v in vs}
        prev: Dict[str, Optional[str]] = {v: None for v in vs}
        dist[origen] = 0.0
        pq: List[Tuple[float, str]] = [(0.0, origen)]

        while pq:
            d_u, u = heapq.heappop(pq)
            if d_u > dist[u]:
                continue
            vecinos = self.sucesores[u] if dirigido else self.vecindad_abierta(u)
            for w in vecinos:
                peso_uw = float(self.peso(u, w))
                if dist[u] + peso_uw < dist[w]:
                    dist[w] = dist[u] + peso_uw
                    prev[w] = u
                    heapq.heappush(pq, (dist[w], w))

        caminos: Dict[str, List[str]] = {}
        for v in vs:
            if dist[v] < float("inf"):
                cam: List[str] = []
                act: Optional[str] = v
                while act is not None:
                    cam.append(act)
                    act = prev[act]
                cam.reverse()
                caminos[v] = cam
        return {"distancias": dist, "predecesores": prev, "caminos": caminos}

    def mst_kruskal_prim(self) -> Dict[str, object]:
        """
        Construye el Árbol de Expansión Mínimo (MST) sobre el grafo subyacente ponderado
        usando tanto el algoritmo de Kruskal como el de Prim (Sección 3.8).
        """
        vs = self.ids_ordenados
        aristas_pond = sorted(
            [(self.peso(u, v), u, v) for u, v in self.aristas],
            key=lambda x: (x[0], x[1], x[2]),
        )

        # 1. Algoritmo de Kruskal (Union-Find)
        padre = {v: v for v in vs}

        def _find(x: str) -> str:
            while padre[x] != x:
                padre[x] = padre[padre[x]]
                x = padre[x]
            return x

        mst_kruskal: List[Tuple[str, str, int]] = []
        descartadas_kruskal: List[Tuple[str, str, int]] = []
        for w, u, v in aristas_pond:
            ru, rv = _find(u), _find(v)
            if ru != rv:
                padre[ru] = rv
                mst_kruskal.append((u, v, w))
            else:
                descartadas_kruskal.append((u, v, w))

        # 2. Algoritmo de Prim (partiendo de N1)
        inicio = vs[0]
        en_mst: Set[str] = {inicio}
        mst_prim: List[Tuple[str, str, int]] = []
        while len(en_mst) < len(vs):
            mejor: Optional[Tuple[int, str, str]] = None
            for u, v in self.aristas:
                if (u in en_mst) ^ (v in en_mst):
                    w = self.peso(u, v)
                    cand = (w, u, v)
                    if mejor is None or cand < mejor:
                        mejor = cand
            if mejor is None:
                break
            w, u, v = mejor
            en_mst.append if False else None
            en_mst.add(u)
            en_mst.add(v)
            mst_prim.append((u, v, w))

        costo_total = sum(w for _, _, w in mst_kruskal)
        return {
            "mst_kruskal": mst_kruskal,
            "descartadas_kruskal": descartadas_kruskal,
            "mst_prim": mst_prim,
            "costo_total": costo_total,
            "num_aristas_mst": len(mst_kruskal),
        }

    # ------------------------------------------------------------------------
    # 4. UNIDAD 4: ANÁLISIS DE REDES – DISTANCIAS BFS Y CENTRALIDADES C_D, C_C, C_B
    # ------------------------------------------------------------------------
    def distancias_bfs_pares(self, dirigido: bool = False) -> Dict[Tuple[str, str], Optional[int]]:
        """
        Calcula la distancia geodésica d(u, v) en número de aristas mediante BFS
        para todo par de vértices (Unidad 4.3, diap. 8-9).
        Si no existe camino, d(u, v) = None (representa ∞).
        """
        vs = self.ids_ordenados
        dist: Dict[Tuple[str, str], Optional[int]] = {
            (u, v): None for u in vs for v in vs
        }
        for origen in vs:
            dist[(origen, origen)] = 0
            cola: deque[str] = deque([origen])
            while cola:
                u = cola.popleft()
                d_u = dist[(origen, u)]
                assert d_u is not None
                vecinos = self.sucesores[u] if dirigido else self.vecindad_abierta(u)
                for w in vecinos:
                    if dist[(origen, w)] is None:
                        dist[(origen, w)] = d_u + 1
                        cola.append(w)
        return dist

    def caminos_mas_cortos_entre(
        self,
        s: str,
        t: str,
        dirigido: bool = False,
    ) -> List[List[str]]:
        """
        Devuelve todos los caminos geodésicos (más cortos en número de aristas) entre s y t.
        Su cardinalidad es σ_st (Unidad 4.3, diap. 16-17).
        """
        if s == t:
            return [[s]]
        dist_map = self.distancias_bfs_pares(dirigido=dirigido)
        d_obj = dist_map[(s, t)]
        if d_obj is None:
            return []

        resultados: List[List[str]] = []

        def _backtrack(actual: str, camino: List[str]) -> None:
            if len(camino) - 1 == d_obj:
                if actual == t:
                    resultados.append(list(camino))
                return
            d_act = len(camino) - 1
            vecinos = self.sucesores[actual] if dirigido else self.vecindad_abierta(actual)
            for sig in vecinos:
                if sig not in camino and dist_map[(s, sig)] == d_act + 1:
                    camino.append(sig)
                    _backtrack(sig, camino)
                    camino.pop()

        _backtrack(s, [s])
        return resultados

    def analisis_centralidades_unidad4(self) -> Dict[str, object]:
        """
        Calcula las tres medidas de centralidad de la Unidad 4 (MSc Iván Gómez):
          1. Centralidad de grado:
             - No dirigido: C_D(v) = deg(v) / (n - 1)
             - Dirigido: C_D⁻(v) = grad⁻(v) / (n - 1) y C_D⁺(v) = grad⁺(v) / (n - 1)
          2. Centralidad de cercanía:
             - En grafo subyacente conexo: C_C(v) = (n - 1) / ∑_{u≠v} d(v, u)
             - En digrafo (no fuertemente conexo, diap. 14): Variante armónica
               H(v) = (1 / (n - 1)) ∑_{u≠v} (1 / d_dir(v, u)) con 1/∞ = 0.
          3. Centralidad de intermediación (Betweenness):
             - C_B(v) = ∑_{s<t, s,t≠v} (σ_st(v) / σ_st)
             - Normalizada dividiendo entre (n - 1)(n - 2) / 2.
        """
        vs = self.ids_ordenados
        n = len(vs)
        denom_grado = max(n - 1, 1)
        denom_cb_nodir = max((n - 1) * (n - 2) / 2.0, 1.0)
        denom_cb_dir = max(float((n - 1) * (n - 2)), 1.0)

        dist_nodir = self.distancias_bfs_pares(dirigido=False)
        dist_dir = self.distancias_bfs_pares(dirigido=True)

        # Diámetro del grafo subyacente conexo
        diametro_nodir = max(
            (d for d in dist_nodir.values() if d is not None),
            default=0,
        )
        diametro_dir = max(
            (d for d in dist_dir.values() if d is not None),
            default=0,
        )

        # Precalcular todos los caminos geodésicos para intermediación
        caminos_nodir: Dict[Tuple[str, str], List[List[str]]] = {}
        for i in range(n):
            for j in range(i + 1, n):
                s, t = vs[i], vs[j]
                caminos_nodir[(s, t)] = self.caminos_mas_cortos_entre(s, t, dirigido=False)

        caminos_dir: Dict[Tuple[str, str], List[List[str]]] = {}
        for s in vs:
            for t in vs:
                if s != t:
                    cams = self.caminos_mas_cortos_entre(s, t, dirigido=True)
                    if cams:
                        caminos_dir[(s, t)] = cams

        tabla: List[Dict[str, object]] = []
        for v in vs:
            # 1. Grado
            deg_sub = self.grado_no_dirigido(v)
            cd = deg_sub / denom_grado
            cd_in = self.grado_entrada(v) / denom_grado
            cd_out = self.grado_salida(v) / denom_grado

            # 2. Cercanía (no dirigido conexo) y Cercanía Armónica (digrafo)
            suma_dist = sum(
                dist_nodir[(v, u)] or 0 for u in vs if u != v
            )
            cc = (n - 1) / suma_dist if suma_dist > 0 else 0.0

            suma_arm_dir = sum(
                (1.0 / dist_dir[(v, u)])  # type: ignore[operator]
                for u in vs
                if u != v and dist_dir[(v, u)] is not None and dist_dir[(v, u)] > 0  # type: ignore[operator]
            )
            h_dir = suma_arm_dir / denom_grado

            # 3. Intermediación no dirigida C_B(v)
            cb_nodir = 0.0
            for (s, t), lista_c in caminos_nodir.items():
                if s == v or t == v or not lista_c:
                    continue
                sigma_st = len(lista_c)
                sigma_st_v = sum(1 for c in lista_c if v in c[1:-1])
                cb_nodir += sigma_st_v / sigma_st

            # Intermediación dirigida C_B_dir(v)
            cb_dir = 0.0
            for (s, t), lista_c in caminos_dir.items():
                if s == v or t == v or not lista_c:
                    continue
                sigma_st = len(lista_c)
                sigma_st_v = sum(1 for c in lista_c if v in c[1:-1])
                cb_dir += sigma_st_v / sigma_st

            tabla.append({
                "id": v,
                "corto": self.nodos[v].corto,
                "deg": deg_sub,
                "cd": cd,
                "cd_in": cd_in,
                "cd_out": cd_out,
                "suma_dist": suma_dist,
                "cc": cc,
                "h_dir": h_dir,
                "cb": cb_nodir,
                "cb_norm": cb_nodir / denom_cb_nodir,
                "cb_dir": cb_dir,
                "cb_dir_norm": cb_dir / denom_cb_dir,
            })

        lider_cd = max(tabla, key=lambda x: float(x["cd"]))["id"]  # type: ignore[arg-type]
        lider_cc = max(tabla, key=lambda x: float(x["cc"]))["id"]  # type: ignore[arg-type]
        lider_cb = max(tabla, key=lambda x: float(x["cb"]))["id"]  # type: ignore[arg-type]

        return {
            "tabla": tabla,
            "diametro_no_dirigido": diametro_nodir,
            "diametro_dirigido": diametro_dir,
            "lider_grado": lider_cd,
            "lider_cercania": lider_cc,
            "lider_intermediacion": lider_cb,
            "distancias_no_dirigidas": dist_nodir,
            "distancias_dirigidas": dist_dir,
        }

    # ------------------------------------------------------------------------
    # Matrices, Warshall y Caminos
    # ------------------------------------------------------------------------
    def ancestros(self, destino: str) -> Set[str]:
        visitados: Set[str] = set()
        cola: deque[str] = deque(self.predecesores[destino])
        while cola:
            u = cola.popleft()
            if u not in visitados:
                visitados.add(u)
                cola.extend(self.predecesores[u])
        return visitados

    def matriz_adyacencia(self, dirigido: bool = True) -> Tuple[List[str], List[List[int]]]:
        orden = self.ids_ordenados
        idx = {v: i for i, v in enumerate(orden)}
        n = len(orden)
        matriz = [[0] * n for _ in range(n)]
        for u, v in self.aristas:
            matriz[idx[u]][idx[v]] = 1
            if not dirigido:
                matriz[idx[v]][idx[u]] = 1
        return orden, matriz

    def matriz_incidencia(
        self,
        dirigido: bool = True,
    ) -> Tuple[List[str], List[Tuple[str, str]], List[List[int]]]:
        """
        Si dirigido=True: B[i][e] = -1 (origen), +1 (destino), 0 (otro). Cada columna suma 0.
        Si dirigido=False: M[i][e] = 1 si v_i es extremo de e, 0 si no (Unidad 3.3, diap. 15).
                           Cada columna suma 2 y cada fila suma deg(v_i).
        """
        orden_v = self.ids_ordenados
        aristas = self.aristas
        idx = {v: i for i, v in enumerate(orden_v)}
        matriz = [[0] * len(aristas) for _ in range(len(orden_v))]
        for j, (u, v) in enumerate(aristas):
            matriz[idx[u]][j] = -1 if dirigido else 1
            matriz[idx[v]][j] = 1
        return orden_v, aristas, matriz

    def clausura_transitiva_warshall(self) -> Tuple[List[str], List[List[int]]]:
        orden, base = self.matriz_adyacencia(dirigido=True)
        n = len(orden)
        w = [fila[:] for fila in base]
        for k in range(n):
            for i in range(n):
                if w[i][k]:
                    for j in range(n):
                        if w[k][j]:
                            w[i][j] = 1
        return orden, w

    def propiedades_relacion_alcanzabilidad(self) -> Dict[str, object]:
        orden, w = self.clausura_transitiva_warshall()
        n = len(orden)
        irreflexiva = all(w[i][i] == 0 for i in range(n))
        asimetrica = all(
            not (w[i][j] == 1 and w[j][i] == 1)
            for i in range(n)
            for j in range(n)
        )
        transitiva = all(
            not (w[i][k] == 1 and w[k][j] == 1 and w[i][j] == 0)
            for i in range(n)
            for k in range(n)
            for j in range(n)
        )
        pares = [
            (orden[i], orden[j])
            for i in range(n)
            for j in range(n)
            if w[i][j] == 1
        ]
        return {
            "irreflexiva": irreflexiva,
            "asimetrica": asimetrica,
            "transitiva": transitiva,
            "es_orden_parcial_estricto": irreflexiva and asimetrica and transitiva,
            "num_pares_alcanzables": len(pares),
            "pares": pares,
        }

    def todos_los_caminos(self, origen: str, destino: str) -> List[List[str]]:
        if origen not in self.nodos or destino not in self.nodos:
            return []
        resultados: List[List[str]] = []

        def _dfs(actual: str, camino: List[str]) -> None:
            if actual == destino:
                resultados.append(list(camino))
                return
            for sig in self.sucesores[actual]:
                if sig not in camino:
                    camino.append(sig)
                    _dfs(sig, camino)
                    camino.pop()

        _dfs(origen, [origen])
        return resultados

    def camino_critico(self) -> Tuple[int, List[str]]:
        orden = self.orden_topologico()
        if not orden:
            return 0, []
        dist: Dict[str, int] = {v: 0 for v in orden}
        prev: Dict[str, Optional[str]] = {v: None for v in orden}
        for u in orden:
            for w in self.sucesores[u]:
                if dist[u] + 1 > dist[w]:
                    dist[w] = dist[u] + 1
                    prev[w] = u
        fin = max(orden, key=lambda v: dist[v])
        camino: List[str] = []
        actual: Optional[str] = fin
        while actual is not None:
            camino.append(actual)
            actual = prev[actual]
        camino.reverse()
        return dist[fin], camino

    # ------------------------------------------------------------------------
    # 5. NAVEGACIÓN CIUDADANA ("GOOGLE MAPS DE ARROYOS"): SUBGRAFO SEGURO Y DIJKSTRA
    # ------------------------------------------------------------------------
    def corredores_viales_extra(self) -> List[Tuple[str, str, int, str]]:
        """
        Conexiones viales/peatonales de cota alta entre las arterias del sector Uninorte
        (no forman parte del cauce hidráulico dirigido E, pero sí de la malla vial urbana
        G_vial por donde una persona o vehículo puede desviarse para esquivar un arroyo).
        """
        res: List[Tuple[str, str, int, str]] = []
        Candidatos = [
            ("N1", "N2", 520, "Interconexión Av. Circunvalar – Cra 53 (Rotonda Makro)"),
            ("N3", "N5", 480, "Corredor Universitario – Acceso Norte Campus (Coliseo)"),
        ]
        for u, v, w, desc in Candidatos:
            if u in self.nodos and v in self.nodos:
                res.append((u, v, w, desc))
        return res

    def calcular_ruta_segura(
        self,
        origen: str,
        destino: str,
        evitar_preventivos: bool = False,
        hora_pico: bool = False,
    ) -> Dict[str, object]:
        """
        Calcula la Ruta Segura (tipo 'Google Maps de Arroyos') entre 'origen' y 'destino':
          1. Construye la red vial no dirigida G_vial = (V, E_vial, w) que une los tramos
             del sector Uninorte y los corredores de desvío en cota alta.
          2. Define el conjunto de vértices bloqueados por arroyos:
               V_bloq = {v ∈ V : q_v = ROJO}  (o {ROJO, NARANJA, AMARILLO} si evitar_preventivos=True).
          3. Aplica el concepto de Subgrafo Inducido (Prof. Yesneri Zuleta, Unidad 3):
               G_seguro = G_vial - V_bloq = G_vial[V \\ V_bloq]
             y ejecuta el algoritmo de Dijkstra con pesos dinámicos ajustados por tráfico
             (hora_pico) y penalización preventiva en nodos AMARILLO/NARANJA.
          4. Compara la Ruta Habitual (sin considerar inundación) frente a la Ruta Segura
             Recomendada para mostrar qué arroyos se esquivan y el tiempo estimado en minutos.
        """
        if origen not in self.nodos or destino not in self.nodos:
            raise ValueError(f"Los nodos {origen} y {destino} deben pertenecer a V.")

        vs = self.ids_ordenados

        # Construcción de lista de adyacencia vial no dirigida con distancia física en metros
        adj_vial: Dict[str, Dict[str, int]] = {v: {} for v in vs}
        for u, v in self.aristas:
            w = self.peso(u, v)
            adj_vial[u][v] = w
            adj_vial[v][u] = w

        extras = self.corredores_viales_extra()
        for u, v, w, _ in extras:
            adj_vial[u][v] = w
            adj_vial[v][u] = w

        # Factores de congestión vehicular/peatonal en hora pico en arterias principales
        aristas_hora_pico: Dict[Tuple[str, str], float] = {
            ("N1", "N4"): 1.45,  # Cra 51B frente a Uninorte
            ("N4", "N6"): 1.35,  # Cra 51B hacia Villa Campestre
            ("N1", "N2"): 1.30,  # Circunvalar
            ("N2", "N3"): 1.25,  # Rotonda Cra 53 / Portoazul
            ("N3", "N7"): 1.20,  # Corredor Universitario
        }

        def _factor_trafico(u: str, v: str) -> float:
            if not hora_pico:
                return 1.0
            par = (u, v) if (u, v) in aristas_hora_pico else (v, u)
            return aristas_hora_pico.get(par, 1.10)

        # Velocidad media de desplazamiento urbano (m/min): ~250 m/min (~15 km/h multimodal)
        vel_m_por_min = 250.0

        def _dijkstra_vial(bloqueados: Set[str], penalizar_riesgo: bool) -> Dict[str, object]:
            if origen in bloqueados or destino in bloqueados:
                return {
                    "existe": False,
                    "camino": [],
                    "aristas": [],
                    "distancia_m": 0,
                    "tiempo_min": 0.0,
                    "costo_ponderado": float("inf"),
                }

            dist_pond: Dict[str, float] = {v: float("inf") for v in vs}
            prev: Dict[str, Optional[str]] = {v: None for v in vs}
            dist_pond[origen] = 0.0
            pq: List[Tuple[float, str]] = [(0.0, origen)]

            while pq:
                c_u, u = heapq.heappop(pq)
                if c_u > dist_pond[u]:
                    continue
                if u == destino:
                    break
                for w_vec, dist_m in adj_vial[u].items():
                    if w_vec in bloqueados:
                        continue
                    f_traf = _factor_trafico(u, w_vec)
                    f_riesgo = 1.0
                    if penalizar_riesgo:
                        est_w = self.nodos[w_vec].estado
                        est_u = self.nodos[u].estado
                        if est_w is Estado.NARANJA or est_u is Estado.NARANJA:
                            f_riesgo = 1.60
                        elif est_w is Estado.AMARILLO or est_u is Estado.AMARILLO:
                            f_riesgo = 1.30
                    costo_arista = float(dist_m) * f_traf * f_riesgo
                    if dist_pond[u] + costo_arista < dist_pond[w_vec]:
                        dist_pond[w_vec] = dist_pond[u] + costo_arista
                        prev[w_vec] = u
                        heapq.heappush(pq, (dist_pond[w_vec], w_vec))

            if dist_pond[destino] == float("inf"):
                return {
                    "existe": False,
                    "camino": [],
                    "aristas": [],
                    "distancia_m": 0,
                    "tiempo_min": 0.0,
                    "costo_ponderado": float("inf"),
                }

            camino: List[str] = []
            act: Optional[str] = destino
            while act is not None:
                camino.append(act)
                act = prev[act]
            camino.reverse()

            aristas_cam: List[Tuple[str, str]] = [
                (camino[i], camino[i + 1]) for i in range(len(camino) - 1)
            ]
            dist_total_m = sum(adj_vial[u][v] for u, v in aristas_cam)
            tiempo_total_min = sum(
                (adj_vial[u][v] * _factor_trafico(u, v)) / vel_m_por_min
                for u, v in aristas_cam
            )
            return {
                "existe": True,
                "camino": camino,
                "aristas": aristas_cam,
                "distancia_m": dist_total_m,
                "tiempo_min": round(tiempo_total_min, 1),
                "costo_ponderado": round(dist_pond[destino], 1),
            }

        # 1. Ruta habitual (sin bloqueos por arroyos)
        ruta_habitual = _dijkstra_vial(bloqueados=set(), penalizar_riesgo=False)

        # 2. Conjunto de vértices bloqueados V_bloq
        estados_bloqueo = (
            {Estado.ROJO, Estado.NARANJA, Estado.AMARILLO}
            if evitar_preventivos
            else {Estado.ROJO}
        )
        nodos_bloqueados: Set[str] = {
            v for v, n in self.nodos.items() if n.estado in estados_bloqueo
        }

        # 3. Ruta segura sobre el subgrafo inducido G_vial[V \ V_bloq]
        ruta_segura = _dijkstra_vial(
            bloqueados=nodos_bloqueados,
            penalizar_riesgo=not evitar_preventivos,
        )

        cam_hab: List[str] = list(ruta_habitual["camino"])  # type: ignore[arg-type]
        cam_seg: List[str] = list(ruta_segura["camino"])  # type: ignore[arg-type]
        peligros_en_habitual = [
            v for v in cam_hab if self.nodos[v].estado in estados_bloqueo
        ]

        aristas_bloqueadas: Set[Tuple[str, str]] = set()
        for u in vs:
            for v in adj_vial[u]:
                if u in nodos_bloqueados or v in nodos_bloqueados:
                    aristas_bloqueadas.add((u, v))

        motivo_sin_ruta = ""
        if not ruta_segura["existe"]:
            if origen in nodos_bloqueados:
                motivo_sin_ruta = (
                    f"El punto de origen {origen} ({self.nodos[origen].corto}) se encuentra "
                    f"actualmente en estado {self.nodos[origen].estado.value} (inundado/bloqueado)."
                )
            elif destino in nodos_bloqueados:
                motivo_sin_ruta = (
                    f"El destino {destino} ({self.nodos[destino].corto}) se encuentra "
                    f"actualmente en estado {self.nodos[destino].estado.value} (inundado/bloqueado)."
                )
            else:
                motivo_sin_ruta = (
                    f"Todos los caminos entre {origen} y {destino} están cortados por arroyos activos "
                    f"en V_bloq = {{{', '.join(sorted(nodos_bloqueados))}}} (vértice de corte/cuello de botella)."
                )

        return {
            "origen": origen,
            "destino": destino,
            "evitar_preventivos": evitar_preventivos,
            "hora_pico": hora_pico,
            "nodos_bloqueados": sorted(nodos_bloqueados),
            "nodos_seguros": sorted(set(vs) - nodos_bloqueados),
            "aristas_bloqueadas": aristas_bloqueadas,
            "corredores_extra": extras,
            "ruta_habitual": ruta_habitual,
            "peligros_en_habitual": peligros_en_habitual,
            "ruta_segura": ruta_segura,
            "hay_ruta_segura": bool(ruta_segura["existe"]),
            "cambio_ruta": bool(ruta_segura["existe"] and cam_seg != cam_hab),
            "motivo_sin_ruta": motivo_sin_ruta,
        }


# ============================================================================
# 4. CONSTRUCCIÓN DE LA TOPOLOGÍA DE LA ZONA UNINORTE
# ============================================================================
FUENTE_OFICIAL = "Oficial (cuenca/sumidero, CRA – según el autor)"
FUENTE_TERRENO = "Observación de terreno (aportada por el autor)"
FUENTE_AUTOR = "Aportado por el autor (sin clasificar)"


def crear_cuenca_uninorte() -> CuencaDAG:
    """
    Red de 9 nodos de la vertiente occidental de la zona de Uninorte, con pesos
    w(u, v) = distancia aproximada de recorrido hidráulico en metros (para Dijkstra y MST).
    """
    g = CuencaDAG()
    vertices = [
        ("N1", "Entrada Circunvalar / Cra 51B", "Circunvalar / Cra 51B", FUENTE_AUTOR),
        ("N2", "Rotonda Makro / Cra 53", "Rotonda Makro / Cra 53", FUENTE_TERRENO),
        (
            "N3",
            "Depresión Portoazul (Cra 53 / Corredor Universitario)",
            "Depresión Portoazul",
            FUENTE_TERRENO,
        ),
        ("N4", "Frente Uninorte / Cra 51B (Puerta 1)", "Frente Uninorte / 51B", FUENTE_TERRENO),
        ("N5", "Drenaje interno del campus / canchas", "Drenaje interno campus", FUENTE_TERRENO),
        (
            "N6",
            "Box-culvert Villa Campestre / Cra 51B",
            "Box-culvert V. Campestre",
            FUENTE_TERRENO,
        ),
        (
            "N7",
            "Confluencia canal colector perimetral",
            "Canal colector perimetral",
            FUENTE_TERRENO,
        ),
        ("N8", "Arroyo León (Troncal / Eduardo Santos)", "Arroyo León", FUENTE_OFICIAL),
        (
            "N9",
            "Ciénaga de Mallorquín (sumidero final)",
            "Ciénaga de Mallorquín",
            FUENTE_OFICIAL,
        ),
    ]
    for v in vertices:
        g.agregar_nodo(*v)

    # Aristas (u, v, peso_en_metros_aprox)
    aristas_ponderadas = [
        ("N1", "N4", 450),
        ("N2", "N3", 380),
        ("N3", "N7", 1150),
        ("N4", "N5", 320),
        ("N4", "N6", 620),
        ("N5", "N7", 740),
        ("N6", "N7", 510),
        ("N7", "N8", 890),
        ("N8", "N9", 1450),
    ]
    for u, v, w in aristas_ponderadas:
        g.agregar_arista(u, v, peso=w)
    g.orden_topologico()
    return g
