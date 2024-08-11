import logging
from typing import List

from classes.database import DB
from classes.edificio import Edificio, EdificioFIFO
from classes.timer import Timer

logger = logging.getLogger(__name__)


class Simulacion:
    def __init__(
        self,
        nombre: str,
        vehiculos_por_edificio: int,
        archivo_potencias: str,
    ):
        self.nombre = nombre

        # base de datos para importar/exportar datos
        self.db = DB()
        # timer para manejar tiempos
        self.timer = Timer()

        # sacar del header los nombres de cada edificio
        csv_edificios = self.db.headers_de_csv(nombre=archivo_potencias)[1:]

        # revisar que los numeros sean razonables
        if not csv_edificios:
            raise ValueError(f"Cantidad invalida de edificios [{csv_edificios=}]")

        # crear los efificios con sus respectivos vehiculos
        self.edificios: List[Edificio] = [
            EdificioFIFO(
                nombre=e,
                cant_vehiculos=vehiculos_por_edificio,
            )
            for e in csv_edificios
        ]

    def empezar(self):
        # Crea los archivos para cada edificio
        self.db.crear_archivo_de_edificios(self.edificios)

        # mostrar datos de cada vehiculo en los edificios
        for e in self.edificios:
            for v in e.vehiculos:
                logger.info(f"{e} - {v}: {v.max_bateria=}")
                logger.info(f"{e} - {v}: salidas={v.salidas_str}")

        # Inicia la simulacion
        for tiempo, *consumos in self.db.leer_csv("potencia_consumida.csv"):
            # saltar los headers
            if tiempo == "Tiempo":
                continue

            t = self.timer.set_hh_mm(tiempo)
            logger.info(f"Simulacion: t={t.strftime('%H:%M')}")

            for i, e in enumerate(self.edificios):
                e.simular_ciclo(t, consumo=consumos[i])

                # exportar el minuto actual a un .csv
                self.db.guardar_estado_de_edificio(
                    tiempo=self.timer.actual_str,
                    edificio=e,
                )

            # # uncomment this for a step by step execution
            # input("PRESS ENTER TO CONTINUE, CTRL+D TO EXIT")
