"""
Utils

Un aporte para mantener tu codigo ordenado es el criterio DRY: "Don't Repeat Yourself".
Consiste en que si repites la misma funcion o el mismo codigo varias veces,
probablemente puedas sacar eso para mantener todo mas simple y facil de leer.

En este caso saqué la funcion normal, porque la estabas usando en todos los parametros.
"""
import numpy as np


def get_rand_normal(mean: int, d_est: int) -> float:
    return abs(np.random.normal(mean, d_est))
