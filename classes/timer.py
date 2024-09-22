"""
TIMER

Clase que contiene funciones relacionadas al paso del tiempo
"""

import datetime
import logging

import helpers.constants as c

logger = logging.getLogger(__name__)


class Timer:
    def __init__(self) -> None:
        # parte hoy a las 00:00:00
        self.fecha_actual = datetime.date.today()
        self.tiempo_actual = None

    @staticmethod
    def str_to_time(t_str: str) -> datetime.datetime:
        return datetime.datetime.strptime(t_str, "%H:%M")

    def new_time(self, time_str: str) -> datetime.datetime:
        """
        Crea instancias de datetime a partir de un string "HH:MM"
        y la fecha actual
        """
        return datetime.datetime.combine(
            self.fecha_actual,
            self.str_to_time(time_str).time(),
        )

    @staticmethod
    def distancia_en_minutos(
        desde: datetime.datetime | None = None,
        hasta: datetime.datetime | None = None,
    ):
        # total difference in minutes
        return (hasta - desde).total_seconds() / 60

    def set_hh_mm(self, time_str: str) -> datetime.datetime:
        """
        Crea instancias de datetime a partir de un string "HH:MM"
        y reemplaza el tiempo actual con el entregado
        """
        # revisar si pasamos al sgte día
        if self.tiempo_actual and time_str == "0:00":
            self.fecha_actual = (self.tiempo_actual + datetime.timedelta(days=1)).date()
            logger.debug(f"Timer: new day -> {self.fecha_actual.strftime('%y-%m-%d')}")

        # transform time_str into datetime
        t = self.new_time(time_str)

        # save the time and return it
        self.tiempo_actual = t
        return self.tiempo_actual

    @property
    def actual_str(self):
        return datetime.datetime.strftime(
            self.tiempo_actual,
            "%Y-%m-%d %H:%M",
        )

    def time_in_range(
        self,
        t: datetime,
        t_0: str,
        t_f: str,
    ) -> bool:
        current_time = t.time()

        # obtener tiempos inicial y final
        t_0_time = self.str_to_time(t_0).time()
        t_f_time = self.str_to_time(t_f).time()

        # Caso 1: Horas en el mismo dia
        if t_0_time <= t_f_time:
            return t_0_time <= current_time <= t_f_time
        # Caso 2: Horas de un dia al siguiente
        else:
            return current_time >= t_0_time or current_time <= t_f_time
