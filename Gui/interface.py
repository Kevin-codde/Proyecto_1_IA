import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from Core.busquedas import (
    busqueda_a_estrella,
    busqueda_amplitud,
    busqueda_costo_uniforme,
    busqueda_profundidad_iterativa,
)
from Core.estado import ProblemaRescate
from Core.heuristica import (
    HEURISTICAS_DISPONIBLES,
    h_distancia_real_condenadas,
    h_manhattan_condenadas,
)
from Core.mapa import ErrorMapa, Mapa
from Core.victimas import ErrorVictimas, cargar_victimas, validar_contra_mapa


def _cargar_mapa_archivo(ruta):
    return Mapa.desde_archivo(ruta)


def _obtener_dimensiones_mapa(mapa):
    filas = getattr(mapa, "alto", None)
    if filas is None:
        filas = getattr(mapa, "filas", 0)
        if isinstance(filas, (list, tuple)):
            filas = len(filas)
    columnas = getattr(mapa, "ancho", getattr(mapa, "columnas", 0))
    return int(filas), int(columnas)


def _obtener_celda_mapa(mapa, r, c):
    if hasattr(mapa, "filas") and isinstance(mapa.filas, (list, tuple)):
        return mapa.filas[r][c]
    elif hasattr(mapa, "cuadricula"):
        return mapa.cuadricula[r][c]
    return "."


class InterfazRescate:
    def __init__(self, root):
        self.root = root
        self.root.title("Proyecto 1: Agente de Rescate con Víctimas en Riesgo")
        self.root.geometry("1180x750")
        self.root.minsize(980, 680)

        # Colores
        self.COLORES = {
            "fondo": "#ECEFF1",
            "pared": "#263238",
            "libre": "#FFFFFF",
            "borde_celda": "#CFD8DC",
            "inicio": "#E0E0E0",
            "agente": "#1976D2",
            "viva": "#F57C00",
            "viva_texto": "#FFFFFF",
            "rescatada": "#2E7D32",
            "muerta": "#C62828",
            "texto_claro": "#FFFFFF",
            "panel": "#FFFFFF",
        }

        # Datos del problema
        self.ruta_mapa = None
        self.ruta_victimas = None
        self.mapa = None
        self.victimas = None
        self.problema = None

        # Variables de simulacion
        self.resultado_actual = None
        self.camino_estados = []
        self.paso_actual = 0
        self.animando = False
        self.id_after_animacion = None

        # Variables de control
        self.var_algoritmo = tk.StringVar(value="A*")
        self.var_heuristica = tk.StringVar(value="Distancia Real (Más Informada)")
        self.var_velocidad = tk.IntVar(value=350)
        self.var_estado_mapa = tk.StringVar(value="Pendiente de cargar")
        self.var_estado_victimas = tk.StringVar(value="Pendiente de cargar")
        self.var_info_tick = tk.StringVar(value="Simulación en espera")

        self._configurar_estilos()
        self._construir_interfaz()
        self._autocargar_archivos_defecto()

    def _configurar_estilos(self):
        style = ttk.Style()
        style.theme_use("clam")
        self.root.configure(bg=self.COLORES["fondo"])

    def _construir_interfaz(self):
        main_frame = tk.Frame(self.root, bg=self.COLORES["fondo"], padx=10, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Panel izquierdo
        panel_izquierdo = tk.Frame(main_frame, bg=self.COLORES["fondo"], width=420)
        panel_izquierdo.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        panel_izquierdo.pack_propagate(False)

        # 1. Carga de archivos
        frame_archivos = ttk.LabelFrame(panel_izquierdo, text=" 1. Carga de Archivos ", padding=10)
        frame_archivos.pack(fill=tk.X, pady=(0, 8))

        f_mapa = tk.Frame(frame_archivos)
        f_mapa.pack(fill=tk.X, pady=2)
        btn_mapa = ttk.Button(f_mapa, text="Examinar Mapa...", command=self.cargar_archivo_mapa)
        btn_mapa.pack(side=tk.LEFT)
        self.lbl_mapa_status = tk.Label(
            f_mapa, textvariable=self.var_estado_mapa, fg="#C62828", font=("Segoe UI", 9, "bold")
        )
        self.lbl_mapa_status.pack(side=tk.LEFT, padx=8)

        f_vic = tk.Frame(frame_archivos)
        f_vic.pack(fill=tk.X, pady=2)
        btn_vic = ttk.Button(f_vic, text="Examinar Víctimas...", command=self.cargar_archivo_victimas)
        btn_vic.pack(side=tk.LEFT)
        self.lbl_vic_status = tk.Label(
            f_vic, textvariable=self.var_estado_victimas, fg="#C62828", font=("Segoe UI", 9, "bold")
        )
        self.lbl_vic_status.pack(side=tk.LEFT, padx=8)

        # 2. Configuracion del algoritmo
        frame_config = ttk.LabelFrame(panel_izquierdo, text=" 2. Configuración del Algoritmo ", padding=10)
        frame_config.pack(fill=tk.X, pady=(0, 8))

        tk.Label(frame_config, text="Algoritmo de búsqueda:").pack(anchor=tk.W)
        cb_algo = ttk.Combobox(
            frame_config,
            textvariable=self.var_algoritmo,
            values=["A*", "BFS", "UCS", "IDDFS"],
            state="readonly",
        )
        cb_algo.pack(fill=tk.X, pady=(2, 6))
        cb_algo.bind("<<ComboboxSelected>>", self._al_cambiar_algoritmo)

        self.lbl_heur = tk.Label(frame_config, text="Heurística para A*:")
        self.lbl_heur.pack(anchor=tk.W)
        self.cb_heur = ttk.Combobox(
            frame_config,
            textvariable=self.var_heuristica,
            values=[
                "Distancia Real (Más Informada)",
                "Manhattan Condenadas (Base Enunciado)",
            ],
            state="readonly",
        )
        self.cb_heur.pack(fill=tk.X, pady=(2, 6))

        tk.Label(frame_config, text="Velocidad Simulación (ms por tick):").pack(anchor=tk.W)
        f_vel = tk.Frame(frame_config)
        f_vel.pack(fill=tk.X)
        slider_vel = ttk.Scale(
            f_vel, from_=80, to=1000, variable=self.var_velocidad, orient=tk.HORIZONTAL
        )
        slider_vel.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.lbl_vel = tk.Label(f_vel, text=f"{self.var_velocidad.get()} ms", width=8)
        self.lbl_vel.pack(side=tk.RIGHT)
        slider_vel.configure(command=lambda val: self.lbl_vel.configure(text=f"{int(float(val))} ms"))

        # 3. Controles de ejecucion
        frame_controles = ttk.LabelFrame(panel_izquierdo, text=" 3. Ejecución y Simulación ", padding=10)
        frame_controles.pack(fill=tk.X, pady=(0, 8))

        self.btn_ejecutar = tk.Button(
            frame_controles,
            text="🚀 INICIAR RESCATE",
            command=self.iniciar_rescate,
            bg="#1976D2",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief=tk.RAISED,
            pady=4,
        )
        self.btn_ejecutar.pack(fill=tk.X, pady=(0, 6))

        f_botones_sim = tk.Frame(frame_controles)
        f_botones_sim.pack(fill=tk.X)
        self.btn_pausa = ttk.Button(f_botones_sim, text="⏸ Pausar", command=self.alternar_pausa, state=tk.DISABLED)
        self.btn_pausa.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        self.btn_paso = ttk.Button(f_botones_sim, text="⏭ Paso a Paso", command=self.dar_un_paso, state=tk.DISABLED)
        self.btn_paso.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        self.btn_reiniciar = ttk.Button(
            f_botones_sim, text="⏮ Reiniciar", command=self.reiniciar_animacion, state=tk.DISABLED
        )
        self.btn_reiniciar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        btn_comparar = ttk.Button(
            frame_controles, text="📊 Comparar Todos los Algoritmos", command=self.comparar_todos_algoritmos
        )
        btn_comparar.pack(fill=tk.X, pady=(6, 0))

        # 5. Estadisticas
        frame_stats = ttk.LabelFrame(panel_izquierdo, text=" 5. Estadísticas y Comparación ", padding=8)
        frame_stats.pack(fill=tk.BOTH, expand=True)

        self.txt_estadisticas = tk.Text(
            frame_stats,
            font=("Consolas", 8),
            bg="#212121",
            fg="#E0E0E0",
            wrap=tk.NONE,
            relief=tk.SUNKEN,
            bd=1,
        )
        scroll_y = ttk.Scrollbar(frame_stats, orient=tk.VERTICAL, command=self.txt_estadisticas.yview)
        scroll_x = ttk.Scrollbar(frame_stats, orient=tk.HORIZONTAL, command=self.txt_estadisticas.xview)
        self.txt_estadisticas.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.txt_estadisticas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Panel derecho con el mapa
        panel_derecho = tk.Frame(main_frame, bg=self.COLORES["fondo"])
        panel_derecho.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        frame_marcador = tk.Frame(panel_derecho, bg="#37474F", pady=6, padx=10)
        frame_marcador.pack(fill=tk.X, pady=(0, 6))

        lbl_marcador = tk.Label(
            frame_marcador,
            textvariable=self.var_info_tick,
            font=("Segoe UI", 10, "bold"),
            fg="#ECEFF1",
            bg="#37474F",
        )
        lbl_marcador.pack(side=tk.LEFT)

        frame_leyenda = tk.Frame(frame_marcador, bg="#37474F")
        frame_leyenda.pack(side=tk.RIGHT)
        for texto, col in [
            ("Agente", self.COLORES["agente"]),
            ("Viva", self.COLORES["viva"]),
            ("Rescatada", self.COLORES["rescatada"]),
            ("Muerta", self.COLORES["muerta"]),
            ("Pared", self.COLORES["pared"]),
        ]:
            c_tag = tk.Canvas(frame_leyenda, width=12, height=12, bg=col, highlightthickness=0)
            c_tag.pack(side=tk.LEFT, padx=(6, 2))
            tk.Label(frame_leyenda, text=texto, fg="#FFFFFF", bg="#37474F", font=("Segoe UI", 8)).pack(
                side=tk.LEFT
            )

        self.canvas_mapa = tk.Canvas(
            panel_derecho, bg="#ECEFF1", highlightthickness=1, highlightbackground="#B0BEC5"
        )
        self.canvas_mapa.pack(fill=tk.BOTH, expand=True)
        self.canvas_mapa.bind("<Configure>", lambda e: self.redibujar_mapa())

    def _al_cambiar_algoritmo(self, event=None):
        algo = self.var_algoritmo.get()
        if algo == "A*":
            self.cb_heur.configure(state="readonly")
            self.lbl_heur.configure(fg="#000000")
        else:
            self.cb_heur.configure(state=tk.DISABLED)
            self.lbl_heur.configure(fg="#9E9E9E")

    def _autocargar_archivos_defecto(self):
        if os.path.exists("mapa.txt"):
            self._cargar_mapa_desde_ruta(os.path.abspath("mapa.txt"))
        if os.path.exists("victimas.txt"):
            self._cargar_victimas_desde_ruta(os.path.abspath("victimas.txt"))

    def cargar_archivo_mapa(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar mapa.txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
        )
        if ruta:
            self._cargar_mapa_desde_ruta(ruta)

    def _cargar_mapa_desde_ruta(self, ruta):
        try:
            self.mapa = _cargar_mapa_archivo(ruta)
            self.ruta_mapa = ruta
            filas, columnas = _obtener_dimensiones_mapa(self.mapa)
            self.var_estado_mapa.set(f"✓ {os.path.basename(ruta)} ({filas}x{columnas})")
            self.lbl_mapa_status.configure(fg="#2E7D32")
            self._recrear_problema()
            self.redibujar_mapa()
        except Exception as e:
            messagebox.showerror("Error al cargar mapa", str(e))
            self.var_estado_mapa.set("✗ Error en mapa")
            self.lbl_mapa_status.configure(fg="#C62828")

    def cargar_archivo_victimas(self):
        ruta = filedialog.askopenfilename(
            title="Seleccionar victimas.txt",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")],
        )
        if ruta:
            self._cargar_victimas_desde_ruta(ruta)

    def _cargar_victimas_desde_ruta(self, ruta):
        try:
            self.victimas = cargar_victimas(ruta)
            self.ruta_victimas = ruta
            self.var_estado_victimas.set(f"✓ {os.path.basename(ruta)} ({len(self.victimas)} víctimas)")
            self.lbl_vic_status.configure(fg="#2E7D32")
            self._recrear_problema()
            self.redibujar_mapa()
        except ErrorVictimas as e:
            messagebox.showerror("Error al cargar víctimas", str(e))
            self.var_estado_victimas.set("✗ Error en víctimas")
            self.lbl_vic_status.configure(fg="#C62828")

    def _recrear_problema(self):
        if self.mapa and self.victimas:
            try:
                validar_contra_mapa(self.victimas, self.mapa)
                self.problema = ProblemaRescate(self.mapa, self.victimas)
                self.var_info_tick.set(
                    f"Listo para rescate | {len(self.victimas)} víctimas cargadas | Agente en {self.mapa.inicio}"
                )
            except ErrorVictimas as err:
                messagebox.showerror("Validación Fallida", str(err))
                self.problema = None

    def redibujar_mapa(self):
        self.canvas_mapa.delete("all")
        if not self.mapa:
            self.canvas_mapa.create_text(
                self.canvas_mapa.winfo_width() / 2 or 300,
                self.canvas_mapa.winfo_height() / 2 or 200,
                text="Por favor cargue un archivo mapa.txt",
                fill="#78909C",
                font=("Segoe UI", 12, "italic"),
            )
            return

        canvas_ancho = self.canvas_mapa.winfo_width()
        canvas_alto = self.canvas_mapa.winfo_height()

        filas, cols = _obtener_dimensiones_mapa(self.mapa)

        pad = 20
        ancho_disp = max(canvas_ancho - (pad * 2), 100)
        alto_disp = max(canvas_alto - (pad * 2), 100)

        tam_celda = min(ancho_disp / cols, alto_disp / filas)
        tam_celda = max(tam_celda, 20)

        origen_x = pad + (ancho_disp - (tam_celda * cols)) / 2
        origen_y = pad + (alto_disp - (tam_celda * filas)) / 2

        estado_actual = None
        if self.camino_estados and 0 <= self.paso_actual < len(self.camino_estados):
            estado_actual = self.camino_estados[self.paso_actual]

        # Dibujar casillas
        for r in range(filas):
            for c in range(cols):
                x1 = origen_x + c * tam_celda
                y1 = origen_y + r * tam_celda
                x2 = x1 + tam_celda
                y2 = y1 + tam_celda

                char = _obtener_celda_mapa(self.mapa, r, c)
                if char == "#":
                    color_fondo = self.COLORES["pared"]
                elif (r, c) == self.mapa.inicio:
                    color_fondo = self.COLORES["inicio"]
                else:
                    color_fondo = self.COLORES["libre"]

                self.canvas_mapa.create_rectangle(
                    x1, y1, x2, y2, fill=color_fondo, outline=self.COLORES["borde_celda"], width=1
                )

                if char != "#" and (r, c) == self.mapa.inicio and estado_actual is None:
                    self.canvas_mapa.create_text(
                        (x1 + x2) / 2,
                        (y1 + y2) / 2,
                        text="S",
                        fill="#546E7A",
                        font=("Segoe UI", int(tam_celda * 0.4), "bold"),
                    )

        # Dibujar victimas
        if self.victimas:
            tick_actual = estado_actual.tick if estado_actual else 0
            rescatadas = estado_actual.rescatadas if estado_actual else frozenset()
            vivas = estado_actual.vivas if estado_actual else set(self.victimas.keys())

            for id_v, v in self.victimas.items():
                x1 = origen_x + v.columna * tam_celda
                y1 = origen_y + v.fila * tam_celda
                x2 = x1 + tam_celda
                y2 = y1 + tam_celda

                margin = tam_celda * 0.12
                y_centro = (y1 + y2) / 2
                x_centro = (x1 + x2) / 2

                if id_v in rescatadas:
                    # Victima rescatada
                    self.canvas_mapa.create_rectangle(
                        x1 + margin,
                        y1 + margin,
                        x2 - margin,
                        y2 - margin,
                        fill=self.COLORES["rescatada"],
                        outline="#1B5E20",
                        width=2,
                    )
                    self.canvas_mapa.create_text(
                        x_centro,
                        y_centro - (tam_celda * 0.11),
                        text=f"{id_v} ✓",
                        fill="#FFFFFF",
                        font=("Segoe UI", max(int(tam_celda * 0.19), 9), "bold"),
                    )
                    self.canvas_mapa.create_text(
                        x_centro,
                        y_centro + (tam_celda * 0.15),
                        text="SALVADA",
                        fill="#E8F5E9",
                        font=("Segoe UI", max(int(tam_celda * 0.10), 8), "bold"),
                    )

                elif id_v in vivas and tick_actual <= v.ticks:
                    # Victima viva
                    ticks_restantes = v.ticks - tick_actual
                    self.canvas_mapa.create_rectangle(
                        x1 + margin,
                        y1 + margin,
                        x2 - margin,
                        y2 - margin,
                        fill=self.COLORES["viva"],
                        outline="#E65100",
                        width=2,
                    )
                    self.canvas_mapa.create_text(
                        x_centro,
                        y_centro - (tam_celda * 0.12),
                        text=f"{id_v}",
                        fill="#FFFFFF",
                        font=("Segoe UI", max(int(tam_celda * 0.20), 9), "bold"),
                    )
                    self.canvas_mapa.create_text(
                        x_centro,
                        y_centro + (tam_celda * 0.15),
                        text=f"{ticks_restantes}t",
                        fill="#FFFDE7",
                        font=("Segoe UI", max(int(tam_celda * 0.17), 8), "bold"),
                    )

                else:
                    # Victima muerta
                    self.canvas_mapa.create_rectangle(
                        x1 + margin,
                        y1 + margin,
                        x2 - margin,
                        y2 - margin,
                        fill=self.COLORES["muerta"],
                        outline="#B71C1C",
                        width=2,
                    )
                    self.canvas_mapa.create_text(
                        x_centro,
                        y_centro - (tam_celda * 0.11),
                        text=f"{id_v} ✝",
                        fill="#FFFFFF",
                        font=("Segoe UI", max(int(tam_celda * 0.19), 9), "bold"),
                    )
                    self.canvas_mapa.create_text(
                        x_centro,
                        y_centro + (tam_celda * 0.15),
                        text="0t",
                        fill="#FFCDD2",
                        font=("Segoe UI", max(int(tam_celda * 0.14), 8), "bold"),
                    )

        # Dibujar agente
        pos_agente = (estado_actual.fila, estado_actual.columna) if estado_actual else self.mapa.inicio
        ax1 = origen_x + pos_agente[1] * tam_celda
        ay1 = origen_y + pos_agente[0] * tam_celda
        ax2 = ax1 + tam_celda
        ay2 = ay1 + tam_celda

        ag_margin = tam_celda * 0.18
        self.canvas_mapa.create_oval(
            ax1 + ag_margin,
            ay1 + ag_margin,
            ax2 - ag_margin,
            ay2 - ag_margin,
            fill=self.COLORES["agente"],
            outline="#0D47A1",
            width=3,
        )
        self.canvas_mapa.create_text(
            (ax1 + ax2) / 2,
            (ay1 + ay2) / 2,
            text="A",
            fill="#FFFFFF",
            font=("Segoe UI", int(tam_celda * 0.32), "bold"),
        )

    def iniciar_rescate(self):
        if not self.problema:
            messagebox.showwarning("Atención", "Debe cargar mapa.txt y victimas.txt válidos antes de iniciar.")
            return

        self._detener_animacion()

        algoritmo = self.var_algoritmo.get()
        self.var_info_tick.set(f"Ejecutando {algoritmo}...")
        self.root.update_idletasks()

        if algoritmo == "A*":
            heur_nombre = self.var_heuristica.get()
            if "Real" in heur_nombre:
                heur = h_distancia_real_condenadas
            else:
                heur = h_manhattan_condenadas
            resultado = busqueda_a_estrella(self.problema, heur)
        elif algoritmo == "BFS":
            resultado = busqueda_amplitud(self.problema)
        elif algoritmo == "UCS":
            resultado = busqueda_costo_uniforme(self.problema)
        elif algoritmo == "IDDFS":
            resultado = busqueda_profundidad_iterativa(self.problema)
        else:
            messagebox.showerror("Error", f"Algoritmo '{algoritmo}' no reconocido.")
            return

        self.resultado_actual = resultado
        self.camino_estados = resultado.camino
        self.paso_actual = 0

        self.btn_pausa.configure(state=tk.NORMAL, text="⏸ Pausar")
        self.btn_paso.configure(state=tk.NORMAL)
        self.btn_reiniciar.configure(state=tk.NORMAL)

        self.animando = True
        self._animar_paso()

    def _animar_paso(self):
        if not self.animando:
            return

        if self.paso_actual < len(self.camino_estados):
            self._actualizar_vista_paso()
            self.paso_actual += 1
            delay = self.var_velocidad.get()
            self.id_after_animacion = self.root.after(delay, self._animar_paso)
        else:
            self.animando = False
            self.btn_pausa.configure(text="▶ Reanudar", state=tk.DISABLED)
            self._al_finalizar_simulacion()

    def _actualizar_vista_paso(self):
        estado = self.camino_estados[self.paso_actual]
        accion_desc = ""
        if self.paso_actual > 0 and self.paso_actual - 1 < len(self.resultado_actual.acciones):
            accion_desc = f" | Acción: {self.resultado_actual.acciones[self.paso_actual - 1]}"

        self.var_info_tick.set(
            f"Tick: {estado.tick} / {self.resultado_actual.ticks}{accion_desc} | "
            f"Salvadas: {len(estado.rescatadas)} | "
            f"Fallecidas: {estado.muertas} | "
            f"Vivas pendientes: {len(estado.vivas)}"
        )
        self.redibujar_mapa()

    def alternar_pausa(self):
        if self.animando:
            self._detener_animacion()
            self.btn_pausa.configure(text="▶ Continuar")
        else:
            if self.paso_actual >= len(self.camino_estados):
                self.paso_actual = 0
            self.animando = True
            self.btn_pausa.configure(text="⏸ Pausar")
            self._animar_paso()

    def dar_un_paso(self):
        self._detener_animacion()
        self.btn_pausa.configure(text="▶ Continuar")
        if self.paso_actual < len(self.camino_estados):
            self._actualizar_vista_paso()
            self.paso_actual += 1
            if self.paso_actual >= len(self.camino_estados):
                self._al_finalizar_simulacion()

    def reiniciar_animacion(self):
        self._detener_animacion()
        self.paso_actual = 0
        if self.camino_estados:
            self._actualizar_vista_paso()
        self.btn_pausa.configure(state=tk.NORMAL, text="▶ Continuar")

    def _detener_animacion(self):
        self.animando = False
        if self.id_after_animacion:
            self.root.after_cancel(self.id_after_animacion)
            self.id_after_animacion = None

    def _al_finalizar_simulacion(self):
        res = self.resultado_actual
        if not res:
            return

        res_bfs = busqueda_amplitud(self.problema)
        res_ucs = busqueda_costo_uniforme(self.problema)
        res_iddfs = busqueda_profundidad_iterativa(self.problema)
        res_a_star = busqueda_a_estrella(self.problema, h_distancia_real_condenadas)

        reporte = self._formatear_reporte_completo(res, [res_bfs, res_ucs, res_iddfs, res_a_star])

        self.txt_estadisticas.delete("1.0", tk.END)
        self.txt_estadisticas.insert(tk.END, reporte)

    def comparar_todos_algoritmos(self):
        if not self.problema:
            messagebox.showwarning("Atención", "Cargue mapa.txt y victimas.txt primero.")
            return

        self.var_info_tick.set("Ejecutando comparativa de algoritmos...")
        self.root.update_idletasks()

        res_bfs = busqueda_amplitud(self.problema)
        res_ucs = busqueda_costo_uniforme(self.problema)
        res_iddfs = busqueda_profundidad_iterativa(self.problema)
        res_a_star = busqueda_a_estrella(self.problema, h_distancia_real_condenadas)

        reporte = self._formatear_reporte_completo(res_a_star, [res_bfs, res_ucs, res_iddfs, res_a_star])

        self.txt_estadisticas.delete("1.0", tk.END)
        self.txt_estadisticas.insert(tk.END, reporte)
        self.var_info_tick.set("Comparación finalizada con éxito.")

    def _formatear_reporte_completo(self, res_simulacion, lista_algoritmos):
        sep = "+----------------------------------------------------------+\n"
        salida = []
        salida.append(sep)
        salida.append("| RESULTADO DE LA SIMULACION                               |\n")
        salida.append(f"| Victimas totales   : {self.problema.total:<36}|\n")
        salida.append(f"| Victimas rescatadas: {res_simulacion.rescatadas:<36}|\n")
        salida.append(f"| Victimas fallecidas: {res_simulacion.fallecidas:<36}|\n")
        salida.append(f"| Ticks totales      : {res_simulacion.ticks:<36}|\n")
        salida.append(sep)
        salida.append("| COMPARACION DE ALGORITMOS                                |\n")
        salida.append("| Algoritmo | Nodos | Tiempo  | Rescatadas | Fallecidas    |\n")

        for r in lista_algoritmos:
            tiempo_str = f"{r.tiempo:.4f}s"
            salida.append(
                f"| {r.algoritmo:<9} | {r.expandidos:<5} | {tiempo_str:<7} | {r.rescatadas:<10} | {r.fallecidas:<13} |\n"
            )

        salida.append(sep)
        return "".join(salida)


def main():
    root = tk.Tk()
    app = InterfazRescate(root)
    root.mainloop()


if __name__ == "__main__":
    main()
