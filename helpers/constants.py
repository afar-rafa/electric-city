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

# Cargar variables desde el archivo env.txt
config = dotenv_values(f"{script_dir}/env.txt")

# usar la carpeta para encontrar el input
FILE_EXT = "csv"
POTENCIAS_CSV = f"{script_dir}/potencia_consumida.csv"

# Tiempo en minutos que avanza entre cada ciclo de tiempo
MINS_POR_CICLO = int(config.get("MINS_POR_CICLO", 15))

LOG_LEVEL = config.get("LOG_LEVEL", "INFO")
SIMULAR_FIFO = bool(int(config.get("SIMULAR_FIFO", 1)))
SIMULAR_ROUNDROBIN = bool(int(config.get("SIMULAR_ROUNDROBIN", 1)))
SIMULAR_INTELIGENTE = bool(int(config.get("SIMULAR_INTELIGENTE", 1)))

# Cambiar seed para obtener otra simulación aleatoria
SEED = int(config.get("SEED", 0))
np.random.seed(SEED)
random.seed(SEED)

# ------------------- Constantes Edificios --------------------
VEHÍCULOS_POR_EDIFICIO = int(config.get("VEHÍCULOS_POR_EDIFICIO", 5))
POTENCIA_DECLARADA = int(float(config.get("POTENCIA_DECLARADA", 25000)))
POT_DISPONIBLE_MINIMA = int(config.get("POT_DISPONIBLE_MINIMA", 30))

LIMITAR_CARGADORES = bool(int(config.get("LIMITAR_CARGADORES", 1)))
TOPE_DE_CARGADORES = int(config.get("TOPE_DE_CARGADORES", 2))
POTENCIA_MIN_CARGADORES = float(config.get("POTENCIA_MIN_CARGADORES", 2.2))
POTENCIA_CARGADORES = float(config.get("POTENCIA_CARGADORES", 7.4))
TOPE_TIEMPO_DE_MANEJO = int(config.get("TOPE_TIEMPO_DE_MANEJO", 3 * 60))

# Periodos de falla reducen la potencia disponible a un 10%
HAY_FALLA = bool(int(config.get("HAY_FALLA", 0)))
INICIO_HORARIO_FALLA = config.get("INICIO_HORARIO_FALLA", "18:00")
FINAL_HORARIO_FALLA = config.get("FINAL_HORARIO_FALLA", "20:00")
REDUCCION_EN_FALLA = float(config.get("REDUCCION_EN_FALLA", 10))

# ------------------- Constantes vehículos --------------------
VELOCIDAD_PROMEDIO = int(config.get("VELOCIDAD_PROMEDIO", 50))  # KM/h
CANT_SALIDAS = int(config.get("CANT_SALIDAS", 3))

HORA_PRIMERA_SALIDA = "07:30"  # 07:30 +/- 45 mins
HORA_ULTIMO_REGRESO = "21:00"  # 21:00 +/- 45 mins
# Cant de salidas entre ambos tiempos
MIN_SALIDAS = int(config.get("MIN_SALIDAS", 1))
MAX_SALIDAS = int(config.get("MAX_SALIDAS", 3))

# ----- Promedios y varianzas de valores aleatorios -----
# Bateria maxima
AVG_BATERIA_MAX = float(config.get("AVG_BATERIA_MAX", 82.3))
VAR_BATERIA_MAX = float(config.get("VAR_BATERIA_MAX", 28.67))
# Bateria inicial (por defecto 50% +/- 5 KW)
AVG_BATERIA_INI = float(config.get("AVG_BATERIA_INI", AVG_BATERIA_MAX / 2))
VAR_BATERIA_INI = float(config.get("VAR_BATERIA_INI", 25))
# Rendimiento
AVG_RENDIMIENTO = float(config.get("AVG_RENDIMIENTO", 5.97))
VAR_RENDIMIENTO = float(config.get("VAR_RENDIMIENTO", 1.16))
