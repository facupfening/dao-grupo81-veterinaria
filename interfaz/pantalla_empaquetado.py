import flet as ft

from interfaz.pantalla import (Dialogo, Pantalla, ahora, boton_nuevo, campo, campo_fecha, formulario, id_elegido, lista, opcion,
                               subtitulo, tarjeta, vaciar)
from negocio.gestor_envios import GestorEnvios


class PantallaEmpaquetado(Pantalla):
    titulo = "Empaquetado de muestras"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorEnvios(ruta)
        self.muestras = ft.Column(spacing=2)
        self.conservadora = lista("Conservadora *", ancho=340)
        self.responsable = campo("Responsable *")
        self.fecha = campo_fecha("Fecha y hora *")
        self.dialogo = Dialogo("Nuevo remito", [formulario(self.conservadora, self.responsable, self.fecha)],
                               self.empaquetar, texto_boton="Empaquetar")

    def controles(self):
        return [
            ft.Row(controls=[boton_nuevo("Empaquetar las muestras marcadas", self.nuevo)]),
            tarjeta(subtitulo("Muestras extraídas"), self.muestras),
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

    def nuevo(self, e):
        vaciar(self.conservadora, self.responsable)
        self.fecha.value = ahora()
        self._abrir_dialogo(self.dialogo)

    def empaquetar(self, e):
        self._intentar(self._empaquetar)

    def _empaquetar(self):
        elegidas = [c.data for c in self.muestras.controls if isinstance(c, ft.Checkbox) and c.value]
        resultado = self.gestor.empaquetar(elegidas, id_elegido(self.conservadora, "Conservadora"), self.fecha.value,
                                           self.responsable.value)
        self._cerrar_dialogo()
        self.refrescar()
        self._informar(f"Remito {resultado['numero']} emitido con el precinto {resultado['precinto']}.")
