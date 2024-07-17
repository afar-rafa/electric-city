"""
TIMER

Este es solo un draft en donde trate de crear una clase que vaya trackeando el paso del tiempo
"""
import datetime
import helpers.constants as c

class Timer:
    def __init__(self) -> None:
        # parte en 2024/01/01 00:00:00
        self.tiempo_actual = datetime.datetime(2024, 1, 1)

    @property
    def actual(self):
        return datetime.datetime.strftime(
            self.tiempo_actual,
            "%Y/%m/%d %H:%M",
        )

    def siguiente_ciclo(self):
        self.tiempo_actual += datetime.timedelta(minutes=c.MINS_POR_CICLO)
