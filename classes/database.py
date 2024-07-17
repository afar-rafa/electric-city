import csv
from typing import List

from classes.models import Edificio


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
        name: str,
        rows: List[str | int | float],
    ):
        # writing to csv file
        with open(name, "a") as csvfile:
            # creating a csv writer object
            csvwriter = csv.writer(csvfile)
            # writing the data rows
            csvwriter.writerows(rows)

    def crear_archivo_de_edificio(self, e: Edificio):
        self.crear_csv(
            name=f"{e}",
            headers=["Tiempo"] + [f"{v}" for v in e.vehiculos]
        )


# field names
fields = ["Time", "Battery"]
# data rows of csv file
rows = [
    ["Nikhil", "COE"],
    ["Sanchit", "COE"],
    ["Aditya", "IT"],
    ["Sagar", "SE"],
    ["Prateek", "MCE"],
    ["Sahil", "EP"],
]
# name of csv file
filename = "test.csv"

db = DB()
db.write_csv_file(
    filename,
    fields,
    rows,
)
