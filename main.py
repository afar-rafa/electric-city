import logging

from classes.simulacion import Simulacion
from helpers.constants import LOG_LEVEL

logger = logging.getLogger(__name__)
logging.basicConfig(
    encoding="utf-8", level=LOG_LEVEL, format="[%(levelname)s]\t%(message)s"
)
POTENCIAS_CSV = "potencia_consumida.csv"

# Esto es para repetir la misma ejecución random
s = Simulacion(
    "Super City",
    vehiculos_por_edificio=3,
    archivo_potencias=POTENCIAS_CSV,
)

s.empezar()
