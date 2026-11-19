# Heuristicas para A*

def h_cero(problema, estado):
    return 0


def distancia_manhattan(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])


# Cuenta cuantas victimas mueren seguro usando distancia Manhattan
def h_manhattan_condenadas(problema, estado):
    condenadas = 0
    pos_agente = (estado.fila, estado.columna)

    for id_v in estado.vivas:
        v = problema.victimas[id_v]
        ticks_rest = v.ticks - estado.tick
        dist_m = distancia_manhattan(pos_agente, (v.fila, v.columna))
        if dist_m > ticks_rest:
            condenadas += 1

    return condenadas


# Cuenta cuantas victimas mueren considerando las paredes del mapa
def h_distancia_real_condenadas(problema, estado):
    condenadas = 0
    pos_agente = (estado.fila, estado.columna)

    for id_v in estado.vivas:
        ticks_rest = problema.victimas[id_v].ticks - estado.tick
        dist_mapa = problema.dist_real[id_v].get(pos_agente)
        if dist_mapa is None or dist_mapa > ticks_rest:
            condenadas += 1

    return condenadas


heuristica_recomendada = h_distancia_real_condenadas

HEURISTICAS_DISPONIBLES = {
    "A* (Distancia Real)": h_distancia_real_condenadas,
    "A* (Manhattan)": h_manhattan_condenadas,
    "UCS": h_cero,
}
