"""
Utils

Un aporte para mantener tu codigo ordenado es el criterio DRY: "Don't Repeat Yourself".
Consiste en que si repites la misma funcion o el mismo codigo varias veces,
probablemente puedas sacar eso para mantener todo mas simple y facil de leer.

En este caso saqué la funcion normal, porque la estabas usando en todos los parametros.
"""

import datetime
from random import sample

import numpy as np

from helpers.constants import MINS_POR_CICLO


def get_rand_normal(mean: int, d_est: int) -> float:
    return float(
        np.round(
            abs(
                np.random.normal(mean, d_est),
            ),
            decimals=2,
        )
    )


def get_hh_mm_time(timestamp: str, dia: int) -> datetime.datetime:
    """
    Crea instancias de datetime.time a partir de un "HH:MM" string
    """
    t = datetime.datetime.combine(
        datetime.date.today(),
        datetime.time(*[int(i) for i in timestamp.split(":")]),
    ) + datetime.timedelta(days=dia)
    return t


def distancia_en_minutos(
    desde: datetime.datetime | None = None,
    hasta: datetime.datetime | None = None,
):
    # total difference in minutes
    return (hasta - desde).total_seconds() / 60


default_time = datetime.datetime.combine(
    datetime.date.today(),
    datetime.time(0, 0),
)


def salidas_random(
    cant: int,
    desde: datetime.datetime | None = None,
    hasta: datetime.datetime | None = None,
):
    if not desde:
        desde = default_time
    if not hasta:
        hasta = default_time + datetime.timedelta(days=1)

    # obtener slots de tiempo en el periodo
    minutes = distancia_en_minutos(desde, hasta)
    slots = int(minutes / MINS_POR_CICLO)

    # determinar salidas random
    eventos = sample(
        range(slots + 1),  # incluido el ultimo elemento
        cant * 2,  # salida + llegada
    )

    # obtener una lista de tiempos equivalente a cada salida/llegada del día
    times = sorted(
        [desde + datetime.timedelta(minutes=m * MINS_POR_CICLO) for m in eventos],
    )

    # devolverlos en tuplas de (salida, llegada)
    return [(times[i], times[i + 1]) for i in range(0, len(times), 2)]
