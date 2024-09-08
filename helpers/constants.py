import math
import os
import random
import sys

import numpy as np

# ------------------- Constantes Simulacion -------------------
# Obtener la carpeta en donde se ejecutó main.py
script_path = os.path.abspath(sys.argv[0])
script_dir = os.path.dirname(script_path)
# usar la carpeta para encontrar el input
POTENCIAS_CSV = f"{script_dir}/potencia_consumida.csv"

# Tiempo en minutos que avanza entre cada ciclo de tiempo
MINS_POR_CICLO = 15
LOG_LEVEL = "INFO"
SIMULAR_FIFO = True
SIMULAR_INTELIGENTE = True

# Cambiar seed para obtener otra simulación aleatoria
SEED = 20
np.random.seed(SEED)
random.seed(SEED)

# ------------------- Constantes Edificios --------------------
VEHICULOS_POR_EDIFICIO = 4
MAX_VEHICULOS_EN_CARGA = 1  # (Opcional)
POTENCIA_DECLARADA = 25000  # KW * 10%
POTENCIA_CARGADORES = 7  # KWh
TOPE_TIEMPO_DE_MANEJO = 3 * 60 # 3 horas max manejando por viaje
# HORARIO_DE_FALLA = ('15:00', '20:00')

# ------------------- Constantes Vehiculos --------------------
CANT_SALIDAS = 3
# AVG de autos
MAX_BATERIA_AVG = 82.3  # kWh
MAX_BATERIA_STD = math.sqrt(28.67)  # kWh
RENDIMIENTO_AVG = 5.97  # km/kWh
RENDIMIENTO_STD = math.sqrt(1.16)  # km/kWh

# TODO: Falta logica para estas variables
# MIN_SALIDAS = 1
# MAX_SALIDAS = 3
