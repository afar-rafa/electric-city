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
from helpers.utils import get_hh_mm_time, get_rand_normal, salidas_random

logger = logging.getLogger()

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
        self.max_bateria = get_rand_normal(c.EV_BATTERY_AVG, c.EV_BATTERY_SD)
        # Cuanto tiene la bateria inicialmente (y que no sobrepase el limite)
        self.energia = get_rand_normal(c.EV_ENERGY_AVG, c.EV_ENERGY_SD)
        self.energia = min(self.energia, self.max_bateria)

        self.rendimiento = get_rand_normal(c.EV_PERF_AVG, c.EV_PERF_SD)
        self.consumo = get_rand_normal(c.EV_CONS_AVG, c.EV_CONS_SD)

        # el vehiculo parte sin un edificio asignado,
        # pero se le asigna uno cuando son creados en un edificio
        self.nombre = nombre
        self.edificio = None

        # obtener salidas para el dia
        self.salidas = salidas_random(
            cant=3,
        )

    def cargar(self, energia: int):
        """
        Carga la energia indicada.
        Si sobrepasa lo que aguanta la bateria, deja el valor de la bateria
        """
        self.energia += energia
        self.energia = min(self.energia, self.max_bateria)

    @property
    def necesita_cargarse(self) -> bool:
        """
        TODO: Aca falta incluir logica para que revise
        si tiene suficiente para su sgte viaje
        """
        return not self.cargado_full

    @property
    def cargado_full(self) -> bool:
        return self.energia == self.max_bateria

    def en_el_edificio(self, t: datetime.time) -> bool:
        """
        retorna true si esta en el edificio en el tiempo t
        """
        for salida, llegada in self.salidas:
            if salida <= t <= llegada:
                print(f"esta fuera: {salida} <= {t} <= {llegada} = {salida <= t <= llegada}")
                return False
        
        print(f"esta dentro: {salida} <= {t} <= {llegada} = {salida <= t <= llegada}")
        return True

    def consumir_energia(self):
        """
        Gasta energia segun consumo * minutos
        """
        gasto = self.consumo  # * c.MINS_POR_CICLO
        print(f"{self} perdio bateria {gasto=}")
        self.energia -= gasto

    ############################################################
    # Helper tools
    ############################################################
    def __str__(self) -> str:
        return self.nombre

    @property
    def salidas_str(self):
        return [
            (s.strftime("%H:%M"), e.strftime("%H:%M"))
            for s, e in self.salidas
        ]


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
        self.potencia_declarada = get_rand_normal(1000, 500)
        self.potencia_cargadores = get_rand_normal(100, 20)
        self.potencia_disponble: float | None = None

        self.cola_de_espera = []

        # La cola de los vehiculos que estan cargando
        self.cola_de_carga: List[Vehiculo] = []
        # self.cola_de_carga = ColaFIFO()

        # create 1 vehicle for each count requested
        self.vehiculos: List[Vehiculo] = []
        for i in range(cant_vehiculos):
            # crear un nuevo vehiculo
            v = Vehiculo(f"V{i + 1}")
            # asignarle este edificio
            v.edificio = self
            # y agregarlo a la lista de self.vehicles
            self.vehiculos.append(v)

    def actualizar_potencia_disponble(self, consumo: str) -> None:
        """
        potencia disponble = potencia maxima - consumo
        (no puede ser negativa)

        Se asigna al edificio actual en cada ciclo de tiempo
        """
        self.potencia_disponble = max(
            np.subtract(self.potencia_declarada, np.float16(consumo)), 0
        )

    ############################################################
    # Lista de espera
    ############################################################    
    def agregar_a_cola_de_espera(self, v: Vehiculo):
        if v not in self.cola_de_espera and v not in self.cola_de_carga:
            print(f"agregado {v} a cola de espera")
            self.cola_de_espera.append(v)

    def siguiente_en_cola_de_espera(self) -> Vehiculo:
        return self.cola_de_espera.pop(0)

    ############################################################
    # Lista de carga
    ############################################################
    def cola_de_carga_llena(self):
        return len(self.cola_de_carga) >= c.MAX_VEHICULOS_EN_CARGA

    def agregar_a_cola_de_carga(self, v: Vehiculo):
        if v not in self.cola_de_carga:
            print(f"agregado {v} a cola de carga")
            self.cola_de_carga.append(v)

    def cargar_vehiculos(self):
        """
        A cada vehiculo le suma:
        E = E + (Potencia_cargador * paso_tiempo)
        """
        carga = self.potencia_cargadores * c.MINS_POR_CICLO
        for vehiculo in self.cola_de_carga:
            print(f"cargando {vehiculo} con {carga=}")
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
            # si esta fuera, descontarle bateria segun corresponda
            if not v.en_el_edificio:
                # sacarlo de las colas
                self.sacar_de_cola_de_espera(v)
                self.sacar_de_cola_de_carga(v)
                v.consumir_energia()

            # si esta en el edificio, cargarlo si es necesario
            else:
                # agregar los vehiculos que no estan a full
                if not v.necesita_cargarse:
                    self.agregar_a_cola_de_espera(v)

                    # agregarlo a cola de carga si se puede
                    if not self.cola_de_carga_llena():
                        self.agregar_a_cola_de_carga(
                            self.siguiente_en_cola_de_espera(),
                        )


        # cargar vehiculos en cola de carga
        self.cargar_vehiculos()
        # sacar los que quedaron full
        self.limpiar_cola_de_carga()

    ############################################################
    # Helper tools
    ############################################################
    def __str__(self) -> str:
        return self.nombre

class NoBuildingsException(Exception):
    pass

POTENCIAS_CSV = "potencia_consumida.csv"


class Simulacion:
    def __init__(
        self,
        nombre: str,
        cant_edificios: int,
        vehiculo_por_edificio: int,
    ):
        self.nombre = nombre

        # base de datos para importar/exportar datos
        self.db = DB()

        # sacar del header los nombres de cada edificio
        csv_edificios = self.db.obtener_headers_de_csv(nombre=POTENCIAS_CSV)[1:]

        # revisar que los numeros sean razonables
        if not csv_edificios:
            raise ValueError(f"Cantidad invalida de edificios [{csv_edificios=}]")

        # crear los efificios con sus respectivos vehiculos
        self.edificios: List[Edificio] = [
            Edificio(
                nombre=e,
                cant_vehiculos=1,
            ) for e in csv_edificios
        ]



    def empezar(self):
        # Crea los archivos para cada edificio
        [self.db.crear_archivo_de_edificio(e) for e in self.edificios]
        [[print(f"{v}: {v.salidas_str}") for v in e.vehiculos] for e in self.edificios]

        # Inicia la simulacion
        for tiempo, *consumos in self.db.leer_fila_de_csv("potencia_consumida.csv"):
            # saltar los headers
            if tiempo == "Tiempo":
                continue
            t = get_hh_mm_time(tiempo)
            for i, e in enumerate(self.edificios):
                consumo = consumos[i]
                e.actualizar_potencia_disponble(consumo)
                # print(t, consumos)

                e.simular_ciclo(t)

                # exportar el minuto actual a un .csv
                self.db.actualizar_estado_de_edificio(t, e)
