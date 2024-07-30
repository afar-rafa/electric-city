"""
TIMER

Este es solo un draft en donde trate de crear una clase que vaya trackeando el paso del tiempo
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
    def new_time(time_str: str) -> datetime.datetime:
        """
        Crea instancias de datetime a partir de un string "HH:MM"
        y la fecha actual
        """
        h, m = (int(i) for i in time_str.split(":"))
        return datetime.datetime.combine(
                datetime.datetime.now().date(),
                datetime.time(hour=h, minute=m),
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
        t = datetime.datetime.combine(
            self.fecha_actual,
            datetime.time(*[int(i) for i in time_str.split(":")]),
        )

        # save the time and return it
        self.tiempo_actual = t
        return self.tiempo_actual

    @property
    def actual_str(self):
        return datetime.datetime.strftime(
            self.tiempo_actual,
            "%Y-%m-%d %H:%M",
        )
