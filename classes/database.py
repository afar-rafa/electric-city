import csv
import logging
from typing import List

from classes.edificio import Edificio


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

    def leer_csv(
        self,
        nombre: str,
    ):
        with open(nombre, newline="") as csvfile:
            spamreader = csv.DictReader(
                csvfile, delimiter=CSV_DELIMITER, quotechar=CSV_QUOTECHAR
            )
            for row in spamreader:
                yield row

    def headers_de_csv(self, nombre):
        with open(nombre, newline="") as csvfile:
            spamreader = csv.reader(
                csvfile, delimiter=CSV_DELIMITER, quotechar=CSV_QUOTECHAR
            )
            for row in spamreader:
                return row

    def crear_archivo_de_edificios(self, edificios: List["Edificio"]):  # type: ignore
        [
            self.crear_csv(
                name=f"{e}.csv",
                headers=["Tiempo", "Potencia Disponible"]
                + [f"{v}" for v in e.vehiculos],
            )
            for e in edificios
        ]

    def guardar_estado_de_edificio(self, tiempo: str, edificio: Edificio):
        fila = [tiempo, edificio.potencia_disponble] + edificio.bateria_de_vehiculos

        logger.info("Simulacion: %s", fila)
        self.agregar_a_csv(nombre=f"{edificio}.csv", fila=fila)

        if edificio.tipo_edificio == Edificio.TIPO_INT:
            fila = [tiempo] + edificio.prioridad_de_vehiculos
            self.agregar_a_csv(nombre=f"Prioridades {edificio}.csv", fila=fila)
