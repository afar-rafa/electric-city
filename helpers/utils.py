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
    return np.round(
        abs(
            np.random.normal(mean, d_est),
        ),
        decimals=2,
    )


def get_hh_mm_time(timestamp: str) -> datetime.time:
    """
    Crea instancias de datetime.time a partir de un "HH:MM" string
    """
    return datetime.time(*[int(i) for i in timestamp.split(":")])


def distancia_en_minutos(
    desde: datetime.time | None = None,
    hasta: datetime.time | None = None,
):
    if not desde:
        desde = datetime.time(0, 0)

    # Convert both datetime.time instances to datetime instances on the same arbitrary date
    today = datetime.datetime.today().date()
    start_datetime = datetime.datetime.combine(today, desde)

    if not hasta:
        end_datetime = datetime.datetime.combine(
            today, datetime.time(0, 0)
        ) + datetime.timedelta(days=1)
    else:
        end_datetime = datetime.datetime.combine(today, hasta)

    difference = end_datetime - start_datetime

    # total difference in minutes
    return difference.total_seconds() / 60


def salidas_random(
    cant: int,
    desde: datetime.time | None = None,
    hasta: datetime.time | None = None,
):
    if not desde:
        desde = datetime.time(0, 0)

    # determinar salidas random
    minutes = distancia_en_minutos(desde, hasta)
    slots = int(minutes / MINS_POR_CICLO)
    eventos = sample(
        range(slots + 1),  # incluido el ultimo elemento
        cant * 2,  # salida + llegada
    )

    # obtener una lista de tiempos equivalente a cada salida/llegada del día
    initial_time = datetime.datetime.combine(datetime.datetime.today(), desde)
    times = sorted([(initial_time + datetime.timedelta(minutes=m*MINS_POR_CICLO)).time() for m in eventos])

    # devolverlos en tuplas de (salida, llegada)
    return [
        (times[i], times[i + 1])
        for i in range(0, len(times), 2)
    ]
