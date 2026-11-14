#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de pruebas unitarias para el Sistema de Monitoreo de Arroyos (Matemáticas Discretas).
Cubre:
  - Autómata Finito Determinista (AFD) y Consenso Booleano.
  - Unidad 3 y Prof. Yesneri Zuleta: Vecindades, Grados (δ, Δ, δ±, Δ±), TAM y Corolario,
    Bipartición, Subgrafo inducido G - v, Euler/Hamilton/Planaridad, Trazas BFS/DFS,
    Dijkstra y Árbol de Expansión Mínimo (Kruskal y Prim).
  - Unidad 4: Distancias geodésicas BFS, Diámetro y Centralidades (Grado, Cercanía,
    Variante Armónica e Intermediación).

Ejecutar con:
    python -m unittest test_arroyos.py -v
"""

from __future__ import annotations

import unittest
from typing import List, Tuple

from modelo_discreto import (
    AFD,
    Estado,
    Simbolo,
    ValidadorConsenso,
    crear_cuenca_uninorte,
)
from sistema_alerta import SistemaAlerta


class TestAFD(unittest.TestCase):
    """Pruebas formales sobre el Autómata Finito Determinista M = (Q, Σ, δ, q0, F)."""

    def test_totalidad_y_determinismo_delta(self) -> None:
        afd = AFD()
        self.assertEqual(afd.estado, Estado.VERDE)
        self.assertEqual(len(AFD.DELTA), len(AFD.Q) * len(AFD.SIGMA))
        for q in Estado:
            for s in Simbolo:
                self.assertIn((q, s), AFD.DELTA)
                self.assertIsInstance(AFD.DELTA[(q, s)], Estado)

    def test_transiciones_y_estado_absorbente_rojo(self) -> None:
        afd = AFD()
        self.assertEqual(afd.procesar(Simbolo.ALERTA), (Estado.VERDE, Estado.AMARILLO))
        self.assertEqual(afd.procesar(Simbolo.REPORTE), (Estado.AMARILLO, Estado.NARANJA))
        self.assertEqual(afd.procesar(Simbolo.CONSENSO), (Estado.NARANJA, Estado.ROJO))
        self.assertTrue(afd.es_aceptacion())
        self.assertEqual(afd.procesar(Simbolo.REPORTE), (Estado.ROJO, Estado.ROJO))
        self.assertEqual(afd.procesar(Simbolo.ALERTA), (Estado.ROJO, Estado.ROJO))
        self.assertEqual(afd.procesar(Simbolo.REINICIO), (Estado.ROJO, Estado.VERDE))
        self.assertFalse(afd.es_aceptacion())

    def test_funcion_transicion_extendida_palabra(self) -> None:
        afd = AFD()
        palabra = [Simbolo.REPORTE, Simbolo.ALERTA, Simbolo.CONSENSO]
        pasos = afd.procesar_palabra(palabra)
        self.assertEqual(len(pasos), 3)
        self.assertEqual(afd.estado, Estado.ROJO)
        self.assertEqual(afd.palabra, palabra)
        afd.reiniciar()
        self.assertEqual(afd.estado, Estado.VERDE)
        self.assertEqual(len(afd.palabra), 0)


class TestValidadorConsenso(unittest.TestCase):
    """Pruebas del predicado de consenso booleano C(R, k) = (|R| >= k)."""

    def test_cardinalidad_conjunto_y_umbral(self) -> None:
        reportantes = {"C-001", "C-001", "C-002"}
        self.assertEqual(len(reportantes), 2)
        self.assertFalse(ValidadorConsenso.consenso(reportantes, k=3))
        reportantes.add("C-003")
        self.assertTrue(ValidadorConsenso.consenso(reportantes, k=3))


class TestUnidad3YProfZuleta(unittest.TestCase):
    """Pruebas de los temas de Unidad 3 (MSc Iván Gómez y Prof. Yesneri Zuleta)."""

    def setUp(self) -> None:
        self.g = crear_cuenca_uninorte()

    def test_vecindades_extremos_tam_y_corolario(self) -> None:
        # Vecindades en N7
        self.assertEqual(self.g.vecindad_entrada("N7"), ["N3", "N5", "N6"])
        self.assertEqual(self.g.vecindad_salida("N7"), ["N8"])
        self.assertEqual(self.g.vecindad_abierta("N7"), ["N3", "N5", "N6", "N8"])
        self.assertEqual(self.g.vecindad_cerrada("N7"), ["N3", "N5", "N6", "N7", "N8"])

        ext = self.g.extremos_grados()
        self.assertEqual(ext["delta_min"], 1)
        self.assertEqual(ext["delta_max"], 4)
        self.assertEqual(ext["delta_in_min"], 0)
        self.assertEqual(ext["delta_in_max"], 3)
        self.assertEqual(ext["delta_out_min"], 0)
        self.assertEqual(ext["delta_out_max"], 2)
        self.assertEqual(ext["suma_grados_no_dirigido"], 18)
        self.assertEqual(ext["dos_m"], 18)
        # Corolario: número par de vértices con grado impar
        self.assertEqual(len(ext["vertices_impares"]), 4)
        self.assertEqual(len(ext["vertices_impares"]) % 2, 0)

    def test_biparticion_y_subgrafo_inducido(self) -> None:
        bip = self.g.analisis_bipartito()
        self.assertTrue(bip["es_bipartito"])
        v1 = set(bip["V1"])
        v2 = set(bip["V2"])
        self.assertEqual(len(v1 & v2), 0)
        self.assertEqual(len(v1 | v2), 9)
        for u, v in self.g.aristas:
            self.assertTrue((u in v1 and v in v2) or (u in v2 and v in v1))

        # G - N7 desconecta toda la cuenca alta del sumidero N9
        sub_n7 = self.g.subgrafo_inducido_sin_vertice("N7")
        self.assertTrue(sub_n7["es_punto_articulacion"])
        self.assertGreater(sub_n7["num_componentes"], 1)
        self.assertIn("N4", sub_n7["desconectados_del_sumidero"])

    def test_euler_hamilton_y_planaridad(self) -> None:
        ehp = self.g.analisis_euler_hamilton_plano()
        self.assertFalse(ehp["tiene_circuito_euler"])
        self.assertFalse(ehp["tiene_camino_euler"])
        self.assertFalse(ehp["cumple_dirac"])
        self.assertFalse(ehp["cumple_ore"])
        self.assertTrue(ehp["cumple_cota_general"])
        self.assertTrue(ehp["cumple_cota_bipartita"])
        self.assertEqual(ehp["caras_F"], 2)
        self.assertTrue(ehp["verifica_euler_plano"])

    def test_matrices_incidencia_dirigida_y_no_dirigida(self) -> None:
        orden_v, aristas, mat_nodir = self.g.matriz_incidencia(dirigido=False)
        for col in range(len(aristas)):
            self.assertEqual(sum(mat_nodir[i][col] for i in range(len(orden_v))), 2)
        for i, v in enumerate(orden_v):
            self.assertEqual(sum(mat_nodir[i]), self.g.grado_no_dirigido(v))

        _, _, mat_dir = self.g.matriz_incidencia(dirigido=True)
        for col in range(len(aristas)):
            self.assertEqual(sum(mat_dir[i][col] for i in range(len(orden_v))), 0)

    def test_trazas_bfs_dfs_dijkstra_y_mst(self) -> None:
        t_bfs = self.g.traza_bfs_detallada("N4", dirigido=True)
        t_dfs = self.g.traza_dfs_detallada("N4", dirigido=True)
        self.assertEqual(t_bfs["orden_visita"][0], "N4")
        self.assertEqual(t_dfs["orden_visita"][0], "N4")
        # En BFS desde N4, N5 y N6 se visitan antes que N7; en DFS, N7 se visita antes que N6
        self.assertLess(t_bfs["orden_visita"].index("N6"), t_bfs["orden_visita"].index("N7"))
        self.assertLess(t_dfs["orden_visita"].index("N7"), t_dfs["orden_visita"].index("N6"))

        mst = self.g.mst_kruskal_prim()
        self.assertEqual(mst["num_aristas_mst"], 8)
        self.assertEqual(len(mst["descartadas_kruskal"]), 1)
        # La arista más pesada del ciclo N4-N5-N7-N6 es (N5, N7) de 740 m -> se descarta
        self.assertEqual(mst["descartadas_kruskal"][0][:2], ("N5", "N7"))

        dijk = self.g.dijkstra("N4", dirigido=True)
        # De N4 a N7: vía N5 cuesta 320+740=1060m; vía N6 cuesta 620+510=1130m -> gana vía N5
        self.assertEqual(dijk["distancias"]["N7"], 1060.0)
        self.assertEqual(dijk["caminos"]["N7"], ["N4", "N5", "N7"])


class TestUnidad4Centralidades(unittest.TestCase):
    """Pruebas de Análisis de Redes (Unidad 4: Distancias BFS y Centralidades C_D, C_C, C_B)."""

    def setUp(self) -> None:
        self.g = crear_cuenca_uninorte()

    def test_distancias_geodesicas_y_centralidades(self) -> None:
        cent = self.g.analisis_centralidades_unidad4()
        self.assertEqual(cent["diametro_no_dirigido"], 5)
        self.assertEqual(cent["diametro_dirigido"], 5)

        # N7 es el nodo más central en las tres medidas sobre el grafo subyacente
        self.assertEqual(cent["lider_grado"], "N7")
        self.assertEqual(cent["lider_cercania"], "N7")
        self.assertEqual(cent["lider_intermediacion"], "N7")

        # Entre N4 y N7 hay exactamente 2 caminos más cortos de longitud 2
        caminos_n4_n7 = self.g.caminos_mas_cortos_entre("N4", "N7", dirigido=False)
        self.assertEqual(len(caminos_n4_n7), 2)


class TestSistemaAlerta(unittest.TestCase):
    """Pruebas de integración del flujo de reportes, consenso y propagación BFS."""

    def test_flujo_reportes_consenso_y_propagacion(self) -> None:
        eventos: List[Tuple[str, str]] = []
        cuenca = crear_cuenca_uninorte()
        sistema = SistemaAlerta(cuenca, k=3, log=lambda m, e: eventos.append((m, e)))

        sistema.enviar_reporte("N4")
        sistema.enviar_reporte("N4")
        self.assertEqual(cuenca.nodos["N4"].estado, Estado.NARANJA)

        sistema.enviar_reporte("N4")
        self.assertEqual(cuenca.nodos["N4"].estado, Estado.ROJO)
        for desc in ["N5", "N6", "N7", "N8", "N9"]:
            self.assertEqual(cuenca.nodos[desc].estado, Estado.AMARILLO)
        for no_desc in ["N1", "N2", "N3"]:
            self.assertEqual(cuenca.nodos[no_desc].estado, Estado.VERDE)

        informe = sistema.generar_informe_texto()
        self.assertIn("CENTRALIDAD DE GRADO, CERCANÍA E INTERMEDIACIÓN", informe)


class TestRutaSeguraGoogleMapsArroyos(unittest.TestCase):
    """Pruebas del navegador de Ruta Segura (tipo Google Maps de arroyos con Dijkstra en G - V_bloq)."""

    def setUp(self) -> None:
        self.cuenca = crear_cuenca_uninorte()
        self.sistema = SistemaAlerta(self.cuenca, k=3, log=lambda m, e: None)

    def test_ruta_habitual_sin_arroyos(self) -> None:
        info = self.cuenca.calcular_ruta_segura("N1", "N6")
        self.assertTrue(info["hay_ruta_segura"])
        self.assertFalse(info["cambio_ruta"])
        self.assertEqual(info["ruta_segura"]["camino"], ["N1", "N4", "N6"])
        self.assertEqual(info["ruta_segura"]["distancia_m"], 1070)

    def test_desvio_automatico_cuando_n4_se_inunda(self) -> None:
        # Al alcanzar consenso en N4 (Frente Uninorte / Cra 51B), N4 pasa a ROJO
        for _ in range(3):
            self.sistema.enviar_reporte("N4")
        self.assertEqual(self.cuenca.nodos["N4"].estado, Estado.ROJO)

        # El navegador debe esquivar N4 automáticamente usando los corredores de cota alta (N1->N2->N3->N7->N6)
        info = self.cuenca.calcular_ruta_segura("N1", "N6", evitar_preventivos=False)
        self.assertTrue(info["hay_ruta_segura"])
        self.assertTrue(info["cambio_ruta"])
        self.assertIn("N4", info["nodos_bloqueados"])
        self.assertNotIn("N4", info["ruta_segura"]["camino"])
        self.assertEqual(info["ruta_segura"]["camino"][0], "N1")
        self.assertEqual(info["ruta_segura"]["camino"][-1], "N6")

    def test_bloqueo_total_en_punto_de_articulacion_n7(self) -> None:
        # Si N7 (cuello de botella con máxima intermediación C_B) entra en ROJO, N9 queda incomunicado
        for _ in range(3):
            self.sistema.enviar_reporte("N7")
        info = self.cuenca.calcular_ruta_segura("N1", "N9")
        self.assertFalse(info["hay_ruta_segura"])
        self.assertIn("N7", info["nodos_bloqueados"])


if __name__ == "__main__":
    unittest.main()
