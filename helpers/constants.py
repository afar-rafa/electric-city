import math

# ------------------- Constantes Simulacion -------------------
# Tiempo en minutos que avanza entre cada ciclo de tiempo
MINS_POR_CICLO = 15
LOG_LEVEL = "INFO"

# ------------------- Constantes Edificios --------------------
MAX_VEHICULOS_EN_CARGA = 3
POTENCIA_DECLARADA = 250000  # KW
POTENCIA_CARGADORES = 7  # KWh

# ------------------- Constantes Vehiculos --------------------
# AVG de autos
MAX_BATERIA_AVG = 82.3              # kWh
MAX_BATERIA_STD = math.sqrt(28.67)  # kWh
RENDIMIENTO_AVG = 5.97              # km/kWh
RENDIMIENTO_STD = math.sqrt(1.16)   # km/kWh

# TODO: Falta logica para estas variables
CANT_SALIDAS = 3
# MIN_SALIDAS = 1
# MAX_SALIDAS = 3
