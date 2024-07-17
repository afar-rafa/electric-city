"""
Classes

Luego de tener las constantes y "helper functions" (utils) creamos las clases
base que necesitarás para que tu memoria pueda partir: vehiculos y edificios
"""

from queue import Queue
from typing import List, Optional

from classes.database import DB
import helpers.constants as c
from helpers.utils import get_rand_normal

class Vehiculo:
    """
    Clase principal para crear un vehiculo electrico.
    """
    def __init__(self, nombre: str):
        """
        Cada vehiculo es creado con sus variables ya definidas
        usando la funcion normal que esta en utils
        y las constantes de mas arriba
        """
        # El maximo que aguanta la bateria
        self.bateria = get_rand_normal(c.EV_BATTERY_AVG, c.EV_BATTERY_SD)
        # Cuanto tiene la bateria inicialmente (y que no sobrepase el limite)
        self.energia = get_rand_normal(c.EV_ENERGY_AVG, c.EV_ENERGY_SD)
        self.energia = min(self.energia, self.bateria)

        self.rendimiento = get_rand_normal(c.EV_PERF_AVG, c.EV_PERF_SD)
        self.consumo = get_rand_normal(c.EV_CONS_AVG, c.EV_CONS_SD)
        self.estado = get_rand_normal(c.EV_T0_AVG, c.EV_T0_SD)

        # el vehiculo parte sin un edificio asignado,
        # pero se le asigna uno cuando son creados en un edificio
        self.nombre = nombre
        self.edificio = None

    def cargar(self, energia: int):
        """
        Carga la energia indicada.
        Si sobrepasa lo que aguanta la bateria, deja el valor de la bateria
        """
        self.energia += energia
        self.energia = min(self.energia, self.bateria)

    @property
    def cargado_full(self) -> bool:
        return self.energia == self.bateria

    @property
    def en_el_edificio(self) -> bool:
        """
        TODO: agregar logica para ver si está o no fuera
        """
        return False

    def simular_ciclo(self):
        """
        Descontar bateria segun corresponda
        TODO: calcular la wea
        """
        self.energia -= 100

    ############################################################
    # Helper tools
    ############################################################
    def __str__(self) -> str:
        return self.nombre


class Edificio:
    """
    Clase principal para crear un edificio.

    Al momento de crearse le debes pasar cuántos vehiculos
    quieres que tenga:

    EJ: crear un edificio con 10 autos:
    
    ```
    b = Edificio(cant_vehiculos=10)
    ```
    """
    def __init__(
            self,
            nombre: str,
            cant_vehiculos: int,
            db: DB = DB(),
    ):
        # building parameters
        self.nombre = nombre
        self.potencia = get_rand_normal(100, 20)
        self.consumo = get_rand_normal(100, 20)
        self.potencia_cargadores = get_rand_normal(100, 20)
        self.db = db

        # Empty queues for all vehicles
        # se usa get() y put() para manejar sus vehiculos
        self.cola_de_espera = Queue()

        # La cola de los vehiculos que estan cargando
        self.cola_de_carga: List[Vehiculo] = []
        # self.cola_de_carga = ColaFIFO()

        # create 1 vehicle for each count requested
        self.vehiculos: List[Vehiculo] = []
        for i in range(cant_vehiculos):
            # crear un nuevo vehiculo
            v = Vehiculo(f"V{i + 1}")
            # asignarle este edificio
            v.edificio = self
            # y agregarlo a la lista de self.vehicles
            self.vehiculos.append(v)

    @property
    def potencia_disponble(self):
        """
        potencia disponble = potencia maxima - consumo
        """
        return self.potencia - self.consumo

    ############################################################
    # Lista de espera
    ############################################################
    def agregar_a_cola_de_espera(self, v: Vehiculo):
        self.cola_de_espera.put(v)

    def siguiente_en_cola_de_espera(self) -> Vehiculo:
        return self.cola_de_espera.get()

    ############################################################
    # Lista de carga
    ############################################################
    def cola_de_carga_llena(self):
        return len(self.cola_de_carga) >= c.MAX_VEHICULOS_EN_CARGA

    def agregar_a_cola_de_carga(self, v: Vehiculo):
        self.cola_de_carga.append(v)

    def cargar_vehiculos(self):
        """
        A cada vehiculo le suma:
        E = E + (Potencia_cargador * paso_tiempo)
        """
        for vehiculo in self.cola_de_carga:
            vehiculo.cargar(
                self.potencia_cargadores * c.MINS_POR_CICLO
            )

    def limpiar_cola_de_carga(self, v: Vehiculo):
        """
        Quita los vehiculos que ya estan a full carga
        """
        self.cola_de_carga = [
            v for v in self.cola_de_carga
            # esto crea la lista nueva solo con los autos
            # que no están a full
            if not v.cargado_full()
        ]

    ############################################################
    # Simular paso del tiempo
    ############################################################
    def simular_ciclo(self):
        for v in self.vehiculos:
            # agregar los vehiculos que no estan a full y no hayan salido
            # a la cola de espera
            if not v.cargado_full and v.en_el_edificio:
                self.agregar_a_cola_de_espera(v)
            
            # agregar lo que se pueda a cola de carga
            while not self.cola_de_carga_llena():
                self.agregar_a_cola_de_carga(
                    self.siguiente_en_cola_de_espera(),
                )
            
            # cargar vehiculos en cola de carga
            self.cargar_vehiculos()
            # sacar los que quedaron full
            self.limpiar_cola_de_carga()

            # si esta fuera, descontarle bateria segun corresponda
            if not v.en_el_edificio:
                v.simular_ciclo()
        
        # guardar estado de los vehiculos en la db
        self.db.agregar_a_csv(
            name=f"{self}",
            rows=["ahora lol"] + [v.energia for v in self.vehiculos]
        )
    

    ############################################################
    # Helper tools
    ############################################################
    # def __repr__(self) -> str:
    #     """
    #     Esto solo define lo que se muestra cuando haces print(edificio).

    #     Con esto, esta configurado para imprimir todas sus variables.
    #     Puedes intentarlo haciendo:

    #     b = Building(vehicles_count=3)
    #     print(b)
    #     """
    #     return "Edificio(" + \
    #         "".join(
    #             [
    #                 f"\n  {var} = {getattr(self, var)}"
    #                 for var in vars(self)
    #                 # no imprime building porque
    #                 # ese se imprime en su propia clase:
    #                 if var != "vehiculos"
    #             ]
    #         ) + \
    #         f"\n  cant(vehiculos) = {len(self.vehiculos)}" + \
    #         "\n)"

    def __str__(self) -> str:
        return self.nombre

class NoBuildingsException(Exception):
    pass

class Ciudad:
    def __init__(
            self,
            nombre: str,
            cant_edificios: int,
            vehiculo_por_edificio: int,
    ):
        self.nombre = nombre

        # base de datos para importar/exportar datos
        self.db = DB()

        # revisar que los numeros sean razonables
        if cant_edificios <= 0:
            raise ValueError(f"Cantidad invalida de edificios [{cant_edificios=}]")
        if vehiculo_por_edificio <= 0:
            raise ValueError(f"Cantidad invalida de vehiculos [{vehiculo_por_edificio=}]")

        # crear los efificios con sus respectivos vehiculos
        self.edificios: List[Edificio] = []
        for i in range(cant_edificios):
            # nuevo edificio con X vehiculos
            e = Edificio(
                nombre=f"Edificio {i + 1}",
                cant_vehiculos=vehiculo_por_edificio,
                db = self.db,
            )
            # asignarlo a esta ciudad
            e.ciudad = self
            # y agregarlo a la lista de self.edificios
            self.edificios.append(e)

    def simular(self, dias: int = 1):
        """
        Corre una simulación para la ciudad en donde los vehiculos salen y entran
        de sus edificios, exportando al final las baterías de cada uno.
        """
        # Esto deberia ser tiempo eventualmente
        for i in range(60):
            # simular paso de tiempo en cada edificio
            for e in self.edificios:
                e.simular_ciclo()

    def __str__(self) -> str:
        return f"Ciudad('{self.nombre}')"