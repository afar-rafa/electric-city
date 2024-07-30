import logging
import random
from classes.models import Simulacion
from helpers.constants import LOG_LEVEL

import numpy as np

logger = logging.getLogger(__name__)
logging.basicConfig(
    encoding="utf-8", level=LOG_LEVEL, format="[%(levelname)s]\t%(message)s"
)
POTENCIAS_CSV = "potencia_consumida.csv"

# Esto es para repetir la misma ejecución random
SEED = 2
np.random.seed(SEED)
random.seed(SEED)

s = Simulacion(
    "Super City",
    vehiculos_por_edificio=7,
    archivo_potencias=POTENCIAS_CSV,
)

s.empezar()
