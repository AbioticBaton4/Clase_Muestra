from pyspark.sql import SparkSession
from pyspark.sql.functions import (col, hour, dayofweek, when, count, desc, year,
                                   avg, min as spark_min, max as spark_max, approx_count_distinct,
                                   lit, round as spark_round, unix_timestamp, log1p as spark_log1p,
                                   concat, concat_ws, sum as spark_sum, rand, row_number)
from typing import List, Dict, Any, Union, Tuple # Para anotaciones de tipo más precisas (opcional para el docstring en sí)
from pyspark.sql.types import LongType, IntegerType, DoubleType, StringType
import os
import time
import psutil
import glob
from functools import reduce # Para hacer la unión de muchos dataframes
from pyspark.sql import DataFrame, Window# Para type hinting en reduce
import traceback # Para errores
import shutil # Para eliminar archivos
from pyspark.ml import Transformer, Pipeline, PipelineModel
from pyspark.ml.feature import StringIndexer, OneHotEncoder
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
from pyspark.ml.evaluation import MulticlassClassificationEvaluator, ClusteringEvaluator
from typing import Literal
import functools
from typing import Optional
from pyspark.ml.feature import VectorAssembler
import altair as alt
import pandas as pd
import numpy as np
from pyspark.ml.functions import vector_to_array
from pyspark.ml.feature import PCA

def measure_time(func):
    '''
    Decorador para medir el tiempo de ejecución de una función dada.

    Parámetros:
    - func: función a decorar.

    Retorna:
    - Función decorada que imprime el tiempo de ejecución.
    '''
    def wrapper(*args, **kwargs):
        start = time.time()  # ⏱ Start the timer
        result = func(*args, **kwargs)  # 🔁 Execute the original function
        end = time.time()  # ⏱ Stop the timer
        print(f"{func.__name__} executed in {end - start:.4f} seconds")  # 📋 Print the elapsed time
        return result  # 🏁 Return the original result
    return wrapper  # 🔁 Return the decorated function

def adjust_cores(core_options):
    '''
    Ajusta el número de núcleos a usar en función del sistema y la opción proporcionada.

    Parámetros:
    - core_options: puede ser None, un entero, o una cadena ('auto').

    Retorna:
    - Número entero de núcleos a usar.
    '''
    max_cores = os.cpu_count()
    if core_options is None:
        return 1
    elif isinstance(core_options, int):
        return core_options if core_options <= max_cores else max_cores
    elif isinstance(core_options, str):
        if core_options == "auto":
            return max_cores // 2
        else:
            try:
                return int(core_options)
            except ValueError:
                raise ValueError("Invalid core options. Must be an integer or 'auto'.")
    else:
        raise TypeError("Invalid core options type. Must be int or str.")

@measure_time
def create_spark_session(app_name="Spark DataFrame Example", core_options=None, driver_memory = "4g", executor_memory = "4gb"):
    '''
    Crea una sesión de Spark con la configuración especificada para núcleos y memoria.

    Parámetros:
    - app_name: nombre de la aplicación Spark.
    - core_options: número de núcleos (ej: 2, 4) o 'auto'.
    - memory_options: configuración de memoria (actualmente no utilizada explícitamente para modificar config más allá de los defaults).
    - hadoop_home_path: Ruta al directorio HADOOP_HOME (ej: "C:/hadoop_utils" o "C:\\hadoop_utils").
                         Necesario principalmente en Windows.

    Retorna:
    - Objeto SparkSession creado.
    '''
    cores = adjust_cores(core_options)
    master_option = f'local[{cores}]'

    builder = SparkSession.builder \
        .master(master_option) \
        .appName(app_name) \
        .config("spark.sql.repl.eagerEval.enabled", True) \
        .config("spark.executor.memory", executor_memory) \
        .config("spark.driver.memory",driver_memory)

    spark = builder.getOrCreate()
    
    print('Spark session creada con éxito.')
    print(f"Opción Master: {master_option}") # Muestra la configuración de cores utilizada
    return spark

def read_data(spark, path):
    '''
    Lee un archivo Parquet o CSV desde la ruta especificada y lo carga en un DataFrame de Spark.

    Parámetros:
    - spark: objeto SparkSession.
    - path: ruta del archivo a leer.

    Retorna:
    - DataFrame de Spark.
    '''
    ext = os.path.splitext(path)[-1].lower()

    if ext == ".parquet":
        df = spark.read.parquet(path)
        print(f"✅ DataFrame loaded from Parquet: {path}")
    elif ext == ".csv":
        df = spark.read.option("header", True).option("inferSchema", True).csv(path)
        print(f"✅ DataFrame loaded from CSV: {path}")
    else:
        raise ValueError(f"❌ Unsupported file format: {ext}")
    return df

@measure_time
def basic_cleaning(df: DataFrame, cleaning_conditions : list) -> DataFrame:
    '''
    Realiza limpieza básica en el DataFrame.

    Parámetros:
    - df: DataFrame de entrada.
    - cleaning_conditions: lista de condiciones booleanas (tipo Spark).
    Retorna:
    - DataFrame limpio.
    '''

    print("\n--- Limpiando Datos ---")
    original_count = df.count()
    combined_condition = reduce(lambda x, y: x & y, cleaning_conditions)
    print(f"Cantidad de filas originales: {original_count}")
    df = df.filter(combined_condition)
    cleaned_count = df.count()
    print(f"✅ Limpieza básica completada.")
    print(f"Cantidad de filas después de limpieza básica: {cleaned_count} ({(cleaned_count / original_count) * 100:.2f}%)")    
    return df

def get_default_cleaning_conditions() -> List[str]:
    '''
    Devuelve una lista de condiciones de limpieza predeterminadas para el DataFrame.

    Retorna:
    - Lista de condiciones de limpieza.
    '''
    return [
        col("trip_distance") > 0,
        col("total_amount") >= 0,
        year(col("tpep_pickup_datetime")) >= 2022,
        year(col("tpep_pickup_datetime")) <= 2025
    ]

@measure_time
def adjust_features(
        df: DataFrame, 
        zone_lookup :DataFrame,
        show:bool = True,
        clean_data :bool = False,
        cleaning_conditions: Optional[List[str]] = None) -> DataFrame:
    '''
    Ajusta las características del DataFrame de acuerdo a las especificaciones dadas.
    Parámetros:
    - df: DataFrame de entrada.
    - zone_lookup: DataFrame de búsqueda de zonas (con columnas LocationID, Borough, Zone).
    - show: Si es True, muestra las primeras filas del DataFrame ajustado.
    - clean_data: Si es True, aplica limpieza básica al DataFrame.
    - cleaning_conditions: Lista de condiciones de limpieza. Si es None, se usan las condiciones predeterminadas.
    Retorna:
    - DataFrame ajustado con nuevas características.
    '''

    print("\n--- Ajustando Características del DataFrame ---")
    if clean_data:
        if cleaning_conditions is None:
            print("No se proporcionaron condiciones de limpieza. Usando condiciones predeterminadas.")
            cleaning_conditions = get_default_cleaning_conditions()
        df = basic_cleaning(df, cleaning_conditions)
        
    # Viaje a/desde Aeropuerto
    # Comunes: JFK=132, LaGuardia=138, Newark=1
    jfk_id = 132
    lga_id = 138
    print("\n--- Creando Variables de Caracterización ---")
    zone_lookup = zone_lookup.withColumnRenamed("LocationID", "ZoneID") \
                            .withColumnRenamed("Borough", "ZoneBorough") \
                            .withColumnRenamed("Zone", "ZoneName")
    
    # print("Calculando cuantiles de trip_distance para definir categorías...")
    # quantiles = df.approxQuantile("trip_distance", [0.25, 0.5, 0.75], 0.01)
    # q1 = quantiles[0]
    # median = quantiles[1]
    # q3 = quantiles[2]
    # print(f"Cuantiles de Distancia: Q1={q1:.2f}, Median={median:.2f}, Q3={q3:.2f}")

    print("Ajustando Variables...")
    df = df.join(zone_lookup.alias("PU"), col("PULocationID") == col("pu.ZoneID"), "left") \
        .withColumnRenamed("service_zone", "PU_service_zone") \
        .withColumnRenamed("ZoneBorough", "PU_ZoneBorough") \
        .withColumnRenamed("ZoneName", "PU_ZoneName") \
        .drop('ZoneID') \
        .join(zone_lookup.alias("do"), col("DOLocationID") == col("do.ZoneID"), "left") \
        .withColumnRenamed("service_zone", "DO_service_zone") \
        .withColumnRenamed("ZoneBorough", "DO_ZoneBorough") \
        .withColumnRenamed("ZoneName", "DO_ZoneName") \
        .drop('ZoneID') \
        .drop("do.ZoneID", "do.ZoneBorough", "do.ZoneName", "do.service_zone", 'ZoneID') \
        .withColumn("PU_hour", hour(col("tpep_pickup_datetime"))) \
        .withColumn("PU_hour_category",
                    when((col("PU_hour") >= 6) & (col("PU_hour") < 10), "Morning")
                    .when((col("PU_hour") >= 10) & (col("PU_hour") < 16), "Midday")
                    .when((col("PU_hour") >= 16) & (col("PU_hour") < 20), "Afternoon/Peak")
                    .when((col("PU_hour") >= 20) & (col("PU_hour") < 24), "Night")
                    .otherwise("Early Morning")) \
        .withColumn("day_of_week", dayofweek(col("tpep_pickup_datetime"))) \
        .withColumn("day_type", 
                    when((col("day_of_week") >= 2) & (col("day_of_week") <= 6), "Weekday")  # Monday to Friday
                    .otherwise("Weekend")) \
        .withColumn("is_airport_trip",
                    when((col("PULocationID") == jfk_id) | (col("DOLocationID") == jfk_id) |
                        (col("PULocationID") == lga_id) | (col("DOLocationID") == lga_id), "Yes")
                    .otherwise("No")) \
        .withColumn("payment_type",
                    when(col("payment_type") == 1, "Card")
                    .when(col("payment_type") == 2, "Cash")
                    .when(col("payment_type").isin([3, 4, 5, 6]), "Other") # Agrupar menos comunes
                    .otherwise("Unknown")) \
        .withColumn("PU_ZoneBorough",
                    when(col("PU_ZoneBorough") == "Manhattan", lit("Manhattan"))
                    .when(col("PU_ZoneBorough") == "Queens", lit("Queens"))
                    .otherwise(lit("Others"))) \
        .withColumn("trip_duration", (unix_timestamp(col("tpep_dropoff_datetime")) - unix_timestamp(col("tpep_pickup_datetime")))/ 60) \
        # .withColumn("distance_category",
        #             when(col("trip_distance") <= q1, "Short")
        #             .when((col("trip_distance") > q1) & (col("trip_distance") <= q3), "Medium")
        #             .otherwise(f"Long")) \
    print(f"✅ Variables de caracterización creadas. Total de columnas: {len(df.columns)}")
    print(f"Columnas: {df.columns}")
    #
    if show:
        print("Primeras 5 filas del DataFrame ajustado:")
        df.show(5, False)
    return df

@measure_time
def save_data(
    df: DataFrame,
    output_base_directory: str,
    parquet_filename: str,
    data_subdirectory: str = 'data' # Permite personalizar el subdirectorio 'data'
) -> str:
    """
    Guarda un DataFrame de PySpark en un archivo Parquet único de forma "atómica"
    utilizando un directorio temporal.

    Esto significa que primero escribe en un directorio temporal y luego mueve
    el archivo resultante al destino final. Esto ayuda a evitar archivos
    Parquet incompletos si el proceso falla a mitad de camino.

    Args:
        df (DataFrame): El DataFrame de PySpark a guardar.
        output_base_directory (str): El directorio base donde se creará
                                     el 'data_subdirectory' y el archivo.
        parquet_filename (str): El nombre deseado para el archivo Parquet final
                                      (e.g., 'dataset_c.parquet').
        data_subdirectory (str, optional): El nombre del subdirectorio dentro de
                                             'output_base_directory' donde se guardará
                                             el archivo. Por defecto es 'data'.

    Returns:
        str: La ruta completa al archivo Parquet final guardado.

    Raises:
        FileNotFoundError: Si el archivo part-*.parquet no se encuentra después de escribir.
        Exception: Propaga otras excepciones de PySpark o del sistema de archivos.
    """
    if not parquet_filename.endswith('.parquet'):
        print(f"Advertencia: El nombre del archivo '{parquet_filename}' no termina en .parquet. Se usará tal cual.")

    # 1. Definir rutas
    final_data_directory = os.path.join(output_base_directory, data_subdirectory)
    final_file_path = os.path.join(final_data_directory, parquet_filename)
    # Usar un nombre de directorio temporal único
    temporary_write_directory = os.path.join(final_data_directory, f"temp_{parquet_filename}_{os.urandom(4).hex()}")

    print(f"Configuración de rutas:")
    print(f"  Directorio base de salida: {output_base_directory}")
    print(f"  Subdirectorio de datos: {data_subdirectory}")
    print(f"  Directorio final de datos: {final_data_directory}")
    print(f"  Directorio temporal de escritura: {temporary_write_directory}")
    print(f"  Ruta del archivo final: {final_file_path}")

    # 2. Asegurar que el directorio de datos final exista
    os.makedirs(final_data_directory, exist_ok=True)
    print(f"Directorio de datos '{final_data_directory}' asegurado/creado.")

    try:
        # 3. Escribir el DataFrame en el directorio temporal
        print(f"Escribiendo DataFrame en directorio temporal: {temporary_write_directory}...")
        df.coalesce(1).write.mode("overwrite").parquet(temporary_write_directory)
        print(f"✅ DataFrame creado en {temporary_write_directory}")

        # 4. Encontrar el archivo part-* generado
        search_pattern = os.path.join(glob.escape(temporary_write_directory), 'part-*.parquet')
        part_files = glob.glob(search_pattern)

        if not part_files:
            raise FileNotFoundError(f"No se encontró ningún archivo part-*.parquet usando el patrón '{search_pattern}' en {temporary_write_directory}")
        if len(part_files) > 1:
            print(f"Advertencia: Se encontraron múltiples archivos part-* en {temporary_write_directory}. Se usará el primero: {part_files}")

        source_part_file = part_files[0]
        print(f"Archivo Parquet temporal encontrado: {source_part_file}")

        # 5. Mover y renombrar el archivo temporal a la ruta final deseada
        print(f"Moviendo y renombrando a: {final_file_path}...")
        shutil.move(source_part_file, final_file_path)
        print(f"✅ Archivo guardado como: {final_file_path}")
        return final_file_path

    except Exception as e:
        print(f"❌ Error durante el guardado del Parquet: {e}")
        raise

    finally:
        # 6. Limpiar: eliminar el directorio temporal
        if os.path.exists(temporary_write_directory):
            print(f"Eliminando directorio temporal: {temporary_write_directory}...")
            try:
                shutil.rmtree(temporary_write_directory)
                print(f"✅ Directorio temporal eliminado.")
            except Exception as e_clean:
                print(f"⚠️ Error al eliminar el directorio temporal '{temporary_write_directory}': {e_clean}")


def add_partition_keys(df, partition_cols,separator="|"):
    """
    Añade claves de partición al DataFrame.
    """
    return df.withColumn("partition_key", concat_ws(separator, *partition_cols))

# Se define una función para obtener las proporciones de los grupos de variables de caracterización
def calculate_partition_distribution(
        dataset: DataFrame,
        partition_cols: Optional[list[str]] = None,
        separator: Optional[str] = "||",
        round: int = 4,
        show_info: bool = False,
        total_records: Optional[int] = None):
    """Calcula la distribución de particiones en un DataFrame de Spark.
    Parámetros:
    - dataset: DataFrame de Spark que contiene la columna 'partition_key'.
    - partition_cols: Lista de columnas que se usarán para crear la clave de partición.
    - separator: Separador para concatenar los valores de las columnas de partición.
    - round: Número de decimales para redondear el porcentaje.
    - show_info: Si es True, muestra información sobre las particiones encontradas.
    - total_records: Número total de registros en el DataFrame. Si es None, se
        calcula automáticamente.
    Retorna:
    - DataFrame con la distribución de particiones, incluyendo el número de registros y el porcentaje
        de cada partición.
    """
    if "partition_key" not in dataset.columns:
        raise ValueError("El DataFrame debe contener una columna 'partition_key' para calcular la distribución de particiones.")

    if total_records is None:
        total_records = dataset.count()
    partition_counts = dataset.groupBy("partition_key").agg(
                                    count("*").alias("numero_registros")
                                    ).withColumn("porcentaje",
                                    spark_round((col("numero_registros") / total_records) * 100, round) # Calcula % y redondea a 4 decimales
                                    ).orderBy(desc("porcentaje"))
    if show_info:
        total_partitions = partition_counts.count()
        print(f"\nSe encontraron {total_partitions} combinaciones de partición.")
        print("Mostrando los tamaños de las particiones (ordenadas):")
        partition_counts.show(total_partitions, truncate=False)  # Muestra todas las particiones y sus tamaños
    # Muestra todas las particiones y sus tamaños
    return partition_counts

def get_percentage_for_key(
        dataset: DataFrame,
        key_to_find: str,
        total_records: Optional[int] = None,
        round_digits: int = 4) -> float:
    """
    Calcula el porcentaje de registros para una única y específica partition_key.
    Asume que el dataset ya está cacheado para un rendimiento óptimo en bucles.

    Parámetros:
    - dataset: El DataFrame de Spark (preferiblemente cacheado).
    - key_to_find: El valor específico de la 'partition_key' a buscar.
    - total_records: El conteo total de registros del DataFrame (pre-calculado).
    - round_digits: El número de decimales para el resultado.

    Retorna:
    - Un flotante que representa el porcentaje.
    """
    if total_records == 0:
        return 0.0
    elif total_records is None:
        total_records = dataset.count()

    # Acción de Spark: filtra por la clave y cuenta. Es mucho más rápido que un groupBy.
    key_count = dataset.filter(col("partition_key") == key_to_find).count()

    # El cálculo se hace en Python, es instantáneo.
    percentage = (key_count / total_records) * 100
    
    return round(percentage, round_digits)

# Se define una función optimizada para obtener las proporciones de los grupos
def calculate_partition_distribution_optimized(
        dataset: DataFrame,
        partition_cols: Optional[list[str]] = None, # Parámetro mantenido por consistencia
        separator: Optional[str] = "||", # Parámetro mantenido por consistencia
        round_digits: int = 4,
        show_info: bool = False,
        show_limit: int = 100): # Límite para el .show() para evitar OOM
    """
    Calcula la distribución de particiones en un DataFrame de Spark de forma optimizada.

    Parámetros:
    - dataset: DataFrame de Spark que contiene la columna 'partition_key'.
    - partition_cols: (Opcional) No se usa directamente en la lógica optimizada pero se mantiene.
    - separator: (Opcional) No se usa directamente en la lógica optimizada pero se mantiene.
    - round_digits: Número de decimales para redondear el porcentaje.
    - show_info: Si es True, muestra información sobre las particiones encontradas.
    - show_limit: Número máximo de filas a mostrar con .show() para proteger el driver.

    Retorna:
    - DataFrame con la distribución de particiones.
    """
    if "partition_key" not in dataset.columns:
        raise ValueError("El DataFrame debe contener una columna 'partition_key'.")

    # Paso 1: Realizar la agregación inicial (transformación)
    # Contamos los registros por cada 'partition_key'.
    partition_counts_agg = dataset.groupBy("partition_key").agg(
        count("*").alias("numero_registros")
    )

    # Paso 2: Usar una función de ventana para calcular el total sin una acción .count() previa.
    # La ventana vacía "Window.partitionBy()" aplica la agregación a todo el DataFrame.
    window_spec = Window.partitionBy()
    
    # Calculamos el total de registros y el porcentaje en una sola pasada (transformación).
    # Esto evita el costoso `dataset.count()` inicial.
    partition_distribution = partition_counts_agg.withColumn(
        "porcentaje",
        spark_round(
            (col("numero_registros") / spark_sum("numero_registros").over(window_spec)) * 100,
            round_digits
        )
    ).orderBy(desc("porcentaje"))

    # Paso 3: Usar cache() ANTES de cualquier acción para reutilizar el DataFrame calculado.
    # Esto es crucial si `show_info` es True, ya que se realizarán múltiples acciones.
    partition_distribution.cache()

    if show_info:
        # Acción 1: Contar el número de particiones únicas.
        # Gracias a .cache(), esta operación será muy rápida.
        total_partitions = partition_distribution.count()
        
        print(f"\nSe encontraron {total_partitions} combinaciones de partición.")
        print(f"Mostrando hasta {show_limit} de los tamaños de las particiones (ordenadas):")
        
        # Acción 2: Mostrar los resultados.
        # Usamos `show_limit` para evitar traer demasiados datos al driver.
        partition_distribution.show(show_limit, truncate=False)

    # Es una buena práctica liberar la memoria caché cuando ya no se necesita.
    dataset.unpersist() # Si el DataFrame original fue cacheado antes.
    # El return del DataFrame `partition_distribution` permitirá al usuario decidir
    # si quiere hacer un .unpersist() más tarde.
    
    return partition_distribution

def get_sampled_data(
    df: DataFrame,
    target_key: str,
    k: int = 1000,
    epsilon: float = 0.01,
    target_value: float = 0.5,
    seed: Optional[int] = None,
    basic_logs: bool = True,
    persist_df: bool = False
    ):
    print("\nAsignando IDs aleatorios para el muestreo...")
    total_rows = df.count()
    window_spec = Window.orderBy(rand()) if seed is None else Window.orderBy(rand(seed))
    df_with_id = df.withColumn("id", row_number().over(window_spec))
    if persist_df:
        df_with_id.persist()

    num_batches = (total_rows + k - 1) // k
    print(f"\n--- INICIANDO PROCESO DE MUESTREO ITERATIVO ---")
    print(f"Objetivo: Estabilizar el porcentaje de la partición '{target_key}'(valor: {target_value})")
    print(f"Tamaño de batch (k): {k}")
    print(f"Numero total de batches: {num_batches}")
    print(f"Umbral de convergencia (epsilon): {epsilon}%")

    convergence_log = []

    for batch_num in range(num_batches):
        start_id = (batch_num * k) + 1
        end_id = (batch_num + 1) * k

        if end_id > total_rows:
            end_id = total_rows

        print(f"\nProcesando batch {batch_num + 1}/{num_batches} (IDs {start_id} a {end_id})...")
        current_batch_df = df_with_id.filter(f"id <= {end_id}").drop("id")

        # Conteo de la partición objetivo (usualmente usando df.count() pero para evitar problemas de memoria y andar recalculando se uso el ID del final del batch) 
        
        if basic_logs:
            all_stats = None
            current_percentage = get_percentage_for_key(current_batch_df, target_key, total_records=end_id)  
        else:
            all_stats = calculate_partition_distribution_optimized(dataset=current_batch_df)
            # all_stats = calculate_partition_distribution(dataset=batch_union_df, total_records=temp_count)
            stats_row = all_stats.filter(col("partition_key") == target_key).first()['porcentaje']
            current_percentage = stats_row if stats_row is not None else 0.0

        current_stats = {
            'all_stats': all_stats,
            'percentage': current_percentage,
            'cumulative_count': end_id
            }
        
        diff = abs(current_percentage - target_value)
        print(f"Tamaño Acumulado: {end_id}")
        print(f"Nuevo Porcentaje de '{target_key}': {current_percentage:.4f}%")
        print(f"Diferencia con respecto al target: {diff:.5f}%")

        if diff <= epsilon:
            print(f"\n¡CONVERGENCIA ALCANZADA!")
            print(f"La métrica se ha estabilizado en la iteración {batch_num + 1} (diferencia < {epsilon}%).")
            convergence_log.append(current_stats)
            final_end_id = end_id
            break

        convergence_log.append(current_stats)

    # --- Resultados Finales y Limpieza ---
    print("\n\n--- PROCESO FINALIZADO ---")
    if len(convergence_log) < num_batches:
        print(f"El proceso se detuvo anticipadamente en el paso {len(convergence_log)} de {num_batches}.")
    else:
        print("El proceso completó todos los batches sin alcanzar el umbral de convergencia.")

    print("\nHistorial de convergencia del porcentaje:")
    for i, stats in enumerate(convergence_log):
        print(f"Paso {i+1} (Count: {stats['cumulative_count']}): Porcentaje de '{target_key}' = {stats['percentage']:.4f}%")

    if persist_df:
        df_with_id.unpersist()

    # --- Construcción del DataFrame Final (UNA SOLA VEZ) ---
    print(f"Construyendo el DataFrame final con IDs hasta {final_end_id}.")
    result_df = df_with_id.filter(f"id <= {final_end_id}").drop("id")

    return result_df, convergence_log

class CustomNaFillTransformer(Transformer):
    '''
    Transformer para llenar valores nulos en un DataFrame de Spark.
    Parámetros:
    - fill_map: diccionario que mapea nombres de columnas a valores de llenado.
    '''
    def __init__(self, fill_map):
        super(CustomNaFillTransformer, self).__init__()
        self.fill_map = fill_map

    def _transform(self, dataset):
        return dataset.na.fill(self.fill_map)
    
class PassengerCategorizerTransformer(Transformer):
    '''
    Transforma la columna 'passenger_count' en una categoría de pasajeros.
    
    Parámetros:
    - input_col_name: Nombre de la columna de entrada (default: "passenger_count").
    - output_col_name: Nombre de la columna de salida (default: "passenger_count_category").
    '''

    def __init__(self, input_col_name="passenger_count", output_col_name="passenger_count_category"):
        super(PassengerCategorizerTransformer, self).__init__()
        # Inicializa el Transformer
        self.input_col_name = input_col_name
        self.output_col_name = output_col_name

    def _transform(self, dataset):
        input_c = self.input_col_name
        output_c = self.output_col_name

        # Asegura de que la columna exista antes de intentar transformarla
        if input_c not in dataset.columns:
            # Lanzar un error o simplemente devuelve el dataset sin cambios
            print(f"Advertencia: La columna de entrada '{input_c}' no se encontró en el DataFrame.")
            return dataset

        return dataset.withColumn(output_c,
            when(col(input_c).isin([0, 1]), "1 Passenger")
            .when(col(input_c).isin([2, 3]), "2-3 Passengers")
            .when(col(input_c) >= 4, "4+ Passengers")
            .otherwise(col(input_c).cast(StringType()))
        )

class TipCategorizerTransformer(Transformer):
    '''
    Transforma la columna 'tip_amount' en una categoría de pasajeros.
    
    Parámetros:
    - input_col_name: Nombre de la columna de entrada (default: "tip_amount").
    - output_col_name: Nombre de la columna de salida (default: "tip_amount").
    '''

    def __init__(self, input_col_name="tip_amount", output_col_name="tip_category"):
        super(TipCategorizerTransformer, self).__init__()
        # Inicializa el Transformer
        self.input_col_name = input_col_name
        self.output_col_name = output_col_name

    def _transform(self, dataset):
        input_c = self.input_col_name
        output_c = self.output_col_name

        # Asegura de que la columna exista antes de intentar transformarla
        if input_c not in dataset.columns:
            # Lanzar un error o simplemente devuelve el dataset sin cambios
            print(f"Advertencia: La columna de entrada '{input_c}' no se encontró en el DataFrame.")
            return dataset

        return dataset.withColumn(output_c,
            when(col(input_c) == 0, 'No Tip')
            .when((col(input_c) > 0) & (col(input_c) <= 2.0), 'Low Tip')
            .when((col(input_c) > 2.0) & (col(input_c) <= 5.0), 'Medium Tip')
            .otherwise('High Tip'))

class CastTypeTransformer(Transformer):
    '''
    Transformer para aplicar log1p a columnas específicas de un DataFrame de Spark.
    Parámetros:
    - columns: lista de nombres de columnas a transformar.
    Retorna:
    - DataFrame con las columnas transformadas.
    '''
    def __init__(self, cast_dict:dict):
        super(CastTypeTransformer, self).__init__()
        self.cast_dict = cast_dict

    def _transform(self, dataset):
        for column, new_type in self.cast_dict.items():
            if column not in dataset.columns:
                raise ValueError(f"La columna '{column}' no existe en el DataFrame.")
            dataset = dataset.withColumn(column, col(column).cast(new_type))
        return dataset

class DropColumnsTransformer(Transformer):
    '''
    Transformer para eliminar columnas de un DataFrame de Spark.
    Parámetros:
    - columns_to_drop: lista de nombres de columnas a eliminar.
    Retorna:
    - DataFrame sin las columnas especificadas.
    '''
    def __init__(self, columns_to_drop):
        super(DropColumnsTransformer, self).__init__()
        self.columns_to_drop = columns_to_drop

    def _transform(self, dataset):
        return dataset.drop(*self.columns_to_drop)
    
class ConditionFilterTransformer(Transformer):
    '''
    Transformer para filtrar un DataFrame de Spark basado en una condición.
    Parámetros:
    - filter_condition_expression: expresión de condición para filtrar el DataFrame.
    Retorna:
    - DataFrame filtrado según la condición.
    '''
    def __init__(self,filter_condition_expression):
        super(ConditionFilterTransformer, self).__init__()
        if filter_condition_expression is None:
                raise ValueError("filter_condition_expression no puede ser None")
        self.filter_condition_expression = reduce(lambda x, y: x & y, filter_condition_expression)

    def _transform(self, dataset):
        # Aplicar la condición pasada al constructor
        return dataset.filter(self.filter_condition_expression)
    
class Log1Transformer(Transformer):
    '''
    Transformer para aplicar log1p a columnas específicas de un DataFrame de Spark.
    Parámetros:
    - columns: lista de nombres de columnas a transformar.
    Retorna:
    - DataFrame con las columnas transformadas.
    '''
    def __init__(self, columns):
        super(Log1Transformer, self).__init__()
        self.columns = columns

    def _transform(self, dataset):
        for col_name in self.columns:
            dataset = dataset.withColumn(col_name, spark_round(spark_log1p(col(col_name)), 2))
        return dataset
    
class DropOutliersTransformer(Transformer):
    '''
    Transformer para eliminar outliers de un DataFrame de Spark.
    Parámetros:
    - columns: lista de nombres de columnas a transformar.
    Retorna:
    - DataFrame sin los outliers.
    '''
    def __init__(self, columns):
        super(DropOutliersTransformer, self).__init__()
        self.columns = columns

    def _transform(self, dataset):
        for column in self.columns:
            # Calcular los límites inferior y superior
            q1 = dataset.approxQuantile(column, [0.25], 0.01)[0]
            q3 = dataset.approxQuantile(column, [0.75], 0.01)[0]
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            # Filtrar los outliers
            dataset = dataset.filter((col(column) >= lower_bound) & (col(column) <= upper_bound))
        return dataset
    
class SuffixRemoverTransformer(Transformer):
    '''
    Transformer para eliminar un sufijo de los nombres de las columnas de un DataFrame de Spark.
    Parámetros:
    - suffix: sufijo a eliminar.
    Retorna:
    - DataFrame con los nombres de las columnas modificados.
    '''
    def __init__(self, suffix):
        super(SuffixRemoverTransformer, self).__init__()
        self.suffix = suffix

    def _transform(self, dataset):
        new_columns = [col_name[:-len(self.suffix)] if col_name.endswith(self.suffix) else col_name for col_name in dataset.columns]
        return dataset.toDF(*new_columns)

class SuffixAdderTransformer(Transformer):
    '''
    Transformer para añadir un sufijo a los nombres de las columnas de un DataFrame de Spark.
    Parámetros:
    - suffix: sufijo a añadir.
    - columns: lista de nombres de columnas a las que se les añadirá el sufijo.
    Retorna:
    - DataFrame con los nombres de las columnas modificados.
    '''
    def __init__(self, suffix, columns:list):
        super(SuffixAdderTransformer, self).__init__()
        self.suffix = suffix
        self.columns = columns

    def _transform(self, dataset):
        new_columns = [col_name + self.suffix if col_name in self.columns else col_name for col_name in dataset.columns]
        return dataset.toDF(*new_columns)
    

def adjust_pipeline_list(pipeline_list:list) -> list:
    """
    Ajusta la lista de transformadores para evitar errores de tipo.
    """
    adjusted_list = []
    for transformer in pipeline_list:
        # Verifica si es una lista de transformadores
        if isinstance(transformer, list):
            adjusted_list.extend(transformer)
        else:
            adjusted_list.append(transformer)
    return adjusted_list

def preprocess_data(
    df_M:DataFrame,
    filter_conditions:list,
    fill_settings:dict,
    transformations_columns:dict,
    get_preprocessing_pipeline:bool = False,
    ) ->  Union[DataFrame, Tuple[DataFrame, PipelineModel]] :
    """
    Preprocesa el DataFrame df_M aplicando una serie de transformaciones y filtros.

    Args:
        df_M (DataFrame): DataFrame de entrada que contiene los datos a preprocesar
        filter_conditions (list): Lista de condiciones para filtrar el DataFrame
        fill_settings (dict): Diccionario que define cómo rellenar los valores nulos
        transformations_columns (dict): Diccionario que contiene las columnas a transformar
        get_preprocessing_pipeline (bool): Si es True, devuelve el pipeline de preprocesamiento junto con el DataFrame transformado
    Returns:
        DataFrame: DataFrame transformado después de aplicar los filtros y transformaciones
        PipelineModel: (opcional) Modelo del pipeline de preprocesamiento si get_preprocessing_pipeline es True

    """
    # Definimos los transformadores personalizados necesarios
    filter_transformer = ConditionFilterTransformer(filter_condition_expression=filter_conditions)
    na_fill_transformer = CustomNaFillTransformer(fill_map=fill_settings)
    cast_type_transformer = CastTypeTransformer(cast_dict=transformations_columns['cast_columns'])
    drop_columns_transformer = DropColumnsTransformer(columns_to_drop=transformations_columns['drop_columns'])  
    passenger_categorizer_transformer = PassengerCategorizerTransformer(input_col_name="passenger_count", output_col_name="passenger_count")
    tip_categorizer_transformer = TipCategorizerTransformer(input_col_name="tip_amount", output_col_name="tip_category")
    dropoutliers_transformer = DropOutliersTransformer(columns=transformations_columns['outliers_columns'])
    log1_transformer = Log1Transformer(transformations_columns['log1p_columns'])

    transformers_list = [
        filter_transformer, 
        na_fill_transformer,
        cast_type_transformer, 
        passenger_categorizer_transformer, 
        tip_categorizer_transformer,
        dropoutliers_transformer,
        log1_transformer, 
        drop_columns_transformer
        ]
    
    # Ajustamos la lista de transformadores si es necesario
    transformers_list = adjust_pipeline_list(transformers_list)

    # Preparamos el DataFrame aplicando la lista de transformadores
    data_preprocessing_pipeline = Pipeline(stages=transformers_list)
    pipeline_model = data_preprocessing_pipeline.fit(df_M)
    df_transformed = pipeline_model.transform(df_M)

    # Si se requiere el pipeline de preprocesamiento, lo devolvemos junto con el DataFrame transformado
    if get_preprocessing_pipeline:
        return df_transformed, pipeline_model
    # Si no se requiere el pipeline, solo devolvemos el DataFrame transformado
    else:
        return df_transformed

def transform_data(
        df:DataFrame,
        features:list[str],
        cat_cols:Optional[list[str]] = None,
        num_cols:Optional[list[str]] = None, 
        target: str | None = None,
        key = "partition_key",
        show_df:bool = False
        ) -> tuple[DataFrame, Pipeline]:
    try:
        df = df.select(key,*features,target)  if target else df.select(key,*features)
    except Exception as e:
        print(f"Error al seleccionar columnas: {e}")
        raise
    print('Ajustando el DataFrame para la transformación...')
    if cat_cols is None:
        cat_cols = [f for f in df.columns if df.schema[f].dataType == StringType() and (f not in [target, key])]
        print(f"Columnas categóricas detectadas: {cat_cols}")
    if num_cols is None:
        num_cols = [f for f in df.columns if f not in cat_cols + [target, key]]
        print(f"Columnas numéricas detectadas: {num_cols}")

    # Convertir columnas categóricas a índices
    indexers = [StringIndexer(inputCol=col, outputCol=f"{col}_index") for col in cat_cols]
    
    # Codificar las columnas categóricas
    encoders = [OneHotEncoder(inputCols=[f"{col}_index"], outputCols=[f"{col}_ohe"]) for col in cat_cols]
    
    # Ensamblar las características
    assembler = VectorAssembler(
        inputCols=[f"{col}_ohe" for col in cat_cols] + num_cols,
        outputCol="features"
    )
    
    # Transformar la columna objetivo
    if target:
        if isinstance(df.schema[target].dataType, StringType):
            # Si la columna objetivo es categórica, usar StringIndexer
            print(f"Transformando la columna objetivo '{target}' a índices...")
            target_indexer = StringIndexer(inputCol=target, outputCol="label")
            stages = indexers + encoders + [assembler, target_indexer]
        else:
            # Si la columna objetivo es numérica, simplemente renombrarla
            print(f"Renombrando la columna objetivo '{target}' a 'label'...")
            stages = indexers + encoders + [assembler]
            df = df.withColumnRenamed(target, "label")
    else:
        stages = indexers + encoders + [assembler]
    # Crear el pipeline
    pipeline = Pipeline(stages=stages)
    
    # Ajustar el pipeline al DataFrame
    model = pipeline.fit(df)
    
    # Transformar el DataFrame
    transformed_df = model.transform(df).select(key,'features','label') if target else model.transform(df).select(key,'features')

    if show_df:
        print("DataFrame transformado:")
        transformed_df.show(5, truncate=False)
    
    return transformed_df, model

def plot_target_distribution(
        df:DataFrame, 
        target:str ='label',
        title:str = 'Distribución de la Variable Objetivo',
        x_axis_title:str = 'Categoría de Propina',
        y_axis_title:str = 'Número de Viajes',
        dictionary_labels = {
        1: 'No Tip',
        2: 'Low Tip',
        0: 'Medium Tip',
        3: 'High Tip'}
        ): 
    df = df.toPandas()  # Convertir a pandas para Altair
    count_df = df[target].value_counts().reset_index()
    count_df.columns = [target, 'count']  # Renombrar las columnas para claridad

    # Reemplazar los valores de 'label' con las categorías correspondientes
    count_df[target] = count_df[target].map(dictionary_labels)

    # Crear el gráfico de barras
    bar_chart = alt.Chart(count_df).mark_bar().encode(
        y=alt.Y(f'{target}:N', title=y_axis_title, sort= '-x'),  # Ordenar por el eje X de forma descendente

        x=alt.X('count:Q', title=x_axis_title),

        # (Opcional pero recomendado) Añadir un tooltip interactivo
        tooltip=[
            alt.Tooltip(target, title='Categoría'),
            alt.Tooltip('count', title='Total Viajes')
        ],
        
        # (Opcional) Asignar un color diferente a cada barra
        color=alt.Color(f'{target}:N', legend=None) # legend=None para no mostrar la leyenda redundante

    ).properties(
        title=title,
        width=600,  # Ancho del gráfico
        height=300   # Alto del gráfico
    )# ).interactive() # Permite hacer zoom y pan en el gráfico

    # Para mostrar el gráfico
    bar_chart.show()

def adjust_split_size(train_size, test_size, variation:int = 0.04):
    """
    Ajusta el tamaño de la división entre entrenamiento y prueba.
    
    :param train_size: Tamaño original del conjunto de entrenamiento.
    :param test_size: Tamaño original del conjunto de prueba.
    :param variation: Variación permitida en el tamaño del conjunto de entrenamiento.
    :return: Nuevos tamaños ajustados para entrenamiento y prueba.
    """
    new_train_size = train_size - variation
    new_test_size = test_size + variation
    return new_train_size, new_test_size

def partition_train_test(    
    df: DataFrame,
    train_percent: float = 0.8,
    test_percent: float = 0.2,
    key: str = "partition_key",
    seed: int = 42,
    adjust_percentages: bool = True,
    variation = 0.04,
) -> tuple[DataFrame | None, DataFrame | None]:
    """
    Divide cada DataFrame en una lista en conjuntos de entrenamiento y prueba,
    luego une los resultados.

    Args:
        df: DataFrame de entrada.
        train_percent: Porcentaje para el conjunto de entrenamiento.
        test_percent: Porcentaje para el conjunto de prueba.
        seed: Semilla para la división aleatoria para reproducibilidad.
        adjust_percentages: Si es True, ajusta los porcentajes de entrenamiento y prueba.
        variation: Variación permitida en el tamaño del conjunto de entrenamiento.
    Returns:
        Una tupla (train_df, test_df).
        Puede retornar (None, None) si no hay datos para procesar.
    """

    if adjust_percentages:
        train_percent, test_percent = adjust_split_size(train_percent, test_percent, variation)

    train_data_parts = []
    test_data_parts = []
    stratum_counts = df.groupBy(key).count().distinct()
    print(f"Procesando {stratum_counts.count()} estratos únicos")
    stratum_counts_combined = df.groupBy(key).count().collect()
    for row in stratum_counts_combined:
        stratum = row[key]
        temp_df = df.filter(df[key] == stratum)
        train_df, test_df = temp_df.randomSplit([train_percent, test_percent], seed=seed)
        train_data_parts.append(train_df)
        test_data_parts.append(test_df)

    if not train_data_parts: # Implica que todas las particiones estaban vacías o la lista original estaba vacía
        print("Advertencia: No hay datos de entrenamiento para unir (todas las particiones estaban vacías o la lista inicial lo estaba).")
        # De nuevo, manejar el retorno de DataFrames vacíos con esquema o None
        return None, None

    # Unir todas las particiones de entrenamiento y prueba
    original_total_count = df.count()
    train_df = reduce(DataFrame.unionAll, train_data_parts)
    test_df = reduce(DataFrame.unionAll, test_data_parts)
    
    # Contar después de dropear
    final_train_count = train_df.count()
    final_test_count = test_df.count()
    print(f"Conteo final entrenamiento: {final_train_count} ({final_train_count/original_total_count:.0%} del total original)")
    print(f"Conteo final prueba: {final_test_count} ({final_test_count/original_total_count:.0%} del total original)")

    return train_df, test_df

def read_train_test(
        spark: SparkSession,
        train_file: str = 'data\train_test\train.parquet',
        test_file: str = 'data\train_test\test.parquet'
        ) -> tuple[DataFrame, DataFrame]:

    try:
        train_df = read_data(spark, train_file)
        test_df = read_data(spark, test_file)
    except Exception as e:
        print(f"Error cargando los datos: {e}")
        print("Verifica las rutas y el formato de los archivos.")
        spark.stop()
        exit()

    return train_df, test_df

def plot_clusters_altair(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    color_col: str,
    title: str = "Visualización de Clusters en 2D usando PCA",
    x_title: str = "Primer Componente Principal (PC1)",
    y_title: str = "Segundo Componente Principal (PC2)",
    legend_title: str = "ID del Cluster",
    width: int = 800,
    height: int = 600,
    point_size: int = 60,
    opacity: float = 0.8,
    color_scheme: str = 'rainbow',
    x_domain: Optional[List[float]] = None,
    y_domain: Optional[List[float]] = None
) -> alt.Chart:
    """
    Crea un gráfico de dispersión interactivo con Altair para visualizar clusters.

    Args:
        data (pd.DataFrame): El DataFrame de pandas que contiene los datos.
        x_col (str): El nombre de la columna para el eje X.
        y_col (str): El nombre de la columna para el eje Y.
        color_col (str): El nombre de la columna para colorear los puntos (ID del cluster).
        title (str, optional): Título principal del gráfico.
        x_title (str, optional): Título del eje X.
        y_title (str, optional): Título del eje Y.
        legend_title (str, optional): Título de la leyenda de colores.
        width (int, optional): Ancho del gráfico en píxeles.
        height (int, optional): Alto del gráfico en píxeles.
        point_size (int, optional): Tamaño de los puntos.
        opacity (float, optional): Opacidad de los puntos (de 0 a 1).
        color_scheme (str, optional): Esquema de colores de Altair.
        x_domain (List[float], optional): Rango para hacer zoom en el eje X. Ej: [-3, -1].
        y_domain (List[float], optional): Rango para hacer zoom en el eje Y. Ej: [0.5, 1.0].

    Returns:
        alt.Chart: El objeto de gráfico de Altair, listo para ser mostrado.
    """
    # Define las escalas para el zoom opcional
    x_scale = alt.Scale(domain=x_domain) if x_domain else alt.Undefined
    y_scale = alt.Scale(domain=y_domain) if y_domain else alt.Undefined

    # Construye la lista de tooltips dinámicamente
    tooltips = [
        alt.Tooltip(f'{x_col}:Q', title=x_title, format=".2f"),
        alt.Tooltip(f'{y_col}:Q', title=y_title, format=".2f"),
        alt.Tooltip(f'{color_col}:N', title=legend_title)
    ]

    chart = alt.Chart(data).mark_circle(
        size=point_size,
        opacity=opacity
    ).encode(
        x=alt.X(f'{x_col}:Q', title=x_title, scale=x_scale),
        y=alt.Y(f'{y_col}:Q', title=y_title, scale=y_scale),
        color=alt.Color(f'{color_col}:N',
            scale=alt.Scale(scheme=color_scheme),
            legend=alt.Legend(title=legend_title)
        ),
        tooltip=tooltips
    ).properties(
        title=alt.TitleParams(text=title, fontSize=16),
        width=width,
        height=height
    ).interactive()

    return chart

def get_pca_df(df, input_col:str="features", pca_col:str="pca_features", to_pandas:bool=False):
    """
    Aplica PCA al DataFrame para reducir la dimensionalidad a 2 dimensiones.
    Args:
        df (DataFrame): DataFrame de entrada con la columna de características.
        input_col (str): Nombre de la columna de entrada que contiene las características.
        pca_col (str): Nombre de la columna de salida para las características PCA.
        to_pandas (bool): Si es True, devuelve un DataFrame de pandas, si es False, devuelve un DataFrame de Spark.
    Returns:
        DataFrame: DataFrame con las características PCA reducidas a 2 dimensiones.
    """
    K= 2
    pca = PCA(k=K, inputCol=input_col, outputCol=pca_col)
    pca_model = pca.fit(df)
    df_pca = pca_model.transform(df)
    df_pca = df_pca.withColumn(pca_col, vector_to_array(col(pca_col)))
    df_pca = df_pca.select(input_col, col(pca_col)[0].alias("PC1"), col(pca_col)[1].alias("PC2"), "cluster_id")

    return df_pca if not to_pandas else df_pca.toPandas()

# Diccionario de métricas para modelos supervisados
_SUPPORTED_SUPERVISED_METRICS = {
    "accuracy": "Accuracy",
    "f1": "F1-Score",
    "weightedPrecision": "Weighted Precision",
    "weightedRecall": "Weighted Recall"
}
# Diccionario de métricas para modelos no supervisados
_SUPPORTED_UNSUPERVISED_METRICS = {
    "silhouette": "Silhouette Score",
}
# Este diccionario mapea el tipo de modelo a su respectivo diccionario de métricas.
_METRICS_BY_TYPE = {
    "supervised": _SUPPORTED_SUPERVISED_METRICS,
    "unsupervised": _SUPPORTED_UNSUPERVISED_METRICS
}

def validate_model_type(func):
    """
    Decorador que valida el parámetro 'model_type' de una función.
    """
    @functools.wraps(func) # Preserva el nombre y docstring de la función original
    def wrapper(*args, **kwargs):
        # Busca 'model_type' en los argumentos de la función
        if 'model_type' in kwargs:
            model_type = kwargs['model_type']
        else:
            # Asume que es el segundo argumento posicional (después de metrics_list)
            # NOTA: Esto se puede hacer más robusto con el módulo 'inspect'
            try:
                model_type = args[1] 
            except IndexError:
                 # Si no se encuentra, se usará el valor por defecto que ya tiene la funcion
                 # por lo que no es necesario validarlo aqui. Pasamos el control
                 pass

        if 'model_type' in locals() and model_type not in _METRICS_BY_TYPE:
             raise ValueError(
                f"El tipo de modelo '{model_type}' no es válido. "
                f"Use uno de: {list(_METRICS_BY_TYPE.keys())}"
            )
        
        return func(*args, **kwargs)
    return wrapper

def ensure_valid_metrics(func):
    """
    Decorador que valida que 'metric_names' (si se proporciona) sea una lista
    de métricas compatible con el 'model_type' pasado a la función.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        model_type = kwargs.get('model_type')
        metric_names = kwargs.get('metric_names')
        
        if not metric_names:
            # Si no hay métricas que chequear, solo validamos que el model_type exista si fue proporcionado
            if model_type and model_type not in _METRICS_BY_TYPE:
                 raise ValueError(f"El tipo de modelo '{model_type}' no es válido.")
            return func(*args, **kwargs)

        if not model_type:
            raise TypeError(f"La función '{func.__name__}' fue llamada con 'metric_names' pero sin 'model_type'.")

        # Usamos nuestra función de lógica pura.
        if not are_supported_metrics(metric_names, model_type):
            raise ValueError(
                f"La lista de métricas {metric_names} contiene valores inválidos para el modelo '{model_type}'. "
                f"Las válidas son: {list(_METRICS_BY_TYPE[model_type].keys())}"
            )
            
        return func(*args, **kwargs)
    return wrapper

@validate_model_type
def are_supported_metrics(
    metrics_list: list[str], 
    model_type: Literal["supervised", "unsupervised"] = "supervised"
) -> bool:
    """
    Verifica si TODAS las métricas en una lista son soportadas para un 
    tipo de modelo dado.

    Args:
        metrics_list (list[str]): La lista de métricas a verificar.
        model_type (str): El tipo de modelo contra el cual validar.

    Raises:
        ValueError: Si el model_type no es uno de los soportados.

    Returns:
        bool: True si todas las métricas son válidas, False en caso contrario.
    """

    supported_keys = _METRICS_BY_TYPE[model_type].keys()
    
    # 3. Realiza la comprobación UNA SOLA VEZ.
    return set(metrics_list).issubset(supported_keys)

@validate_model_type
def get_supported_metrics(
    model_type: Literal["supervised", "unsupervised"] = "supervised"
) -> list[str]:
    """
    Obtiene una lista de las métricas soportadas para un tipo de modelo dado.

    Args:
        model_type (str): El tipo de modelo ('supervised' o 'unsupervised'). 
                          Por defecto es 'supervised'.

    Raises:
        ValueError: Si el model_type no es uno de los soportados.

    Returns:
        list[str]: Una lista con los códigos de las métricas (ej. 'f1', 'silhouette').
    """
    # Lógica principal: simple, directa y escalable gracias al diccionario maestro.
    return list(_METRICS_BY_TYPE[model_type].keys())

@validate_model_type
def get_metric_name(
    metric_code: str, 
    model_type: Literal["supervised", "unsupervised"] = "supervised"
) -> str:
    """
    Obtiene el nombre legible de una métrica dada su clave y tipo de modelo.

    Args:
        metric_code (str): Código de la métrica (ej. 'f1', 'silhouette').
        model_type (str): Tipo de modelo ('supervised' o 'unsupervised'). 
                          Por defecto es 'supervised'.

    Raises:
        ValueError: Si el model_type no es uno de los soportados.

    Returns:
        Optional[str]: Nombre legible de la métrica o None si no se encuentra.
    """
    # Lógica principal: busca en el diccionario maestro.
    return _METRICS_BY_TYPE[model_type].get(metric_code, None)

@ensure_valid_metrics
def get_metrics_values(
    predictions: DataFrame,
    metric_names: list[str], 
    model_type: Literal["supervised", "unsupervised"] = "supervised",
    label_col: Optional[str] = None,
    show_metrics: bool = True,
    get_metrics: bool = True
) -> dict | None:
    """
    Obtiene un evaluador de Spark ML para una métrica específica y tipo de modelo.
    Args:
        metric_name (str): Nombre de la métrica (ej. 'f1', 'silhouette').
        model_type (str): Tipo de modelo ('supervised' o 'unsupervised'). 
                          Por defecto es 'supervised'.
        label_col (Optional[str]): Columna de etiquetas para modelos supervisados.
    Raises:
        ValueError: Si el model_type no es uno de los soportados o si la métrica no es válida.
    Returns:
        Evaluador de Spark ML correspondiente a la métrica y tipo de modelo.
    """
    metric_values = {}
    for metric_name in metric_names:
        if model_type == "supervised":
           evaluator = MulticlassClassificationEvaluator(
                labelCol=label_col, 
                predictionCol="prediction", 
                metricName=metric_name
            )
        elif model_type == "unsupervised":
            evaluator = ClusteringEvaluator(
                featuresCol="features", 
                predictionCol="cluster_id", 
                metricName=metric_name
            )
        metric_value = evaluator.evaluate(predictions)
        metric_values[metric_name] = metric_value
    
    if show_metrics:
        print("\nMétricas de clasificación:")
        supported_metrics = _METRICS_BY_TYPE[model_type]
        [print(f"{supported_metrics[metric_name]}: {value:.4f}") for metric_name, value in metric_values.items()]
    if get_metrics:
        return metric_values