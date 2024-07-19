import csv
import datetime
from typing import List

import numpy as np

CSV_DELIMITER = "\t"
CSV_QUOTECHAR = '"'


class DB:
    def crear_csv(
        self,
        name: str,
        headers: List[str],
    ):
        # writing to csv file
        with open(name, "w") as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(csvfile)
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
            csvwriter = csv.writer(csvfile)
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
            name=f"{e}.csv", headers=["Tiempo"] + [f"{v}" for v in e.vehiculos]
        )

    def actualizar_estado_de_edificio(self, t: datetime.time, e: "Edificio"):  # type: ignore
        tiempo = t.strftime("%H:%M")
        energias = [float(np.round(v.energia, 2)) for v in e.vehiculos]
        print([tiempo] + [energias])
        self.agregar_a_csv(nombre=f"{e}.csv", fila=[tiempo] + energias)
