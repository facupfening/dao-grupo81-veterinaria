import flet as ft

from interfaz.pantalla import Pantalla, ahora, campo, formulario, id_elegido, lista, opcion, subtitulo
from negocio.gestor_envios import GestorEnvios


class PantallaEmpaquetado(Pantalla):
    titulo = "Empaquetado de muestras"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorEnvios(ruta)
        self.muestras = ft.Column(spacing=2)
        self.conservadora = lista("Conservadora", ancho=340)
        self.responsable = campo("Responsable")
        self.fecha = campo("Fecha (AAAA-MM-DD HH:MM)")

    def controles(self):
        return [
            subtitulo("Muestras extraídas"),
            self.muestras,
            formulario(self.conservadora, self.responsable, self.fecha),
            ft.Row(controls=[ft.Button("Empaquetar y generar remito", on_click=self.empaquetar)]),
        ]

    def refrescar(self):
        self.muestras.controls = [
            ft.Checkbox(
                label=f"{m['codigo']} - {m['analisis']} ({m['temp_min']} a {m['temp_max']} °C) - {m['prioridad']}",
                value=False,
                data=m["id"],
            )
            for m in self.gestor.listar_muestras_para_empaquetar()
        ] or [ft.Text("No hay muestras para empaquetar.")]
        self.conservadora.value = None
        self.conservadora.options = [
            opcion(c["id"], f"{c['codigo']} ({c['temp_min']} a {c['temp_max']} °C, capacidad {c['capacidad']})")
            for c in self.gestor.listar_conservadoras_disponibles()
        ]
        self.fecha.value = ahora()

    def empaquetar(self, e):
        self._intentar(self._empaquetar)

    def _empaquetar(self):
        elegidas = [c.data for c in self.muestras.controls if isinstance(c, ft.Checkbox) and c.value]
        resultado = self.gestor.empaquetar(elegidas, id_elegido(self.conservadora, "Conservadora"), self.fecha.value,
                                           self.responsable.value)
        self.refrescar()
        self._informar(f"Remito {resultado['numero']} emitido con el precinto {resultado['precinto']}.")
