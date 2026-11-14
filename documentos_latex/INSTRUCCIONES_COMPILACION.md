# Archivos LaTeX para Entrega en Brightspace

Esta carpeta contiene el código fuente completo en **LaTeX** de los dos documentos PDF exigidos para el curso **Matemáticas Discretas (NRC 3230)** — Prof. **Iván Yesid Gómez Gómez** — **Grupo 1**:

1. `paper_arroyos_apa.tex`: Documento escrito final con normas APA (7.ª edición), estructura de 7 secciones, diagramas vectoriales en TikZ, tablas reales calculadas por el sistema, referencias APA y enlace al repositorio en GitHub.
2. `presentacion_arroyos_beamer.tex`: Diapositivas en LaTeX Beamer (16:9) estructuradas exactamente para **10 minutos** de sustentación repartidos equitativamente entre los **5 integrantes** (2 minutos por persona).
3. `mapa_barranquilla_google.png` y `mapa_panoramico_uninorte.png`: Imágenes incluidas por ambos `.tex`.

## Cómo generar los PDF (2 opciones)

### Opción A: Overleaf (recomendada, sin instalar nada)
1. Comprime la carpeta `documentos_latex` en un archivo `.zip`.
2. En Overleaf selecciona **New Project -> Upload Project** y sube el `.zip`.
3. Para generar el PDF del documento escrito, elige `paper_arroyos_apa.tex` como *Main document* en el menú y pulsa **Recompile -> Download PDF**.
4. Para generar las diapositivas, cambia *Main document* a `presentacion_arroyos_beamer.tex`, pulsa **Recompile -> Download PDF**.

### Opción B: Local con TeXstudio + MiKTeX
Si deseas compilar localmente desde **TeXstudio** en Windows, instala la distribución **MiKTeX** (que provee `pdflatex.exe`) y compila dos veces cada archivo `.tex` para resolver referencias cruzadas y números de página.

## Reparto de tiempos para la sustentación (10 min exactos)
- **0:00 – 2:00** | **Jesús De León Jiménez**: Diapositivas 3 y 4 (Problema en Barranquilla, impacto, objetivos).
- **2:00 – 4:00** | **Samuel De Oro Torres**: Diapositivas 5 y 6 (Conjuntos, consenso $C(R,k)$, estados discretos, DAG y Kahn).
- **4:00 – 6:00** | **Karvin García Polo**: Diapositiva 7 (Unidad 3: Lema Apretón de Manos, bipartición, punto de articulación $N_7$, MST).
- **6:00 – 8:00** | **Juan Sierra Varela**: Diapositivas 8 y 9 (Unidad 4: Centralidades, BFS por capas, desvío Dijkstra $1070\text{ m} \to 2560\text{ m}$).
- **8:00 – 10:00** | **Andrés Torres García**: Diapositivas 10 y 11 (Arquitectura Python, mapa web 25 nodos/71 rutas OSM, 14/14 pruebas, conclusiones/limitaciones + demo).
