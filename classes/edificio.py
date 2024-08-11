import datetime
import logging
from typing import List

import numpy as np

import helpers.constants as c
from classes.vehiculo import Vehiculo

logger = logging.getLogger(__name__)


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
    pass


class EdificioAlgoritmo(Edificio):
    pass


class EdificioTercero(Edificio):
    pass
