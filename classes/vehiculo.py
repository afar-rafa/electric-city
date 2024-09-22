import datetime
import logging
import math
from random import randrange

import helpers.constants as c
from classes.timer import Timer
from helpers.utils import (
    distancia_en_minutos,
    get_rand_normal,
    get_rand_time,
    salidas_random,
)

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
        self.tiempo_en_espera = 0

        # obtener salidas para el dia
        primera_salida = get_rand_time(Timer.new_time(c.HORA_PRIMERA_SALIDA))
        ultimo_regreso = get_rand_time(Timer.new_time(c.HORA_ULTIMO_REGRESO))

        cant_salidas = 3
        if c.MIN_SALIDAS and c.MAX_SALIDAS and c.MIN_SALIDAS <= c.MAX_SALIDAS:
            cant_salidas = randrange(c.MIN_SALIDAS, c.MAX_SALIDAS + 1)

        self.salidas = salidas_random(
            cant=cant_salidas,
            desde=primera_salida,
            hasta=ultimo_regreso,
        )
        self.siguiente_salida = 0  # indice

        # ------------------------ parametros ------------------------
        std_b_max = math.sqrt(c.VAR_BATERIA_MAX)
        self.max_bateria = get_rand_normal(c.AVG_BATERIA_MAX, std_b_max)

        # Cuanto tiene la bateria inicialmente (y que no sobrepase el limite)
        std_b_ini = math.sqrt(c.VAR_BATERIA_INI)
        self.bateria = get_rand_normal(c.AVG_BATERIA_INI, std_b_ini)
        self.bateria = min(self.bateria, self.max_bateria)

        # rendimiento (KM/KWh) y equivalente en consumo (KWh/KM)
        std_r = math.sqrt(c.VAR_RENDIMIENTO)
        self.rendimiento = get_rand_normal(c.AVG_RENDIMIENTO, std_r)
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
        self.bateria = max(self.bateria, 0)

    @property
    def prioridad(self) -> float:
        """
        valor a usar al ordenar los vehiculos en un edificio
        """
        prioridad = self.gasto_restante_dia - self.bateria

        logger.info(
            f"{self.edificio}: {self} -- g={self.gasto_restante_dia:.2f} - b={self.bateria:.2f} = p={prioridad:.2f}"
        )
        return prioridad

    def gasto_de_viaje(
        self,
        t_inicio: datetime.datetime,
        t_final: datetime.datetime,
    ) -> float:
        total_minutos = (t_final - t_inicio).total_seconds() / 60
        # limitar las horas de viaje
        total_minutos = min(total_minutos, c.TOPE_TIEMPO_DE_MANEJO)

        return self.consumo_de_viaje(self.velocidad_promedio, minutos=total_minutos)

    @property
    def gasto_sgte_salida(self) -> float:
        salida, llegada = self.salidas[self.siguiente_salida]
        return self.gasto_de_viaje(salida, llegada)

    @property
    def gasto_restante_dia(self) -> float:
        """
        Total de viajes que le quedan en el día
        """
        gasto = 0
        salidas_restantes = self.salidas[self.siguiente_salida :]
        logger.debug(
            f"{self.edificio}: {self} - Revisando salidas restantes {salidas_restantes}"
        )

        for s in salidas_restantes:
            gasto += self.gasto_de_viaje(s[0], s[1])

        logger.debug(f"{self.edificio}: {self} - Gasto calculado [{gasto=}]")
        return gasto

    def esta_manejando(self, t: datetime.time) -> bool:
        salida, llegada = self.salidas[self.siguiente_salida]

        # si el viaje dura menos de 3 horas, linealmente
        if distancia_en_minutos(salida, llegada) < c.TOPE_TIEMPO_DE_MANEJO:
            return True

        elif t <= salida + datetime.timedelta(hours=1, minutes=30):
            return True

        elif t >= llegada - datetime.timedelta(hours=1, minutes=30):
            return True

        return False

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
        self.tiempo_en_espera = 0
        self.bateria += energia
        self.bateria = min(self.bateria, self.max_bateria)
        logger.debug(
            f"{self.edificio}: {self} carga energia [bateria={self.bateria:.2f}]"
        )

    def actualizar_status(self, t: datetime.time) -> None:
        """
        self.necesita_carga:  si tiene suficiente para su sgte viaje
        self.en_el_edificio:  si esta en el edificio en el tiempo t
        """
        # Revisar si tiene suficiente para su siguiente viaje
        self.necesita_carga = self.necesita_cargarse

        # agrega tiempo en espera de cada ciclo
        self.tiempo_en_espera += c.MINS_POR_CICLO

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

        logger.debug(f"{self}: esta dentro de {self.edificio}")
        self.en_el_edificio = True

    ############################################################
    # Helper tools
    ############################################################
    def __repr__(self) -> str:
        return self.nombre

    @property
    def salidas_str(self):
        return [(s.strftime("%H:%M"), e.strftime("%H:%M")) for s, e in self.salidas]
