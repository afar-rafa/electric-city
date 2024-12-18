import logging

from classes.simulacion import Simulacion
from helpers.constants import INPUT_FILE, LOG_LEVEL

logger = logging.getLogger(__name__)
logging.basicConfig(
    encoding="utf-8", level=LOG_LEVEL, format="[%(levelname)s]\t%(message)s"
)

# Esto es para repetir la misma ejecución random
s = Simulacion(
    "Super City",
    archivo_potencias=INPUT_FILE,
)

s.empezar()
