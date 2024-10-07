import logging
from typing import List, Optional

import helpers.constants as c
from classes.database import DB
from classes.edificio import Edificio
from classes.timer import Timer

logger = logging.getLogger(__name__)


class Simulacion:
    def __init__(
        self,
        nombre: str,
        archivo_potencias: str,
    ):
        self.nombre = nombre

        # base de datos para importar/exportar datos
        self.db = DB()
        # timer para manejar tiempos
        self.timer = Timer()

        # sacar del header los nombres de cada edificio
        csv_edificios = self.db.leer_headers(nombre=archivo_potencias)[1:]
        logger.warning(f"Simulacion - {csv_edificios=}")

        # revisar que los numeros sean razonables
        if not csv_edificios:
            raise ValueError(f"Cantidad invalida de edificios [{csv_edificios=}]")

        # crear los efificios con sus respectivos vehículos
        self.edificios: List[Edificio] = []
        for e in csv_edificios:
            edificio = Edificio(
                nombre=e,
            )
            if c.SIMULAR_FIFO:
                self.edificios.append(
                    edificio.copia_FIFO(),
                )

            if c.SIMULAR_ROUNDROBBIN:
                self.edificios.append(
                    edificio.copia_RoundRobbin(),
                )

            if c.SIMULAR_INTELIGENTE:
                e = edificio.copia_Inteligente()
                self.edificios.append(e)

    def empezar(self):
        # Crea los archivos para cada edificio
        self.db.crear_archivo_de_edificios(self.edificios)

        # mostrar datos de cada vehículo en los edificios
        for e in self.edificios:
            for v in e.vehículos:
                logger.info(f"{e} - {v}: {v.max_bateria=}, {v.bateria=}")
                logger.info(f"{e} - {v}: salidas={v.salidas_str}")

        # Inicia la simulación
        for rows in self.db.leer(c.POTENCIAS_CSV):
            # saltar los headers

            t = self.timer.set_hh_mm(rows["Tiempo"])

            for i, e in enumerate(self.edificios):
                e.simular_ciclo(
                    t,
                    porcentaje_consumo=rows[e.nombre],
                )

                # exportar el minuto actual a un .csv
                self.db.guardar_estado_de_edificio(
                    tiempo=self.timer.actual_str,
                    edificio=e,
                )

            # # uncomment this for a step by step execution
            # input("PRESS ENTER TO CONTINUE, CTRL+D TO EXIT")
