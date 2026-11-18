#Victima : (id,fila,columna,ticks_supervivencia)
#Ejemplo:
# V1,1,4,5
# v2,3,6,12

# `dataclass` genera automáticamente __init__, __repr__ y __eq__ a partir de
# los campos declarados.
from dataclasses import dataclass

class ErrorVictimas(Exception):
    """Error de lectura/validación de victimas.txt."""
    
    
# frozen=True hace la instancia INMUTABLE: nadie puede cambiar los ticks de una
# víctima por accidente a mitad de la búsqueda. Además la vuelve hasheable.

@dataclass(frozen=True)
class Victima:
    """Una víctima con posición fija y un tiempo de supervivencia en ticks."""
    id: str        # Etiqueta única, por ejemplo "V1".
    fila: int      # Fila de la celda donde está la víctima.
    columna: int   # Columna de la celda donde está la víctima.
    ticks: int     # Tick máximo en el que todavía puede ser rescatada.

#Carga de archivo      
def cargar_victimas(ruta):
    
    try:
        with open(ruta, "r", encoding="utf-8-sig") as archivo:
            lineas = [linea.strip() for linea in archivo]
    except OSError as error:
        raise ErrorVictimas(f"No se pudo abrir el archivo de víctimas: {error}") from error

    victimas = {}                
    for numero, linea in enumerate(lineas, start=1):
        if linea == "":
            continue

        partes = [parte.strip() for parte in linea.split(",")]

        if partes[0].lower() == "id":
            continue

        if len(partes) != 4:
            raise ErrorVictimas(f"Línea {numero}: se esperaban 4 campos y hay {len(partes)}.")

        identificador = partes[0]
        try:
            fila, columna, ticks = int(partes[1]), int(partes[2]), int(partes[3])
        except ValueError as error:
            raise ErrorVictimas(f"Línea {numero}: fila, columna y ticks deben ser enteros.") from error

        if ticks < 0:
            raise ErrorVictimas(f"Línea {numero}: los ticks no pueden ser negativos.")

        # Dos víctimas con el mismo id harían que una pise a la otra en el dict.
        if identificador in victimas:
            raise ErrorVictimas(f"Línea {numero}: el id '{identificador}' está repetido.")

        victimas[identificador] = Victima(identificador, fila, columna, ticks)

    # Un archivo sin víctimas haría trivial el problema; se avisa al usuario.
    if not victimas:
        raise ErrorVictimas("El archivo no contiene ninguna víctima.")
    return victimas

# Verificar que cada víctima esté en una celda válida del mapa.
def validar_contra_mapa(victimas, mapa):
    ocupadas = set()
    for v in victimas.values():
        # Debe estar dentro del mapa y no sobre una pared.
            if not mapa.es_transitable(v.fila, v.columna):
                raise ErrorVictimas(
                    f"{v.id} está en ({v.fila},{v.columna}): fuera del mapa o sobre una pared."
                )
            # Una víctima sobre 'S' se rescataría en el tick 0 sin moverse: caso ambiguo.
            if (v.fila, v.columna) == mapa.inicio:
                raise ErrorVictimas(f"{v.id} está sobre la posición inicial del agente.")
            if (v.fila, v.columna) in ocupadas:
                raise ErrorVictimas(f"{v.id} comparte celda con otra víctima.")
            ocupadas.add((v.fila, v.columna))