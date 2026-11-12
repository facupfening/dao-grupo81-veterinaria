import flet as ft

from interfaz.pantalla import (Dialogo, Pantalla, boton_nuevo, campo_fecha, fila_de_tabla, formulario, id_elegido, lista,
                               opcion, subtitulo, tabla, tarjeta, vaciar)
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
        self.veterinario = lista("Veterinario", al_elegir=self.elegir_veterinario)
        self.mascota = lista("Mascota *")
        self.inicio = campo_fecha("Inicio *")
        self.fin = campo_fecha("Fin *", desde=self.inicio)
        self.tabla = tabla("Inicio", "Fin", "Mascota", "Estado", "Acciones")
        self.dialogo = Dialogo("Nuevo turno", [formulario(self.mascota, self.inicio, self.fin)], self.reservar,
                               texto_boton="Reservar")

    def controles(self):
        return [
            ft.Row(controls=[self.veterinario, boton_nuevo("Nuevo turno", self.nuevo)]),
            tarjeta(
                subtitulo("Turnos del veterinario elegido"),
                ft.Row(controls=[self.tabla], scroll=ft.ScrollMode.AUTO),
            ),
        ]

    def refrescar(self):
        self.mascota.options = [opcion(m["id"], f"{m['nombre']} ({m['responsable']})")
                                for m in self.mascotas.listar_detallado()]
        self.veterinario.options = [opcion(v["id"], f"{v['apellido']}, {v['nombre']}")
                                    for v in self.catalogos.listar_veterinarios()]
        self._mostrar_turnos()

    def elegir_veterinario(self, e):
        self._mostrar_turnos()

    def nuevo(self, e):
        if not self.veterinario.value:
            self._informar_error("Primero elegí el veterinario del turno.")
            return
        vaciar(self.mascota, self.inicio, self.fin)
        nombres = {o.key: o.text for o in self.veterinario.options}
        self._abrir_dialogo(self.dialogo, f"Nuevo turno con {nombres[self.veterinario.value]}")

    def reservar(self, e):
        self._intentar(self._reservar)

    def _reservar(self):
        self.gestor.reservar_turno(id_elegido(self.mascota, "Mascota"), id_elegido(self.veterinario, "Veterinario"),
                                   self.inicio.value, self.fin.value)
        self._informar("Turno reservado.")
        self._cerrar_dialogo()
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
                [ft.IconButton(ft.Icons.CANCEL, tooltip="Cancelar", icon_color=ft.Colors.RED_700,
                               on_click=lambda e, id=t["id"]: self.cancelar(id))]
                if t["estado"] == "Reservado" else [ft.Text("-")],
            )
            for t in self.gestor.listar_turnos(int(self.veterinario.value))
        ]
