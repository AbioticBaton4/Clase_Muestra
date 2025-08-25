# Introducción y Aplicación de IA

Este repositorio contiene el material necesario para la clase muestra sobre una introducción práctica a los conceptos de Inteligencia Artificial y su aplicación en el análisis de datos. El objetivo de este proyecto es demostrar un flujo de trabajo básico para analizar un conjunto de datos utilizando librerías populares de Python.

!(https://i.imgur.com/4J7f8bY.png)


***

## 🚀 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado lo siguiente en tu sistema:

* **Git:** Para clonar este repositorio.
* **Python 3.8 o superior:** El código de este proyecto requiere una versión de Python 3.8 en adelante.
* **Miniconda o Anaconda:** Para gestionar los entornos y paquetes de manera sencilla.
* **Visual Studio Code:** (Recomendado) Un editor de código moderno y muy popular para trabajar con Python. Puedes descargarlo [aquí](https://code.visualstudio.com/).

***

## ⚙️ Instalación y Configuración

Sigue estos pasos para preparar todo en tu computadora.

### Paso 1: Descargar el Código

Primero, clona este repositorio en tu máquina local y navega al directorio del proyecto.

```bash
# Clona el repositorio
git clone https://github.com/AbioticBaton4/Clase_Muestra
# Entra en la carpeta del proyecto
cd CLASE_MUESTRA
```
### Paso 2: Configurar el Entorno

Ahora que tienes los archivos, elige **una** de las siguientes dos opciones para instalar las librerías necesarias.

#### Opción A: Usando Conda (Recomendado)

Este método instalará la **versión correcta de Python** y todas las librerías automáticamente.

```bash
# Crea el entorno llamado 'clase_muestra' a partir del archivo
conda env create -f environment.yml

# Activa el entorno recién creado
conda activate clase_muestra_env
```

#### Opción B: Usando pip y Entorno Virtual

Este método usa tu instalación local de Python (asegúrate que sea 3.8+).

```bash
# Crea el entorno virtual (puedes llamarlo 'venv')
python3 -m venv venv

# Actívalo
# En Windows:
.\venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instala los paquetes requeridos
pip install -r requirements.txt
```

¡Y listo! Tu entorno ya está configurado.

## ▶️ Uso

Con tu entorno (`conda` o `venv`) activado, ya puedes ejecutar el script principal o abrir el proyecto en VS Code.

```bash
# Para ejecutar un script desde la terminal
python nombre_del_script_principal.py

# Para abrir el proyecto en VS Code
code .
```