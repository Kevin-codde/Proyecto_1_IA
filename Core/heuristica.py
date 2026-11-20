def h_cero(problema, estado):
    """Heuristica nula para Costo Uniforme (UCS)."""
    return 0


def distancia_manhattan(posicion_origen, posicion_destino):
    """Calcula distancia en cuadricula sin considerar paredes."""
    return abs(posicion_origen[0] - posicion_destino[0]) + abs(posicion_origen[1] - posicion_destino[1])


def h_manhattan_condenadas(problema, estado):
    """Cuenta cuantas victimas vivas ya no se alcanzan a salvar usando distancia Manhattan."""
    victimas_perdidas = 0
    posicion_agente = (estado.fila, estado.columna)

    # Revisamos cada victima que sigue viva en este estado
    for id_victima in estado.vivas:
        victima = problema.victimas[id_victima]
        tiempo_restante = victima.ticks - estado.tick
        distancia_pasos = distancia_manhattan(posicion_agente, (victima.fila, victima.columna))

        # Si el número de pasos es mayor que el tiempo, entonces no se puede salvar
        if distancia_pasos > tiempo_restante:
            victimas_perdidas += 1

    return victimas_perdidas


def h_distancia_real_condenadas(problema, estado):
    """Cuenta cuantas victimas vivas mueren considerando las paredes del mapa (distancias reales)."""
    victimas_perdidas = 0
    posicion_agente = (estado.fila, estado.columna)

    for id_victima in estado.vivas:
        tiempo_restante = problema.victimas[id_victima].ticks - estado.tick
        distancia_en_laberinto = problema.dist_real[id_victima].get(posicion_agente)

        # Si no hay camino (None) o la distancia real supera los ticks restantes, se pierde
        if distancia_en_laberinto is None or distancia_en_laberinto > tiempo_restante:
            victimas_perdidas += 1

    return victimas_perdidas


# Heuristica mas informada que domina a Manhattan
heuristica_recomendada = h_distancia_real_condenadas

HEURISTICAS_DISPONIBLES = {
    "A* (Distancia Real)": h_distancia_real_condenadas,
    "A* (Manhattan)": h_manhattan_condenadas,
    "UCS": h_cero,
}
