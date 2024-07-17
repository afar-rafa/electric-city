import datetime as dt
from typing import Self, SupportsIndex
import helpers.constants as c


class Timer:
    def __init__(self) -> None:
        # parte en 2024/01/01 00:00:00
        self.tiempo_actual = dt.datetime(2024, 1, 1)

    @property
    def actual(self):
        return dt.datetime.strftime(
            self.tiempo_actual,
            "%Y/%m/%d %H:%M",
        )

    def siguiente_ciclo(self):
        self.tiempo_actual += dt.timedelta(minutes=c.MINS_POR_CICLO)


class Time:
    def __init__(self, time: str = "") -> None:
        self.t = dt.datetime(2024, 1, 1)
        if time:
            m = dt.datetime.strptime(time, "%H:%M")
            self.t = self.t.replace(
                hour=m.hour,
                minute=m.minute,
            )

    ############################################################
    # Helper tools
    ############################################################
    def __repr__(self) -> str:
        """ """
        return f"Time[{self.t}]"


def horas_a_numeros(inicio: Time, final: Time):
    pass


print(Time())
print(Time(""))
print(Time("12:34"))
