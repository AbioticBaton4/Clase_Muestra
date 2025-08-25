import cv2
import numpy as np
from sklearn.cluster import KMeans
from skimage.color import rgb2lab, lab2rgb
import matplotlib.pyplot as plt
import random
from PIL import Image

def show_multi_images(images, titles=None, figsize=(12, 5), cols = 3,subtitle='Comparing Images', cmap=None):
    """
    Muestra la imagen original junto con las imágenes a comparar y permite títulos personalizados.

    Parámetros:
    - images: Lista de imágenes o variantes de la imagen origial.
    - titles: Lista opcional de títulos para las imágenes o variantes.
              Si no se proporciona, se generan títulos genéricos.
    - figsize: Tamaño de la figura.
    - subtitle: Título de la figura.
    - cmap: Mapa de colores para mostrar las imágenes.
    """
    if titles is None:
        titles = [f'Image {i+1}' for i in range(len(images))]

    if len(images) != len(titles):
        raise ValueError("El número de imágenes debe coincidir con el número de títulos.")

    total_images = len(images)
    rows = int(np.ceil(total_images / cols))
    
    # Crear los subgráficos
    fig, axs = plt.subplots(rows, cols, figsize=figsize)
    fig.suptitle(subtitle)
    
    # Convertir axs en un arreglo unidimensional para facilitar la iteración
    axs = axs.ravel()

    # Mostrar las imágenes cuantizadas con sus títulos personalizados
    for i, (img, title) in enumerate(zip(images, titles)):
        axs[i].imshow(img, cmap=cmap)
        axs[i].set_title(title)
        axs[i].axis('off')  # Ocultar ejes

    # Ocultar subplots vacíos
    for i in range(total_images, len(axs)):
        axs[i].axis('off')
        
    # Ajustar la visualización
    plt.tight_layout()
    plt.show()

def load_image(image_path):
    """
    Carga una imagen y la convierte en un array RGB.
    """
    # image = Image.open(image_path).convert("RGB")
    return np.array(Image.open(image_path).convert("RGB"))

class KMeansImageSegmenter:
    def __init__(self, k=3, max_iters=10, tol=1e-4):
        """
        Inicializa el segmentador de imágenes con K-Means.
        
        Parámetros:
            k (int): Número de clusters (colores en la imagen segmentada).
            max_iters (int): Número máximo de iteraciones.
            tol (float): Tolerancia para la convergencia.
        """
        self.k = k
        self.max_iters = max_iters
        self.tol = tol
        self.centroids = None
        self.labels = None
    
    # def load_image(self, image_path):
    #     """
    #     Carga una imagen y la convierte en un array RGB.
    #     """
    #     image = Image.open(image_path).convert("RGB")
    #     return np.array(image)
    
    def initialize_centroids(self, pixels):
        """
        Inicializa K centroides seleccionando aleatoriamente K píxeles de la imagen.
        """
        return pixels[random.sample(range(len(pixels)), self.k)]
    
    def assign_clusters(self, pixels):
        """
        Asigna cada píxel al centroide más cercano usando la distancia euclidiana.
        """
        distances = np.linalg.norm(pixels[:, np.newaxis] - self.centroids, axis=2)
        return np.argmin(distances, axis=1)
    
    def update_centroids(self, pixels):
        """
        Recalcula los centroides tomando el promedio de los píxeles asignados a cada cluster.
        """
        return np.array([pixels[self.labels == i].mean(axis=0) if np.any(self.labels == i) else self.centroids[i] for i in range(self.k)])
    
    def fit(self, image):
        """
        Aplica el algoritmo K-Means para segmentar una imagen en K colores.
        """
        # image = self.load_image(image_path)
        pixels = image.reshape(-1, 3).astype(float)
        self.centroids = self.initialize_centroids(pixels)
        
        for _ in range(self.max_iters):
            self.labels = self.assign_clusters(pixels)
            new_centroids = self.update_centroids(pixels)
            
            if np.linalg.norm(new_centroids - self.centroids) < self.tol:
                break
            self.centroids = new_centroids
        
        segmented_pixels = self.centroids[self.labels].reshape(image.shape).astype(np.uint8)
        return Image.fromarray(segmented_pixels)
    
    def get_cluster_masks(self, image):
        """
        Genera una máscara binaria para cada cluster en la imagen segmentada.
        """
        # image = self.load_image(image_path)
        height, width, _ = image.shape
        labels_reshaped = self.labels.reshape(height, width)
        
        masks = []
        for i in range(self.k):
            mask = (labels_reshaped == i).astype(np.uint8) * 255  # Convertimos a 0 y 255
            masks.append(mask)
        
        return masks

    def apply_masks(self, image):
        """
        Aplica las máscaras a la imagen original para mostrar qué partes corresponden a cada cluster.
        """
        # image = self.load_image(image_path)
        masks = self.get_cluster_masks(image)
        
        masked_images = []
        for mask in masks:
            # Convertimos la máscara en 3 canales para aplicarla a la imagen original
            mask_3ch = np.stack([mask] * 3, axis=-1)
            masked_image = cv2.bitwise_and(image, mask_3ch)
            masked_images.append(masked_image)
        
        return masked_images

def show_segmentation_example(image_path, k, figsize1=(12, 5), figsize2 = (12, 5), cols =3):
    """
    Muestra una comparación entre la imagen original y su versión segmentada
    utilizando el algoritmo K-Means, además de visualizar las máscaras de los
    clusters generados.

    Parámetros:
    -----------
    image_path : str
        Ruta de la imagen a procesar.
    k : int
        Número de clusters (colores) a utilizar en la segmentación.
    figsize1 : tuple, opcional
        Tamaño de la figura para la comparación de la imagen original y segmentada.
        Formato (ancho, alto). Valor por defecto: (12, 5).
    figsize2 : tuple, opcional
        Tamaño de la figura para la visualización de las máscaras de los clusters.
        Formato (ancho, alto). Valor por defecto: (12, 5).
    cols : int, opcional
        Número de columnas en la cuadrícula de subplots para las máscaras de los clusters.
        Valor por defecto: 3.

    Retorna:
    --------
    No retorna ningún valor, pero muestra dos conjuntos de imágenes:
    1. Imagen original junto con la imagen segmentada.
    2. Máscaras de los clusters generados por el algoritmo K-Means.
    """
    
    image = load_image(image_path)
    segmenter = KMeansImageSegmenter(k=k)
    segmented_image = segmenter.fit(image)
    masks = segmenter.apply_masks(image)
    # Mostrar la imagen segmentada
    show_multi_images(
        [image,segmented_image], 
        titles=['Imagen Original', f'Imagen Segmentada ({k} colores)'],
        cols=2,
        subtitle = "Comparación de Imagen Original y Segmentada",
        figsize=figsize1
    )

    # Mostrar las máscaras de los clusters
    show_multi_images(
        masks,
        titles= [f"Cluster {i+1}" for i in range(k)],
        cols=cols,
        subtitle = "Máscaras de los Clusters",
        figsize=figsize2
    )
    
    