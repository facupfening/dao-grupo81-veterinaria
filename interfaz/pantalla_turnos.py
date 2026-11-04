import flet as ft

from interfaz.pantalla import Pantalla, campo, fila_de_tabla, formulario, id_elegido, lista, opcion, subtitulo, tabla
from negocio.gestor_atencion import GestorAtencion
from negocio.gestor_catalogos import GestorCatalogos
from negocio.gestor_mascotas import GestorMascotas


class PantallaTurnos(Pantalla):
    titulo = "Agenda de turnos"

    def __init__(self, ruta):
        super().__init__()
        self.gestor = GestorAtencion(ruta)
        self.mascotas = GestorMascotas(ruta)
        self.catalogos = GestorCatalogos(ruta)
        self.mascota = lista("Mascota")
        self.veterinario = lista("Veterinario", al_elegir=self.elegir_veterinario)
        self.inicio = campo("Inicio (AAAA-MM-DD HH:MM)", ancho=290)
        self.fin = campo("Fin (AAAA-MM-DD HH:MM)", ancho=290)
        self.tabla = tabla("Inicio", "Fin", "Mascota", "Estado", "Acciones")

    def controles(self):
        return [
            formulario(self.mascota, self.veterinario, self.inicio, self.fin),
            ft.Row(controls=[ft.Button("Reservar turno", on_click=self.reservar)]),
            subtitulo("Turnos del veterinario elegido"),
            ft.Row(controls=[self.tabla], scroll=ft.ScrollMode.AUTO),
        ]

    def refrescar(self):
        self.mascota.options = [opcion(m["id"], f"{m['nombre']} ({m['responsable']})")
                                for m in self.mascotas.listar_detallado()]
        self.veterinario.options = [opcion(v["id"], f"{v['apellido']}, {v['nombre']}")
                                    for v in self.catalogos.listar_veterinarios()]
        self._mostrar_turnos()

    def elegir_veterinario(self, e):
        self._mostrar_turnos()

    def reservar(self, e):
        self._intentar(self._reservar)

    def _reservar(self):
        self.gestor.reservar_turno(id_elegido(self.mascota, "Mascota"), id_elegido(self.veterinario, "Veterinario"),
                                   self.inicio.value, self.fin.value)
        self._informar("Turno reservado.")
        self.inicio.value = ""
        self.fin.value = ""
        self._mostrar_turnos()

    def cancelar(self, id):
        self._intentar(lambda: self._cancelar(id))

    def _cancelar(self, id):
        self.gestor.cancelar_turno(id)
        self._informar("Turno cancelado.")
        self._mostrar_turnos()

    def _mostrar_turnos(self):
        if not self.veterinario.value:
            self.tabla.rows = []
            return
        self.tabla.rows = [
            fila_de_tabla(
                [t["inicio"], t["fin"], t["mascota"], t["estado"]],
                [ft.IconButton(ft.Icons.CANCEL, tooltip="Cancelar", on_click=lambda e, id=t["id"]: self.cancelar(id))]
                if t["estado"] == "Reservado" else [ft.Text("-")],
            )
            for t in self.gestor.listar_turnos(int(self.veterinario.value))
        ]
