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


class Edificio:
    """
    Clase principal para crear un edificio.

    Al momento de crearse le debes pasar cuántos vehiculos
    quieres que tenga:

    EJ: crear un edificio con 10 autos:

    ```
    b = Edificio(
        nombre="Edificio FIFO",
        cant_vehiculos=10,
    )
    ```
    """

    def __init__(
        self,
        nombre: str,
        cant_vehiculos: int,
    ):
        self.nombre = nombre

        # Potencia total disponible del edificio
        self.potencia_declarada = c.POTENCIA_DECLARADA

        # potencia de los cargadores de Vehiculos
        self.potencia_cargadores = c.POTENCIA_CARGADORES

        # potencia disponible, calculada en todo momento
        self.potencia_disponble: float | None = None

        # colas de vehiculos
        self.cola_de_espera: List[Vehiculo] = []
        self.cola_de_carga: List[Vehiculo] = []

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
    def _agregar_a_cola_de_espera(self, v: Vehiculo):
        if v not in self.cola_de_espera and v not in self.cola_de_carga:
            logger.debug(f"{v}: agregando a cola de espera")
            self.cola_de_espera.append(v)
            logger.debug(f"{v}: {self.cola_de_espera=}")

    def agregar_a_cola_de_espera(self, autos_a_cargar: List[Vehiculo]):
        # primero poner en espera los que necesitan carga para su sgte viaje
        for v in [v for v in autos_a_cargar if v.necesita_carga]:
            logger.info(
                f"%s: {v} - necesita carga [{v.bateria:.2f} < {v.gasto_sgte_salida:.2f}]",
                self,
            )
            self._agregar_a_cola_de_espera(v)

        # luego los que no estan a full
        for v in [v for v in autos_a_cargar if not v.necesita_carga]:
            logger.info(
                f"%s: {v} - no esta a full [{v.bateria:.2f} < {v.max_bateria:.2f}]",
                self,
            )
            self._agregar_a_cola_de_espera(v)

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
    def agregar_a_cola_de_carga(self, v: Vehiculo):
        if v not in self.cola_de_carga:
            logger.debug(f"{v}: agregando a cola de carga")
            self.cola_de_carga.append(v)

    def actualizar_cola_de_carga(self):
        while self.cola_de_espera and not self.cola_de_carga_llena:
            self.agregar_a_cola_de_carga(
                self.siguiente_en_cola_de_espera(),
            )
        logger.info(f"%s: actualizada {self.cola_de_carga=}", self)

    def limpiar_cola_de_carga(self):
        """
        Quita los vehiculos que ya estan a full carga
        """
        self.cola_de_carga = [v for v in self.cola_de_carga if v.necesita_carga]

    @property
    def cola_de_carga_llena(self):
        return len(self.cola_de_carga) >= c.MAX_VEHICULOS_EN_CARGA

    @property
    def energia_a_cargar(self) -> float:
        return self.potencia_cargadores * c.MINS_POR_CICLO / 60  # KWmin

    def cargar_vehiculos(self):
        """
        A cada vehiculo le suma:
        E = E + (Potencia_cargador * paso_tiempo)
        """
        carga = self.energia_a_cargar
        for vehiculo in self.cola_de_carga:
            logger.debug(f"{vehiculo}: cargando con {carga}")
            vehiculo.cargar(carga)

    def sacar_de_cola_de_carga(self, v: Vehiculo):
        if v in self.cola_de_carga:
            logger.debug(f"{v}: sacando de cola de carga")
            self.cola_de_carga.remove(v)

    @property
    def bateria_de_vehiculos(self):
        return [float(np.round(v.bateria, 2)) for v in self.vehiculos]

    ############################################################
    # Simular paso del tiempo
    ############################################################
    def simular_ciclo(
        self,
        t: datetime.time,
        consumo: str,
    ):
        self.actualizar_potencia_disponble(consumo)

        # los esto es para separar aquellos que necesitan carga para
        # su siguiente viaje y aquellos que solo no están a 100%
        autos_a_cargar: List[Vehiculo] = []

        for v in self.vehiculos:
            logger.debug("%s: revisando %s", self, v)
            v.actualizar_status(t)

            # si esta fuera, descontarle bateria segun corresponda
            if not v.en_el_edificio:
                # sacarlo de las colas
                self.sacar_de_cola_de_espera(v)
                self.sacar_de_cola_de_carga(v)
                v.viajar()

            # si esta en el edificio, cargarlo si es necesario
            else:
                # agregar los vehiculos que no estan a full
                if not v.cargado_full:
                    autos_a_cargar.append(v)

        # pasar a cola de espera los autos que necesiten carga
        logger.debug(f"%s: {autos_a_cargar=}", self)
        self.agregar_a_cola_de_espera(autos_a_cargar)

        logger.info(f"%s: {self.cola_de_espera=}", self)

        # agregar vehiculos a cola de carga si se puede
        self.actualizar_cola_de_carga()

        # cargar vehiculos en cola de carga
        self.cargar_vehiculos()

        # sacar los que quedaron ok
        self.limpiar_cola_de_carga()

        logger.info(f"{self}: finalmente {self.cola_de_carga=}")

    ############################################################
    # Helper tools
    ############################################################
    def __repr__(self) -> str:
        return self.nombre


class EdificioFIFO(Edificio):
    ############################################################
    # Cola de espera
    ############################################################
    # def agregar_a_cola_de_espera(self, v: Vehiculo):
    #     if v not in self.cola_de_espera and v not in self.cola_de_carga:
    #         logger.debug(f"{v}: agregando a cola de espera")
    #         self.cola_de_espera.append(v)
    #         logger.debug(f"{v}: {self.cola_de_espera=}")

    # def siguiente_en_cola_de_espera(self) -> Vehiculo:
    #     return self.cola_de_espera.pop(0)
    pass


class Simulacion:
    def __init__(
        self,
        nombre: str,
        vehiculos_por_edificio: int,
        archivo_potencias: str,
    ):
        self.nombre = nombre

        # base de datos para importar/exportar datos
        self.db = DB()
        # timer para manejar tiempos
        self.timer = Timer()

        # sacar del header los nombres de cada edificio
        csv_edificios = self.db.headers_de_csv(nombre=archivo_potencias)[1:]

        # revisar que los numeros sean razonables
        if not csv_edificios:
            raise ValueError(f"Cantidad invalida de edificios [{csv_edificios=}]")

        # crear los efificios con sus respectivos vehiculos
        self.edificios: List[Edificio] = [
            EdificioFIFO(
                nombre=e,
                cant_vehiculos=vehiculos_por_edificio,
            )
            for e in csv_edificios
        ]

    def empezar(self):
        # Crea los archivos para cada edificio
        self.db.crear_archivo_de_edificios(self.edificios)

        # mostrar datos de cada vehiculo en los edificios
        for e in self.edificios:
            for v in e.vehiculos:
                logger.info(f"{e} - {v}: {v.max_bateria=}")
                logger.info(f"{e} - {v}: salidas={v.salidas_str}")

        # Inicia la simulacion
        for tiempo, *consumos in self.db.leer_csv("potencia_consumida.csv"):
            # saltar los headers
            if tiempo == "Tiempo":
                continue

            t = self.timer.set_hh_mm(tiempo)
            logger.info(f"Simulacion: t={t.strftime('%H:%M')}")

            for i, e in enumerate(self.edificios):
                e.simular_ciclo(t, consumo=consumos[i])

                # exportar el minuto actual a un .csv
                self.db.guardar_estado_de_edificio(
                    tiempo=self.timer.actual_str,
                    edificio=e,
                )

            # # uncomment this for a step by step execution
            # input("PRESS ENTER TO CONTINUE, CTRL+D TO EXIT")
