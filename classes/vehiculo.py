import datetime
import logging

import helpers.constants as c
from classes.timer import Timer
from helpers.utils import get_rand_normal, salidas_random

logger = logging.getLogger(__name__)


class Vehiculo:
    """
    Clase principal para crear un vehiculo electrico.
    """

    def __init__(self, nombre: str):
        """
        Cada vehiculo es creado con sus variables ya definidas
        usando la funcion normal que esta en utils
        y las constantes de mas arriba
        """
        self.nombre = nombre

        # se le asigna un edificio cuando son creados en uno
        self.edificio = None
        self.en_el_edificio = True
        self.necesita_carga = None

        # obtener salidas para el dia
        self.salidas = salidas_random(
            cant=c.CANT_SALIDAS,
            desde=Timer.new_time("09:00"),
            hasta=Timer.new_time("21:00"),
        )
        self.siguiente_salida = 0  # indice

        # ------------------------ parametros ------------------------
        self.max_bateria = get_rand_normal(c.MAX_BATERIA_AVG, c.MAX_BATERIA_STD)

        # Cuanto tiene la bateria inicialmente (y que no sobrepase el limite)
        self.bateria = get_rand_normal(c.MAX_BATERIA_AVG / 2, c.MAX_BATERIA_STD)
        self.bateria = min(self.bateria, self.max_bateria)

        # rendimiento en KM/KWh
        self.rendimiento = get_rand_normal(c.RENDIMIENTO_AVG, c.RENDIMIENTO_STD)
        # consumo en KWh/KM
        self.consumo = 1 / self.rendimiento

        self.velocidad_promedio = 50  # KM/h

    def consumo_de_viaje(self, velocidad: int, minutos: int) -> float:
        return self.consumo * velocidad * minutos / 60  # KW/min

    def viajar(self):
        """
        Gasta energia segun consumo, velocidad promedio y tiempo
        """
        gasto = self.consumo_de_viaje(self.velocidad_promedio, c.MINS_POR_CICLO)
        logger.info(f"{self} perdio bateria [{gasto=:.2f}]")

        self.bateria -= gasto

        # que no baje de 0
        self.bateria = max(self.bateria, -5)

    @property
    def gasto_sgte_salida(self) -> float:
        salida, llegada = self.salidas[self.siguiente_salida]
        return self.consumo_de_viaje(
            self.velocidad_promedio, minutos=(llegada - salida).total_seconds() / 60
        )

    @property
    def necesita_cargarse(self) -> bool:
        """
        Revisa si tiene suficiente para su sgte viaje
        """
        necesita_carga = self.bateria < self.gasto_sgte_salida
        logger.debug(
            f"{self}: necesita_cargarse? [bateria={self.bateria:.2f} < {self.gasto_sgte_salida:.2f}] = {necesita_carga}"
        )
        return necesita_carga

    @property
    def cargado_full(self) -> bool:
        return self.bateria == self.max_bateria

    def cargar(self, energia: int):
        """
        Carga la energia indicada.
        Si sobrepasa lo que aguanta la bateria, deja el valor de la bateria
        """
        self.bateria += energia
        self.bateria = min(self.bateria, self.max_bateria)
        logger.info(f"{self} carga energia [bateria={self.bateria:.2f}]")

    def actualizar_status(self, t: datetime.time) -> None:
        """
        self.necesita_carga:  si tiene suficiente para su sgte viaje
        self.en_el_edificio:  si esta en el edificio en el tiempo t
        """
        # Revisar si tiene suficiente para su siguiente viaje
        self.necesita_carga = self.necesita_cargarse

        # Revisar si está en el edificio
        salida, llegada = self.salidas[self.siguiente_salida]
        logger.debug(
            f"{self}: actualizar_status {salida.strftime('%H:%M')} <= {t.strftime('%H:%M')} <= {llegada.strftime('%H:%M')} = {salida <= t <= llegada}"
        )

        if salida <= t <= llegada:
            logger.info(f"{self}: esta fuera de {self.edificio}")

            if t == llegada:
                self.siguiente_salida = (self.siguiente_salida + 1) % len(self.salidas)
                logger.info(f"{self}: {self.siguiente_salida=}")

            self.en_el_edificio = False
            return

        logger.info(f"{self}: esta dentro de {self.edificio}")
        self.en_el_edificio = True

    ############################################################
    # Helper tools
    ############################################################
    def __repr__(self) -> str:
        return self.nombre

    @property
    def salidas_str(self):
        return [(s.strftime("%H:%M"), e.strftime("%H:%M")) for s, e in self.salidas]
