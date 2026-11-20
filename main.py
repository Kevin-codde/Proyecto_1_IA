import sys
import tkinter as tk
from Gui.interface import InterfazRescate


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        from Core.busquedas import (
            busqueda_a_estrella,
            busqueda_amplitud,
            busqueda_costo_uniforme,
            busqueda_profundidad_iterativa,
        )
        from Core.estado import ProblemaRescate
        from Core.heuristica import h_distancia_real_condenadas, h_manhattan_condenadas
        from Core.mapa import Mapa
        from Core.victimas import cargar_victimas, validar_contra_mapa

        mapa = Mapa.desde_archivo("mapa.txt")
        victimas = cargar_victimas("victimas.txt")
        validar_contra_mapa(victimas, mapa)
        problema = ProblemaRescate(mapa, victimas)

        print("==================================================")
        print("  COMPARACION DE ALGORITMOS")
        print("==================================================")
        for nombre, algo, kwargs in [
            ("BFS", busqueda_amplitud, {}),
            ("UCS", busqueda_costo_uniforme, {}),
            ("IDDFS", busqueda_profundidad_iterativa, {}),
            ("A* (Manhattan)", busqueda_a_estrella, {"heuristica": h_manhattan_condenadas}),
            ("A* (Dist Real)", busqueda_a_estrella, {"heuristica": h_distancia_real_condenadas}),
        ]:
            res = algo(problema, **kwargs)
            print(
                f"[{nombre:16}] Exp: {res.expandidos:4} | Gen: {res.generados:4} | "
                f"Rescatadas: {res.rescatadas}/{problema.total} | Fallecidas: {res.fallecidas} | "
                f"Ticks: {res.ticks} | Tiempo: {res.tiempo:.4f}s"
            )
            print(f"  Ruta acciones: {''.join(res.acciones)}")
        return

    root = tk.Tk()
    app = InterfazRescate(root)
    root.mainloop()


if __name__ == "__main__":
    main()
