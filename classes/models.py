"""
Classes

Luego de tener las constantes y "helper functions" (utils) creamos las clases
base que necesitarás para que tu memoria pueda partir: vehiculos y edificios
"""

import datetime
import logging
from queue import Queue
from typing import List, Optional

import numpy as np

from classes.database import DB
import helpers.constants as c
from classes.timer import Timer
from helpers.utils import get_hh_mm_time, get_rand_normal, salidas_random

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
        # El maximo que aguanta la bateria
        self.max_bateria = get_rand_normal(c.MAX_BATERIA_AVG, c.MAX_BATERIA_STD)
        # Cuanto tiene la bateria inicialmente (y que no sobrepase el limite)
        self.bateria = get_rand_normal(c.MAX_BATERIA_AVG / 2, c.MAX_BATERIA_STD)
        self.bateria = min(self.bateria, self.max_bateria)

        # rendimiento en KM/KWh
        self.rendimiento = get_rand_normal(c.RENDIMIENTO_AVG, c.RENDIMIENTO_STD)
        # consumo en KWh/KM
        self.consumo = 1 / self.rendimiento

        # el vehiculo parte sin un edificio asignado,
        # pero se le asigna uno cuando son creados en un edificio
        self.nombre = nombre
        self.edificio = None
        self.velocidad_promedio = 50  # KM/h

        # obtener salidas para el dia
        self.salidas = salidas_random(
            cant=3,
        )
        self.siguiente_salida = self.salidas[0]

    @property
    def consumo_mins(self) -> float:
        return self.consumo * self.velocidad_promedio / 60  # KW/min

    def cargar(self, energia: int):
        """
        Carga la energia indicada.
        Si sobrepasa lo que aguanta la bateria, deja el valor de la bateria
        """
        self.bateria += energia
        self.bateria = min(self.bateria, self.max_bateria)
        logger.info(f"{self} carga energia [bateria={self.bateria:.2f}]")

    @property
    def necesita_cargarse(self) -> bool:
        """
        TODO: Aca falta incluir logica para que revise
        si tiene suficiente para su sgte viaje
        """
        return not self.cargado_full

    @property
    def cargado_full(self) -> bool:
        return self.bateria == self.max_bateria

    def en_el_edificio(self, t: datetime.time) -> bool:
        """
        retorna true si esta en el edificio en el tiempo t
        """
        for salida, llegada in self.salidas:
            if salida <= t <= llegada:
                logger.debug(
                    f"esta fuera: {salida} <= {t} <= {llegada} = {salida <= t <= llegada}"
                )
                return False

        logger.debug(
            f"esta dentro: {salida} <= {t} <= {llegada} = {salida <= t <= llegada}"
        )
        return True

    def consumir_energia(self):
        """
        Gasta energia segun consumo * minutos
        """
        gasto = self.consumo_mins * c.MINS_POR_CICLO
        logger.info(f"{self} perdio bateria [{gasto=:.2f}]")
        self.bateria -= gasto

    ############################################################
    # Helper tools
    ############################################################
    def __repr__(self) -> str:
        return self.nombre

    @property
    def salidas_str(self):
        return [(s.strftime("%H:%M"), e.strftime("%H:%M")) for s, e in self.salidas]


class Edificio:
    """
    Clase principal para crear un edificio.

    Al momento de crearse le debes pasar cuántos vehiculos
    quieres que tenga:

    EJ: crear un edificio con 10 autos:

    ```
    b = Edificio(cant_vehiculos=10)
    ```
    """

    def __init__(
        self,
        nombre: str,
        cant_vehiculos: int,
    ):
        self.nombre = nombre

        # Potencia total disponible del edificio
        self.potencia_declarada = 250000  # KW
        # self.potencia_declarada = get_rand_normal(250000, 50000)

        # potencia de cargadores de Vehiculos
        self.potencia_cargadores = 15  # KWh
        # self.potencia_cargadores = get_rand_normal(15, 7) # KWh

        # potencia disponible, calculada en todo momento
        self.potencia_disponble: float | None = None

        # colas de vehiculos
        self.cola_de_espera: List[Vehiculo] = []
        self.cola_de_carga: List[Vehiculo] = []
        # TODO: pasar a su propia clase:
        # self.cola_de_carga = ColaFIFO()

        # crear vehiculos
        self.vehiculos: List[Vehiculo] = []
        for i in range(cant_vehiculos):
            # crear un nuevo vehiculo
            v = Vehiculo(f"Vehiculo {i + 1}")

            # asignarle este edificio
            v.edificio = self

            # y agregarlo a la lista de vehiculos
            self.vehiculos.append(v)

    def actualizar_potencia_disponble(self, consumo: str) -> None:
        """
        potencia disponble = potencia maxima - consumo
        (no puede ser negativa)

        Se asigna al edificio actual en cada ciclo de tiempo
        """
        consumo = float(consumo)
        logger.debug(
            f"{self}: actualizando potencia [declarada={self.potencia_declarada}, {consumo=}]"
        )
        self.potencia_disponble = max(self.potencia_declarada - consumo, 0)

    ############################################################
    # Cola de espera
    ############################################################
    def agregar_a_cola_de_espera(self, v: Vehiculo):
        if v not in self.cola_de_espera and v not in self.cola_de_carga:
            logger.debug(f"{v}: agregando a cola de espera")
            self.cola_de_espera.append(v)
            logger.debug(f"{v}: {self.cola_de_espera=}")

    def sacar_de_cola_de_espera(self, v: Vehiculo):
        if v in self.cola_de_espera:
            logger.debug(f"{v}: sacando de cola de espera")
            self.cola_de_espera.remove(v)
            logger.debug(f"{v}: {self.cola_de_espera=}")

    def siguiente_en_cola_de_espera(self) -> Vehiculo:
        return self.cola_de_espera.pop(0)

    ############################################################
    # Lista de carga
    ############################################################
    @property
    def cola_de_carga_llena(self):
        return len(self.cola_de_carga) >= c.MAX_VEHICULOS_EN_CARGA

    @property
    def pot_carga_mins(self) -> float:
        return self.potencia_cargadores / 60  # KWmin

    def agregar_a_cola_de_carga(self, v: Vehiculo):
        if v not in self.cola_de_carga:
            logger.debug(f"{v}: agregando a cola de carga")
            self.cola_de_carga.append(v)

    def sacar_de_cola_de_carga(self, v: Vehiculo):
        if v in self.cola_de_carga:
            logger.debug(f"{v}: sacando de cola de carga")
            self.cola_de_carga.remove(v)

    def cargar_vehiculos(self):
        """
        A cada vehiculo le suma:
        E = E + (Potencia_cargador * paso_tiempo)
        """
        carga = self.pot_carga_mins * c.MINS_POR_CICLO
        for vehiculo in self.cola_de_carga:
            logger.debug(f"{vehiculo}: cargando con {carga}")
            vehiculo.cargar(carga)

    def limpiar_cola_de_carga(self):
        """
        Quita los vehiculos que ya estan a full carga
        """
        self.cola_de_carga = [v for v in self.cola_de_carga if not v.cargado_full]

    ############################################################
    # Simular paso del tiempo
    ############################################################
    def simular_ciclo(
        self,
        t: datetime.time,
    ):
        for v in self.vehiculos:
            logger.debug("%s: revisando %s", self, v)
            # si esta fuera, descontarle bateria segun corresponda
            if not v.en_el_edificio(t):
                logger.debug(f"%s: {v} - no esta en el edificio", self)
                # sacarlo de las colas
                self.sacar_de_cola_de_espera(v)
                self.sacar_de_cola_de_carga(v)
                v.consumir_energia()

            # si esta en el edificio, cargarlo si es necesario
            else:
                logger.debug(f"%s: {v} - esta en el edificio", self)
                # agregar los vehiculos que no estan a full
                if v.necesita_cargarse:
                    logger.debug(f"%s: {v} - necesita cargarse", self)
                    self.agregar_a_cola_de_espera(v)

        # agregar vehiculos a cola de carga si se puede
        logger.debug(f"%s: {self.cola_de_espera=}", self)
        logger.debug(f"%s: inicial {self.cola_de_carga=}", self)

        while self.cola_de_espera and not self.cola_de_carga_llena:
            self.agregar_a_cola_de_carga(
                self.siguiente_en_cola_de_espera(),
            )
        logger.debug(f"%s: actualizada {self.cola_de_carga=}", self)

        # cargar vehiculos en cola de carga
        self.cargar_vehiculos()
        # sacar los que quedaron full
        self.limpiar_cola_de_carga()
        logger.debug(f"%s: final {self.cola_de_carga=}", self)

    ############################################################
    # Helper tools
    ############################################################
    def __repr__(self) -> str:
        return self.nombre


class NoBuildingsException(Exception):
    pass


POTENCIAS_CSV = "potencia_consumida.csv"


class Simulacion:
    def __init__(
        self,
        nombre: str,
        vehiculos_por_edificio: int,
    ):
        self.nombre = nombre

        # base de datos para importar/exportar datos
        self.db = DB()
        self.timer = Timer()

        # sacar del header los nombres de cada edificio
        csv_edificios = self.db.obtener_headers_de_csv(nombre=POTENCIAS_CSV)[1:]

        # revisar que los numeros sean razonables
        if not csv_edificios:
            raise ValueError(f"Cantidad invalida de edificios [{csv_edificios=}]")

        # crear los efificios con sus respectivos vehiculos
        self.edificios: List[Edificio] = [
            Edificio(
                nombre=e,
                cant_vehiculos=vehiculos_por_edificio,
            )
            for e in csv_edificios
        ]

    def empezar(self):
        # Crea los archivos para cada edificio
        [self.db.crear_archivo_de_edificio(e) for e in self.edificios]
        [
            [logger.info(f"{v}: {v.salidas_str}") for v in e.vehiculos]
            for e in self.edificios
        ]

        # Inicia la simulacion
        for tiempo, *consumos in self.db.leer_fila_de_csv("potencia_consumida.csv"):
            # saltar los headers
            if tiempo == "Tiempo":
                continue

            t = self.timer.set_hh_mm(tiempo)

            for i, e in enumerate(self.edificios):
                consumo = consumos[i]
                e.actualizar_potencia_disponble(consumo)

                e.simular_ciclo(t)

                # exportar el minuto actual a un .csv
                self.db.actualizar_estado_de_edificio(
                    tiempo=self.timer.actual_str, 
                    e=e,
                )

            last_time = t
            # stop -=1
            # if not stop:
            #     break
