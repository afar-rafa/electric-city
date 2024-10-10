import csv
import logging
from typing import List, Union
import os
import openpyxl

from helpers.constants import FILE_EXT
from classes.edificio import Edificio

CSV_DELIMITER = "\t"
CSV_QUOTECHAR = '"'
OUTPUT_FOLDER = "outputs"

logger = logging.getLogger(__name__)


# Clase base para manejar archivos
class DBFileHandler:
    def crear_archivo(self, nombre: str, headers: List[str]):
        raise NotImplementedError

    def agregar_fila(self, nombre: str, fila: List[Union[str, int, float]]):
        raise NotImplementedError

    def leer(self, nombre: str):
        raise NotImplementedError

    def leer_headers(self, nombre: str):
        raise NotImplementedError


# Para archivos CSV
class CSVFileHandler(DBFileHandler):
    def crear_archivo(self, nombre: str, headers: List[str]):
        with open(nombre, "w") as csv_file:
            csv_writer = csv.writer(
                csv_file,
                delimiter=CSV_DELIMITER,
                quotechar=CSV_QUOTECHAR,
            )
            csv_writer.writerow(headers)

    def agregar_fila(
        self,
        nombre: str,
        fila: List[Union[str, int, float]],
    ):
        with open(nombre, "a") as csv_file:
            csv_writer = csv.writer(
                csv_file,
                delimiter=CSV_DELIMITER,
                quotechar=CSV_QUOTECHAR,
            )
            csv_writer.writerow(fila)

    def leer(
        self,
        nombre: str,
    ):
        with open(nombre, newline="") as csv_file:
            spamreader = csv.DictReader(
                csv_file,
                delimiter=CSV_DELIMITER,
                quotechar=CSV_QUOTECHAR,
            )
            for row in spamreader:
                yield row

    def leer_headers(self, nombre: str):
        with open(nombre, newline="") as csv_file:
            spamreader = csv.reader(
                csv_file,
                delimiter=CSV_DELIMITER,
                quotechar=CSV_QUOTECHAR,
            )
            for row in spamreader:
                return row


# Paras archivos Excel (.xlsx)
class ExcelFileHandler(DBFileHandler):
    def crear_archivo(self, nombre: str, headers: List[str]):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(headers)
        wb.save(nombre)

    def agregar_fila(self, nombre: str, fila: List[Union[str, int, float]]):
        wb = openpyxl.load_workbook(nombre)
        ws = wb.active
        ws.append(fila)
        wb.save(nombre)

    def leer(self, nombre: str):
        wb = openpyxl.load_workbook(nombre)
        ws = wb.active
        for row in ws.iter_rows(values_only=True):
            yield dict(
                # Assuming first row as header
                zip([cell.value for cell in ws[1]], row)
            )

    def leer_headers(self, nombre: str):
        wb = openpyxl.load_workbook(nombre)
        ws = wb.active
        # First row as headers
        return [cell.value for cell in ws[1]]


# Clase principal que selecciona el lector de archivos adecuado
class DB:
    handler = None

    def _get_handler(self, file_name: str) -> DBFileHandler:
        if not self.handler:
            extension = os.path.splitext(file_name)[1].lower()
            if extension == ".csv":
                self.handler = CSVFileHandler()
            elif extension == ".xlsx":
                self.handler = ExcelFileHandler()
            else:
                raise ValueError(f"Unsupported file extension: {extension}")

        return self.handler

    def crear_archivo(self, nombre: str, headers: List[str]):
        handler = self._get_handler(nombre)
        handler.crear_archivo(nombre, headers)

    def agregar_fila(self, nombre: str, fila: List[Union[str, int, float]]):
        handler = self._get_handler(nombre)
        handler.agregar_fila(nombre, fila)

    def leer(self, nombre: str):
        handler = self._get_handler(nombre)
        return handler.leer(nombre)

    def leer_headers(self, nombre: str):
        handler = self._get_handler(nombre)
        return handler.leer_headers(nombre)

    def crear_archivo_de_edificios(self, edificios: List["Edificio"]):  # type: ignore
        for e in edificios:
            self.crear_archivo(
                nombre=f"{OUTPUT_FOLDER}/{e}.{FILE_EXT}",
                headers=["Tiempo", "Potencia Disponible"]
                + [f"{v}" for v in e.vehículos],
            )
            if e.tipo_edificio == Edificio.TIPO_INT:
                self.crear_archivo(
                    nombre=f"{OUTPUT_FOLDER}/Prioridades {e}.{FILE_EXT}",
                    headers=["Tiempo"] + [f"{v}" for v in e.vehículos],
                )

    def guardar_estado_de_edificio(self, tiempo: str, e: Edificio):
        fila = [tiempo, e.potencia_disponible] + e.bateria_de_vehículos

        logger.info("Simulación: %s", fila)
        self.agregar_fila(nombre=f"{OUTPUT_FOLDER}/{e}.{FILE_EXT}", fila=fila)

        if e.tipo_edificio == Edificio.TIPO_INT:
            fila = [tiempo] + e.prioridad_de_vehículos
            self.agregar_fila(
                nombre=f"{OUTPUT_FOLDER}/Prioridades {e}.{FILE_EXT}", fila=fila
            )
