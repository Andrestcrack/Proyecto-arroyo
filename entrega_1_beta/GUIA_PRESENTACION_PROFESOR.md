# GUÍA RÁPIDA DE PRESENTACIÓN – ENTREGA 1 (BETA)
**Proyecto**: Sistema Colaborativo de Alerta Temprana de Arroyos (Campus Uninorte)  
**Materia**: Matemáticas Discretas – Universidad del Norte  

---

## 1. ¿Cómo ejecutar el proyecto?
Abre la terminal en esta carpeta y ejecuta:
```bash
python arroyos_beta_uninorte.py
```

---

## 2. Guion para exponer al profesor en 3 minutos

### Minuto 1: Contexto y Justificación del Problema Real
> *"Profesor, en Barranquilla los arroyos pluviales paralizan la movilidad y ponen en riesgo a los estudiantes y ciudadanos. Nuestro proyecto modela la red de drenaje y escorrentía como un **Grafo Dirigido Simple $G = (V, A)$**, donde cada vértice representa un punto crítico de acumulación de agua y cada arista la dirección en que fluye la corriente por gravedad."*

### Minuto 2: Demostración Interactiva en la Aplicación
1. **Mostrar los nodos en el mapa de cercanías Uninorte**:
   - Señala el recorrido que hace el agua por gravedad desde la Circunvalar (`N1`), Cra 53 (`N2`) y Uninorte (`N4`/`N5`) hacia Villa Campestre (`N6`), Eduardo Santos (`N7`), Arroyo León (`N8`) y finalmente la Ciénaga de Mallorquín (`N9`).
   - Haz clic en cualquier nodo (por ejemplo `N4` o `N5`). Señala cómo en el panel derecho se calculan instantáneamente sus **vecindades de entrada $N^-(v)$, salida $N^+(v)$, abierta $N(v)$ y cerrada $N[v]$**, así como sus **grados $\text{grad}(v)$**.
2. **Simular el arroyo**:
   - Pulsa el botón **`📢 Registrar Reporte Ciudadano (+1)`** hasta llegar a $k=3$ o pulsa **`🌊 Simular Arroyo en Cabecera`**.
   - Muestra cómo el nodo pasa a **ROJO** (alerta crítica) y automáticamente propaga el estado **AMARILLO** preventivo hacia su vecindad de salida $N^+(v)$.

### Minuto 3: Sustentación de Matemáticas Discretas (Unidad 3)
Haz clic en los 3 botones de consulta:
1. **Botón 1: Grados, Vecindades y TAM**:
   - Muestra la verificación del **Teorema del Apretón de Manos (TAM)**:
     $$\sum \text{grad}^-(v) = \sum \text{grad}^+(v) = m = 10$$
     $$\sum \text{grad}(v) = 2m = 20$$
   - Señala el **Corolario**: el número de vértices de grado impar es par.
2. **Botón 2: Lista y Matriz de Adyacencia**:
   - Muestra cómo la matriz $A$ representa en memoria binaria las conexiones entre bloques.
3. **Botón 3: Matriz de Incidencia**:
   - Demuestra que cada columna suma exactamente 2 porque cada arista une dos vértices.

---

## 3. ¿Qué responder si el profesor pregunta por las siguientes entregas?
> *"Para las siguientes entregas ya tenemos desarrollado el escalamiento a nivel metropolitano (toda Barranquilla hasta la Ciénaga de Mallorquín y el Arroyo León), ruteo tipo Google Maps con el algoritmo de Dijkstra sobre el subgrafo inducido libre de arroyos $G - V_{\text{bloqueados}}$, y el control de estados de alerta con consenso ciudadano $C(R, k)$."*
