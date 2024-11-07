import datetime
from functools import cache
import logging
import math
from random import randrange
from typing import List, Tuple

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

        # obtener salidas para el dia
        t = Timer()
        primera_salida = get_rand_time(t.new_time(c.HORA_PRIMERA_SALIDA))
        ultimo_regreso = get_rand_time(t.new_time(c.HORA_ULTIMO_REGRESO))

        if c.MIN_SALIDAS and c.MAX_SALIDAS and c.MIN_SALIDAS <= c.MAX_SALIDAS:
            cant_salidas = randrange(c.MIN_SALIDAS, c.MAX_SALIDAS + 1)
            logger.warning(f"{self}: Usando cant de salidas seteada de {cant_salidas}")
        else:
            cant_salidas = c.CANT_SALIDAS
            logger.warning(f"{self}: Usando cant de salidas fija de {cant_salidas}")

        self.salidas: List[Tuple[datetime.datetime, datetime.datetime]] = (
            salidas_random(
                cant=cant_salidas,
                desde=primera_salida,
                hasta=ultimo_regreso,
            )
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

        self.velocidad_promedio = c.VELOCIDAD_PROMEDIO

    def consumo_de_viaje(self, velocidad: int, minutos: int) -> float:
        distancia = velocidad * minutos / 60  # km
        return distancia / self.rendimiento  # km / km/kWh = kWh

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
        valor a usar al ordenar los vehículos en un edificio

        actualmente es el porcentaje de bateria que necesita para realizar todos sus viajes
        """
        prioridad = self.gasto_total_del_dia - self.bateria / self.max_bateria

        logger.info(
            f"{self.edificio} - {self}: [gasto_restante={self.gasto_total_del_dia:.1f} - bateria={self.bateria:.1f} = prioridad={prioridad:.1f}]"
        )
        return prioridad

    def gasto_de_viaje(
        self,
        t_inicio: datetime.datetime,
        t_final: datetime.datetime,
    ) -> float:
        """
        Gasto de energia en KWh para un viaje en un tiempo determinado
        topando el tiempo de manejo a un maximo de minutos
        (usado para calcular el gasto cuando los autos salen del edificio)
        """
        total_minutos = (t_final - t_inicio).total_seconds() / 60

        # limitar las horas de viaje
        total_minutos = min(total_minutos, c.TOPE_TIEMPO_DE_MANEJO)

        return self.consumo_de_viaje(self.velocidad_promedio, minutos=total_minutos)

    @property
    def gasto_sgte_salida(self) -> float:
        salida, llegada = self.salidas[self.siguiente_salida]
        return self.gasto_de_viaje(salida, llegada)

    @property
    @cache
    def gasto_total_del_dia(self) -> float:
        """
        Total de % de bateria que se requiere diariamente
        incluyendo la holgura de alta demanda
        """
        gasto = 0

        # total de KWh que se consume en un dia
        for s in self.salidas:
            gasto += self.gasto_de_viaje(s[0], s[1])

        logger.debug(f"{self.edificio}: {self} - Gasto total del dia [gasto=%.2f%%, holgura=%.2f%%]", gasto/self.max_bateria, c.HOLGURA_ALTA_DEMANDA/100)

        # retornar gasto en relación a la bateria total
        # (agregando la holgura de alta demanda)
        return (gasto / self.max_bateria) + (c.HOLGURA_ALTA_DEMANDA / 100)

    def esta_manejando(self, t: datetime.datetime) -> bool:
        salida, llegada = self.salidas[self.siguiente_salida]
        distancia_t = distancia_en_minutos(salida, llegada)

        logger.info(
            f"{self.edificio}: {self} - "
            f"esta_manejando [salida={salida.strftime('%H:%M')}, llegada={llegada.strftime('%H:%M')}, {distancia_t=}]"
        )

        # si el viaje dura 3 horas o menos, linealmente
        if c.TOPE_TIEMPO_DE_MANEJO <= distancia_t:
            tope_de_manejo = datetime.timedelta(minutes=c.TOPE_TIEMPO_DE_MANEJO / 2)

            if (salida + tope_de_manejo).time() <= t.time() <= (llegada - tope_de_manejo).time():
                logger.info(f"{self.edificio}: {self} - no esta_manejando [False]")
                return False

        logger.info(f"{self.edificio}: {self} - esta_manejando [True]")
        return True

    @property
    def necesita_cargarse(self) -> bool:
        """
        Revisa si tiene suficiente para funcionar durante el día
        """
        necesita_carga = self.bateria < self.gasto_total_del_dia
        logger.debug(
            f"{self}: necesita_cargarse? [bateria={self.bateria:.2f} < {self.gasto_total_del_dia:.2f}] = {necesita_carga}"
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
        # agregar la bateria
        self.bateria += energia
        # si la bateria esta llena, no se puede cargar mas
        self.bateria = min(self.bateria, self.max_bateria)
        logger.debug(
            f"{self.edificio}: {self} carga energia [bateria={self.bateria:.2f}]"
        )

        # tambien guardar la carga en potencia_usada_por_autos del edificio
        self.edificio.potencia_usada_por_autos += energia

    def actualizar_status(self, t: datetime.datetime) -> None:
        """
        self.necesita_carga:  si tiene suficiente para su sgte viaje
        self.en_el_edificio:  si esta en el edificio en el tiempo t
        """
        # Revisar si tiene suficiente para su siguiente viaje
        self.necesita_carga = self.necesita_cargarse

        # Revisar si está en el edificio
        salida, llegada = self.salidas[self.siguiente_salida]
        s = salida.time()
        l = llegada.time()
        t_t = t.time()
        logger.debug(
            f"%s: actualizar_status %s <= %s <= %s = %s",
            self,
            s.strftime("%H:%M"),
            t_t.strftime("%H:%M"),
            l.strftime("%H:%M"),
            s <= t_t <= l,
        )

        if s <= t_t <= l:
            logger.info(f"{self}: esta fuera de {self.edificio}")

            if t_t == l:
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
