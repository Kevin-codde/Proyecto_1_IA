from collections import deque


class ErrorMapa(Exception):
    #Para mostrar los errores si el mapa esta mal
    pass


class Mapa:
    #Movimientos que puede hacer el agente (Norte, Sur, Este, Oeste)
    DIRECCIONES = (
        ("N", -1, 0),
        ("S", 1, 0),
        ("E", 0, 1),
        ("O", 0, -1),
    )

    def __init__(self, filas):
        #Primero revisamos que el mapa no este vacio
        if not filas or not filas[0]:
            raise ErrorMapa("El mapa está vacío.")

        #Guardamos el tamaño del mapa
        self.alto = len(filas)
        self.ancho = len(filas[0])
        self.inicio = None

        #Recorremos las filas para validar el mapa y buscar la S
        for f, fila in enumerate(filas):
            #Todas las filas deben tener el mismo tamaño
            if len(fila) != self.ancho:
                raise ErrorMapa(f"La fila {f} no tiene el mismo ancho que las demás.")

            for c, celda in enumerate(fila):
                #Solo se permiten paredes, caminos libres y la S
                if celda not in ("#", ".", "S"):
                    raise ErrorMapa(f"Carácter no permitido '{celda}' en ({f}, {c}).")

                if celda == "S":
                    #Si ya encontramos una S, no puede haber otra
                    if self.inicio is not None:
                        raise ErrorMapa("El mapa debe tener una sola posición inicial S.")
                    self.inicio = (f, c)

        #Si no encontramos la S, no sabemos donde empieza el agente
        if self.inicio is None:
            raise ErrorMapa("El mapa debe tener una posición inicial S.")

        #Guardamos las filas como tupla para no modificar el mapa
        self.filas = tuple(filas)

    @classmethod
    def desde_archivo(cls, ruta):
        #Leemos el mapa desde el archivo txt
        try:
            with open(ruta, "r", encoding="utf-8-sig") as archivo:
                filas = [linea.rstrip("\r\n") for linea in archivo if linea.strip()]
        except OSError as error:
            raise ErrorMapa(f"No se pudo leer el mapa: {error}") from error

        return cls(filas)

    def es_transitable(self, fila, columna):
        #Revisamos que la posicion este dentro del mapa
        if not (0 <= fila < self.alto and 0 <= columna < self.ancho):
            return False

        #Si hay una pared no podemos pasar
        return self.filas[fila][columna] != "#"

    def vecinos(self, fila, columna):
        #Aqui guardamos los movimientos que si puede hacer el agente
        resultado = []

        for accion, cambio_fila, cambio_columna in self.DIRECCIONES:
            nueva_fila = fila + cambio_fila
            nueva_columna = columna + cambio_columna

            #Solo agregamos las posiciones donde se puede pasar
            if self.es_transitable(nueva_fila, nueva_columna):
                resultado.append((accion, nueva_fila, nueva_columna))

        return resultado

    def distancias_desde(self, origen):
        #Calculamos cuantos movimientos hay desde una posicion hasta las demas
        if not self.es_transitable(*origen):
            raise ErrorMapa("La posición de origen no es transitable.")

        #La distancia desde el origen hasta el mismo es 0
        distancias = {origen: 0}
        cola = deque([origen])

        #Recorremos el mapa por amplitud para encontrar los caminos mas cortos
        while cola:
            fila, columna = cola.popleft()

            for _, nueva_fila, nueva_columna in self.vecinos(fila, columna):
                posicion = (nueva_fila, nueva_columna)

                #Si no hemos pasado por esta posicion guardamos su distancia
                if posicion not in distancias:
                    distancias[posicion] = distancias[(fila, columna)] + 1
                    cola.append(posicion)

        return distancias
