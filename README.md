# Sistema Colaborativo de Alerta Temprana y Ruteo Seguro de Arroyos (Barranquilla – Uninorte)

Proyecto final de **Matemáticas Discretas** (Universidad del Norte) que modela la red de escorrentía pluvial del corredor **Uninorte – Villa Campestre – Arroyo León – Ciénaga de Mallorquín** y la malla vial de **Barranquilla** mediante estructuras formales de **Teoría de Grafos (Unidades 3 y 4)**, análisis de redes y lógica discreta de consenso ciudadano.

🔗 **Repositorio oficial:** https://github.com/Andrestcrack/Proyecto-arroyo

---

## 1. Requisitos e Instalación

No se requieren librerías externas ni `pip install`. Todo el proyecto funciona únicamente con la **biblioteca estándar de Python** (`tkinter`, `http.server`, `json`, `urllib`, `heapq`, `collections`).

- **Python:** `3.9` o superior (probado en Windows con Python `3.15`).
- **Módulo gráfico:** `tkinter` (incluido por defecto en las instalaciones estándar de Python para Windows y macOS; en Linux puede instalarse con `sudo apt install python3-tk`).
- **Navegador web moderno** (Chrome, Edge o Firefox) para visualizar la vista interactiva estilo Google Maps.

### Clonar el repositorio
```bash
git clone https://github.com/Andrestcrack/Proyecto-arroyo.git
cd Proyecto-arroyo
```

---

## 2. Cómo Ejecutar el Proyecto

### A. Aplicación Principal de Escritorio + Mapa Web Interactivo (Entrega Final)
Ejecuta en la carpeta raíz:
```bash
python arroyos_uninorte.py
```
Desde la interfaz gráfica puedes:
- Hacer clic sobre los **9 nodos hidráulicos** (`N1` a `N9`) en el mapa **Cercanías Uninorte** o cambiar parámetros de consenso ($k$).
- Simular reportes ciudadanos, propagación preventiva aguas abajo por **BFS**, y observar en vivo las transiciones discretas de estados de alerta $f: Q \times \Sigma \to Q$.
- Calcular **rutas seguras por las calles** con **Dijkstra** sobre el subgrafo inducido libre de arroyos $G_{\text{vial}} - V_{\text{bloq}}$.
- Consultar todos los análisis formales de **Unidad 3 y Unidad 4**: grados, vecindades $N^-(v), N^+(v), N(v), N[v]$, Teorema del Apretón de Manos (TAM), matriz de adyacencia/incidencia, bipartición, subgrafo inducido $G - v$ (punto de articulación `N7`), Euler/Hamilton/Planaridad, trazas BFS/DFS, MST (Kruskal y Prim) y centralidades ($C_D$, $C_C$, $H$, $C_B$).
- Pulsar el botón **`🌐 Abrir Mapa Web Interactivo (Google Maps Real)`** para lanzar el servidor web local en `http://localhost:8080`.

### B. Servidor Web Interactivo ("Google Maps de Arroyos" – 25 Nodos)
También puede ejecutarse directamente desde la terminal:
```bash
python -c "from servidor_web_arroyos import iniciar_servidor_web; iniciar_servidor_web(puerto=8080, abrir_navegador=True)"
```
Incluye:
- **25 nodos monitoreados en tiempo real**: los 9 nodos de la cuenca Uninorte (`N1`–`N9`) más **16 nodos en las vías principales de Barranquilla** (`N10`–`N25`: Vía 40, Cra 51B, Cra 53, Cra 46 / Av. Olaya Herrera, Calle 84, Calle 76, Calle 72, Av. Murillo, Calle 30 y Av. Circunvalar).
- **Ruteo real calle por calle** con trazado OSRM (OpenStreetMap) y **71 corredores viales precargados** para operar y desviar el tráfico por calles reales incluso sin conexión externa.

### C. Prototipo Beta Preliminar (Entrega 1)
```bash
python entrega_1_beta/arroyos_beta_uninorte.py
```

---

## 3. Ejecutar las Pruebas Unitarias Automatizadas

El repositorio incluye **14 pruebas unitarias** que verifican formalmente la función discreta de transición de estados, el consenso booleano, las propiedades de Unidad 3 (TAM, vecindades, bipartición, $G - v$, Euler/Hamilton/Planaridad, matrices, trazas BFS/DFS/Dijkstra/MST), las centralidades de Unidad 4 y el algoritmo de desvío seguro:

```bash
python -m unittest test_arroyos.py -v
```

Resultado esperado: `Ran 14 tests ... OK`.

---

## 4. Estructura del Repositorio

```text
Proyecto-arroyo/
├── arroyos_uninorte.py        # Punto de entrada principal de la aplicación
├── modelo_discreto.py         # Estados, Consenso Booleano, CuencaDAG, Unidad 3, Unidad 4 y Dijkstra vial
├── sistema_alerta.py          # Coordinación de eventos, propagación BFS y generación de informes
├── interfaz_app.py            # Interfaz gráfica de escritorio (tkinter): mapa, monitoreo y rutas seguras
├── servidor_web_arroyos.py    # Servidor HTTP local + Google Maps interactivo con 25 nodos y ruteo vial
├── recursos_mapa.py           # Imagen base del mapa codificada en Base64
├── test_arroyos.py            # Suite de 14 pruebas unitarias (unittest)
├── mapa_barranquilla_google.png
├── mapa_panoramico_uninorte.png
└── entrega_1_beta/            # Prototipo inicial (Entrega 1) y guías de presentación
```
