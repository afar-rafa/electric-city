import csv
import datetime
import logging
from typing import List

import numpy as np

CSV_DELIMITER = "\t"
CSV_QUOTECHAR = '"'

logger = logging.getLogger(__name__)


class DB:
    def crear_csv(
        self,
        name: str,
        headers: List[str],
    ):
        # writing to csv file
        with open(name, "w") as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(
                csvfile, delimiter=CSV_DELIMITER, quotechar=CSV_QUOTECHAR
            )
            # writing the fields
            csvwriter.writerow(headers)

    def agregar_a_csv(
        self,
        nombre: str,
        fila: List[str | int | float],
    ):
        # writing to csv file
        with open(nombre, "a") as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(
                csvfile, delimiter=CSV_DELIMITER, quotechar=CSV_QUOTECHAR
            )
            # writing the data filas
            csvwriter.writerows([fila])

    def leer_fila_de_csv(
        self,
        nombre: str,
    ):
        with open(nombre, newline="") as csvfile:
            spamreader = csv.reader(
                csvfile, delimiter=CSV_DELIMITER, quotechar=CSV_QUOTECHAR
            )
            for row in spamreader:
                yield row

    def obtener_headers_de_csv(self, nombre):
        with open(nombre, newline="") as csvfile:
            spamreader = csv.reader(
                csvfile, delimiter=CSV_DELIMITER, quotechar=CSV_QUOTECHAR
            )
            for row in spamreader:
                return row

    def crear_archivo_de_edificio(self, e: "Edificio"):  # type: ignore
        self.crear_csv(
            name=f"{e}.csv",
            headers=["Tiempo", "Potencia Disponible"] + [f"{v}" for v in e.vehiculos],
        )

    def actualizar_estado_de_edificio(self, tiempo: str, e: "Edificio"):  # type: ignore
        energias = [float(np.round(v.bateria, 2)) for v in e.vehiculos]

        fila = [tiempo, e.potencia_disponble] + energias
        logger.info("Simulacion: %s", fila)
        self.agregar_a_csv(nombre=f"{e}.csv", fila=fila)
