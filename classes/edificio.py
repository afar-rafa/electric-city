import copy
import datetime
import logging
from random import randrange
from typing import List, Optional

import numpy as np

from classes.timer import Timer
import helpers.constants as c
from classes.vehiculo import Vehiculo

logger = logging.getLogger(__name__)


class Edificio:
    """
    Clase principal para crear un edificio.

    Al momento de crearse le debes pasar cuántos vehículos
    quieres que tenga:

    EJ: crear un edificio con 10 autos:

    ```
    b = Edificio(
        nombre="Edificio 1",
    )
    ```
    """

    TIPO_FIFO = "FIFO"
    TIPO_RR = "RoundRobbin"
    TIPO_INT = "INT"

    def __init__(
        self,
        nombre: str,
    ):
        self.nombre = nombre
        self.tipo_edificio = ""  # FIFO/RoundRobbin/Inteligente

        # Potencia total disponible del edificio
        self.potencia_declarada = c.POTENCIA_DECLARADA

        # potencia de los cargadores de vehículos
        self.potencia_cargadores: float = c.POTENCIA_CARGADORES

        # potencia disponible, calculada durante la simulacion
        self.potencia_disponible: float | None = None

        # colas de vehículos
        self.cola_de_espera: List[Vehiculo] = []
        self.cola_de_carga: List[Vehiculo] = []

        # crear vehículos
        self.vehículos: List[Vehiculo] = []

        # si no se especifican, toma una cant al azar
        cant_v = c.VEHÍCULOS_POR_EDIFICIO or randrange(1, self.tope_vehículos + 1)
        for i in range(cant_v):
            # crear un nuevo vehiculo
            v = Vehiculo(f"VE{i + 1}")

            # asignarle este edificio
            v.edificio = self

            # y agregarlo a la lista de vehículos
            self.vehículos.append(v)

    @property
    def tope_vehículos(self):
        """
        Cada edificio debe crear una cantidad random de vehículos:

        Máximo: 70% * (P. declarada / P. cargadores)
        """
        return int(self.potencia_declarada / self.potencia_cargadores * 0.7)

    def actualizar_potencia_disponible(
        self,
        t: datetime.datetime,
        porcentaje_consumo: str,
    ) -> None:
        """
        potencia disponble = potencia maxima - consumo
        (no puede ser negativa)

        Se asigna al edificio actual en cada ciclo de tiempo
        """
        # si es un periodo de falla, reducir la potencia,
        # si no, basarse en la potencia declarada y consumida
        if c.HAY_FALLA and Timer().time_in_range(
            t, c.INICIO_HORARIO_FALLA, c.FINAL_HORARIO_FALLA
        ):
            consumo = c.POTENCIA_DECLARADA * c.REDUCCION_EN_FALLA
            logger.info(
                f"{self}: t={t.strftime('%H:%M')} {consumo=} (Horario de Falla)"
            )
        else:
            p_consumo = float(porcentaje_consumo) / 100
            consumo = max(  # permitir siempre un minimo de potencia si esta existe
                c.POTENCIA_DECLARADA * p_consumo, c.POT_DISPONIBLE_MINIMA
            )
            logger.debug(f"{self}: t={t.strftime('%H:%M')} {consumo=}")

        self.potencia_disponible = max(self.potencia_declarada - consumo, 0)
        logger.info(
            f"{self}: actualizando potencia "
            f"[declarada={self.potencia_declarada}, "
            f"{consumo=:.1f}, "
            f"disponible={self.potencia_disponible}]"
        )

    ############################################################
    # Transformaciones
    # Estos metodos retornan una copia del edificio transformado
    # a un FIFO/RoundRobbin/Inteligente
    ############################################################
    def copia_FIFO(self):
        e = copy.deepcopy(self)
        e.__class__ = EdificioFIFO
        e.tipo_edificio = self.TIPO_FIFO
        return e

    def copia_RoundRobbin(self):
        e = copy.deepcopy(self)
        e.__class__ = EdificioRoundRobbin
        e.tipo_edificio = self.TIPO_RR
        e.ultimo_v_cargado = 0
        return e

    def copia_Inteligente(self):
        e = copy.deepcopy(self)
        e.__class__ = EdificioInteligente
        e.tipo_edificio = self.TIPO_INT
        return e

    ############################################################
    # Cola de espera
    ############################################################
    def _agregar_a_cola_de_espera(self, v: Vehiculo):
        """
        Esto se debe aplicar segun la logica de cada edificio
        """
        raise NotImplementedError

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
            logger.debug(
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
        if v not in self.cola_de_carga and not self.cola_de_carga_llena:
            logger.debug(f"{v}: agregando a cola de carga")
            self.cola_de_carga.append(v)

    def actualizar_cola_de_carga(self):
        while self.cola_de_espera and not self.cola_de_carga_llena:
            self.agregar_a_cola_de_carga(
                self.siguiente_en_cola_de_espera(),
            )
        logger.debug(f"%s: actualizada {self.cola_de_carga=}", self)

    def limpiar_cola_de_carga(self):
        """
        Esto se debe aplicar segun la logica de cada edificio
        """
        raise NotImplementedError

    @property
    def cola_de_carga_llena(self):
        max_capacidad = int(self.potencia_disponible / self.potencia_cargadores)

        if c.LIMITAR_CARGADORES and c.TOPE_DE_CARGADORES < max_capacidad:
            max_capacidad = c.TOPE_DE_CARGADORES

        logger.debug(
            f"cola_de_carga_llena? en_carga={len(self.cola_de_carga)} >= {max_capacidad=}"
        )
        return len(self.cola_de_carga) >= max_capacidad

    @property
    def energia_a_cargar(self) -> float:
        return self.potencia_cargadores * c.MINS_POR_CICLO / 60  # KWmin

    def cargar_vehículos(self):
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
    def bateria_de_vehículos(self):
        return [float(np.round(v.bateria / v.max_bateria, 2)) for v in self.vehículos]

    @property
    def prioridad_de_vehículos(self):
        return [float(np.round(v.prioridad, 2)) for v in self.vehículos]

    ############################################################
    # Simular paso del tiempo
    ############################################################
    def simular_ciclo(
        self,
        t: datetime.datetime,
        porcentaje_consumo: str,
    ):
        logger.debug(f"{self}: t={t.strftime('%H:%M')} {porcentaje_consumo=}")

        self.actualizar_potencia_disponible(t, porcentaje_consumo)

        # los esto es para separar aquellos que necesitan carga para
        # su siguiente viaje y aquellos que solo no están a 100%
        autos_a_cargar: List[Vehiculo] = []

        for v in self.vehículos:
            logger.debug("%s: revisando %s", self, v)
            v.actualizar_status(t)

            # si esta fuera, descontarle bateria segun corresponda
            if not v.en_el_edificio:
                # sacarlo de las colas
                self.sacar_de_cola_de_espera(v)
                self.sacar_de_cola_de_carga(v)

                if v.esta_manejando(t):
                    v.viajar()

            # si esta en el edificio, cargarlo si es necesario
            else:
                # agregar los vehículos que no estan a full
                if not v.cargado_full:
                    autos_a_cargar.append(v)

        # pasar a cola de espera los autos que necesiten carga
        logger.debug(f"%s: {autos_a_cargar=}", self)
        self.agregar_a_cola_de_espera(autos_a_cargar)

        logger.debug(f"%s: {self.cola_de_espera=}", self)

        # agregar vehículos a cola de carga si se puede
        self.actualizar_cola_de_carga()

        # cargar vehículos en cola de carga
        self.cargar_vehículos()

        # sacar los que quedaron ok
        self.limpiar_cola_de_carga()

        logger.debug(f"{self}: finalmente {self.cola_de_carga=}")

    ############################################################
    # Helper tools
    ############################################################
    def __repr__(self) -> str:
        return f"{self.nombre} {self.tipo_edificio}"


class EdificioFIFO(Edificio):
    """
    Apenas los vehículos estan en cola de espera
    se agregan a la cola de carga en orden de llegada
    pero solo los saca cuando estan a full o salen del edificio
    """

    def _agregar_a_cola_de_espera(self, v: Vehiculo):
        if v not in self.cola_de_carga and v not in self.cola_de_espera:
            logger.debug(f"{v}: agregando a cola de espera")
            self.cola_de_espera.append(v)
            logger.debug(f"{v}: {self.cola_de_espera=}")

    def limpiar_cola_de_carga(self):
        """
        Quita sólo los vehículos que ya estan a full carga
        """
        self.cola_de_carga = [v for v in self.cola_de_carga if not v.cargado_full]


class EdificioRoundRobbin(Edificio):
    """
    Apenas los vehículos estan en cola de espera
    se agregan a la cola de carga en orden de llegada
    """

    def _agregar_a_cola_de_espera(self, v: Vehiculo):
        """
        RoundRobbin no usa lista de espera
        """
        pass

    def actualizar_cola_de_carga(self):
        """
        En vez de la cola de espera, RoundRobbin recorre la lista
        de vehículos desde el último que cargó hasta que llena la
        cola de carga o los recorre todos
        """
        v_inicial = int(self.ultimo_v_cargado)
        total_vehículos = len(self.vehículos)

        for i in range(1, total_vehículos + 1):
            # si la cola está llena terminar el ciclo
            if self.cola_de_carga_llena:
                break

            # obtener sgte vehículos en la lista
            num_vehiculo = (i + v_inicial) % total_vehículos
            v = self.vehículos[num_vehiculo]

            if v.en_el_edificio and not v.cargado_full:
                self.agregar_a_cola_de_carga(v)

            self.ultimo_v_cargado = num_vehiculo

        logger.debug(f"%s: actualizada {self.cola_de_carga=}", self)

    def limpiar_cola_de_carga(self):
        """
        Borra todos los vehículos, ya que
        se rotan al atualizar la cola de carga
        """
        self.cola_de_carga = []


class EdificioInteligente(Edificio):
    """
    Cuando los vehículos estan en cola de espera
    los ordena según:
    - su % de energía en la batería
    - cuánto tiempo lleva en espera
    """

    def _agregar_a_cola_de_espera(self, v: Vehiculo):
        """
        Agrega el vehículo y luego reordena
        la cola de carga segun prioridad
        """
        if v not in self.cola_de_espera and v not in self.cola_de_carga:
            logger.debug(f"{v}: agregando a cola de espera")
            self.cola_de_espera.append(v)

            # ordenar en orden descendente así seguimos sacando
            # el primer valor siempre
            logger.debug(f"{v}: reordenando cola de espera")
            self.cola_de_espera.sort(key=lambda v: v.prioridad, reverse=True)
            logger.debug(f"{v}: {self.cola_de_espera=}")

    def limpiar_cola_de_carga(self):
        """
        Quita todos los vehículos, ya que
        se repriorizan en cada iteracion
        """
        self.cola_de_carga = []
