# Clustering (K-Means) para segmentación de imágenes

## ¿Qué es la segmentación de imágenes?

La segmentación de imágenes es el proceso de dividir una imagen en diferentes regiones o conjuntos de píxeles con características similares. El objetivo principal es simplificar la representación de la imagen para facilitar su análisis o procesamiento. Se utiliza en aplicaciones como visión por computadora, análisis médico, reconocimiento de objetos y más.

### Algoritmos de segmentación de imágenes
🔹 Basados en umbralización
* Umbralización simple
* Umbralización adaptativa
* Método de Otsu

🔹 Basados en clustering
* K-Means
* Mean-Shift
* Gaussian Mixture Models (GMM)

🔹 Basados en regiones
* Crecimiento de regiones
* Dividir y fusionar (Split and Merge)
* Watershed

🔹 Basados en contornos
* Detección de bordes (Canny, Sobel, Prewitt)
* Active Contours (Snakes)

🔹 Basados en aprendizaje profundo
* Redes Neuronales Convolucionales (CNN)
* U-Net
* Mask R-CNN

## Clustering K-Means para Segmentación de Imágenes


El objetivo de K-Means en segmentación de imágenes es **agrupar píxeles similares** en distintas regiones según sus características (generalmente basadas en color, textura o intensidad).

Cada píxel $\mathbf{x}_i$ es un punto en un espacio de características (por ejemplo, en un espacio de color como RGB o Lab).

---

### Algoritmo de K-Means

El algoritmo de K-Means sigue estos pasos:

1. **Inicialización**: Seleccionar $K$ centroides $\mathbf{\mu}_j$ de forma aleatoria o con un método como **K-Means++**.

2. **Asignación de Clústeres**: Para cada píxel $\mathbf{x}_i$, asignarlo al clúster más cercano:
   
   $$
   c_i = \arg\min_{j} \|\mathbf{x}_i - \mathbf{\mu}_j\|^2
   $$
   
   donde $c_i$ es el índice del clúster asignado a $\mathbf{x}_i$.

3. **Actualización de Centroides**: Recalcular los centroides como el promedio de los puntos asignados a cada clúster:
   
   $$
   \mathbf{\mu}_j = \frac{1}{|C_j|} \sum_{\mathbf{x}_i \in C_j} \mathbf{x}_i
   $$
   
   donde $C_j$ es el conjunto de píxeles asignados al clúster $j$.

4. **Repetición**: Repetir los pasos 2 y 3 hasta que los centroides **dejen de cambiar** significativamente o se alcance un número máximo de iteraciones.

---

### Distancias Comunes en Segmentación

La métrica de distancia afecta la calidad de la segmentación. Algunas opciones son:

- **Euclidiana** (más común en RGB/Lab):
  
  $$
  d(\mathbf{x}_i, \mathbf{\mu}_j) = \sqrt{(R_i - R_j)^2 + (G_i - G_j)^2 + (B_i - B_j)^2}
  $$

- **Manhattan (L1)**:
  
  $$
  d(\mathbf{x}_i, \mathbf{\mu}_j) = |R_i - R_j| + |G_i - G_j| + |B_i - B_j|
  $$

- **CIEDE2000** (para mejorar percepción visual en Lab):
  
  $$
  d_{\text{CIEDE2000}}(\mathbf{x}_i, \mathbf{\mu}_j) = \text{función compleja en Lab}
  $$

---

### Métodos de Mejora

- **K-Means en espacio de color y coordenadas espaciales**:
  - En vez de usar solo $(R,G,B)$, se pueden usar **coordenadas espaciales** $(x,y)$ para evitar regiones discontinuas:
    
    $$
    \mathbf{x}_i = (R, G, B, x, y)
    $$

- **K-Means con PCA**:
  - Si los datos tienen muchas dimensiones, se puede usar **Análisis de Componentes Principales (PCA)** para reducirlos antes de aplicar K-Means.

- **K-Means con histogramas de color**:
  - Se agrupan píxeles según histogramas en lugar de valores individuales.

- **Método de Elbow para elegir $K$**:
  - Se calcula la **Suma de Errores Cuadrados (SSE)** para distintos valores de $K$ y se usa la "curva de codo":
    
    $$
    \text{SSE} = \sum_{i=1}^{N} \|\mathbf{x}_i - \mathbf{\mu}_{c_i}\|^2
    $$

---

### Cuándo usar K-Means para segmentación de imágenes

* Cuando la segmentación se basa en colores
* Cuando se busca una segmentación rápida y simple
* Para preprocesamiento en otros métodos de visión por computadora
* Para imágenes con poco ruido y bien diferenciadas


---

### Cuándo **NO** usar K-Means para segmentación de imágenes
* Cuando la segmentación requiere información espacial
* Para imágenes con mucho ruido o texturas complejas
* Si los objetos no están bien diferenciados en color
* Cuando la imagen tiene cambios de iluminación


