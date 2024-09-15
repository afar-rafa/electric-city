import math
import os
import random
import sys

from dotenv import dotenv_values
import numpy as np


# ------------------- Constantes Simulacion -------------------
# Obtener la carpeta en donde se ejecutó main.py
script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)

# Cargar variables desde el .env
config = dotenv_values(f"{script_dir}/.env")
# usar la carpeta para encontrar el input
POTENCIAS_CSV = f"{script_dir}/potencia_consumida.csv"

# Tiempo en minutos que avanza entre cada ciclo de tiempo
MINS_POR_CICLO = int(config.get("MINS_POR_CICLO", 15))
LOG_LEVEL = config.get("LOG_LEVEL", "INFO")
SIMULAR_FIFO = bool(config.get("SIMULAR_FIFO", True))
SIMULAR_INTELIGENTE = bool(config.get("SIMULAR_INTELIGENTE", True))

# Cambiar seed para obtener otra simulación aleatoria
SEED = int(config.get("SEED", 0))
np.random.seed(SEED)
random.seed(SEED)

# ------------------- Constantes Edificios --------------------
VEHICULOS_POR_EDIFICIO = int(config.get("VEHICULOS_POR_EDIFICIO", 4))
MAX_VEHICULOS_EN_CARGA = int(config.get("MAX_VEHICULOS_EN_CARGA", 1))
POTENCIA_DECLARADA = int(float(config.get("POTENCIA_DECLARADA", 25000)))
POTENCIA_CARGADORES = int(config.get("POTENCIA_CARGADORES", 7))
TOPE_TIEMPO_DE_MANEJO = int(config.get("TOPE_TIEMPO_DE_MANEJO", 3 * 60))

INICIO_HORARIO_FALLA = config.get("INICIO_HORARIO_FALLA", "15:00")
FINAL_HORARIO_FALLA = config.get("FINAL_HORARIO_FALLA", "20:00")

# ------------------- Constantes Vehiculos --------------------
CANT_SALIDAS = int(config.get("CANT_SALIDAS", 3))

# AVG de autos
MAX_BATERIA_AVG = float(config.get("MAX_BATERIA_AVG", 82.3))
MAX_BATERIA_STD2 = float(config.get("MAX_BATERIA_STD2", 28.67))
RENDIMIENTO_AVG = float(config.get("RENDIMIENTO_AVG", 5.97))
RENDIMIENTO_STD2 = float(config.get("RENDIMIENTO_STD2", 1.16))

MAX_BATERIA_STD = math.sqrt(MAX_BATERIA_STD2)  # kWh
RENDIMIENTO_STD = math.sqrt(RENDIMIENTO_STD2)  # km/kWh

# TODO: Falta logica para estas variables
# MIN_SALIDAS = 1
# MAX_SALIDAS = 3
