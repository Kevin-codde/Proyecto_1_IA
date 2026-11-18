#Creacion del estado

class Estado : 
    #Lo creamos para ahorrar memoria, evitando crear diccionarios
    __slots__ = ("fila","columna","vivas","ticks","rescatadas","victimas","_clave","_hash")
    
    def __init__(self,fila,columna,vivas,ticks,rescatadas,victimas):
        
        self.fila = fila
        self.columna = columna
        self.vivas = vivas
        self.ticks = ticks
        self.rescatadas = rescatadas
        self.victimas = victimas
        
        
        #Generacion de clave para identidad
        self._clave = (fila,columna,vivas,ticks,rescatadas)
        
        #Clave hash
        self._hash = hash(self._clave)
    
             
    def __equ__(self,otro):
        #Igualdad por clave
        if not isinstance(otro,Estado):
            return NotImplemented
        return self._clave == otro._clave
    
    def __hash__(self):
        # si a == b entonces hash(a) == hash(b)
        return self._hash

    def __repr__(self):
        
        return (f"Estado(pos=({self.fila},{self.columna}), tick={self.tick}, "
                f"vivas={sorted(self.vivas)}, rescatadas={sorted(self.rescatadas)})")
        

class ProblemaRescate:
    
    def __init__(self,mapa,victimas):
        
        self.mapa = mapa
        self.victima = victimas
        #lo usamos para calcular costos y estadisticas
        self.total = len(victimas) 
        #(posicion -> id)
        self.pos_a_id = {(v.fila,v.columna): v.id for v in victimas.values()}
        
        #Distancias reales hacia cada victima
        self.dist_real = {
            #mi posicion hasta victima x
            v.id: mapa.distancias_desde((v.fila,v.columna)) for v in victimas.values()
        }
        #limite para garantizar que llegamos a meta tick > max(ticks) util para Costo Uniforme
        self.horizonte = max(v.ticks for v in victimas.values()) + 1
            
        
    #Estado inicial y acciones
    
    def estado_inicial(self):
       #Agente en 'S', todas las víctimas vivas, tick = 0  
       fila, columna = self.mapa.inicio
       return Estado(fila,columna,frozenset(self.victimas),0,frozenset(),0)
   
    def sucesores(self,estado):
        
        resultado = []
        #costo de movimiento 1 tick
        nuevo_tick = estado.tick + 1
        
        for accion, nueva_fila , nueva_columna in self.mapa.vecinos(estado.fila,estado.columna):
            
            #Partimos desde el estado padre
            #Cada operacion crea un frozenset nuevo
            vivas = estado.vivas
            rescatadas = estado.rescatadas
            
            #hay una victima en la celda que llegamos?
            id_aqui = self.pos_a_id.get((nueva_fila,nueva_columna))
            #Preguntamos:
            #Hay algo en dicha celda?
            #sigue viva y pendiente
            #Llegue a tiempo?
            if(id_aqui is not None and id_aqui in vivas and self.victimas[id_aqui].ticks >= nuevo_tick):
                #sacamela de las vivas
                vivas = vivas - {id_aqui} 
                #metela en recatadas
                rescatadas | {id_aqui}
            
            #victimas difuntas en este tick
            murieron = {v for v in vivas if self.victimas[v].ticks < nuevo_tick}
            if murieron:
                vivas = vivas - murieron
            #Acumulamos el conteo de muertas para g(n) en costo uniforme y A*
            muertas = estado.muertas + len(murieron)
            
            resultado.append(
                (accion,Estado(nueva_fila,nueva_columna,vivas,nuevo_tick,rescatadas,muertas))
            )
        return resultado
    
    #Prueba de meta y costos
    
    def ticks_restantes(self,estado,id_victima):
        #ticks restantes de victima
        return self.victimas[id_victima].ticks - estado.tick
    
    def es_alcanzable(self,estado,id_victima):
        #si no hay camino hacia la victima, get devuelve None
        distancia = self.dist_real[id_victima].get((estado.fila,estado.columna))
        return distancia is not None and distancia <= self.ticks_restantes(estado,id_victima)
    
    def es_meta(self,estado):
        #Sabemos que estamos en meta cuando no podemos recatar mas
        return not any(self.es_alcanzable(estado,v) for v in estado.vivas)
    #Aqui se calcula las muertas con las vivas que no alcanzo a rescatar en caso de llegar a meta
    def costo(self,estado,es_meta):
        return estado.muertas + (len(estado.vivas) if es_meta else 0)