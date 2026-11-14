# Entrega 1 (Versión Beta Preliminar) – Monitoreo de Escorrentía en Cercanías Uninorte

Esta carpeta contiene el **prototipo inicial (Versión Beta)** del proyecto de Matemáticas Discretas, diseñado para la **primera entrega**.

## Ejecución
```bash
python arroyos_beta_uninorte.py
```

## Alcance de esta Versión Beta (Entrega 1)
1. **Escala geográfica (Corredor Uninorte – Arroyo León – Mallorquín)**:
   - Utiliza el mapa satelital/vial enfocado de las **Cercanías de Uninorte** (`mapa_campus_uninorte.png`, también incrustado en Base64 dentro de `arroyos_beta_uninorte.py`).
   - Modela los 9 vértices $v \in V$ del corredor de escorrentía pluvial:
     - `N1`: Circunvalar / Cra 51B (Intercambiador Villa Julia)
     - `N2`: Cra 53 / PriceSmart (Rotonda de acceso oriental)
     - `N3`: Depresión Portoazul (Corredor Universitario)
     - `N4`: Frente Uninorte (Puerta 1 / Cra 51B)
     - `N5`: Drenaje Interno Campus Uninorte
     - `N6`: Villa Campestre (Box-culvert / canal colector)
     - `N7`: Eduardo Santos (Confluencia canal perimetral)
     - `N8`: Arroyo León (Vía La Playa)
     - `N9`: Ciénaga de Mallorquín (Desembocadura y sumidero final)
2. **Conceptos de Matemáticas Discretas incluidos (Unidad 3.1 – 3.3 y Prof. Yesneri Zuleta)**:
   - Definición formal del grafo $G = (V, A)$ y clasificación (**simple** y **dirigido**).
   - **Vecindades**: vecindad de entrada $N_G^-(v)$, vecindad de salida $N_G^+(v)$, vecindad abierta $N_G(v)$ y vecindad cerrada $N_G[v] = N_G(v) \cup \{v\}$.
   - **Grados (valencias) y extremos**: $\text{grad}^-(v)$, $\text{grad}^+(v)$, $\text{grad}(v)$, grado mínimo $\delta(G)$, grado máximo $\Delta(G)$, y extremos dirigidos $\delta^\pm(G), \Delta^\pm(G)$.
   - **Teorema del Apretón de Manos (TAM)** ($\sum \text{grad}(v) = 2m$ y $\sum \text{grad}^-(v) = \sum \text{grad}^+(v) = m$) y su **Corolario** (número par de vértices con grado impar).
   - **Representaciones matriciales y en lista**: Lista de adyacencia, Matriz de adyacencia $A$ y Matriz de incidencia $M$.
   - Propagación preliminar de alertas únicamente a vecinos directos de salida $N_G^+(v)$.

## Evolución hacia la Entrega Final (Carpeta Raíz)
En la entrega final (`../arroyos_uninorte.py`), el modelo evoluciona para cubrir:
- **Ampliación geográfica a toda la red metropolitana de Barranquilla**: mapa interactivo web completo con ruteo seguro calle por calle.
- **Resto de la Unidad 3**: Bipartición $V_1 \cup V_2$, subgrafo inducido $G - v$, conectividad fuerte vs. débil, Teorema de Euler, Teoremas de Dirac y Ore (Hamilton), Grafos Planos ($V - E + F = 2$), trazas completas paso a paso de **BFS vs. DFS**, árboles con raíz, **Dijkstra** y **Árbol de Expansión Mínimo (Kruskal y Prim)**.
- **Unidad 4 completa (Análisis de Redes)**: las 4 preguntas de modelación, distancias geodésicas con BFS, diámetro y las 3 medidas de centralidad (**Grado $C_D$, Cercanía $C_C$ / Armónica $H$ e Intermediación $C_B$**).
- **Modelo discreto de estados de alerta** $f: Q \times \Sigma \to Q$ con transición determinista y consenso ciudadano $C(R, k)$.
