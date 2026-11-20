# Agente de Rescate con Víctimas en Riesgo (Proyecto 1 – Grupo 51)


## Ejecución

```bash
cd Proyecto1
python main.py
```

## Estructura (y responsables)
## Integrantes

* **Kevin Andres Bejarano** — Código: `2067678`
* **Jose David Marmol Otero** — Código: `2266370`
* **Luis David Mendoza Manzano** — Código: `2067621`

```
Proyecto1/
├── Core/
│   ├── estado.py        Estado + reglas del juego (sucesores, meta, costo)
│   ├── mapa.py          Lectura del mapa, vecinos, distancias reales
│   ├── victimas.py      Víctima + lectura/validación de victimas.txt
│   ├── busquedas.py     (BFS)  (UCS, IDDFS)  (A*)
│   └── heuristicas.py   h(n) para A* + prueba de admisibilidad
├── GUI/
│   └── interface.py      Tkinter: carga, configuración, animación, estadísticas
├── main.py
├── mapa.txt             
├── victimas.txt         
└── .gitignore
```
