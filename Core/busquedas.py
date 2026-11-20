#Busqueda informada

import heapq  #Cola de prioridad
import itertools # lo utilizamos para generar numeros crecientes para el desempate
import time
from Core.heuristica import h_cero 
from collections import deque

#Implementación  de los 4 algoritmos de busqueda :
#    Amplitud               
#    Costo Uniforme         
#    Profundidad Iterativa  
#    A*  

#Estructura de apoyo
#Para formar el arbol de movimientos
class Nodo:
    #salva mi pc de millones de diccionarios :)
    __slots__ = ("estado","padre","accion")
    def __init__(self,estado,padre=None , accion=None):
        self.estado = estado
        self.padre = padre #mi puntero
        self.accion = accion
    
#Reconstruccion de camino
    
def _reconstruir_camino(nodo):
        camino = []
            
        while nodo is not None:
            camino.append(nodo.estado)
            nodo = nodo.padre
        
        #recorrer de raiz a meta
        camino.reverse()
        
        return camino
        

#Contenedor con todo lo que necesitamos    
class Resultado:
    def __init__(self,algoritmo,nodo_meta,problema,expandidos,generados,tiempo):
        self.algoritmo = algoritmo
        self.camino = _reconstruir_camino(nodo_meta)
        self.acciones = self._acciones(nodo_meta)
        self.expandidos = expandidos
        self.generados = generados
        self.tiempo = tiempo
        final = nodo_meta.estado
        self.rescatadas = len(nodo_meta.estado.rescatadas)
        self.fallecidas = problema.total - self.rescatadas
        self.ticks = final.tick
    
    #convertimos el metodo a estatico para tomar el nodo que tenemos no self
    @staticmethod
    def _acciones(nodo):
        
        acciones = []
        
        while nodo is not None and nodo.padre is not None:
            acciones.append(nodo.accion)
            nodo = nodo.padre
        acciones.reverse()
        return acciones
#metodo para comparar entre dos metas, cual es mas eficiente
def _clave_calidad(nodo):
    return (-len(nodo.estado.rescatadas),nodo.estado.tick)


#Busqueda en amplitud - BFS
def busqueda_amplitud(problema):
    inicio_reloj = time.perf_counter()
    inicial = problema.estado_inicial()
    cola = deque([Nodo(inicial)])
    visitados = {inicial}
    expandidos = 0
    generados = 1
    mejor = None

    while cola:
        nodo = cola.popleft()
        estado = nodo.estado

        #si ya no podemos rescatar mas, comparamos esta ruta
        if problema.es_meta(estado):
            if mejor is None or _clave_calidad(nodo) < _clave_calidad(mejor):
                mejor = nodo

            #si salvamos a todos, ya tenemos la mejor solucion
            if len(estado.rescatadas) == problema.total:
                break
            continue

        #revisamos los movimientos posibles desde este estado
        expandidos += 1
        for accion, hijo in problema.sucesores(estado):
            if hijo in visitados:
                continue
            visitados.add(hijo)
            generados += 1
            cola.append(Nodo(hijo, nodo, accion))

    return Resultado("BFS", mejor, problema, expandidos, generados,
                     time.perf_counter() - inicio_reloj)

    
#Funcion auxiliar para Costo uniforme y A*
def _busqueda_por_prioridad(problema,heuristica,nombre):
    inicio_reloj = time.perf_counter() #calucula el tiempo desde inicio hasta el final
    inicial = problema.estado_inicial() #punto de partida
    desempate = itertools.count() 
    
    def evaluar(estado):
        #Se calcula f(n) para un estado
        meta = problema.es_meta(estado)
        g = problema.costo(estado,meta)
        h = 0 if meta else heuristica(problema,estado)
        
        return g + h
    
    frontera = [(evaluar(inicial),inicial.tick,next(desempate),Nodo(inicial))]
    visitados = {inicial} #mismo estado mismo g(n)
    expandidos = 0
    generados = 1
    meta_encontrada = None
    
    while frontera:
        #ignorar los 3 primeros elementos y dejara el que necesitamos (Nodo)
        _, _, _, nodo = heapq.heappop(frontera)
        
        if problema.es_meta(nodo.estado):
            meta_encontrada = nodo #primera meta extraida optima
            break
        expandidos += 1
        for accion , hijo in problema.sucesores(nodo.estado):
            if hijo in visitados:
                continue
            visitados.add(hijo)
            generados += 1
            heapq.heappush(frontera,(evaluar(hijo),hijo.tick , next(desempate),Nodo(hijo,nodo,accion)))
    return Resultado(nombre,meta_encontrada,problema,expandidos,generados,time.perf_counter() - inicio_reloj)


#Costo uniforme (UCS) 
def busqueda_costo_uniforme(problema):
    """UCS: ordena solo por g(n) (muertes acumuladas). Equivale a A* con h = 0."""
    return _busqueda_por_prioridad(problema, h_cero, "UCS") 


#Profundidad Iterativa (IDDFS)
def busqueda_profundidad_iterativa(problema):
    inicio_reloj = time.perf_counter()
    inicial = problema.estado_inicial()
    expandidos = 0
    generados = 0
    mejor = None
    
    for limite in range(problema.horizonte + 1):
        pila = [Nodo(inicial)]
        visitados = {inicial}
        generados += 1
        cortado = False
        
        while pila:
            nodo = pila.pop()
            estado = nodo.estado
            
            if problema.es_meta(estado):
                if mejor is None or _clave_calidad(nodo) < _clave_calidad(mejor):
                    mejor = nodo
                continue
            
            if estado.tick >= limite:
                cortado = True
                continue
            expandidos += 1
            for accion, hijo in problema.sucesores(estado):
                if hijo in visitados:
                    continue
                visitados.add(hijo)
                generados += 1
                pila.append(Nodo(hijo,nodo,accion))
        
        # Parada anticipada: ya se rescató a todos con el menor tick posible
        # (los límites menores no la encontraron)
        if mejor is not None and len(mejor.estado.rescatadas) == problema.total:
            break
        
        # Parada por exploración completa: nada fue recortado por el límite
        if not cortado:
            break
        
    return Resultado("IDDFS",mejor,problema,expandidos,generados,time.perf_counter() - inicio_reloj)


# Busqueda A*
def busqueda_a_estrella(problema, heuristica=None):
    if heuristica is None:
        from Core.heuristica import heuristica_recomendada
        heuristica = heuristica_recomendada
    return _busqueda_por_prioridad(problema, heuristica, "A*")
