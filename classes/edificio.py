import copy
import datetime
import logging
from random import randrange
from typing import List

import numpy as np

import helpers.constants as c
from classes.timer import Timer
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
    TIPO_RR = "RR"
    TIPO_INT = "INT"

    def __init__(
        self,
        nombre: str,
        timer: Timer,
    ):
        self.nombre = nombre
        self.tipo_edificio = ""  # FIFO/RoundRobin/Inteligente
        self.timer = timer

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
        Se asigna al edificio actual en cada ciclo de tiempo
        """
        porcentaje_disponible = 1 - (float(porcentaje_consumo) / 100)

        # aplicar el factor de escala
        porcentaje_disponible *= c.FACTOR_DE_ESCALA / 100

        # si es un periodo de falla, reducir la potencia total
        if c.HAY_FALLA and Timer().time_in_range(
            t, c.INICIO_HORARIO_FALLA, c.FINAL_HORARIO_FALLA
        ):
            logger.warning(
                f"%s: Reducción por falla [t=%s, potencia_declarada=%.2f * %d%% -> %.2f, cargadores=%.1fKWh]",
                self,
                t.strftime("%H:%M"),
                self.potencia_declarada,
                c.REDUCCION_EN_FALLA,
                self.potencia_declarada * c.REDUCCION_EN_FALLA / 100,
                c.POTENCIA_MIN_CARGADORES,
            )
            self.potencia_declarada = c.POTENCIA_DECLARADA * c.REDUCCION_EN_FALLA / 100
            self.potencia_cargadores = c.POTENCIA_MIN_CARGADORES

        elif self.potencia_declarada != c.POTENCIA_DECLARADA:
            self.potencia_declarada = c.POTENCIA_DECLARADA
            self.potencia_cargadores = c.POTENCIA_CARGADORES

        self.potencia_disponible = self.potencia_declarada * porcentaje_disponible
        logger.info(
            f"{self}: actualizando potencia "
            f"[declarada={self.potencia_declarada}, "
            f"{porcentaje_disponible=:.3f}, "
            f"disponible={self.potencia_disponible:.3f}]"
        )

    ############################################################
    # Transformaciones
    # Estos metodos retornan una copia del edificio transformado
    # a un FIFO/RoundRobin/Inteligente
    ############################################################
    def copia_FIFO(self):
        e = copy.deepcopy(self)
        e.__class__ = EdificioFIFO
        e.tipo_edificio = self.TIPO_FIFO
        return e

    def copia_RoundRobin(self):
        e = copy.deepcopy(self)
        e.__class__ = EdificioRoundRobin
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

    def agregar_a_cola_de_espera(
        self, t: datetime.datetime, autos_a_cargar: List[Vehiculo]
    ):
        # ordenar los autos a cargar, poniendo primero los que necesitan carga
        autos_a_cargar.sort(key=lambda v: v.necesita_carga, reverse=True)

        for v in autos_a_cargar:
            bateria_actual = v.bateria / v.max_bateria
            message = ""

            # si estamos en horario de alta demanda y el auto tiene suficiente para el resto del dia, no agregar
            if (
                c.HAY_ALTA_DEMANDA
                and self.timer.time_in_range(
                    t, c.INICIO_HORARIO_ALTA_DEMANDA, c.FINAL_HORARIO_ALTA_DEMANDA
                )
            ):
                if bateria_actual >= v.gasto_total_del_dia:
                    logger.info(
                        f"%s: %s - Saltando por horario de alta demanda [t=(%s<%s<%s), bateria=%.2f%%, necesita=%.2f%%, necesita_carga=%s]",
                        self,
                        v,
                        c.INICIO_HORARIO_ALTA_DEMANDA,
                        t.strftime("%H:%M"),
                        c.FINAL_HORARIO_ALTA_DEMANDA,
                        bateria_actual,
                        v.gasto_total_del_dia,
                        v.necesita_carga,
                    )
                    continue
                else:
                    message = " en alta demanda"

            logger.info(
                f"%s: %s - Agregando a espera%s [t=(%s<%s<%s), bateria=%.2f%%, necesita=%.2f%%, necesita_carga=%s]",
                self,
                v,
                message,
                c.INICIO_HORARIO_ALTA_DEMANDA,
                t.strftime("%H:%M"),
                c.FINAL_HORARIO_ALTA_DEMANDA,
                bateria_actual,
                v.gasto_total_del_dia,
                v.necesita_carga,
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
        self.agregar_a_cola_de_espera(t, autos_a_cargar)

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
        No saca los vehículos a menos que no esten a full carga o
        deban viajar (mientras la potencia disponible lo permita)
        """
        # saca los que estan a full
        for v in self.cola_de_carga:
            if v.cargado_full:
                self.sacar_de_cola_de_carga(v)
        
        # revisar limite segun potencia
        if self.cola_de_carga_llena:
            max_capacidad = int(self.potencia_disponible / self.potencia_cargadores)

            if c.LIMITAR_CARGADORES and c.TOPE_DE_CARGADORES < max_capacidad:
                max_capacidad = c.TOPE_DE_CARGADORES

            self.cola_de_carga = self.cola_de_carga[:max_capacidad]


class EdificioRoundRobin(Edificio):
    """
    Apenas los vehículos estan en cola de espera
    se agregan a la cola de carga en orden de llegada
    """

    def _agregar_a_cola_de_espera(self, v: Vehiculo):
        """
        RoundRobin no usa lista de espera
        """
        pass

    def actualizar_cola_de_carga(self):
        """
        En vez de la cola de espera, RoundRobin recorre la lista
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
