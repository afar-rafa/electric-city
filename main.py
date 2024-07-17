from classes.models import Ciudad

city = Ciudad(
    "Super City",
    cant_edificios=1,
    vehiculo_por_edificio=1,
)

for edificio in city.edificios:
    print(edificio)