import logging
from classes.models import Simulacion
from helpers.constants import LOG_LEVEL

logger = logging.getLogger(__name__)
logging.basicConfig(
    encoding="utf-8", level=LOG_LEVEL, format="[%(levelname)s]\t%(message)s"
)

s = Simulacion(
    "Super City",
    vehiculos_por_edificio=5,
)

s.empezar()
